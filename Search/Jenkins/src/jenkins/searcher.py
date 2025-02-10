import asyncio
from typing import List, Dict
from functools import partial
import itertools
from src.config.settings import (
    KEYWORDS, MAX_WORKERS, MAX_PROCESSES, 
    CHUNK_SIZE, MAX_CONTEXT_LINES
)
from src.utils.logger import setup_logger
from src.utils.timer import timer_decorator
from src.utils.checkpoint import CheckpointManager
from src.models.search_result import SearchResult, CodeMatch
from src.jenkins.client import JenkinsClient

logger = setup_logger(__name__)

class JenkinsSearcher:
    def __init__(self):
        self.checkpoint = CheckpointManager()
        self.lines_cache = []
    
    def _search_chunk(self, chunk: List[tuple], keywords: List[str]) -> List[Dict]:
        matches = []
        for i, line in chunk:
            for keyword in keywords:
                if keyword.lower() in line.lower():
                    start_idx = max(0, i - MAX_CONTEXT_LINES)
                    end_idx = i + MAX_CONTEXT_LINES + 1
                    context_lines = self.lines_cache[start_idx:end_idx]
                    matches.append(CodeMatch(
                        keyword=keyword,
                        line_number=i + 1,
                        line_content=line.strip(),
                        context='\n'.join(line.strip() for line in context_lines)
                    ))
        return matches
    
    @timer_decorator
    async def process_job(self, server: str, group: str, job: dict, client: JenkinsClient) -> SearchResult:
        try:
            if not self.checkpoint.should_process_job(job['url']):
                return None
            
            config = await client.get_config_xml(job['url'])
            self.lines_cache = config.split('\n')
            
            chunks = list(zip(range(len(self.lines_cache)), self.lines_cache))
            chunk_size = max(1, len(chunks) // MAX_PROCESSES)
            chunks = [chunks[i:i + chunk_size] for i in range(0, len(chunks), chunk_size)]
            
            matches = []
            for chunk in chunks:
                chunk_matches = self._search_chunk(chunk, KEYWORDS)
                matches.extend(chunk_matches)
                
            if matches:
                logger.info(f"Encontradas {len(matches)} ocorrências em {job['name']}")
                return SearchResult(
                    server=server,
                    group=group,
                    project=job['name'],
                    url=job['url'],
                    matches=matches
                )
                
            self.checkpoint.save_checkpoint(job=job['url'])
            
        except Exception as e:
            logger.error(f"Erro ao processar projeto {job['name']}")
        
        return None