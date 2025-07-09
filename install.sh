#!/bin/bash

# Script de instalação e configuração do AWS Multi-Account Agent

set -e

echo "=== AWS Multi-Account Agent - Instalação ==="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para imprimir mensagens coloridas
print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verifica se Python está instalado
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 não encontrado. Instale Python 3.8+ antes de continuar."
    exit 1
fi

# Verifica versão do Python
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    print_error "Python $REQUIRED_VERSION+ é necessário. Versão atual: $PYTHON_VERSION"
    exit 1
fi

print_success "Python $PYTHON_VERSION encontrado"

# Cria ambiente virtual
print_info "Criando ambiente virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Ambiente virtual criado"
else
    print_info "Ambiente virtual já existe"
fi

# Ativa ambiente virtual
print_info "Ativando ambiente virtual..."
source venv/bin/activate

# Atualiza pip
print_info "Atualizando pip..."
pip install --upgrade pip

# Instala dependências
print_info "Instalando dependências..."
pip install -r requirements.txt

# Instala o pacote em modo desenvolvimento
print_info "Instalando AWS Agent em modo desenvolvimento..."
pip install -e .

# Configura pre-commit (opcional)
if command -v pre-commit &> /dev/null; then
    print_info "Configurando pre-commit hooks..."
    pre-commit install
    print_success "Pre-commit hooks configurados"
else
    print_info "Pre-commit não encontrado, pulando configuração dos hooks"
fi

# Cria diretórios necessários
print_info "Criando diretórios de configuração..."
mkdir -p ~/.aws-agent/{logs,backups,config}

# Testa instalação
print_info "Testando instalação..."
if python -c "import aws_agent; print('✅ Importação bem-sucedida')" 2>/dev/null; then
    print_success "Instalação concluída com sucesso!"
else
    print_error "Falha na instalação"
    exit 1
fi

echo
echo "=== Próximos Passos ==="
echo "1. Ative o ambiente virtual: source venv/bin/activate"
echo "2. Execute o agente: python -m aws_agent.cli.main --help"
echo "3. Adicione uma conta AWS: python -m aws_agent.cli.main add-account"
echo "4. Inicie o agente: python -m aws_agent.cli.main start"
echo
echo "📚 Documentação: docs/README.md"
echo "🔧 Exemplos: examples/"
echo "🧪 Testes: make test"
echo
print_success "Instalação concluída!"
