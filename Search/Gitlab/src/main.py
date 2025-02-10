import asyncio
import gc
from concurrent.futures import ThreadPoolExecutor
from src.scanner import GitLabScanner
from src.checkpoint import CheckpointService
from src.logger import LogObserver
from time import time
from urllib3.exceptions import ProtocolError
from http.client import RemoteDisconnected
from src.config import SETTINGS

class ScannerApplication:
    def __init__(self, url: str, token: str):
        self.logger = LogObserver()
        self.checkpoint = CheckpointService()
        self.executor = ThreadPoolExecutor(max_workers=int(SETTINGS.get('MAX_THREADS')))
        self.scanner = GitLabScanner(url, token, self.checkpoint, self.logger, self.executor)

    async def run(self) -> int:
        tempo_inicio = time()
        
        try:
            self.logger.info_blue("=" * 80)
            self.logger.info_blue("GitLab Scanner - Busca de palavras-chave em repositórios")
            self.logger.info_blue("=" * 80)
            self.logger.info_blue("Desenvolvido por Leandro Marcos Moreira")
            self.logger.info_blue("-" * 80)
            self.logger.info_blue("Configurações carregadas:")
            self.logger.info_blue("  - URL do GitLab: " + self.scanner.gl.url)
            self.logger.info_blue("  - Palavras-chave: " + ", ".join(self.scanner.keywords))
            self.logger.info_blue("  - Timeout da API: " + str(self.scanner.gl.timeout) + "s")
            self.logger.info_blue("  - Itens por página: " + str(self.scanner.gl.per_page))
            self.logger.info_blue("-" * 80)
            self.logger.info_blue("Iniciando scanner...")
            self.logger.info_blue("-" * 80)
            
            await self.scanner.scan()
            self.logger.info("=" * 80)
            self.logger.info(f"Scanner finalizado em {time() - tempo_inicio:.2f}s")
            self.logger.info("=" * 80)
            return 0
        except KeyboardInterrupt:
            self.logger.info("\nScanner interrompido pelo usuário")
            return 1
        except (ProtocolError, RemoteDisconnected) as e:
            self.logger.error(f"Falha de conexão com o GitLab: {str(e)}")
            return 1
        except Exception as e:
            self.logger.error(f"Falha ao executar scanner: {str(e)}")
            return 1
        finally:
            self.executor.shutdown(wait=True)
            gc.collect()

if __name__ == "__main__":
    import os
    from datetime import datetime
    
    url = os.environ.get('GITLAB_URL')
    token = os.environ.get('PRIVATE_TOKEN')
    
    if not url or not token:
        print("[{}] GITLAB_URL e PRIVATE_TOKEN são obrigatórios".format(
            datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        ))
        exit(1)
        
    app = ScannerApplication(url, token)
    exit(asyncio.run(app.run()))