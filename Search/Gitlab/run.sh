#!/bin/bash

DIR_SCRIPT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

VERMELHO='\033[0;31m'
VERDE='\033[0;32m'
AMARELO='\033[1;33m'
SEM_COR='\033[0m'

registrar() {
    timestamp="${SEM_COR}[$(date +'%d/%m/%Y %H:%M:%S')]${SEM_COR}"
    echo -e "${timestamp} ${VERDE}$1${SEM_COR}"
}

aviso() {
    timestamp="${SEM_COR}[$(date +'%d/%m/%Y %H:%M:%S')]${SEM_COR}"
    echo -e "${timestamp} ${AMARELO}Aviso: $1${SEM_COR}"
}

erro() {
    timestamp="${SEM_COR}[$(date +'%d/%m/%Y %H:%M:%S')]${SEM_COR}"
    echo -e "${timestamp} ${VERMELHO}Erro: $1${SEM_COR}"
    exit 1
}

verificar_ambiente() {
    GITLAB_URL="${GITLAB_URL:-$1}"
    PRIVATE_TOKEN="${PRIVATE_TOKEN:-$2}"

    if [ -z "${GITLAB_URL}" ] || [ -z "${PRIVATE_TOKEN}" ]; then
        erro "Variáveis de ambiente GITLAB_URL e PRIVATE_TOKEN são necessárias.
        
Execute o script assim:
    export GITLAB_URL=\"https://seu-gitlab.com\"
    export PRIVATE_TOKEN=\"seu-token\"
    ./run.sh

Ou em uma única linha:
    GITLAB_URL=\"https://seu-gitlab.com\" PRIVATE_TOKEN=\"seu-token\" ./run.sh"
    fi
}

verificar_python() {
    if ! command -v python3 &> /dev/null; then
        erro "Python 3 não encontrado. Por favor, instale Python 3.8 ou superior."
    fi
    
    versao=$(python3 -V 2>&1 | sed 's/Python //')
    major=$(echo $versao | cut -d. -f1)
    minor=$(echo $versao | cut -d. -f2)
    
    if [ "$major" -lt 3 ] || [ "$major" -eq 3 -a "$minor" -lt 8 ]; then
        erro "Python 3.8 ou superior é necessário. Versão atual: $versao"
    fi
    
    registrar "Python versão $versao encontrado"
}

configurar_venv() {
    if [ ! -d ".venv" ]; then
        registrar "Criando ambiente virtual..."
        python3 -m venv .venv || erro "Falha ao criar ambiente virtual"
        source .venv/bin/activate || erro "Falha ao ativar ambiente virtual"
        pip install --quiet --progress-bar off -r requirements.txt || {
            erro "Falha ao instalar dependências. Verifique o arquivo requirements.txt e sua conexão com a internet."
        }
        registrar "Dependências instaladas com sucesso"
    else
        source .venv/bin/activate || erro "Falha ao ativar ambiente virtual"
        pip freeze | grep -f requirements.txt > /dev/null || {
            registrar "Atualizando dependências..."
            pip install --quiet --progress-bar off -r requirements.txt || erro "Falha ao atualizar dependências"
        }
    fi
}

limpar() {
    registrar "Iniciando limpeza..."
    rm -rf output log
    mkdir -p output log
    registrar "Diretórios output e log limpos"
    rm -rf checkpoints
    mkdir -p checkpoints
    registrar "Checkpoints limpos"
    find . -type d -name "__pycache__" -exec rm -rf {} +
    registrar "Cache do Python limpo"
    registrar "Limpeza finalizada"
}

principal() {
    if [ "$1" = "clean" ]; then
        limpar
        exit 0
    fi
    
    verificar_ambiente "$GITLAB_URL" "$PRIVATE_TOKEN"
    verificar_python
    configurar_venv
    
    export GITLAB_URL
    export PRIVATE_TOKEN
    
    mkdir -p output log checkpoints
    
    PYTHONPATH="${DIR_SCRIPT}:${PYTHONPATH}" python3 -m src.main
    codigo_saida=$?
    
    if [ $codigo_saida -eq 0 ]; then
        registrar "Scanner finalizado com sucesso"
    else
        erro "Scanner finalizado com erro"
    fi
    
    exit $codigo_saida
}

principal "$@"