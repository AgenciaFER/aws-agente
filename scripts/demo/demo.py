#!/usr/bin/env python3
"""
Demonstração do AWS Multi-Account Agent

Este script demonstra todas as funcionalidades do AWS Agent
sem precisar de credenciais AWS reais, usando dados simulados.
"""

import os
import sys
import time
from pathlib import Path

# Adiciona o diretório src ao path para importar os módulos
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from aws_agent.core.config import get_config
from aws_agent.core.account_manager import AccountManager
from aws_agent.core.agent import AWSAgent
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()

def print_header(title: str):
    """Imprime cabeçalho formatado"""
    console.print(Panel(title, style="bold blue"))

def print_success(message: str):
    """Imprime mensagem de sucesso"""
    console.print(f"✅ {message}", style="green")

def print_info(message: str):
    """Imprime mensagem informativa"""
    console.print(f"ℹ️  {message}", style="blue")

def print_warning(message: str):
    """Imprime mensagem de aviso"""
    console.print(f"⚠️  {message}", style="yellow")

def demonstrate_config():
    """Demonstra a configuração do sistema"""
    print_header("🔧 Configuração do Sistema")
    
    config = get_config()
    
    table = Table(title="Configurações Atuais")
    table.add_column("Propriedade", style="cyan")
    table.add_column("Valor", style="magenta")
    
    table.add_row("Diretório Base", str(config.base_dir))
    table.add_row("Diretório de Config", str(config.config_dir))
    table.add_row("Diretório de Logs", str(config.log_dir))
    table.add_row("Arquivo de Credenciais", str(config.credentials_file))
    table.add_row("Nível de Log", config.log_level)
    table.add_row("Região Padrão", config.default_region)
    table.add_row("Timeout de Sessão", f"{config.session_timeout} segundos")
    table.add_row("Máximo de Tentativas", str(config.max_retries))
    
    console.print(table)
    print_success("Configuração carregada com sucesso!")

def demonstrate_account_manager():
    """Demonstra o gerenciador de contas"""
    print_header("👤 Gerenciador de Contas")
    
    # Cria instância do gerenciador
    manager = AccountManager()
    
    print_info("Gerenciador de contas inicializado")
    print_info(f"Arquivo de credenciais: {manager.credentials_file}")
    print_info(f"Chave de criptografia gerada automaticamente")
    
    # Lista contas (será vazio inicialmente)
    accounts = manager.list_accounts()
    
    if not accounts:
        print_warning("Nenhuma conta AWS configurada")
        print_info("Use 'aws-agent add-account' para adicionar uma conta")
    else:
        table = Table(title="Contas AWS Configuradas")
        table.add_column("Nome", style="cyan")
        table.add_column("Região", style="magenta")
        table.add_column("Profile", style="green")
        
        for account in accounts:
            table.add_row(
                account.get('name', 'N/A'),
                account.get('region', 'N/A'),
                account.get('profile_name', 'N/A')
            )
        
        console.print(table)

def demonstrate_agent():
    """Demonstra o agente AWS"""
    print_header("🤖 AWS Agent")
    
    # Cria instância do agente
    agent = AWSAgent()
    
    print_info("AWS Agent inicializado")
    
    # Mostra status
    status = agent.get_status()
    
    table = Table(title="Status do AWS Agent")
    table.add_column("Propriedade", style="cyan")
    table.add_column("Valor", style="magenta")
    
    for key, value in status.items():
        if isinstance(value, bool):
            value = "✅" if value else "❌"
        table.add_row(key, str(value))
    
    console.print(table)
    
    # Mostra serviços disponíveis
    print_info("Serviços disponíveis quando conectado:")
    services = ['ec2', 's3', 'iam', 'lambda']
    
    for service in services:
        console.print(f"  • {service.upper()}: Gerenciamento de recursos {service}")

