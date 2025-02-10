from typing import Dict, Type
from src.jenkins.client import JenkinsClient
from src.utils.logger import setup_logger

logger = setup_logger()

class ClientFactory:
    _clients: Dict[str, Type[JenkinsClient]] = {}
    
    @classmethod
    def register_client(cls, name: str, client_class: Type[JenkinsClient]):
        cls._clients[name] = client_class
    
    @classmethod
    def create_client(cls, client_type: str = "jenkins", **kwargs) -> JenkinsClient:
        try:
            client_class = cls._clients.get(client_type)
            if not client_class:
                raise ValueError(f"Cliente não suportado: {client_type}")
            return client_class(**kwargs)
        except Exception as e:
            logger.error(f"Erro ao criar cliente: {str(e)}")
            raise

# Registra o cliente Jenkins padrão
ClientFactory.register_client("jenkins", JenkinsClient)