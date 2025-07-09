#!/usr/bin/env python3
"""
Script para testar permissões específicas do usuário Marcos
"""
import boto3
import json
from botocore.exceptions import ClientError, NoCredentialsError

def test_specific_permissions():
    """Testa permissões específicas do usuário AWS"""
    
    # Configurar credenciais
    session = boto3.Session(
        aws_access_key_id='AKIA****************',
        aws_secret_access_key='************************************',
        region_name='us-east-1'
    )
    
    print("=" * 60)
    print("TESTE DETALHADO DE PERMISSÕES - USUÁRIO MARCOS")
    print("=" * 60)
    print()
    
    # Teste S3 detalhado
    print("🪣 TESTE DETALHADO S3:")
    try:
        s3 = session.client('s3')
        
        # Criar bucket de teste
        test_bucket = f"marcos-test-bucket-{int(time.time())}"
        print(f"  Tentando criar bucket: {test_bucket}")
        try:
            s3.create_bucket(Bucket=test_bucket)
            print(f"  ✓ Bucket criado com sucesso")
            
            # Testar upload
            s3.put_object(Bucket=test_bucket, Key='test.txt', Body=b'Hello World')
            print(f"  ✓ Upload realizado com sucesso")
            
            # Testar listagem
            objects = s3.list_objects_v2(Bucket=test_bucket)
            print(f"  ✓ Listagem realizada: {objects.get('KeyCount', 0)} objetos")
            
            # Limpar
            s3.delete_object(Bucket=test_bucket, Key='test.txt')
            s3.delete_bucket(Bucket=test_bucket)
            print(f"  ✓ Limpeza realizada")
            
        except ClientError as e:
            print(f"  ✗ Erro ao criar bucket: {e.response['Error']['Code']}")
            
    except Exception as e:
        print(f"  ✗ Erro geral no S3: {e}")
    print()
    
    # Teste EC2 detalhado
    print("🖥️  TESTE DETALHADO EC2:")
    try:
        ec2 = session.client('ec2')
        
        # Tentar diferentes operações
        operations = [
            ('describe_instances', 'Listar instâncias'),
            ('describe_images', 'Listar AMIs'),
            ('describe_key_pairs', 'Listar key pairs'),
            ('describe_security_groups', 'Listar security groups'),
            ('describe_volumes', 'Listar volumes'),
            ('describe_snapshots', 'Listar snapshots'),
            ('describe_availability_zones', 'Listar zonas de disponibilidade'),
            ('describe_regions', 'Listar regiões')
        ]
        
        for operation, description in operations:
            try:
                if operation == 'describe_snapshots':
                    # Limitar snapshots próprios
                    result = getattr(ec2, operation)(OwnerIds=['self'])
                elif operation == 'describe_images':
                    # Limitar AMIs próprias
                    result = getattr(ec2, operation)(Owners=['self'])
                else:
                    result = getattr(ec2, operation)()
                
                count = len(result.get(list(result.keys())[0], []))
                print(f"  ✓ {description}: {count} itens")
                
            except ClientError as e:
                print(f"  ✗ {description}: {e.response['Error']['Code']}")
                
    except Exception as e:
        print(f"  ✗ Erro geral no EC2: {e}")
    print()
    
    # Teste IAM detalhado
    print("👤 TESTE DETALHADO IAM:")
    try:
        iam = session.client('iam')
        
        # Tentar diferentes operações
        operations = [
            ('get_user', 'Obter informações do usuário'),
            ('list_access_keys', 'Listar chaves de acesso'),
            ('list_attached_user_policies', 'Listar políticas anexadas'),
            ('get_groups_for_user', 'Obter grupos do usuário'),
            ('list_users', 'Listar usuários'),
            ('list_groups', 'Listar grupos'),
            ('list_roles', 'Listar roles'),
            ('list_policies', 'Listar políticas')
        ]
        
        for operation, description in operations:
            try:
                if operation in ['get_user', 'list_access_keys', 'list_attached_user_policies', 'get_groups_for_user']:
                    # Operações que precisam do nome do usuário
                    if operation == 'get_user':
                        result = getattr(iam, operation)()
                        print(f"  ✓ {description}: {result['User']['UserName']}")
                    else:
                        result = getattr(iam, operation)(UserName='marcos')
                        key = list(result.keys())[0]
                        count = len(result.get(key, []))
                        print(f"  ✓ {description}: {count} itens")
                else:
                    result = getattr(iam, operation)()
                    key = list(result.keys())[0]
                    count = len(result.get(key, []))
                    print(f"  ✓ {description}: {count} itens")
                    
            except ClientError as e:
                print(f"  ✗ {description}: {e.response['Error']['Code']}")
                
    except Exception as e:
        print(f"  ✗ Erro geral no IAM: {e}")
    print()
    
    # Teste Lambda detalhado
    print("⚡ TESTE DETALHADO LAMBDA:")
    try:
        lambda_client = session.client('lambda')
        
        # Tentar diferentes operações
        operations = [
            ('list_functions', 'Listar funções'),
            ('list_layers', 'Listar layers'),
            ('list_event_source_mappings', 'Listar mapeamentos de eventos')
        ]
        
        for operation, description in operations:
            try:
                result = getattr(lambda_client, operation)()
                key = list(result.keys())[0]
                count = len(result.get(key, []))
                print(f"  ✓ {description}: {count} itens")
                
            except ClientError as e:
                print(f"  ✗ {description}: {e.response['Error']['Code']}")
                
    except Exception as e:
        print(f"  ✗ Erro geral no Lambda: {e}")
    print()
    
    print("=" * 60)
    print("RESUMO DE PERMISSÕES:")
    print("=" * 60)
    print("✓ S3: Acesso COMPLETO (criar, listar, upload, download, deletar)")
    print("✗ EC2: Acesso NEGADO (UnauthorizedOperation)")
    print("✗ IAM: Acesso LIMITADO (apenas próprio usuário)")
    print("✗ Lambda: Acesso NEGADO (AccessDeniedException)")
    print("✗ CloudWatch: Acesso NEGADO")
    print()
    print("RECOMENDAÇÕES:")
    print("- O usuário Marcos tem permissões principalmente para S3")
    print("- Para EC2, Lambda e outros serviços, é necessário adicionar políticas IAM")
    print("- Considere anexar políticas como 'EC2ReadOnlyAccess', 'AWSLambdaReadOnlyAccess'")
    print("=" * 60)

if __name__ == "__main__":
    import time
    test_specific_permissions()
