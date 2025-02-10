import logging
from pathlib import Path
from datetime import datetime

class LogObserver:
    VERDE = '\033[92m'
    VERMELHO = '\033[91m'
    AMARELO = '\033[93m'
    AZUL = '\033[94m'
    RESET = '\033[0m'

    def __init__(self):
        self.logger = logging.getLogger('gitlab_scanner')
        self.logger.setLevel(logging.INFO)
        
        self.logger.handlers.clear()
        
        formatador = logging.Formatter(
            '[%(asctime)s] %(message)s',
            datefmt='%d/%m/%Y %H:%M:%S'
        )
        
        console = logging.StreamHandler()
        console.setFormatter(formatador)
        self.logger.addHandler(console)
        
        diretorio_log = Path('log')
        diretorio_log.mkdir(exist_ok=True)
        manipulador_arquivo = logging.FileHandler('log/scanner.log')
        manipulador_arquivo.setFormatter(formatador)
        self.logger.addHandler(manipulador_arquivo)
    
    def info(self, mensagem: str):
        self.logger.info(mensagem)
    
    def info_blue(self, mensagem: str):
        self.logger.info(f"{self.AZUL}{mensagem}{self.RESET}")
    
    def success(self, mensagem: str):
        self.logger.info(f"{self.VERDE}{mensagem}{self.RESET}")
    
    def warning(self, mensagem: str):
        self.logger.warning(f"{self.AMARELO}{mensagem}{self.RESET}")
    
    def error(self, mensagem: str):
        mensagem = mensagem.replace('error:', '').replace('Error:', '').strip()
        self.logger.error(f"{self.VERMELHO}{mensagem}{self.RESET}")