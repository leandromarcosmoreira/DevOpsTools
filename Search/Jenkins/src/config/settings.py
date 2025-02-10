import os
from pathlib import Path
import multiprocessing
import psutil

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Carrega configurações do arquivo settings.txt
def load_settings():
    settings_file = BASE_DIR / "settings.txt"
    if not settings_file.exists():
        template_file = BASE_DIR / "settings.template.txt"
        if template_file.exists():
            settings_file.write_text(template_file.read_text())
        else:
            raise FileNotFoundError("Arquivo settings.template.txt não encontrado")
        raise FileNotFoundError(
            "\nArquivo de configuração não encontrado!\n"
            "Um arquivo settings.txt foi criado com valores padrão.\n"
            "Por favor, configure-o de acordo com suas necessidades e execute novamente."
        )
    
    settings = {}
    exec(settings_file.read_text(), settings)
    return settings

# Carrega configurações
config = load_settings()

# Configurações dos Servidores
JENKINS_SERVERS = config.get('JENKINS_SERVERS', [])
KEYWORDS = config.get('KEYWORDS', [])

# Configurações de Autenticação
USERNAME = os.getenv("JENKINS_USERNAME") or config.get('USERNAME')
API_TOKEN = os.getenv("JENKINS_API_TOKEN") or config.get('API_TOKEN')

# Otimizações de CPU e Memória
CPU_COUNT = config.get('CPU_COUNT', multiprocessing.cpu_count())
MEMORY_LIMIT = int(psutil.virtual_memory().total * config.get('MEMORY_LIMIT', 0.8))
MAX_CONCURRENT_JOBS = config.get('MAX_CONCURRENT_JOBS', min(CPU_COUNT * 8, 64))
MAX_WORKERS = config.get('MAX_WORKERS', min(CPU_COUNT * 4, 32))
MAX_CONCURRENT_CONNECTIONS = config.get('MAX_CONCURRENT_CONNECTIONS', min(CPU_COUNT * 16, 128))
CHUNK_SIZE = config.get('CHUNK_SIZE', 2 * 1024 * 1024)

# Otimizações de Timeout e Retry
MAX_RETRIES = config.get('MAX_RETRIES', 3)
RETRY_DELAY = config.get('RETRY_DELAY', 0.5)
CONNECTION_TIMEOUT = config.get('CONNECTION_TIMEOUT', 20)
KEEPALIVE_TIMEOUT = config.get('KEEPALIVE_TIMEOUT', 30)

# Otimizações de Cache
CACHE_DIR = BASE_DIR / "cache"
CACHE_DURATION = config.get('CACHE_DURATION', 7200)
CACHE_MAX_SIZE = int(MEMORY_LIMIT * config.get('CACHE_MAX_SIZE', 0.3))

# Configurações de Log
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "jenkins_search.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_MAX_SIZE = config.get('LOG_MAX_SIZE', 5 * 1024 * 1024)
LOG_BACKUP_COUNT = config.get('LOG_BACKUP_COUNT', 3)
LOG_LEVEL = os.getenv("LOG_LEVEL") or config.get('LOG_LEVEL', "INFO")

# Configurações de Resultados
RESULTS_DIR = BASE_DIR / "results"

# Configurações de Contexto
MAX_CONTEXT_LINES = config.get('MAX_CONTEXT_LINES', 5)