import os
from pathlib import Path
from typing import List, Set

def load_settings():
    settings = {}
    settings_file = Path('settings.txt')
    
    if not settings_file.exists():
        raise FileNotFoundError("Arquivo settings.txt não encontrado")
        
    with open(settings_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                settings[key.strip()] = value.strip()
                
    return settings

SETTINGS = load_settings()

# Pool settings
POOL_CONSIZE = int(SETTINGS.get('POOL_CONSIZE', 10))
POOL_MAXSIZE = int(SETTINGS.get('POOL_MAXSIZE', 100))
SEMAPHORE_SIZE = int(SETTINGS.get('SEMAPHORE_SIZE', 10))

# API settings
TIMEOUT_API_GITLAB = int(SETTINGS.get('TIMEOUT_API_GITLAB', 30))
PER_PAGE = int(SETTINGS.get('PER_PAGE', 100))

# Retry settings
RETRY_ATTEMPTS = int(SETTINGS.get('RETRY_ATTEMPTS', 3))
RETRY_WAIT_MULTIPLIER = int(SETTINGS.get('RETRY_WAIT_MULTIPLIER', 2))
RETRY_WAIT_MIN = int(SETTINGS.get('RETRY_WAIT_MIN', 2))
RETRY_WAIT_MAX = int(SETTINGS.get('RETRY_WAIT_MAX', 15))

# Keywords
KEYWORDS = SETTINGS.get('KEYWORDS', '').split(',')

# File paths
OUTPUT_FILE = Path(SETTINGS.get('OUTPUT_FILE', 'output/resultados.xlsx'))
LOG_FILE = Path(SETTINGS.get('LOG_FILE', 'log/scanner.log'))
CHECKPOINT_FILE = Path(SETTINGS.get('CHECKPOINT_FILE', 'checkpoints/progress.json'))

# Cache settings
CACHE_MAX_SIZE = int(SETTINGS.get('CACHE_MAX_SIZE', 1000))
BATCH_SIZE = int(SETTINGS.get('BATCH_SIZE', 50))

# Binary file settings
BINARY_SAMPLE_SIZE = int(SETTINGS.get('BINARY_SAMPLE_SIZE', 1024))
BINARY_THRESHOLD = float(SETTINGS.get('BINARY_THRESHOLD', 0.3))
BINARY_EXTENSIONS: Set[str] = {
    ext.strip() for ext in SETTINGS.get('BINARY_EXTENSIONS', '').split(',')
}

# Text encodings
TEXT_ENCODINGS: List[str] = SETTINGS.get('TEXT_ENCODINGS', '').split(',')

# Terminal colors
COLOR_SUCCESS = SETTINGS.get('COLOR_SUCCESS', '\033[92m')
COLOR_ERROR = SETTINGS.get('COLOR_ERROR', '\033[91m')
COLOR_RESET = SETTINGS.get('COLOR_RESET', '\033[0m')