def demonstrate_cli_commands():
    """Demonstra comandos CLI disponíveis"""
    print_header("💻 Comandos CLI Disponíveis")
    
    commands = [
        ("aws-agent --help", "Mostra ajuda geral"),
        ("aws-agent status", "Mostra status atual do agente"),
        ("aws-agent list-accounts", "Lista contas configuradas"),
        ("aws-agent add-account", "Adiciona nova conta AWS"),
        ("aws-agent remove-account", "Remove conta AWS"),
        ("aws-agent connect <conta>", "Conecta a uma conta específica"),
        ("aws-agent disconnect", "Desconecta da conta atual"),
        ("aws-agent services", "Lista serviços disponíveis"),
        ("aws-agent interactive", "Modo interativo completo"),
        ("aws-agent start", "Inicia com seleção interativa de conta"),
        ("aws-agent backup", "Cria backup da configuração"),
        ("aws-agent cleanup", "Remove credenciais expiradas"),
    ]
    
    table = Table(title="Comandos CLI")
    table.add_column("Comando", style="cyan")
    table.add_column("Descrição", style="magenta")
    
    for command, description in commands:
        table.add_row(command, description)
    
    console.print(table)

def demonstrate_services():
    """Demonstra os serviços AWS suportados"""
    print_header("☁️ Serviços AWS Suportados")
    
    services = [
        {
            "name": "EC2",
            "description": "Gerenciamento de instâncias, volumes, security groups",
            "operations": [
                "Listar/iniciar/parar/reiniciar instâncias",
                "Gerenciar volumes EBS",
                "Configurar security groups",
                "Conexão SSH/RDP/Session Manager"
            ]
        },
        {
            "name": "S3",
            "description": "Gerenciamento de buckets e objetos",
            "operations": [
                "Criar/deletar buckets",
                "Upload/download de arquivos",
                "Configurar políticas de bucket",
                "Gerenciar versionamento"
            ]
        },
        {
            "name": "IAM",
            "description": "Gerenciamento de identidades e acessos",
            "operations": [
                "Gerenciar usuários e grupos",
                "Configurar roles e políticas",
                "Gerenciar chaves de acesso",
                "Auditoria de permissões"
            ]
        },
        {
            "name": "Lambda",
            "description": "Gerenciamento de funções serverless",
            "operations": [
                "Deploy de funções",
                "Gerenciar layers",
                "Configurar triggers",
                "Monitorar execuções"
            ]
        }
    ]
    
    for service in services:
        console.print(f"\n[bold cyan]{service['name']}[/bold cyan]: {service['description']}")
        for operation in service['operations']:
            console.print(f"  • {operation}")

def demonstrate_automation():
    """Demonstra capacidades de automação"""
    print_header("🔄 Automação e Scripts")
    
    print_info("O AWS Agent suporta automação através de:")
    
    automation_features = [
        "Scripts Python usando as classes do core",
        "Comandos CLI em shell scripts",
        "Configuração via variáveis de ambiente",
        "Integração com CI/CD pipelines",
        "Backup e restauração automática",
        "Monitoramento e alertas"
    ]
    
    for feature in automation_features:
        console.print(f"  • {feature}")
    
    console.print(f"\n[bold]Exemplo de script automatizado:[/bold]")
    console.print("Veja o arquivo: examples/advanced_usage.py")

def run_demo():
    """Executa a demonstração completa"""
    console.print("""
[bold blue]🚀 AWS Multi-Account Agent - Demonstração[/bold blue]

Esta demonstração mostra todas as funcionalidades do AWS Agent
sem precisar de credenciais AWS reais.
    """)
    
    try:
        demonstrate_config()
        time.sleep(2)
        
        demonstrate_account_manager()
        time.sleep(2)
        
        demonstrate_agent()
        time.sleep(2)
        
        demonstrate_cli_commands()
        time.sleep(2)
        
        demonstrate_services()
        time.sleep(2)
        
        demonstrate_automation()
        
        console.print("""
[bold green]✅ Demonstração Concluída![/bold green]

Para começar a usar o AWS Agent:

1. [cyan]aws-agent add-account[/cyan] - Adicione suas credenciais AWS
2. [cyan]aws-agent connect <nome-da-conta>[/cyan] - Conecte a uma conta
3. [cyan]aws-agent interactive[/cyan] - Use o modo interativo

Para mais informações, consulte o README.md
        """)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Demonstração interrompida pelo usuário[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Erro durante a demonstração: {e}[/red]")

if __name__ == "__main__":
    run_demo()
