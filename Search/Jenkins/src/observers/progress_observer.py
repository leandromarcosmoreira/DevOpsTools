from typing import Dict, Any, Set
from datetime import datetime
from collections import defaultdict
import asyncio
from src.utils.messages import MessageManager as msg

class ProgressObserver:
    """Monitora e exibe o progresso da busca nos servidores Jenkins"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.processed_items = defaultdict(int)
        self.total_items = defaultdict(int)
        self.matches_count = 0
        self.keywords_by_server = defaultdict(set)
        self.projects_by_server = defaultdict(set)
        self.matches_by_server = defaultdict(lambda: defaultdict(list))
        self.errors_by_server = defaultdict(list)
        self._progress_shown = set()
        self.server_start_times = {}
        self.project_times = defaultdict(dict)
        self.keyword_times = defaultdict(dict)
    
    def update(self, event_type: str, data: Dict[str, Any]):
        """Atualiza o estado do observador com base nos eventos recebidos"""
        
        if event_type == "start_search":
            server = data.get("server", "")
            total = data.get("total_items", 0)
            if server:
                self.total_items[server] = total
                self.server_start_times[server] = datetime.now()
                msg.info(f"Iniciando busca em {server}: {total} projetos")
        
        elif event_type == "project_complete":
            server = data.get("server", "")
            project = data.get("project", "")
            elapsed = data.get("elapsed", 0.0)
            
            if server and project:
                self.project_times[server][project] = elapsed
            
            if server and server not in self._progress_shown:
                self.processed_items[server] += 1
                current = self.processed_items[server]
                total = self.total_items[server]
                
                if current == total:
                    elapsed = datetime.now() - self.server_start_times[server]
                    elapsed_seconds = elapsed.total_seconds()
                    msg.progress(current, total, f"Projetos analisados em {server}", elapsed_seconds)
                    self._progress_shown.add(server)
        
        elif event_type == "keyword_found":
            server = data.get('server', '')
            project = data.get('project', '')
            matches = data.get('matches', [])
            elapsed = data.get('elapsed', 0.0)
            
            if server and project:
                self.projects_by_server[server].add(project)
                for match in matches:
                    keyword = match.keyword
                    self.keywords_by_server[server].add(keyword)
                    self.matches_by_server[server][keyword].append({
                        'project': project,
                        'line': match.line_number,
                        'content': match.line_content,
                        'elapsed': elapsed
                    })
                    self.matches_count += 1
                    
                    if keyword not in self.keyword_times[server]:
                        self.keyword_times[server][keyword] = 0.0
                    self.keyword_times[server][keyword] += elapsed
        
        elif event_type == "search_complete":
            msg.info("Resumo por servidor:")
            
            for server in sorted(self.keywords_by_server.keys()):
                if server in self.server_start_times:
                    elapsed = datetime.now() - self.server_start_times[server]
                    elapsed_seconds = elapsed.total_seconds()
                    msg.info(f"Servidor: {server} ({elapsed_seconds:.2f}s)")
                
                for keyword in sorted(self.keywords_by_server[server]):
                    matches = self.matches_by_server[server][keyword]
                    projects = sorted({m['project'] for m in matches})
                    total_projects = self.total_items[server]
                    msg.info("------------------------------------------------------------")
                    msg.info(f"{keyword}: ({len(matches)} ocorrências em {total_projects} projetos)")
                    msg.info("------------------------------------------------------------")
                    msg.info("Projetos:")
                    for project in projects:
                        project_time = self.project_times[server].get(project, 0.0)
                        msg.info(f"  - {project} ({project_time:.2f}s)")
            
            total_elapsed = datetime.now() - self.start_time
            total_seconds = total_elapsed.total_seconds()
            msg.info("------------------------------------------------------------")
            msg.info(f"Tempo total de execução: {total_seconds:.2f}s")
            msg.info("------------------------------------------------------------")