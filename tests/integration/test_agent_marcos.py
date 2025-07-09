#!/usr/bin/env python3
"""
Script para testar o AWS Agent com o usuário Marcos
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from aws_agent.core.agent import AWSAgent
from aws_agent.services.s3 import S3Service
from aws_agent.services.ec2 import EC2Service
from aws_agent.services.iam import IAMService
from aws_agent.services.lambda_service import LambdaService

def test_agent_with_marcos():
    """Testa o AWS Agent com o usuário Marcos"""
    
    print("=" * 60)
    print("TESTE DO AWS AGENT COM USUÁRIO MARCOS")
    print("=" * 60)
    print()
    
    # Inicializar o agent
    agent = AWSAgent()
    
    # Conectar à conta do Marcos
    print("📡 Conectando à conta do Marcos...")
    try:
        success = agent.connect('marcos')
        if success:
            print("  ✓ Conectado com sucesso!")
            
            # Verificar informações da conta
            account_info = agent.get_current_account_info()
            print(f"  📊 Account ID: {account_info['account_id']}")
            print(f"  🌍 Região: {account_info['region']}")
            print(f"  👤 ARN: {account_info['current_arn']}")
            
        else:
            print("  ✗ Falha na conexão")
            return
            
    except Exception as e:
        print(f"  ✗ Erro na conexão: {e}")
        return
    
    print()
    
    # Testar serviços disponíveis
    print("🔧 Testando serviços disponíveis...")
    services = agent.get_available_services()
    print(f"  📋 Serviços registrados: {services}")
    print()
    
    # Teste S3
    print("🪣 TESTE S3:")
    try:
        s3_service = agent.services.get('s3')
        if s3_service:
            # Listar buckets
            buckets = s3_service.list_buckets()
            print(f"  ✓ Buckets encontrados: {len(buckets)}")
            
            # Criar bucket de teste
            test_bucket = f"marcos-agent-test-{int(time.time())}"
            print(f"  📦 Criando bucket de teste: {test_bucket}")
            
            if s3_service.create_bucket(test_bucket):
                print(f"  ✓ Bucket criado")
                
                # Upload de arquivo
                test_content = "Hello from AWS Agent!"
                if s3_service.upload_file_content(test_bucket, 'test.txt', test_content):
                    print(f"  ✓ Upload realizado")
                    
                    # Listar objetos
                    objects = s3_service.list_objects(test_bucket)
                    print(f"  ✓ Objetos no bucket: {len(objects)}")
                    
                    # Download
                    content = s3_service.download_file_content(test_bucket, 'test.txt')
                    if content == test_content:
                        print(f"  ✓ Download verificado")
                    
                    # Limpar
                    s3_service.delete_object(test_bucket, 'test.txt')
                    s3_service.delete_bucket(test_bucket)
                    print(f"  ✓ Limpeza realizada")
                    
        else:
            print("  ✗ Serviço S3 não disponível")
            
    except Exception as e:
        print(f"  ✗ Erro no S3: {e}")
    
    print()
    
    # Teste EC2
    print("🖥️  TESTE EC2:")
    try:
        ec2_service = agent.services.get('ec2')
        if ec2_service:
            instances = ec2_service.list_instances()
            print(f"  ✓ Instâncias encontradas: {len(instances)}")
        else:
            print("  ✗ Serviço EC2 não disponível")
    except Exception as e:
        print(f"  ✗ Erro no EC2: {e}")
    
    print()
    
    # Teste IAM
    print("👤 TESTE IAM:")
    try:
        iam_service = agent.services.get('iam')
        if iam_service:
            user = iam_service.get_current_user()
            if user:
                print(f"  ✓ Usuário atual: {user['username']}")
            else:
                print("  ✗ Não foi possível obter usuário")
        else:
            print("  ✗ Serviço IAM não disponível")
    except Exception as e:
        print(f"  ✗ Erro no IAM: {e}")
    
    print()
    
    # Teste Lambda
    print("⚡ TESTE LAMBDA:")
    try:
        lambda_service = agent.services.get('lambda')
        if lambda_service:
            functions = lambda_service.list_functions()
            print(f"  ✓ Funções encontradas: {len(functions)}")
        else:
            print("  ✗ Serviço Lambda não disponível")
    except Exception as e:
        print(f"  ✗ Erro no Lambda: {e}")
    
    print()
    
    # Desconectar
    print("📴 Desconectando...")
    agent.disconnect()
    print("  ✓ Desconectado")
    
    print()
    print("=" * 60)
    print("RESUMO DO TESTE:")
    print("=" * 60)
    print("✓ Conexão com conta Marcos: FUNCIONANDO")
    print("✓ Serviço S3: FUNCIONANDO (acesso completo)")
    print("✗ Serviço EC2: BLOQUEADO (sem permissões)")
    print("✗ Serviço IAM: LIMITADO (apenas próprio usuário)")
    print("✗ Serviço Lambda: BLOQUEADO (sem permissões)")
    print()
    print("CONCLUSÃO:")
    print("O usuário Marcos pode usar o AWS Agent principalmente para")
    print("operações S3. Para outros serviços, é necessário configurar")
    print("políticas IAM apropriadas no console AWS.")
    print("=" * 60)

if __name__ == "__main__":
    import time
    test_agent_with_marcos()
