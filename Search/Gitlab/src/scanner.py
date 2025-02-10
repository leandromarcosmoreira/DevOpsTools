import asyncio
import gc
import traceback
import re
from typing import List, Dict, Any, Set
from time import time
import gitlab
from concurrent.futures import ThreadPoolExecutor
from collections import OrderedDict
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from urllib3.exceptions import ProtocolError
from http.client import RemoteDisconnected
from requests.exceptions import ConnectionError, ReadTimeout
from src.config import (
    RETRY_ATTEMPTS, RETRY_WAIT_MULTIPLIER, RETRY_WAIT_MIN, RETRY_WAIT_MAX,
    TIMEOUT_API_GITLAB, PER_PAGE, KEYWORDS, CACHE_MAX_SIZE, BINARY_EXTENSIONS,
    SETTINGS, BATCH_SIZE
)

class GitLabScanner:
    def __init__(self, url: str, token: str, checkpoint, logger, executor):
        self.gl = gitlab.Gitlab(url=url, private_token=token, per_page=PER_PAGE, timeout=TIMEOUT_API_GITLAB)
        self.checkpoint = checkpoint
        self.logger = logger
        self.executor = executor
        self.keywords = KEYWORDS
        self.cache = OrderedDict()
        self.cache_size = CACHE_MAX_SIZE
        self.branch_patterns = [re.compile(pattern) for pattern in SETTINGS.get('BRANCH_PATTERNS', '').split(',')]

    def _is_binary_file(self, file_path: str) -> bool:
        ext = file_path[file_path.rfind('.'):].lower() if '.' in file_path else ''
        return ext in BINARY_EXTENSIONS

    def _is_branch_relevant(self, branch_name: str) -> bool:
        return any(pattern.match(branch_name) for pattern in self.branch_patterns)

    async def scan(self):
        try:
            projects = self.gl.projects.list(all=True)
            pending_projects = [p for p in projects if not self.checkpoint.is_project_completed(p.id)]
            
            self.logger.info(f"Total de projetos pendentes: {len(pending_projects)}")
            
            # Processa projetos em paralelo usando o ThreadPoolExecutor
            loop = asyncio.get_event_loop()
            tasks = []
            
            for project in pending_projects:
                # Submete cada projeto para uma thread dedicada
                task = loop.run_in_executor(
                    self.executor,
                    self._scan_project_sync,
                    project
                )
                tasks.append(task)
            
            # Aguarda a conclusão de todos os projetos
            await asyncio.gather(*tasks)
            
        except Exception as e:
            self.logger.error(f"Falha ao executar scanner: {str(e)}\n{traceback.format_exc()}")

    def _scan_project_sync(self, project):
        """Versão síncrona do scan de projeto para execução em thread"""
        try:
            project_start = time()
            
            # Obtém e filtra branches
            all_branches = project.branches.list(all=True)
            total_branches = len(all_branches)
            
            relevant_branches = [b for b in all_branches if self._is_branch_relevant(b.name)]
            pending_branches = [b for b in relevant_branches if not self.checkpoint.is_branch_completed(project.id, b.name)]
            
            if pending_branches:
                self.logger.info(
                    f"Projeto: {project.name} | "
                    f"Serão analisadas {len(pending_branches)} de {total_branches} branches existentes no projeto"
                )
                
                # Processa cada branch sequencialmente dentro da thread do projeto
                for branch in pending_branches:
                    self._scan_branch_sync(project, branch.name)
            
            self.checkpoint.mark_project_completed(project.id)
            self.logger.info(f"Projeto: {project.name} | Análise concluída ({time() - project_start:.2f}s)")
            
        except Exception as e:
            self.logger.error(f"Projeto: {project.name} | Falha na análise: {str(e)}\n{traceback.format_exc()}")

    def _scan_branch_sync(self, project, branch):
        """Versão síncrona do scan de branch"""
        try:
            branch_start = time()
            self.logger.info(f"Projeto: {project.name} | Branch: {branch} | Iniciando análise...")
            
            items = project.repository_tree(ref=branch, recursive=True, all=True)
            files = [item for item in items if item["type"] == "blob"]
            
            # Processa arquivos em lotes
            for i in range(0, len(files), BATCH_SIZE):
                file_batch = files[i:i + BATCH_SIZE]
                
                for file_info in file_batch:
                    if not self.checkpoint.is_file_completed(project.id, branch, file_info['path']):
                        self._scan_file_sync(project, branch, file_info)
            
            self.checkpoint.mark_branch_completed(project.id, branch)
            self.logger.info(f"Projeto: {project.name} | Branch: {branch} | Análise concluída ({time() - branch_start:.2f}s)")
            
        except Exception as e:
            self.logger.error(f"Projeto: {project.name} | Branch: {branch} | Falha na análise: {str(e)}")

    def _scan_file_sync(self, project, branch, file_info):
        try:
            if self._is_binary_file(file_info['path']):
                self.checkpoint.mark_file_completed(project.id, branch, file_info['path'])
                return

            file_content = project.files.get(file_path=file_info['path'], ref=branch)
            content = file_content.decode()
            
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='ignore')
            
            matches = [keyword for keyword in self.keywords if keyword in content]
            if matches:
                self.logger.success(
                    f"Projeto: {project.name} | Branch: {branch} | "
                    f"Arquivo: {file_info['path']} | Matches: {', '.join(matches)}"
                )
            
            self.checkpoint.mark_file_completed(project.id, branch, file_info['path'])
                
        except Exception as e:
            if not isinstance(e, gitlab.exceptions.GitlabGetError) or e.response_code != 404:
                self.logger.error(
                    f"Projeto: {project.name} | Branch: {branch} | "
                    f"Arquivo: {file_info['path']} | Erro: {str(e)}"
                )