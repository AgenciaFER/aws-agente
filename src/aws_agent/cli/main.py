"""
Interface CLI principal do AWS Agent

Este módulo implementa a interface de linha de comando usando Click,
permitindo interação intuitiva com o agente AWS.
"""

import click
import sys
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint
from pathlib import Path

from ..core.agent import AWSAgent
from ..core.account_manager import AWSCredentials
from ..core.config import get_config

# Console para output formatado
console = Console()
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.panel import Panel
from rich import print as rprint
import json

from ..core.agent import AWSAgent
from ..core.account_manager import AWSCredentials
from ..core.config import get_config


console = Console()


def print_logo():
    """Exibe o logo do AWS Agent"""
    logo = """
╔═══════════════════════════════════════════════════════════════╗
║                     AWS Multi-Account Agent                   ║
║                                                               ║
║  🚀 Gerenciador de múltiplas contas AWS com segurança       ║
║  🔐 Credenciais criptografadas localmente                   ║
║  ⚡ Interface CLI intuitiva e completa                      ║
╚═══════════════════════════════════════════════════════════════╝
"""
    console.print(logo, style="bold blue")

def print_error(message: str):
    """Exibe mensagem de erro formatada"""
    console.print(f"❌ Erro: {message}", style="bold red")

def print_success(message: str):
    """Exibe mensagem de sucesso formatada"""
    console.print(f"✅ Sucesso: {message}", style="bold green")

def print_info(message: str):
    """Exibe mensagem informativa formatada"""
    console.print(f"ℹ️  {message}", style="bold yellow")

def print_warning(message: str):
    """Exibe mensagem de aviso formatada"""
    console.print(f"⚠️  Aviso: {message}", style="bold orange")

@click.group()
@click.version_option(version="1.0.0")
@click.pass_context
def cli(ctx):
    """
    AWS Multi-Account Agent - Gerenciador de múltiplas contas AWS
    
    Um agente completo para gerenciar credenciais AWS de forma segura
    e executar operações em múltiplas contas.
    """
    ctx.ensure_object(dict)
    ctx.obj['agent'] = AWSAgent()

@cli.command()
@click.pass_context
def status(ctx):
    """Mostra o status atual do agente"""
    agent: AWSAgent = ctx.obj['agent']
    
    try:
        status_info = agent.get_status()
        
        # Cria tabela de status
        table = Table(title="AWS Agent Status", show_header=True, header_style="bold magenta")
        table.add_column("Propriedade", style="cyan")
        table.add_column("Valor", style="green")
        
        table.add_row("Conta Atual", status_info.get('current_account', 'Nenhuma'))
        table.add_row("Conectado", "✓" if status_info.get('connected') else "✗")
        table.add_row("Total de Contas", str(status_info.get('total_accounts', 0)))
        table.add_row("Serviços Disponíveis", str(status_info.get('available_services', 0)))
        table.add_row("Nível de Log", status_info.get('log_level', 'INFO'))
        table.add_row("Versão", status_info.get('version', '1.0.0'))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Erro ao obter status: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.pass_context
