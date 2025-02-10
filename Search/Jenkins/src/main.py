import asyncio
import sys
import traceback
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from functools import partial

from src.config.settings import JENKINS_SERVERS, BASE_DIR, MAX_CONCURRENT_JOBS, KEYWORDS
from src.factories.client_factory import ClientFactory
from src.models.search_result import SearchResult, CodeMatch, GitInfo, ProjectError
from src.services.excel_service import ExcelService
from src.observers.progress_observer import ProgressObserver
from src.utils.logger import setup_logger
from src.utils.messages import MessageManager as msg
from src.utils.checkpoint import CheckpointManager
from src.utils.memory import MemoryManager

logger = setup_logger()
memory_manager = MemoryManager()

class JenkinsSearchApp:
    def __init__(self):
        self.checkpoint = CheckpointManager()
        self.excel_service = ExcelService(BASE_DIR / "results")
        self.observers = [ProgressObserver()]
        self.results: List[SearchResult] = []
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_JOBS)
        self.keywords = KEYWORDS
        self.processed_count = 0
    
    def notify_observers(self, event_type: str, data: dict) -> None:
        for observer in self.observers:
            observer.update(event_type, data)
    
    async def process_job(self, server: str, job: dict, client) -> Optional[SearchResult]:
        async with self.semaphore:
            start_time = datetime.now()
            try:
                if not self.checkpoint.should_process_job(job['url']):
                    return None
                
                config = await client.get_config_xml(job['url'])
                if not config:
                    return None
                
                matches = []
                for keyword in self.keywords:
                    if keyword.lower() in config.lower():
                        line_number = next(
                            (i + 1 for i, line in enumerate(config.split('\n'))
                            if keyword.lower() in line.lower()),
                            0
                        )
                        if line_number:
                            lines = config.split('\n')
                            start = max(0, line_number - 6)
                            end = min(len(lines), line_number + 5)
                            context = '\n'.join(lines[start:end])
                            matches.append(CodeMatch(
                                keyword=keyword,
                                line_number=line_number,
                                line_content=lines[line_number - 1].strip(),
                                context=context
                            ))
                
                if matches:
                    result = SearchResult(
                        server=server,
                        group=job.get('group', ''),
                        project=job['name'],
                        url=job['url'],
                        matches=matches
                    )
                    
                    self.notify_observers("keyword_found", {
                        "server": server,
                        "project": job['name'],
                        "matches": matches
                    })
                    
                    return result
                
            except Exception as e:
                error_msg = f"Erro ao processar projeto {job['name']}: {str(e)}\n{traceback.format_exc()}"
                logger.error(error_msg)
                msg.error(error_msg)
                return SearchResult(
                    server=server,
                    group=job.get('group', ''),
                    project=job['name'],
                    url=job['url'],
                    matches=[],
                    error=ProjectError(
                        project=job['name'],
                        url=job['url'],
                        error_type=type(e).__name__,
                        error_message=str(e)
                    )
                )
            finally:
                elapsed = (datetime.now() - start_time).total_seconds()
                self.processed_count += 1
                self.notify_observers("project_complete", {
                    "server": server,
                    "project": job['name'],
                    "processed": self.processed_count,
                    "elapsed": elapsed
                })
                await memory_manager.check_memory()
            
            return None
    
    async def process_server(self, server: str) -> List[SearchResult]:
        server_results = []
        try:
            async with ClientFactory.create_client() as client:
                jobs = await client.get_jobs(server)
                total_jobs = len(jobs)
                
                self.notify_observers("start_search", {
                    "server": server,
                    "total_items": total_jobs
                })
                
                # Processa jobs em lotes para melhor controle
                batch_size = 10
                for i in range(0, len(jobs), batch_size):
                    batch = jobs[i:i + batch_size]
                    tasks = [self.process_job(server, job, client) for job in batch]
                    
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for result in batch_results:
                        if isinstance(result, Exception):
                            error_msg = f"Erro em lote: {str(result)}\n{traceback.format_exc()}"
                            logger.error(error_msg)
                            msg.error(error_msg)
                        elif isinstance(result, SearchResult):
                            server_results.append(result)
                
                self.checkpoint.save_checkpoint(server=server)
                
        except Exception as e:
            error_msg = f"Erro ao processar servidor {server}: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            msg.error(error_msg)
        
        return server_results
    
    async def search_servers(self) -> None:
        try:
            tasks = []
            for server in JENKINS_SERVERS:
                if self.checkpoint.should_process_server(server):
                    tasks.append(self.process_server(server))
            
            if not tasks:
                msg.info("Todos os servidores já foram processados")
                return
            
            results = []
            for task in asyncio.as_completed(tasks):
                try:
                    server_results = await task
                    results.extend(server_results)
                except Exception as e:
                    error_msg = f"Erro ao processar resultados: {str(e)}\n{traceback.format_exc()}"
                    logger.error(error_msg)
                    msg.error(error_msg)
            
            self.results = results
            
            if self.results:
                try:
                    await self.excel_service.save_results(self.results)
                except Exception as e:
                    error_msg = f"Erro ao salvar resultados: {str(e)}\n{traceback.format_exc()}"
                    logger.error(error_msg)
                    msg.error(error_msg)
            
            self.notify_observers("search_complete", {
                "matches_found": sum(len(r.matches) for r in self.results)
            })
            
        except KeyboardInterrupt:
            msg.warning("Pesquisa interrompida pelo usuário. Progresso salvo.")
            sys.exit(1)
        except Exception as e:
            error_msg = f"Erro fatal: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            msg.error(error_msg)
            sys.exit(1)

async def main() -> None:
    try:
        app = JenkinsSearchApp()
        await app.search_servers()
    except Exception as e:
        error_msg = f"Erro na aplicação: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        msg.error(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())