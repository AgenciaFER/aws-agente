#!/usr/bin/env python3
"""
Exemplo avançado de uso do AWS Multi-Account Agent

Este exemplo demonstra como usar o agente para gerenciar
múltiplas contas AWS e realizar operações automatizadas.
"""

import os
import sys
from pathlib import Path
import asyncio
from typing import List, Dict, Any

# Adiciona o diretório src ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from aws_agent.core.agent import AWSAgent
from aws_agent.core.account_manager import AWSCredentials
from aws_agent.services.ec2 import EC2Service
from aws_agent.services.s3 import S3Service
from aws_agent.services.iam import IAMService
from aws_agent.services.lambda_service import LambdaService


def print_banner():
    """Exibe banner do exemplo"""
    print("=" * 70)
    print("🚀 AWS Multi-Account Agent - Exemplo Avançado")
    print("=" * 70)
    print()


def demonstrate_account_management():
    """Demonstra gerenciamento de contas"""
    print("📋 1. Gerenciamento de Contas AWS")
    print("-" * 40)
    
    # Inicializa o agente
    agent = AWSAgent()
    
    # Lista contas existentes
    accounts = agent.list_accounts()
    print(f"Contas configuradas: {len(accounts)}")
    
    if accounts:
        for account in accounts:
            print(f"  - {account['account_name']} ({account['account_id']})")
            print(f"    Região: {account['region']}")
            print(f"    Criada em: {account['created_at']}")
    else:
        print("  Nenhuma conta configurada ainda.")
    
    print()
    return agent


def demonstrate_ec2_operations(agent: AWSAgent):
    """Demonstra operações EC2"""
    print("🖥️  2. Operações EC2")
    print("-" * 40)
    
    if not agent.current_session:
        print("❌ Nenhuma conta conectada. Use 'aws-agent connect <conta>' primeiro.")
        return
    
    # Cria serviço EC2
    ec2_service = EC2Service(agent.current_session, agent.get_current_region())
    
    # Lista instâncias
    print("Listando instâncias EC2...")
    instances = ec2_service.list_instances()
    
    if instances:
        print(f"Encontradas {len(instances)} instâncias:")
        for instance in instances[:5]:  # Primeiras 5
            print(f"  - {instance['instance_id']}: {instance['name']} ({instance['state']})")
            print(f"    Tipo: {instance['instance_type']}")
            print(f"    IP Público: {instance['public_ip'] or 'N/A'}")
    else:
        print("  Nenhuma instância encontrada.")
    
    # Lista security groups
    print("\nListando security groups...")
    security_groups = ec2_service.list_security_groups()
    print(f"Encontrados {len(security_groups)} security groups.")
    
    # Lista key pairs
    print("\nListando key pairs...")
    key_pairs = ec2_service.list_key_pairs()
    print(f"Encontrados {len(key_pairs)} key pairs.")
    
    print()


