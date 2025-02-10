# Jenkins Search

Ferramenta avançada para pesquisa de palavras-chave em projetos Jenkins através da API, com processamento assíncrono e alta performance.

## 🚀 Características

### Performance e Otimização
- ⚡ Processamento assíncrono com asyncio
- 🔄 Processamento paralelo com multiprocessing
- 💾 Sistema de cache inteligente com persistência em disco
- 🧮 Gerenciamento automático de memória e threads
- ⚡ Processamento em chunks para melhor performance
- 🔄 Recuperação automática de interrupções

### Busca e Resultados
- 🔍 Busca em múltiplos servidores Jenkins
- 📊 Exportação detalhada para Excel
- 📝 Contexto de código para cada ocorrência
- 🎯 Busca case-insensitive
- 📋 Filtros automáticos nos resultados

### Monitoramento e Logs
- 📊 Métricas de execução detalhadas
- 📝 Sistema de logs rotativo
- ⏱️ Medição de tempo de execução
- 🔄 Checkpoints para recuperação
- 🛡️ Tratamento robusto de erros

## 📋 Configuração

O arquivo `settings.txt` contém todas as configurações necessárias:

```python
# Configurações dos Servidores Jenkins
JENKINS_SERVERS = [
    "https://jenkins.company.network",
    "https://jenkins-dev.company.network"
]

# Palavras-chave para busca
KEYWORDS = ["gitauto", "gitdev", "gitmenu", "gitnoob", "gitschedule"]

# Configurações de Autenticação
USERNAME = "jenkins_user"  # Seu usuário Jenkins
API_TOKEN = "default_token"  # Seu token de API Jenkins

# Configurações de Performance
CPU_COUNT = 4  # Número de CPUs disponíveis
MEMORY_LIMIT = 0.8  # Limite de uso de memória (80% da memória total)
MAX_CONCURRENT_JOBS = 32  # Máximo de jobs simultâneos
MAX_WORKERS = 16  # Máximo de workers para processamento
MAX_CONCURRENT_CONNECTIONS = 64  # Máximo de conexões simultâneas
CHUNK_SIZE = 2097152  # Tamanho do chunk em bytes (2MB)

# Configurações de Timeout e Retry
MAX_RETRIES = 3  # Número máximo de tentativas
RETRY_DELAY = 0.5  # Delay entre tentativas em segundos
CONNECTION_TIMEOUT = 20  # Timeout de conexão em segundos
KEEPALIVE_TIMEOUT = 30  # Timeout de keepalive em segundos

# Configurações de Cache
CACHE_DURATION = 7200  # Duração do cache em segundos (2 horas)
CACHE_MAX_SIZE = 0.3  # Tamanho máximo do cache (30% da memória disponível)

# Configurações de Log
LOG_MAX_SIZE = 5242880  # Tamanho máximo do arquivo de log (5MB)
LOG_BACKUP_COUNT = 3  # Número de backups do arquivo de log
LOG_LEVEL = "INFO"  # Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)

# Configurações de Contexto
MAX_CONTEXT_LINES = 5  # Número de linhas de contexto antes e depois da ocorrência
```

## 📊 Formato dos Resultados

### Excel
O arquivo Excel gerado contém duas planilhas:

#### Planilha "Detalhes"
Colunas:
- Servidor: URL do servidor Jenkins
- Grupo: Grupo/pasta do projeto
- Projeto: Nome do projeto
- URL: URL completa do projeto
- Palavra-chave: Termo encontrado
- Linha: Número da linha
- Trecho: Conteúdo da linha
- Contexto: Linhas anteriores e posteriores

#### Planilha "Resumo"
Colunas:
- Servidor: URL do servidor Jenkins
- Palavra-chave: Termo pesquisado
- Quantidade: Número de ocorrências

### Logs
Exemplo de saída de log:
```
[15:55:28] Resumo por servidor:
[15:55:28] Servidor: https://jenkins-dev.company.network (9.35s)
[15:55:28] ------------------------------------------------------------
[15:55:28] gitauto: (11 ocorrências em 23 projetos)
[15:55:28] ------------------------------------------------------------
[15:55:28] Projetos:
[15:55:28]   - ExecECM (2.05s)
[15:55:28]   - ExecuteWebServiceDev (2.05s)
[15:55:28] ------------------------------------------------------------
[15:55:28] Tempo total de execução: 21.48s
```

## 🛠️ Requisitos

### Sistema
- Python 3.10 ou superior
- Memória RAM: 4GB mínimo recomendado
- CPU: 2 cores mínimo recomendado

### Acesso
- Acesso aos servidores Jenkins
- Credenciais de API do Jenkins

## 📦 Dependências

```
pandas==2.1.4        # Processamento de dados e exportação Excel
openpyxl==3.1.2     # Suporte a Excel
urllib3==2.0.7      # Requisições HTTP
python-dotenv==1.0.0 # Variáveis de ambiente
colorama==0.4.6     # Cores no terminal
aiohttp==3.9.1      # Cliente HTTP assíncrono
asyncio==3.4.3      # Suporte a async/await
psutil==5.9.6       # Monitoramento de recursos
```

## 🚀 Instalação e Execução

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/jenkins-search.git
cd jenkins-search
```

2. Configure as variáveis de ambiente:
```bash
export JENKINS_USERNAME="seu_usuario"
export JENKINS_API_TOKEN="seu_token"
export LOG_LEVEL="INFO"  # Opcional (default: INFO)
```

3. Execute o script de inicialização:
```bash
chmod +x run.sh
./run.sh
```

### Docker
Alternativamente, use Docker:
```bash
docker-compose up
```

## 📁 Estrutura do Projeto

```
jenkins-search/
├── src/
│   ├── config/
│   │   └── settings.py      # Configurações globais
│   ├── factories/
│   │   └── client_factory.py # Factory para clientes Jenkins
│   ├── jenkins/
│   │   ├── client.py        # Cliente Jenkins assíncrono
│   │   └── searcher.py      # Motor de busca
│   ├── models/
│   │   └── search_result.py # Modelos de dados
│   ├── observers/
│   │   └── progress_observer.py # Observadores de progresso
│   ├── services/
│   │   └── excel_service.py # Serviço de exportação Excel
│   ├── utils/
│   │   ├── cache.py        # Sistema de cache
│   │   ├── checkpoint.py   # Gerenciamento de checkpoints
│   │   ├── logger.py       # Configuração de logs
│   │   ├── memory.py       # Gerenciamento de memória
│   │   ├── messages.py     # Mensagens do terminal
│   │   └── timer.py        # Decorador de tempo
│   └── main.py             # Ponto de entrada
├── results/                # Resultados em Excel
├── logs/                   # Logs da aplicação
├── cache/                  # Cache de requisições
├── docker-compose.yml      # Configuração Docker
├── Dockerfile             # Build da imagem
├── requirements.txt       # Dependências Python
├── run.sh                # Script de execução
└── README.md             # Esta documentação
```

## 📄 Licença

MIT License