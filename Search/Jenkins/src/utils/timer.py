import time
from functools import wraps
from src.utils.logger import setup_logger

logger = setup_logger()

def timer_decorator(func):
    """Decorator para medir o tempo de execução das funções."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger.info(f"Iniciando {func.__name__}...")
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Finalizado {func.__name__} em {duration:.2f} segundos")
        
        return result
    return wrapper