import json
import time
import asyncio
import os
from pathlib import Path
from typing import Any, Dict, Optional
from src.config.settings import CACHE_DIR, CACHE_DURATION, CACHE_MAX_SIZE
from src.utils.logger import setup_logger

logger = setup_logger()

class Cache:
    def __init__(self, max_size: int = CACHE_MAX_SIZE):
        self.max_size = max_size
        self.current_size = 0
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.lock = asyncio.Lock()
        self._ensure_cache_dir()
        
    def _ensure_cache_dir(self):
        """Garante que o diretório de cache existe."""
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Erro ao criar diretório de cache: {str(e)}")
    
    def _get_cache_path(self, key: str) -> Path:
        """Retorna o caminho do arquivo de cache para a chave fornecida."""
        # Sanitiza a chave para um nome de arquivo válido
        safe_key = "".join(c if c.isalnum() else "_" for c in key)
        return CACHE_DIR / f"{safe_key}.json"
    
    async def _check_size(self):
        """Verifica e gerencia o tamanho do cache."""
        if self.current_size > self.max_size:
            async with self.lock:
                # Remove itens mais antigos até atingir 80% do limite
                target_size = int(self.max_size * 0.8)
                items = sorted(
                    self.cache.items(),
                    key=lambda x: x[1]['timestamp']
                )
                
                for key, _ in items:
                    if self.current_size <= target_size:
                        break
                    await self.adelete(key)
    
    async def aget(self, key: str) -> Optional[Any]:
        """Recupera dados do cache de forma assíncrona."""
        async with self.lock:
            if key in self.cache:
                data = self.cache[key]
                if time.time() - data['timestamp'] <= CACHE_DURATION:
                    return data['value']
                await self.adelete(key)
            
            cache_file = self._get_cache_path(key)
            if cache_file.exists():
                try:
                    data = json.loads(cache_file.read_text())
                    if time.time() - data['timestamp'] <= CACHE_DURATION:
                        self.cache[key] = data
                        self.current_size += len(json.dumps(data))
                        await self._check_size()
                        return data['value']
                    cache_file.unlink()
                except Exception as e:
                    logger.error(f"Erro ao ler cache: {str(e)}")
            
            return None
    
    async def aset(self, key: str, value: Any):
        """Armazena dados no cache de forma assíncrona."""
        async with self.lock:
            cache_data = {
                'timestamp': time.time(),
                'value': value
            }
            
            # Calcula tamanho dos dados
            data_size = len(json.dumps(cache_data))
            
            # Verifica se os dados são muito grandes
            if data_size > self.max_size:
                logger.warning(f"Dados muito grandes para cache: {key}")
                return
            
            # Remove item antigo se existir
            if key in self.cache:
                await self.adelete(key)
            
            # Adiciona novo item
            self.cache[key] = cache_data
            self.current_size += data_size
            
            # Persiste no disco
            try:
                cache_file = self._get_cache_path(key)
                cache_file.write_text(json.dumps(cache_data))
            except Exception as e:
                logger.error(f"Erro ao gravar cache: {str(e)}")
            
            await self._check_size()
    
    async def adelete(self, key: str):
        """Remove item do cache de forma assíncrona."""
        if key in self.cache:
            data_size = len(json.dumps(self.cache[key]))
            del self.cache[key]
            self.current_size -= data_size
            
            try:
                cache_file = self._get_cache_path(key)
                if cache_file.exists():
                    cache_file.unlink()
            except Exception as e:
                logger.error(f"Erro ao remover cache: {str(e)}")
    
    async def aclear(self):
        """Limpa todo o cache de forma assíncrona."""
        async with self.lock:
            self.cache.clear()
            self.current_size = 0
            
            try:
                for cache_file in CACHE_DIR.glob("*.json"):
                    cache_file.unlink()
            except Exception as e:
                logger.error(f"Erro ao limpar cache: {str(e)}")