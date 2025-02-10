# GitLab Scanner

Scanner para busca de palavras-chave em repositórios do GitLab.

## Requisitos

- Python 3.8+
- pip (gerenciador de pacotes Python)
- Acesso a uma instância GitLab
- Token de acesso privado do GitLab

## Instalação

1. Extraia o arquivo zip:
```bash
unzip scanner.zip
cd scanner
```

2. Configure as variáveis de ambiente:

```bash
# Linux/macOS
export GITLAB_URL=https://seu-gitlab.com
export PRIVATE_TOKEN=seu-token-aqui

# Windows (PowerShell)
$env:GITLAB_URL = 'https://seu-gitlab.com'
$env:PRIVATE_TOKEN = 'seu-token-aqui'
```

3. Execute o scanner:

```bash
# Execução em uma única linha
GITLAB_URL="https://seu-gitlab.com" PRIVATE_TOKEN="seu-token-aqui" ./run.sh

# Ou após exportar as variáveis
./run.sh

# Para limpar diretórios de output
./run.sh clean
```

O script `run.sh` irá:
- Verificar a versão do Python
- Criar e configurar o ambiente virtual
- Instalar as dependências
- Executar o scanner

## Estrutura do Projeto

```
.
├── src/
│   ├── config/         # Configurações
│   ├── functions/      # Funções principais
│   └── main.py         # Ponto de entrada
├── requirements.txt    # Dependências
├── settings.txt        # Configurações do sistema
└── run.sh             # Script de inicialização
```

## Licença

Este projeto está sob a licença MIT.