def add_account(ctx):
    """Adiciona uma nova conta AWS"""
    agent: AWSAgent = ctx.obj['agent']
    
    try:
        console.print("[bold blue]Adicionando Nova Conta AWS[/bold blue]")
        console.print()
        
        # Coleta informações da conta
        account_name = Prompt.ask("Nome da conta (identificador único)", 
                                default=None)
        
        if not account_name:
            console.print("[red]Nome da conta é obrigatório[/red]")
            return
        
        # Verifica se conta já existe
        if account_name in agent.account_manager.list_accounts():
            if not Confirm.ask(f"Conta '{account_name}' já existe. Deseja sobrescrever?"):
                console.print("[yellow]Operação cancelada[/yellow]")
                return
        
        access_key_id = Prompt.ask("AWS Access Key ID")
        secret_access_key = Prompt.ask("AWS Secret Access Key", password=True)
        
        region = Prompt.ask("Região padrão", default="us-east-1")
        
        # Opcionais
        session_token = Prompt.ask("Session Token (opcional, para MFA)", 
                                  default="", show_default=False)
        if not session_token:
            session_token = None
        
        profile_name = Prompt.ask("Nome do perfil", default=account_name)
        
        mfa_serial = Prompt.ask("MFA Serial (opcional)", default="", 
                               show_default=False)
        if not mfa_serial:
            mfa_serial = None
        
        role_arn = Prompt.ask("Role ARN (opcional)", default="", 
                             show_default=False)
        if not role_arn:
            role_arn = None
        
        external_id = Prompt.ask("External ID (opcional)", default="", 
                                show_default=False)
        if not external_id:
            external_id = None
        
        # Adiciona conta
        console.print()
        console.print("[yellow]Validando credenciais...[/yellow]")
        
        success = agent.add_account(
            account_name=account_name,
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            region=region,
            session_token=session_token,
            profile_name=profile_name,
            mfa_serial=mfa_serial,
            role_arn=role_arn,
            external_id=external_id
        )
        
        if success:
            console.print(f"[green]✓ Conta '{account_name}' adicionada com sucesso![/green]")
        else:
            console.print(f"[red]✗ Falha ao adicionar conta '{account_name}'[/red]")
            sys.exit(1)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Operação cancelada pelo usuário[/yellow]")
    except Exception as e:
        console.print(f"[red]Erro ao adicionar conta: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.pass_context
def list_accounts(ctx):
    """Lista todas as contas configuradas"""
    agent: AWSAgent = ctx.obj['agent']
    
    try:
        accounts = agent.list_accounts()
        
        if not accounts:
            console.print("[yellow]Nenhuma conta configurada[/yellow]")
            return
        
        # Cria tabela de contas
        table = Table(title="Contas AWS Configuradas", show_header=True, 
                     header_style="bold magenta")
        table.add_column("Nome", style="cyan")
        table.add_column("Account ID", style="green")
        table.add_column("Região", style="blue")
        table.add_column("Tipo", style="yellow")
        table.add_column("Status", style="white")
        table.add_column("Última Uso", style="dim")
        
        for account in accounts:
            # Determina tipo de credencial
            cred_type = "Temporária" if account.get('is_temporary') else "Permanente"
            
            # Determina status
            status = "🔴 Expirada" if account.get('is_expired') else "🟢 Ativa"
            if account.get('is_current'):
                status = "🔵 Atual"
            
            # Formata última uso
            last_used = account.get('last_used', '')
            if last_used:
                from datetime import datetime
                dt = datetime.fromisoformat(last_used)
                last_used = dt.strftime('%d/%m/%Y %H:%M')
            else:
                last_used = "Nunca"
            
            table.add_row(
                account['account_name'],
                account.get('account_id', 'N/A'),
                account.get('region', 'N/A'),
                cred_type,
                status,
                last_used
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Erro ao listar contas: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('account_name')
@click.pass_context
def remove_account(ctx, account_name):
    """Remove uma conta AWS"""
    agent: AWSAgent = ctx.obj['agent']
    
    try:
        # Verifica se conta existe
        if account_name not in agent.account_manager.list_accounts():
            console.print(f"[red]Conta '{account_name}' não encontrada[/red]")
            sys.exit(1)
        
        # Confirmação
        if not Confirm.ask(f"Deseja realmente remover a conta '{account_name}'?"):
            console.print("[yellow]Operação cancelada[/yellow]")
            return
        
        success = agent.remove_account(account_name)
        
        if success:
            console.print(f"[green]✓ Conta '{account_name}' removida com sucesso![/green]")
        else:
            console.print(f"[red]✗ Falha ao remover conta '{account_name}'[/red]")
            sys.exit(1)
        
    except Exception as e:
        console.print(f"[red]Erro ao remover conta: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('account_name', required=False)
@click.pass_context
def connect(ctx, account_name):
    """Conecta a uma conta AWS"""
    agent: AWSAgent = ctx.obj['agent']
    
    try:
        # Se não especificou conta, mostra menu
        if not account_name:
            accounts = agent.account_manager.list_accounts()
            
            if not accounts:
                console.print("[yellow]Nenhuma conta configurada[/yellow]")
                console.print("Use 'aws-agent add-account' para adicionar uma conta")
                return
            
            # Menu de seleção
            console.print("[bold blue]Contas Disponíveis:[/bold blue]")
            console.print()
            
            for i, acc in enumerate(accounts, 1):
                console.print(f"[cyan]{i}.[/cyan] {acc}")
            
            console.print()
            
            while True:
                try:
                    choice = Prompt.ask("Selecione uma conta", 
                                      choices=[str(i) for i in range(1, len(accounts) + 1)])
                    account_name = accounts[int(choice) - 1]
                    break
                except (ValueError, IndexError):
                    console.print("[red]Opção inválida[/red]")
        
        # Conecta à conta
        console.print(f"[yellow]Conectando à conta '{account_name}'...[/yellow]")
        
        success = agent.connect(account_name)
        
        if success:
            console.print(f"[green]✓ Conectado à conta '{account_name}' com sucesso![/green]")
            
            # Mostra informações da conta
            account_info = agent.get_current_account_info()
            if account_info:
                console.print()
                console.print(f"[bold]Informações da Conta:[/bold]")
                console.print(f"Account ID: {account_info.get('account_id', 'N/A')}")
                console.print(f"Região: {account_info.get('region', 'N/A')}")
                console.print(f"ARN: {account_info.get('current_arn', 'N/A')}")
        else:
            console.print(f"[red]✗ Falha ao conectar à conta '{account_name}'[/red]")
            sys.exit(1)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Operação cancelada pelo usuário[/yellow]")
    except Exception as e:
        console.print(f"[red]Erro ao conectar: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.pass_context
def disconnect(ctx):
    """Desconecta da conta atual"""
    agent: AWSAgent = ctx.obj['agent']
    
    try:
        if not agent.current_account:
            console.print("[yellow]Nenhuma conta conectada[/yellow]")
            return
        
        current_account = agent.current_account
        agent.disconnect()
        
        console.print(f"[green]✓ Desconectado da conta '{current_account}'[/green]")
        
    except Exception as e:
        console.print(f"[red]Erro ao desconectar: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.pass_context
def services(ctx):
    """Lista serviços AWS disponíveis"""
    agent: AWSAgent = ctx.obj['agent']
    
    try:
        services = agent.get_available_services()
        
        if not services:
            console.print("[yellow]Nenhum serviço disponível[/yellow]")
            return
        
        console.print("[bold blue]Serviços AWS Disponíveis:[/bold blue]")
        console.print()
        
        for service in sorted(services):
            operations = agent.get_service_operations(service)
            console.print(f"[cyan]• {service}[/cyan] ({len(operations)} operações)")
        
    except Exception as e:
        console.print(f"[red]Erro ao listar serviços: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--path', '-p', help='Caminho para o backup')
@click.pass_context
def backup(ctx, path):
    """Cria backup da configuração"""
    agent: AWSAgent = ctx.obj['agent']
    
    try:
        console.print("[yellow]Criando backup da configuração...[/yellow]")
        
        success = agent.backup_configuration(path)
        
        if success:
            console.print("[green]✓ Backup criado com sucesso![/green]")
        else:
            console.print("[red]✗ Falha ao criar backup[/red]")
            sys.exit(1)
        
    except Exception as e:
        console.print(f"[red]Erro ao criar backup: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.pass_context
def cleanup(ctx):
    """Remove credenciais expiradas"""
    agent: AWSAgent = ctx.obj['agent']
    
    try:
        console.print("[yellow]Removendo credenciais expiradas...[/yellow]")
        
        expired = agent.cleanup_expired_credentials()
        
        if expired:
            console.print(f"[green]✓ Removidas {len(expired)} credenciais expiradas:[/green]")
            for account in expired:
                console.print(f"  • {account}")
        else:
            console.print("[green]✓ Nenhuma credencial expirada encontrada[/green]")
        
    except Exception as e:
        console.print(f"[red]Erro ao limpar credenciais: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.pass_context
def interactive(ctx):
    """Modo interativo do AWS Agent"""
    agent: AWSAgent = ctx.obj['agent']
    
    try:
        console.print(Panel.fit(
            "[bold blue]AWS Multi-Account Agent[/bold blue]\n"
            "[dim]Modo Interativo Iniciado[/dim]",
            border_style="blue"
        ))
        
        while True:
            console.print()
            
            # Mostra conta atual
            if agent.current_account:
                console.print(f"[green]Conta Atual: {agent.current_account}[/green]")
            else:
                console.print("[yellow]Nenhuma conta conectada[/yellow]")
            
            # Menu de opções
            console.print("\n[bold]Opções disponíveis:[/bold]")
            console.print("1. Listar contas")
            console.print("2. Conectar a uma conta")
            console.print("3. Adicionar conta")
            console.print("4. Remover conta")
            console.print("5. Status do agente")
            console.print("6. Sair")
            
            choice = Prompt.ask("Selecione uma opção", choices=['1', '2', '3', '4', '5', '6'])
            
            if choice == '1':
                ctx.invoke(list_accounts)
            elif choice == '2':
                ctx.invoke(connect)
            elif choice == '3':
                ctx.invoke(add_account)
            elif choice == '4':
                account_name = Prompt.ask("Nome da conta para remover")
                ctx.invoke(remove_account, account_name=account_name)
            elif choice == '5':
                ctx.invoke(status)
            elif choice == '6':
                console.print("[green]Saindo do modo interativo...[/green]")
                break
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Saindo do modo interativo...[/yellow]")
    except Exception as e:
        console.print(f"[red]Erro no modo interativo: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--name', prompt='Nome da conta', help='Nome amigável da conta')
@click.option('--access-key-id', prompt='Access Key ID', help='AWS Access Key ID')
@click.option('--secret-access-key', prompt='Secret Access Key', hide_input=True, help='AWS Secret Access Key')
@click.option('--region', default='us-east-1', prompt='Região', help='Região AWS padrão')
@click.pass_context
def add_account(ctx, name, access_key_id, secret_access_key, region):
    """Adiciona uma nova conta AWS"""
    agent: AWSAgent = ctx.obj['agent']
    
    console.print(f"\n➕ Adicionando conta '{name}'...", style="bold")
    
    success = agent.add_account(
        account_name=name,
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        region=region
    )
    
    if success:
        print_success(f"Conta '{name}' adicionada com sucesso")
    else:
        print_error(f"Falha ao adicionar conta '{name}'")

@cli.command()
@click.pass_context
def start(ctx):
    """Inicia o agente AWS com seleção interativa de conta"""
    agent: AWSAgent = ctx.obj['agent']
    
    print_logo()
    console.print("Iniciando AWS Multi-Account Agent...\n", style="bold")
    
    # Lista contas disponíveis
    accounts = agent.list_accounts()
    
    if not accounts:
        print_warning("Nenhuma conta AWS configurada.")
        if Confirm.ask("Deseja adicionar uma conta agora?"):
            ctx.invoke(add_account)
            return
        else:
            print_info("Use 'aws-agent add-account' para adicionar uma conta")
            return
    
    # Exibe tabela de contas
    table = Table(title="Contas AWS Disponíveis", show_header=True)
    table.add_column("Nome", style="cyan")
    table.add_column("Account ID", style="magenta")
    table.add_column("Região", style="green")
    table.add_column("Última Utilização", style="yellow")
    table.add_column("Status", style="red")
    
    for account in accounts:
        status = "🟢 Ativa" if account.get('is_current') else "⚪ Disponível"
        if account.get('is_expired'):
            status = "🔴 Expirada"
        
        table.add_row(
            account['account_name'],
            account.get('account_id', 'N/A'),
            account.get('region', 'N/A'),
            account.get('last_used', 'Nunca')[:19] if account.get('last_used') else 'Nunca',
            status
        )
    
    console.print(table)
    
    # Seleção de conta
    account_names = [acc['account_name'] for acc in accounts]
    
    while True:
        selected = Prompt.ask(
            "\nSelecione uma conta para conectar",
            choices=account_names + ['sair'],
            default=account_names[0] if account_names else 'sair'
        )
        
        if selected == 'sair':
            console.print("Saindo...", style="bold yellow")
            return
        
        if agent.connect(selected):
            print_success(f"Conectado à conta '{selected}'")
            break
        else:
            print_error(f"Falha ao conectar à conta '{selected}'")
            continue
    
    # Menu principal
    show_main_menu(ctx)

@cli.command()
@click.pass_context
def list_accounts(ctx):
    """Lista todas as contas AWS configuradas"""
    agent: AWSAgent = ctx.obj['agent']
    
    accounts = agent.list_accounts()
    
    if not accounts:
        print_info("Nenhuma conta AWS configurada")
        return
    
    table = Table(title="Contas AWS Configuradas", show_header=True)
    table.add_column("Nome", style="cyan")
    table.add_column("Account ID", style="magenta")
    table.add_column("Região", style="green")
    table.add_column("Status", style="red")
    
    for account in accounts:
        status = "🟢 Atual" if account.get('is_current') else "⚪ Disponível"
        if account.get('is_expired'):
            status = "🔴 Expirada"
        
        table.add_row(
            account['account_name'],
            account.get('account_id', 'N/A'),
            account.get('region', 'N/A'),
            status
        )
    
    console.print(table)

def show_main_menu(ctx):
    """Exibe o menu principal do agente"""
    agent: AWSAgent = ctx.obj['agent']
    
    while True:
        console.print("\n" + "="*60, style="bold")
        console.print("MENU PRINCIPAL", style="bold blue", justify="center")
        console.print("="*60, style="bold")
        
        account_info = agent.get_current_account_info()
        if account_info:
            console.print(f"📊 Conta atual: {account_info['account_name']} ({account_info['account_id']})")
            console.print(f"🌍 Região: {account_info['region']}")
        
        options = [
            "1. Gerenciar EC2 (Instâncias)",
            "2. Gerenciar S3 (Armazenamento)",
            "3. Gerenciar IAM (Identidades e Acessos)",
            "4. Gerenciar Lambda (Funções)",
            "5. Listar contas",
            "6. Trocar conta",
            "7. Adicionar conta",
            "8. Remover conta",
            "9. Informações da conta atual",
            "10. Status do agente",
            "11. Configurações",
            "12. Sair"
        ]
        
        for option in options:
            console.print(f"  {option}")
        
        choice = Prompt.ask("\nEscolha uma opção", choices=['1','2','3','4','5','6','7','8','9','10','11','12'])
        
        if choice == '1':
            ctx.invoke(ec2)
        elif choice == '2':
            ctx.invoke(s3)
        elif choice == '3':
            ctx.invoke(iam)
        elif choice == '4':
            ctx.invoke(lambda_cmd)
        elif choice == '5':
            ctx.invoke(list_accounts)
        elif choice == '6':
            ctx.invoke(connect)
        elif choice == '7':
            ctx.invoke(add_account)
        elif choice == '8':
            ctx.invoke(remove_account)
        elif choice == '9':
            ctx.invoke(account_info)
        elif choice == '10':
            ctx.invoke(status)
        elif choice == '11':
            show_config_menu(ctx)
        elif choice == '12':
            console.print("Saindo do AWS Agent...", style="bold yellow")
            agent.disconnect()
            break

def show_config_menu(ctx):
    """Exibe menu de configurações"""
    config = get_config()
    
    console.print("\n⚙️  CONFIGURAÇÕES", style="bold blue")
    
    table = Table(show_header=True)
    table.add_column("Configuração", style="cyan")
    table.add_column("Valor", style="magenta")
    
    table.add_row("Diretório de configuração", str(config.config_dir))
    table.add_row("Nível de log", config.log_level)
    table.add_row("Região padrão", config.default_region)
    table.add_row("Timeout de sessão", f"{config.session_timeout}s")
    table.add_row("Versão", config.version)
    
    console.print(table)


# ==============================================================================
# COMANDOS DOS SERVIÇOS AWS
# ==============================================================================

@cli.command()
@click.pass_context
def ec2(ctx):
    """Operações EC2"""
    agent: AWSAgent = ctx.obj['agent']
    
    if not agent.current_account:
        print_error("Nenhuma conta conectada. Use 'connect' primeiro.")
        return
    
    if 'ec2' not in agent.services:
        print_error("Serviço EC2 não disponível")
        return
    
    ec2_service = agent.services['ec2']
    
    while True:
        console.print("\n" + "="*50, style="bold")
        console.print("EC2 - AMAZON ELASTIC COMPUTE CLOUD", style="bold blue", justify="center")
        console.print("="*50, style="bold")
        
        options = [
            "1. Listar instâncias",
            "2. Conectar à primeira instância",
            "3. Detalhes de instância",
            "4. Gerenciar instância (start/stop/reboot)",
            "5. Listar volumes",
            "6. Listar security groups",
            "7. Listar key pairs",
            "8. Voltar ao menu principal"
        ]
        
        for option in options:
            console.print(f"  {option}")
        
        choice = Prompt.ask("\nEscolha uma opção", choices=['1','2','3','4','5','6','7','8'])
        
        if choice == '1':
            show_instances(ec2_service)
        elif choice == '2':
            connect_to_first_instance(ec2_service)
        elif choice == '3':
            show_instance_details(ec2_service)
        elif choice == '4':
            manage_instance(ec2_service)
        elif choice == '5':
            show_volumes(ec2_service)
        elif choice == '6':
            show_security_groups(ec2_service)
        elif choice == '7':
            show_key_pairs(ec2_service)
        elif choice == '8':
            break


@cli.command()
@click.pass_context
def s3(ctx):
    """Operações S3"""
    agent: AWSAgent = ctx.obj['agent']
    
    if not agent.current_account:
        print_error("Nenhuma conta conectada. Use 'connect' primeiro.")
        return
    
    from ..services.s3 import S3Service
    s3_service = S3Service(agent.current_session, agent.get_current_region())
    
    while True:
        console.print("\n" + "="*50, style="bold")
        console.print("S3 - AMAZON SIMPLE STORAGE SERVICE", style="bold blue", justify="center")
        console.print("="*50, style="bold")
        
        options = [
            "1. Listar buckets",
            "2. Criar bucket",
            "3. Listar objetos em bucket",
            "4. Upload de arquivo",
            "5. Download de arquivo",
            "6. Deletar objeto",
            "7. Deletar bucket",
            "8. Informações de bucket",
            "9. Voltar ao menu principal"
        ]
        
        for option in options:
            console.print(f"  {option}")
        
        choice = Prompt.ask("\nEscolha uma opção", choices=['1','2','3','4','5','6','7','8','9'])
        
        if choice == '1':
            show_s3_buckets(s3_service)
        elif choice == '2':
            create_s3_bucket(s3_service)
        elif choice == '3':
            list_s3_objects(s3_service)
        elif choice == '4':
            upload_s3_file(s3_service)
        elif choice == '5':
            download_s3_file(s3_service)
        elif choice == '6':
            delete_s3_object(s3_service)
        elif choice == '7':
            delete_s3_bucket(s3_service)
        elif choice == '8':
            show_s3_bucket_info(s3_service)
        elif choice == '9':
            break


@cli.command()
@click.pass_context
def iam(ctx):
    """Operações IAM"""
    agent: AWSAgent = ctx.obj['agent']
    
    if not agent.current_account:
        print_error("Nenhuma conta conectada. Use 'connect' primeiro.")
        return
    
    from ..services.iam import IAMService
    iam_service = IAMService(agent.current_session, agent.get_current_region())
    
    while True:
        console.print("\n" + "="*50, style="bold")
        console.print("IAM - IDENTITY AND ACCESS MANAGEMENT", style="bold blue", justify="center")
        console.print("="*50, style="bold")
        
        options = [
            "1. Usuário atual",
            "2. Listar usuários",
            "3. Listar grupos",
            "4. Listar roles",
            "5. Listar políticas",
            "6. Criar usuário",
            "7. Criar chave de acesso",
            "8. Resumo da conta",
            "9. Voltar ao menu principal"
        ]
        
        for option in options:
            console.print(f"  {option}")
        
        choice = Prompt.ask("\nEscolha uma opção", choices=['1','2','3','4','5','6','7','8','9'])
        
        if choice == '1':
            show_iam_current_user(iam_service)
        elif choice == '2':
            show_iam_users(iam_service)
        elif choice == '3':
            show_iam_groups(iam_service)
        elif choice == '4':
            show_iam_roles(iam_service)
        elif choice == '5':
            show_iam_policies(iam_service)
        elif choice == '6':
            create_iam_user(iam_service)
        elif choice == '7':
            create_iam_access_key(iam_service)
        elif choice == '8':
            show_iam_account_summary(iam_service)
        elif choice == '9':
            break


@cli.command('lambda')
@click.pass_context
def lambda_cmd(ctx):
    """Operações Lambda"""
    agent: AWSAgent = ctx.obj['agent']
    
    if not agent.current_account:
        print_error("Nenhuma conta conectada. Use 'connect' primeiro.")
        return
    
    from ..services.lambda_service import LambdaService
    lambda_service = LambdaService(agent.current_session, agent.get_current_region())
    
    while True:
        console.print("\n" + "="*50, style="bold")
        console.print("LAMBDA - SERVERLESS COMPUTE", style="bold blue", justify="center")
        console.print("="*50, style="bold")
        
        options = [
            "1. Listar funções",
            "2. Detalhes de função",
            "3. Invocar função",
            "4. Listar versões",
            "5. Listar aliases",
            "6. Ver logs",
            "7. Mapeamentos de eventos",
            "8. Voltar ao menu principal"
        ]
        
        for option in options:
            console.print(f"  {option}")
        
        choice = Prompt.ask("\nEscolha uma opção", choices=['1','2','3','4','5','6','7','8'])
        
        if choice == '1':
            show_lambda_functions(lambda_service)
        elif choice == '2':
            show_lambda_function_details(lambda_service)
        elif choice == '3':
            invoke_lambda_function(lambda_service)
        elif choice == '4':
            show_lambda_versions(lambda_service)
        elif choice == '5':
            show_lambda_aliases(lambda_service)
        elif choice == '6':
            show_lambda_logs(lambda_service)
        elif choice == '7':
            show_lambda_event_mappings(lambda_service)
        elif choice == '8':
            break


@cli.command()
@click.pass_context
def account_info(ctx):
    """Informações da conta atual"""
    agent: AWSAgent = ctx.obj['agent']
    
    if not agent.current_account:
        print_error("Nenhuma conta conectada")
        return
    
    account_info = agent.get_current_account_info()
    
    if not account_info:
        print_error("Não foi possível obter informações da conta")
        return
    
    console.print(f"\n📊 Informações da conta '{agent.current_account}'", style="bold")
    
    table = Table(show_header=False)
    table.add_column("Propriedade", style="cyan")
    table.add_column("Valor", style="magenta")
    
    table.add_row("Nome da Conta", account_info.get('account_name', 'N/A'))
    table.add_row("Account ID", account_info.get('account_id', 'N/A'))
    table.add_row("Região", account_info.get('region', 'N/A'))
    table.add_row("User ID Atual", account_info.get('current_user_id', 'N/A'))
    table.add_row("ARN Atual", account_info.get('current_arn', 'N/A'))
    table.add_row("Sessão Válida", "✓" if account_info.get('session_valid') else "✗")
    
    console.print(table)


# ==============================================================================
# FUNÇÕES AUXILIARES DOS SERVIÇOS
# ==============================================================================

def show_instances(ec2_service):
    """Lista instâncias EC2"""
    console.print("\n📋 Listando instâncias EC2...", style="bold")
    try:
        instances = ec2_service.list_instances()
        if not instances:
            print_info("Nenhuma instância encontrada")
            return
        
        table = Table(title="Instâncias EC2", show_header=True)
        table.add_column("ID", style="cyan")
        table.add_column("Nome", style="magenta")
        table.add_column("Estado", style="green")
        table.add_column("Tipo", style="yellow")
        
        for instance in instances:
            table.add_row(
                instance.get('instance_id', 'N/A'),
                instance.get('name', 'N/A'),
                instance.get('state', 'N/A'),
                instance.get('instance_type', 'N/A')
            )
        
        console.print(table)
    except Exception as e:
        print_error(f"Erro ao listar instâncias: {e}")

def connect_to_first_instance(ec2_service):
    """Conecta à primeira instância disponível"""
    print_info("Funcionalidade de conexão não implementada nesta versão")

def show_instance_details(ec2_service):
    """Mostra detalhes de uma instância"""
    print_info("Funcionalidade de detalhes não implementada nesta versão")

def manage_instance(ec2_service):
    """Gerencia uma instância"""
    print_info("Funcionalidade de gerenciamento não implementada nesta versão")

def show_volumes(ec2_service):
    """Lista volumes EBS"""
    print_info("Funcionalidade de volumes não implementada nesta versão")

def show_security_groups(ec2_service):
    """Lista security groups"""
    print_info("Funcionalidade de security groups não implementada nesta versão")

def show_key_pairs(ec2_service):
    """Lista key pairs"""
    print_info("Funcionalidade de key pairs não implementada nesta versão")

def show_s3_buckets(s3_service):
    """Lista buckets S3"""
    console.print("\n🪣 Listando buckets S3...", style="bold")
    try:
        buckets = s3_service.list_buckets()
        if not buckets:
            print_info("Nenhum bucket encontrado")
            return
        
        table = Table(title="Buckets S3", show_header=True)
        table.add_column("Nome", style="cyan")
        table.add_column("Região", style="green")
        
        for bucket in buckets:
            table.add_row(
                bucket.get('name', 'N/A'),
                bucket.get('region', 'N/A')
            )
        
        console.print(table)
    except Exception as e:
        print_error(f"Erro ao listar buckets: {e}")

def create_s3_bucket(s3_service):
    """Cria um bucket S3"""
    print_info("Funcionalidade de criação de bucket não implementada nesta versão")

def list_s3_objects(s3_service):
    """Lista objetos em um bucket"""
    print_info("Funcionalidade de listagem de objetos não implementada nesta versão")

def upload_s3_file(s3_service):
    """Upload de arquivo para S3"""
    print_info("Funcionalidade de upload não implementada nesta versão")

def download_s3_file(s3_service):
    """Download de arquivo do S3"""
    print_info("Funcionalidade de download não implementada nesta versão")

def delete_s3_object(s3_service):
    """Deleta um objeto do S3"""
    print_info("Funcionalidade de deleção de objeto não implementada nesta versão")

def delete_s3_bucket(s3_service):
    """Deleta um bucket S3"""
    print_info("Funcionalidade de deleção de bucket não implementada nesta versão")

def show_s3_bucket_info(s3_service):
    """Mostra informações de um bucket"""
    print_info("Funcionalidade de informações de bucket não implementada nesta versão")

def show_iam_current_user(iam_service):
    """Mostra informações do usuário atual"""
    console.print("\n👤 Informações do usuário atual...", style="bold")
    try:
        user = iam_service.get_current_user()
        if not user:
            print_error("Não foi possível obter informações do usuário")
            return
        
        table = Table(show_header=False)
        table.add_column("Propriedade", style="cyan")
        table.add_column("Valor", style="magenta")
        
        table.add_row("Nome", user.get('username', 'N/A'))
        table.add_row("ARN", user.get('arn', 'N/A'))
        
        console.print(table)
    except Exception as e:
        print_error(f"Erro ao obter usuário atual: {e}")

def show_iam_users(iam_service):
    """Lista usuários IAM"""
    print_info("Funcionalidade de listagem de usuários não implementada nesta versão")

def show_iam_groups(iam_service):
    """Lista grupos IAM"""
    print_info("Funcionalidade de listagem de grupos não implementada nesta versão")

def show_iam_roles(iam_service):
    """Lista roles IAM"""
    print_info("Funcionalidade de listagem de roles não implementada nesta versão")

def show_iam_policies(iam_service):
    """Lista políticas IAM"""
    print_info("Funcionalidade de listagem de políticas não implementada nesta versão")

def create_iam_user(iam_service):
    """Cria um usuário IAM"""
    print_info("Funcionalidade de criação de usuário não implementada nesta versão")

def create_iam_access_key(iam_service):
    """Cria uma chave de acesso para um usuário"""
    print_info("Funcionalidade de criação de chave de acesso não implementada nesta versão")

def show_iam_account_summary(iam_service):
    """Mostra resumo da conta IAM"""
    print_info("Funcionalidade de resumo da conta não implementada nesta versão")

def show_lambda_functions(lambda_service):
    """Lista funções Lambda"""
    console.print("\n⚡ Listando funções Lambda...", style="bold")
    try:
        functions = lambda_service.list_functions()
        if not functions:
            print_info("Nenhuma função encontrada")
            return
        
        table = Table(title="Funções Lambda", show_header=True)
        table.add_column("Nome", style="cyan")
        table.add_column("Runtime", style="green")
        table.add_column("Handler", style="yellow")
        
        for func in functions:
            table.add_row(
                func.get('function_name', 'N/A'),
                func.get('runtime', 'N/A'),
                func.get('handler', 'N/A')
            )
        
        console.print(table)
    except Exception as e:
        print_error(f"Erro ao listar funções: {e}")

def show_lambda_function_details(lambda_service):
    """Mostra detalhes de uma função Lambda"""
    print_info("Funcionalidade de detalhes de função não implementada nesta versão")

def invoke_lambda_function(lambda_service):
    """Invoca uma função Lambda"""
    print_info("Funcionalidade de invocação não implementada nesta versão")

def show_lambda_versions(lambda_service):
    """Mostra versões de uma função Lambda"""
    print_info("Funcionalidade de versões não implementada nesta versão")

def show_lambda_aliases(lambda_service):
    """Mostra aliases de uma função Lambda"""
    print_info("Funcionalidade de aliases não implementada nesta versão")

def show_lambda_logs(lambda_service):
    """Mostra logs de uma função Lambda"""
    print_info("Funcionalidade de logs não implementada nesta versão")

def show_lambda_event_mappings(lambda_service):
    """Mostra mapeamentos de eventos Lambda"""
    print_info("Funcionalidade de mapeamentos de eventos não implementada nesta versão")


def main():
    """Função principal do CLI"""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n\nOperação interrompida pelo usuário", style="bold yellow")
        sys.exit(1)
    except Exception as e:
        print_error(f"Erro inesperado: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