def demonstrate_s3_operations(agent: AWSAgent):
    """Demonstra operações S3"""
    print("🪣 3. Operações S3")
    print("-" * 40)
    
    if not agent.current_session:
        print("❌ Nenhuma conta conectada.")
        return
    
    # Cria serviço S3
    s3_service = S3Service(agent.current_session, agent.get_current_region())
    
    # Lista buckets
    print("Listando buckets S3...")
    buckets = s3_service.list_buckets()
    
    if buckets:
        print(f"Encontrados {len(buckets)} buckets:")
        for bucket in buckets[:5]:  # Primeiros 5
            print(f"  - {bucket['name']} (região: {bucket['region']})")
            print(f"    Criado em: {bucket['creation_date'].strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Lista objetos do bucket (apenas primeiros 3)
            objects = s3_service.list_objects(bucket['name'], max_keys=3)
            if objects:
                print(f"    Objetos ({len(objects)} de {len(objects)}+):")
                for obj in objects:
                    size = obj['size']
                    if size < 1024:
                        size_str = f"{size} B"
                    elif size < 1024*1024:
                        size_str = f"{size/1024:.1f} KB"
                    else:
                        size_str = f"{size/(1024*1024):.1f} MB"
                    print(f"      - {obj['key']} ({size_str})")
            else:
                print("    Bucket vazio")
    else:
        print("  Nenhum bucket encontrado.")
    
    print()


def demonstrate_iam_operations(agent: AWSAgent):
    """Demonstra operações IAM"""
    print("👤 4. Operações IAM")
    print("-" * 40)
    
    if not agent.current_session:
        print("❌ Nenhuma conta conectada.")
        return
    
    # Cria serviço IAM
    iam_service = IAMService(agent.current_session, agent.get_current_region())
    
    # Obtém usuário atual
    print("Informações do usuário atual:")
    current_user = iam_service.get_current_user()
    if current_user:
        print(f"  - Nome: {current_user['username']}")
        print(f"  - ARN: {current_user['arn']}")
        print(f"  - ID: {current_user['user_id']}")
    
    # Lista usuários
    print("\nListando usuários IAM...")
    users = iam_service.list_users()
    print(f"Encontrados {len(users)} usuários.")
    
    # Lista grupos
    print("\nListando grupos IAM...")
    groups = iam_service.list_groups()
    print(f"Encontrados {len(groups)} grupos.")
    
    # Lista roles
    print("\nListando roles IAM...")
    roles = iam_service.list_roles()
    print(f"Encontradas {len(roles)} roles.")
    
    # Resumo da conta
    print("\nResumo da conta:")
    summary = iam_service.get_account_summary()
    if summary:
        print(f"  - Usuários: {summary.get('Users', 'N/A')}")
        print(f"  - Grupos: {summary.get('Groups', 'N/A')}")
        print(f"  - Roles: {summary.get('Roles', 'N/A')}")
        print(f"  - Políticas: {summary.get('Policies', 'N/A')}")
    
    print()


def demonstrate_lambda_operations(agent: AWSAgent):
    """Demonstra operações Lambda"""
    print("⚡ 5. Operações Lambda")
    print("-" * 40)
    
    if not agent.current_session:
        print("❌ Nenhuma conta conectada.")
        return
    
    # Cria serviço Lambda
    lambda_service = LambdaService(agent.current_session, agent.get_current_region())
    
    # Lista funções
    print("Listando funções Lambda...")
    functions = lambda_service.list_functions()
    
    if functions:
        print(f"Encontradas {len(functions)} funções:")
        for func in functions[:5]:  # Primeiras 5
            print(f"  - {func['function_name']}")
            print(f"    Runtime: {func['runtime']}")
            print(f"    Memória: {func['memory_size']} MB")
            print(f"    Timeout: {func['timeout']}s")
            print(f"    Tamanho: {func['code_size']} bytes")
            print(f"    Última modificação: {func['last_modified']}")
            
            # Lista versões
            versions = lambda_service.list_versions(func['function_name'])
            if len(versions) > 1:  # Mais que só $LATEST
                print(f"    Versões: {len(versions)}")
            
            # Lista aliases
            aliases = lambda_service.list_aliases(func['function_name'])
            if aliases:
                print(f"    Aliases: {', '.join([a['name'] for a in aliases])}")
            
            print()
    else:
        print("  Nenhuma função encontrada.")
    
    print()


def demonstrate_automation_scenario(agent: AWSAgent):
    """Demonstra cenário de automação"""
    print("🤖 6. Cenário de Automação - Auditoria de Segurança")
    print("-" * 50)
    
    if not agent.current_session:
        print("❌ Nenhuma conta conectada.")
        return
    
    security_issues = []
    
    # Cria serviços
    ec2_service = EC2Service(agent.current_session, agent.get_current_region())
    s3_service = S3Service(agent.current_session, agent.get_current_region())
    iam_service = IAMService(agent.current_session, agent.get_current_region())
    
    print("Executando auditoria de segurança...")
    
    # 1. Verifica instâncias EC2 com security groups muito permissivos
    print("  ✓ Verificando security groups EC2...")
    security_groups = ec2_service.list_security_groups()
    for sg in security_groups:
        if sg['inbound_rules'] > 10:
            security_issues.append({
                'service': 'EC2',
                'resource': sg['group_id'],
                'issue': f"Security group com muitas regras ({sg['inbound_rules']})",
                'severity': 'medium'
            })
    
    # 2. Verifica buckets S3 públicos (simulado)
    print("  ✓ Verificando buckets S3...")
    buckets = s3_service.list_buckets()
    for bucket in buckets:
        # Em um cenário real, verificaríamos ACLs e políticas
        # Aqui simulamos encontrar alguns issues
        if 'public' in bucket['name'].lower() or 'temp' in bucket['name'].lower():
            security_issues.append({
                'service': 'S3',
                'resource': bucket['name'],
                'issue': "Bucket com nome suspeito de ser público",
                'severity': 'high'
            })
    
    # 3. Verifica usuários IAM sem MFA
    print("  ✓ Verificando configurações IAM...")
    users = iam_service.list_users()
    if len(users) > 50:
        security_issues.append({
            'service': 'IAM',
            'resource': 'Account',
            'issue': f"Muitos usuários IAM ({len(users)}), considere usar roles",
            'severity': 'low'
        })
    
    # Relatório de auditoria
    print(f"\n📊 Relatório de Auditoria Completo:")
    print(f"   Total de issues encontrados: {len(security_issues)}")
    
    if security_issues:
        print("\n🚨 Issues de Segurança:")
        for issue in security_issues:
            severity_emoji = {'low': '🟡', 'medium': '🟠', 'high': '🔴'}
            print(f"   {severity_emoji[issue['severity']]} [{issue['service']}] {issue['resource']}")
            print(f"      {issue['issue']}")
    else:
        print("   ✅ Nenhum issue de segurança encontrado!")
    
    print()


def main():
    """Função principal do exemplo"""
    print_banner()
    
    try:
        # 1. Gerenciamento de contas
        agent = demonstrate_account_management()
        
        # Verifica se há conta conectada
        status = agent.get_status()
        if not status['connected']:
            print("🔗 Para demonstrar as operações AWS, conecte-se a uma conta:")
            print("   aws-agent connect <nome-da-conta>")
            print()
            print("   Ou adicione uma nova conta:")
            print("   aws-agent add-account")
            print()
            return
        
        print(f"📡 Conectado à conta: {status['current_account']}")
        print(f"🌍 Região: {agent.get_current_region()}")
        print()
        
        # 2-5. Demonstrações de serviços
        demonstrate_ec2_operations(agent)
        demonstrate_s3_operations(agent)
        demonstrate_iam_operations(agent)
        demonstrate_lambda_operations(agent)
        
        # 6. Cenário de automação
        demonstrate_automation_scenario(agent)
        
        print("🎉 Demonstração concluída!")
        print()
        print("💡 Próximos passos:")
        print("   - Explore mais comandos: aws-agent --help")
        print("   - Use o modo interativo: aws-agent interactive")
        print("   - Veja exemplos específicos na pasta examples/")
        
    except KeyboardInterrupt:
        print("\n\n👋 Demonstração interrompida pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro durante a demonstração: {e}")
        print("   Verifique se todas as dependências estão instaladas.")
        sys.exit(1)


if __name__ == "__main__":
    main()
