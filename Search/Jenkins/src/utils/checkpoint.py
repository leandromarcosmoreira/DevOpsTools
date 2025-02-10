import json
from pathlib import Path
from typing import Dict, Any
from src.config.settings import CACHE_DIR
from src.utils.logger import setup_logger

logger = setup_logger()

class CheckpointManager:
    def __init__(self):
        self.checkpoint_file = CACHE_DIR / "checkpoint.json"
        self.current_state = self._load_checkpoint()
    
    def _load_checkpoint(self) -> Dict[str, Any]:
        """Carrega o último checkpoint salvo."""
        if self.checkpoint_file.exists():
            try:
                return json.loads(self.checkpoint_file.read_text())
            except Exception as e:
                logger.error(f"Erro ao carregar checkpoint: {str(e)}")
        return {
            'servers_processed': [],
            'jobs_processed': [],
            'last_server': None,
            'last_job': None
        }
    
    def save_checkpoint(self, server: str = None, job: str = None):
        """Salva o progresso atual."""
        try:
            if server and server not in self.current_state['servers_processed']:
                self.current_state['servers_processed'].append(server)
                self.current_state['last_server'] = server
            
            if job and job not in self.current_state['jobs_processed']:
                self.current_state['jobs_processed'].append(job)
                self.current_state['last_job'] = job
            
            self.checkpoint_file.write_text(json.dumps(self.current_state))
            logger.debug(f"Checkpoint salvo: Servidor={server}, Job={job}")
        except Exception as e:
            logger.error(f"Erro ao salvar checkpoint: {str(e)}")
    
    def clear_checkpoint(self):
        """Limpa o checkpoint atual."""
        try:
            if self.checkpoint_file.exists():
                self.checkpoint_file.unlink()
            self.current_state = self._load_checkpoint()
            logger.info("Checkpoint limpo com sucesso")
        except Exception as e:
            logger.error(f"Erro ao limpar checkpoint: {str(e)}")
    
    def should_process_server(self, server: str) -> bool:
        """Verifica se o servidor deve ser processado."""
        return server not in self.current_state['servers_processed']
    
    def should_process_job(self, job: str) -> bool:
        """Verifica se o job deve ser processado."""
        return job not in self.current_state['jobs_processed']
    
    @property
    def has_checkpoint(self) -> bool:
        """Verifica se existe um checkpoint salvo."""
        return bool(self.current_state['servers_processed'] or self.current_state['jobs_processed'])