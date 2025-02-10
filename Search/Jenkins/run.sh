#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"; }
error() { echo -e "${RED}[$(date +'%H:%M:%S')] Erro: $1${NC}"; exit 1; }

check_python() {
    if ! command -v python3 &> /dev/null; then
        error "Python 3 não encontrado. Por favor, instale Python 3.10 ou superior."
    fi
    version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if (( $(echo "$version < 3.10" | bc -l) )); then
        error "Python 3.10 ou superior é necessário. Versão atual: $version"
    fi
}

setup_venv() {
    if [ ! -d ".venv" ]; then
        log "Criando ambiente virtual..."
        python3 -m venv .venv || error "Falha ao criar ambiente virtual"
        source .venv/bin/activate || error "Falha ao ativar ambiente virtual"
        log "Instalando dependências..."
        pip install -r requirements.txt 2>&1 | tee /tmp/pip.log > /dev/null || {
            cat /tmp/pip.log
            error "Falha ao instalar dependências"
        }
        rm -f /tmp/pip.log
    else
        source .venv/bin/activate || error "Falha ao ativar ambiente virtual"
    fi
}

clean() {
    log "Limpando diretórios..."
    rm -rf cache logs results
}

check_env() {
    if [ -z "$JENKINS_USERNAME" ] || [ -z "$JENKINS_API_TOKEN" ]; then
        error "Variáveis de ambiente JENKINS_USERNAME e JENKINS_API_TOKEN são necessárias"
    fi
}

main() {
    if [ "$1" = "clean" ]; then
        clean
        exit 0
    fi
    
    check_python
    setup_venv
    check_env
    
    log "Iniciando aplicação..."
    
    PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}" python -m src.main
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log "Aplicação finalizada com sucesso"
    else
        error "Aplicação finalizada com erro"
    fi
    
    exit $exit_code
}

main "$@"