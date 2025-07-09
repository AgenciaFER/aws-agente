# Makefile para desenvolvimento do AWS Agent

.PHONY: help install install-dev test test-coverage lint format clean build upload docs

# Configurações
PYTHON := python3
PIP := pip3
PACKAGE_NAME := aws-agent

# Help
help:
	@echo "Comandos disponíveis:"
	@echo "  install      - Instala o pacote"
	@echo "  install-dev  - Instala dependências de desenvolvimento"
	@echo "  test         - Executa testes"
	@echo "  test-coverage - Executa testes com cobertura"
	@echo "  lint         - Executa linting"
	@echo "  format       - Formata código"
	@echo "  clean        - Limpa arquivos temporários"
	@echo "  build        - Constrói o pacote"
	@echo "  upload       - Faz upload para PyPI"
	@echo "  docs         - Gera documentação"

# Instalação
install:
	$(PIP) install -e .

install-dev:
	$(PIP) install -e .[dev]
	pre-commit install

# Testes
test:
	$(PYTHON) -m pytest tests/ -v

test-coverage:
	$(PYTHON) -m pytest tests/ --cov=aws_agent --cov-report=html --cov-report=term-missing

# Linting e formatação
lint:
	$(PYTHON) -m flake8 src/aws_agent tests/
	$(PYTHON) -m mypy src/aws_agent

format:
	$(PYTHON) -m black src/aws_agent tests/ examples/
	$(PYTHON) -m isort src/aws_agent tests/ examples/

# Limpeza
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Build
build: clean
	$(PYTHON) setup.py sdist bdist_wheel

# Upload para PyPI
upload: build
	twine upload dist/*

# Documentação
docs:
	cd docs && make html

# Desenvolvimento
dev-setup: install-dev
	@echo "Ambiente de desenvolvimento configurado!"

# Verificação completa
check: lint test
	@echo "Verificação completa concluída!"

# Lançamento
release: check build upload
	@echo "Lançamento concluído!"
