"""
Exemplo básico de uso do AWS Agent

Este exemplo demonstra como usar o AWS Agent para:
- Adicionar uma conta AWS
- Conectar à conta
- Listar recursos básicos
"""

import sys
import os
from pathlib import Path

# Adiciona o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from aws_agent.core.agent import AWSAgent
from aws_agent.core.config import get_config


def main():
    """Exemplo básico de uso do AWS Agent"""
    
    print("=== AWS Multi-Account Agent - Exemplo Básico ===\n")
    
    # Inicializa o agente
    agent = AWSAgent()
    
    # Exibe configuração atual
    config = get_config()
    print(f"Diretório de configuração: {config.config_dir}")
    print(f"Nível de log: {config.log_level}")
    print(f"Região padrão: {config.default_region}\n")
    
    # Lista contas disponíveis
    accounts = agent.list_accounts()
    print(f"Contas disponíveis: {len(accounts)}")
    
    if accounts:
        print("Contas configuradas:")
        for account in accounts:
            print(f"  - {account['account_name']} ({account.get('account_id', 'N/A')})")
    else:
        print("Nenhuma conta configurada ainda.")
        print("\nPara adicionar uma conta, use:")
        print("  python examples/basic_usage.py --add-account")
        print("\nOu use a interface CLI:")
        print("  python -m aws_agent.cli.main add-account")
    
    print("\n=== Fim do Exemplo ===")


def add_account_example():
    """Exemplo de adição de conta"""
    print("=== Adicionando Conta AWS ===\n")
    
    # Solicita dados da conta
    account_name = input("Nome da conta: ")
    access_key_id = input("Access Key ID: ")
    secret_access_key = input("Secret Access Key: ")
    region = input("Região (padrão: us-east-1): ") or "us-east-1"
    
    # Inicializa o agente
    agent = AWSAgent()
    
    # Adiciona a conta
    print(f"\nAdicionando conta '{account_name}'...")
    
    success = agent.add_account(
        account_name=account_name,
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        region=region
    )
    
    if success:
        print(f"✅ Conta '{account_name}' adicionada com sucesso!")
        
        # Tenta conectar à conta
        print(f"\nTestando conexão com '{account_name}'...")
        if agent.connect(account_name):
            print("✅ Conexão bem-sucedida!")
            
            # Obtém informações da conta
            info = agent.get_current_account_info()
            if info:
                print(f"Account ID: {info.get('account_id', 'N/A')}")
                print(f"User ARN: {info.get('current_arn', 'N/A')}")
        else:
            print("❌ Falha na conexão")
    else:
        print(f"❌ Falha ao adicionar conta '{account_name}'")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--add-account":
        add_account_example()
    else:
        main()
