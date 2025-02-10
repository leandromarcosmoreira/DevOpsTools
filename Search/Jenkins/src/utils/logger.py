import logging
from logging.handlers import RotatingFileHandler
import sys
from pathlib import Path
from src.config.settings import LOG_DIR, LOG_FILE, LOG_FORMAT, LOG_DATE_FORMAT, LOG_MAX_SIZE, LOG_BACKUP_COUNT, LOG_LEVEL

def setup_logger(name: str = __name__):
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Formatador para arquivo - detalhado
    file_formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
    
    # Formatador para console - simplificado
    console_formatter = logging.Formatter('%(message)s')
    
    # Handler para arquivo
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=LOG_MAX_SIZE,
        backupCount=LOG_BACKUP_COUNT
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)
    
    # Filtro para mensagens do console
    class ConsoleFilter(logging.Filter):
        def filter(self, record):
            # Filtra mensagens de debug e mensagens repetitivas
            if record.levelno < logging.INFO:
                return False
            if any(msg in record.msg for msg in [
                'Iniciando get_',
                'Finalizado get_',
                'Erro ao gravar cache',
                'ProcessPoolExecutor'
            ]):
                return False
            return True
    
    console_handler.addFilter(ConsoleFilter())
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger