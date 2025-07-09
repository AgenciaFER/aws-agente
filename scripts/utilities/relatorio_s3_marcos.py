#!/usr/bin/env python3
"""
Relatório completo das instâncias S3 do usuário Marcos
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from aws_agent.core.agent import AWSAgent
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def generate_s3_report():
    """Gera relatório completo dos recursos S3"""
    
    # Header
    console.print(Panel.fit(
        "🪣 RELATÓRIO S3 - USUÁRIO MARCOS\n"
        "AWS Multi-Account Agent",
        style="bold blue"
    ))
    
    # Conectar
    agent = AWSAgent()
    
    try:
        if agent.connect('marcos'):
            console.print("✅ Conectado à conta AWS", style="green")
            
            account_info = agent.get_current_account_info()
            console.print(f"📊 Account ID: {account_info['account_id']}")
            console.print(f"🌍 Região: {account_info['region']}")
            console.print(f"👤 Usuário: {account_info['current_arn'].split('/')[-1]}")
            console.print()
            
            s3_service = agent.services.get('s3')
            if s3_service:
                # Tabela principal de buckets
                bucket_table = Table(title="🪣 Buckets S3", show_header=True)
                bucket_table.add_column("ID", style="dim", width=3)
                bucket_table.add_column("Nome do Bucket", style="cyan", no_wrap=True)
                bucket_table.add_column("Região", style="green", width=10)
                bucket_table.add_column("Data de Criação", style="yellow", width=12)
                bucket_table.add_column("Objetos", style="magenta", width=8)
                bucket_table.add_column("Tamanho Total", style="blue", width=12)
                
                buckets = s3_service.list_buckets()
                total_objects = 0
                total_size = 0
                
                for i, bucket in enumerate(buckets, 1):
                    bucket_name = bucket['name']
                    bucket_region = bucket['region']
                    bucket_date = str(bucket['creation_date']).split(' ')[0]
                    
                    # Estatísticas do bucket
                    try:
                        objects = s3_service.list_objects(bucket_name)
                        obj_count = len(objects)
                        bucket_size = sum(obj['size'] for obj in objects)
                        
                        total_objects += obj_count
                        total_size += bucket_size
                        
                        # Formatar tamanho
                        if bucket_size > 1024*1024:
                            size_str = f"{bucket_size/(1024*1024):.2f} MB"
                        elif bucket_size > 1024:
                            size_str = f"{bucket_size/1024:.2f} KB"
                        else:
                            size_str = f"{bucket_size} B"
                        
                    except Exception as e:
                        obj_count = "Erro"
                        size_str = "N/A"
                    
                    bucket_table.add_row(
                        str(i),
                        bucket_name,
                        bucket_region,
                        bucket_date,
                        str(obj_count),
                        size_str
                    )
                
                console.print(bucket_table)
                
                # Resumo estatístico
                console.print()
                stats_table = Table(title="📊 Estatísticas Gerais", show_header=False)
                stats_table.add_column("Métrica", style="cyan", width=20)
                stats_table.add_column("Valor", style="bold magenta")
                
                # Formatar tamanho total
                if total_size > 1024*1024:
                    total_size_str = f"{total_size/(1024*1024):.2f} MB"
                elif total_size > 1024:
                    total_size_str = f"{total_size/1024:.2f} KB"
                else:
                    total_size_str = f"{total_size} bytes"
                
                stats_table.add_row("Total de Buckets", str(len(buckets)))
                stats_table.add_row("Total de Objetos", str(total_objects))
                stats_table.add_row("Tamanho Total", total_size_str)
                stats_table.add_row("Região Principal", "us-east-1")
                
                console.print(stats_table)
                
                # Detalhes dos objetos por bucket
                if buckets and total_objects > 0:
                    console.print()
                    console.print("📋 [bold]Detalhes dos Objetos por Bucket:[/bold]")
                    
                    for bucket in buckets:
                        bucket_name = bucket['name']
                        
                        try:
                            objects = s3_service.list_objects(bucket_name)
                            
                            if objects:
                                console.print(f"\n🗂️  [bold cyan]{bucket_name}[/bold cyan]:")
                                
                                obj_table = Table(show_header=True, box=None)
                                obj_table.add_column("Arquivo", style="white")
                                obj_table.add_column("Tamanho", style="green", width=10)
                                obj_table.add_column("Modificado", style="yellow", width=12)
                                obj_table.add_column("Tipo", style="blue", width=15)
                                
                                for obj in objects:
                                    # Determinar tipo de arquivo
                                    key = obj['key']
                                    if '.' in key:
                                        file_type = key.split('.')[-1].upper()
                                    else:
                                        file_type = "Pasta" if key.endswith('/') else "Arquivo"
                                    
                                    # Formatar tamanho
                                    size = obj['size']
                                    if size > 1024:
                                        size_str = f"{size/1024:.1f} KB"
                                    else:
                                        size_str = f"{size} B"
                                    
                                    # Data
                                    date_str = str(obj['last_modified']).split(' ')[0]
                                    
                                    obj_table.add_row(
                                        key,
                                        size_str,
                                        date_str,
                                        file_type
                                    )
                                
                                console.print(obj_table)
                            else:
                                console.print(f"\n📭 [dim]{bucket_name}: Bucket vazio[/dim]")
                                
                        except Exception as e:
                            console.print(f"\n❌ [red]{bucket_name}: Erro ao listar objetos[/red]")
                
                # Comandos úteis
                console.print()
                console.print("💡 [bold]Comandos Úteis:[/bold]")
                console.print("• [cyan]python -m aws_agent.cli.main start[/cyan] - CLI interativo")
                console.print("• [cyan]python -m aws_agent.cli.main s3[/cyan] - Menu S3 direto")
                console.print("• [cyan]Opção 2[/cyan] no menu principal - Gerenciar S3")
                
            else:
                console.print("❌ Serviço S3 não disponível", style="red")
        
        else:
            console.print("❌ Falha na conexão", style="red")
    
    except Exception as e:
        console.print(f"❌ Erro: {e}", style="red")
    
    finally:
        agent.disconnect()
        console.print("\n📴 [dim]Desconectado[/dim]")

if __name__ == "__main__":
    generate_s3_report()
