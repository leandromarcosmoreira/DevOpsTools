import urllib.request
import urllib.error
import base64
import json
import time
import aiohttp
import asyncio
import gc
import traceback
from typing import Dict, List, Optional, Set
from contextlib import asynccontextmanager
from src.config.settings import (
    USERNAME, API_TOKEN, MAX_CONCURRENT_CONNECTIONS,
    CONNECTION_TIMEOUT, KEEPALIVE_TIMEOUT, CACHE_MAX_SIZE,
    RETRY_DELAY, MAX_RETRIES
)
from src.utils.logger import setup_logger
from src.utils.cache import Cache
from src.utils.memory import MemoryManager
from src.utils.messages import MessageManager as msg

logger = setup_logger()
cache = Cache(max_size=CACHE_MAX_SIZE)
memory_manager = MemoryManager()

class JenkinsClient:
    def __init__(self):
        auth_string = f"{USERNAME}:{API_TOKEN}"
        self.auth_header = f"Basic {base64.b64encode(auth_string.encode()).decode()}"
        self.session = None
        self.connection_semaphore = asyncio.Semaphore(MAX_CONCURRENT_CONNECTIONS)
        self._server_jobs_cache = {}
        self._folder_jobs_cache = {}
        self._config_cache = {}
        
    async def __aenter__(self):
        try:
            connector = aiohttp.TCPConnector(
                limit=MAX_CONCURRENT_CONNECTIONS,
                ttl_dns_cache=300,
                keepalive_timeout=KEEPALIVE_TIMEOUT,
                force_close=False,
                enable_cleanup_closed=True
            )
            timeout = aiohttp.ClientTimeout(
                total=CONNECTION_TIMEOUT,
                connect=10,
                sock_read=10
            )
            self.session = aiohttp.ClientSession(
                headers={'Authorization': self.auth_header},
                connector=connector,
                timeout=timeout,
                trust_env=True
            )
            return self
        except Exception as e:
            error_msg = f"Erro ao criar sessão Jenkins: {str(e)}\nDetalhes: {traceback.format_exc()}"
            logger.error(error_msg)
            msg.error(error_msg)
            raise
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            try:
                await self.session.close()
            except Exception as e:
                logger.error(f"Erro ao fechar sessão: {str(e)}")
            finally:
                self.session = None
                gc.collect()
    
    @asynccontextmanager
    async def _managed_request(self, url: str):
        for attempt in range(MAX_RETRIES):
            try:
                async with self.connection_semaphore:
                    async with self.session.get(url) as response:
                        if response.status == 401:
                            error_msg = "Erro de autenticação. Verifique suas credenciais Jenkins."
                            logger.error(error_msg)
                            msg.error(error_msg)
                            raise aiohttp.ClientError(error_msg)
                            
                        if response.status == 403:
                            error_msg = "Acesso negado. Verifique suas permissões no Jenkins."
                            logger.error(error_msg)
                            msg.error(error_msg)
                            raise aiohttp.ClientError(error_msg)
                            
                        if response.status == 404:
                            error_msg = f"URL não encontrada: {url}"
                            logger.error(error_msg)
                            msg.error(error_msg)
                            raise aiohttp.ClientError(error_msg)
                            
                        if response.status == 429:  # Rate limit
                            retry_after = int(response.headers.get('Retry-After', RETRY_DELAY))
                            msg.warning(f"Rate limit atingido. Aguardando {retry_after}s...")
                            await asyncio.sleep(retry_after)
                            continue
                            
                        if response.status >= 500:
                            error_msg = f"Erro no servidor Jenkins: {response.status}"
                            logger.error(error_msg)
                            msg.error(error_msg)
                            if attempt < MAX_RETRIES - 1:
                                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                                continue
                            raise aiohttp.ClientError(error_msg)
                            
                        response.raise_for_status()
                        yield response
                        break
                        
            except aiohttp.ClientError as e:
                error_msg = f"Erro de conexão em {url}: {str(e)}"
                if attempt < MAX_RETRIES - 1:
                    msg.warning(f"{error_msg} - Tentativa {attempt + 1} de {MAX_RETRIES}")
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                    continue
                logger.error(f"{error_msg}\nDetalhes: {traceback.format_exc()}")
                msg.error(error_msg)
                raise
            except Exception as e:
                error_msg = f"Erro inesperado em {url}: {str(e)}\nDetalhes: {traceback.format_exc()}"
                logger.error(error_msg)
                msg.error(error_msg)
                raise
    
    async def get_json(self, url: str) -> Dict:
        cache_key = f"json_{url}"
        cached_data = await cache.aget(cache_key)
        
        if cached_data:
            return cached_data
            
        try:
            async with self._managed_request(f"{url.rstrip('/')}/api/json") as response:
                data = await response.json()
                await cache.aset(cache_key, data)
                return data
        except json.JSONDecodeError as e:
            error_msg = f"Erro ao decodificar JSON de {url}: {str(e)}"
            logger.error(error_msg)
            msg.error(error_msg)
            raise
        finally:
            await memory_manager.check_memory()
    
    async def get_config_xml(self, url: str) -> Optional[str]:
        if url in self._config_cache:
            return self._config_cache[url]
            
        cache_key = f"xml_{url}"
        cached_data = await cache.aget(cache_key)
        
        if cached_data:
            self._config_cache[url] = cached_data
            return cached_data
            
        try:
            async with self._managed_request(f"{url.rstrip('/')}/config.xml") as response:
                data = await response.text()
                if not data:
                    logger.warning(f"Config XML vazio para {url}")
                    return None
                await cache.aset(cache_key, data)
                self._config_cache[url] = data
                return data
        except Exception as e:
            error_msg = f"Erro ao obter config.xml de {url}: {str(e)}\nDetalhes: {traceback.format_exc()}"
            logger.error(error_msg)
            msg.error(error_msg)
            return None
        finally:
            await memory_manager.check_memory()

    async def _get_folder_jobs(self, folder_url: str, parent_path: str = "") -> List[Dict]:
        """Obtém recursivamente todos os jobs dentro de uma pasta Jenkins."""
        if folder_url in self._folder_jobs_cache:
            return self._folder_jobs_cache[folder_url]

        try:
            data = await self.get_json(folder_url)
            jobs = []

            if not data or 'jobs' not in data:
                logger.warning(f"Pasta vazia ou inválida: {folder_url}")
                return []

            for job in data['jobs']:
                job_class = job.get('_class', '')
                job_name = job.get('name', '')
                job_url = job.get('url', '')

                # Define o caminho completo do job
                current_path = f"{parent_path}/{job_name}" if parent_path else job_name

                if job_class.endswith('WorkflowJob'):
                    jobs.append({
                        'name': job_name,
                        'url': job_url,
                        'group': parent_path
                    })
                elif job_class.endswith('Folder'):
                    # Processa recursivamente os jobs da subpasta
                    sub_jobs = await self._get_folder_jobs(job_url, current_path)
                    jobs.extend(sub_jobs)

            self._folder_jobs_cache[folder_url] = jobs
            return jobs

        except Exception as e:
            error_msg = f"Erro ao processar pasta {folder_url}: {str(e)}\nDetalhes: {traceback.format_exc()}"
            logger.error(error_msg)
            msg.error(error_msg)
            return []
    
    async def get_jobs(self, server: str) -> List[Dict]:
        if server in self._server_jobs_cache:
            return self._server_jobs_cache[server]
            
        all_jobs = []
        try:
            data = await self.get_json(server)
            
            if not data:
                error_msg = f"Nenhum dado retornado do servidor {server}"
                logger.error(error_msg)
                msg.error(error_msg)
                return []
            
            if 'jobs' not in data:
                error_msg = f"Estrutura de dados inválida do servidor {server}"
                logger.error(error_msg)
                msg.error(error_msg)
                return []
            
            tasks = []
            for job in data['jobs']:
                if job.get('_class', '').endswith('WorkflowJob'):
                    all_jobs.append({
                        'name': job['name'],
                        'url': job['url'],
                        'group': ''
                    })
                elif job.get('_class', '').endswith('Folder'):
                    tasks.append(self._get_folder_jobs(job['url']))
            
            if tasks:
                folder_jobs_list = await asyncio.gather(*tasks, return_exceptions=True)
                for result in folder_jobs_list:
                    if isinstance(result, Exception):
                        error_msg = f"Erro ao processar pasta: {str(result)}\nDetalhes: {traceback.format_exc()}"
                        logger.error(error_msg)
                        msg.error(error_msg)
                    else:
                        all_jobs.extend(result)
            
            self._server_jobs_cache[server] = all_jobs
            return all_jobs
            
        except aiohttp.ClientError as e:
            error_msg = f"Erro de conexão com {server}: {str(e)}\nDetalhes: {traceback.format_exc()}"
            logger.error(error_msg)
            msg.error(error_msg)
            return []
        except Exception as e:
            error_msg = f"Erro ao obter projetos de {server}: {str(e)}\nDetalhes: {traceback.format_exc()}"
            logger.error(error_msg)
            msg.error(error_msg)
            return []