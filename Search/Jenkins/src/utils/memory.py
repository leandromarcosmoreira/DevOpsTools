import gc
import psutil
import asyncio
from typing import Optional
from src.config.settings import MEMORY_LIMIT
from src.utils.logger import setup_logger

logger = setup_logger()

class MemoryManager:
    def __init__(self, threshold: float = 0.8):
        self.threshold = threshold
        self.process = psutil.Process()
        self._last_collection = 0
        self._collection_interval = 60  # segundos
    
    def get_memory_usage(self) -> float:
        """Retorna o uso atual de memória em bytes."""
        return self.process.memory_info().rss
    
    def get_memory_percent(self) -> float:
        """Retorna o percentual de uso de memória."""
        return self.process.memory_percent()
    
    async def force_collection(self):
        """Força coleta de lixo e libera memória."""
        logger.debug("Iniciando coleta de lixo forçada")
        
        # Coleta gerações mais antigas primeiro
        gc.collect(2)
        await asyncio.sleep(0)  # Permite que outras corotinas executem
        
        gc.collect(1)
        await asyncio.sleep(0)
        
        gc.collect(0)
        await asyncio.sleep(0)
        
        # Tenta liberar memória do sistema
        if hasattr(psutil, "Process"):
            try:
                self.process.memory_info()
            except Exception as e:
                logger.error(f"Erro ao liberar memória: {str(e)}")
        
        self._last_collection = asyncio.get_event_loop().time()
        logger.debug("Coleta de lixo concluída")
    
    async def check_memory(self, force: bool = False):
        """Verifica uso de memória e realiza coleta se necessário."""
        current_time = asyncio.get_event_loop().time()
        
        # Verifica se deve realizar coleta
        should_collect = (
            force or
            self.get_memory_usage() > MEMORY_LIMIT * self.threshold or
            current_time - self._last_collection > self._collection_interval
        )
        
        if should_collect:
            memory_before = self.get_memory_usage()
            await self.force_collection()
            memory_after = self.get_memory_usage()
            
            memory_freed = memory_before - memory_after
            if memory_freed > 0:
                logger.info(f"Memória liberada: {memory_freed / 1024 / 1024:.2f} MB")