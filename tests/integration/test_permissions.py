#!/usr/bin/env python3
"""
Script para testar as permissões do usuário Marcos
"""
import boto3
import json
from botocore.exceptions import ClientError, NoCredentialsError

def test_aws_permissions():
    """Testa as permissões do usuário AWS"""
    
    # Configurar credenciais
    session = boto3.Session(
        aws_access_key_id='AKIA****************',
        aws_secret_access_key='************************************',
        region_name='us-east-1'
    )
    
    print("=" * 60)
    print("TESTE DE PERMISSÕES AWS - USUÁRIO MARCOS")
    print("=" * 60)
    print()
    
    # Teste 1: Informações da conta
    print("🏢 INFORMAÇÕES DA CONTA:")
    try:
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        print(f"  ✓ Account ID: {identity['Account']}")
        print(f"  ✓ User ID: {identity['UserId']}")
        print(f"  ✓ ARN: {identity['Arn']}")
    except Exception as e:
        print(f"  ✗ Erro ao obter informações da conta: {e}")
    print()
    
    # Teste 2: EC2 - Instâncias
    print("🖥️  SERVIÇO EC2:")
    try:
        ec2 = session.client('ec2')
        instances = ec2.describe_instances()
        total_instances = 0
        for reservation in instances['Reservations']:
            total_instances += len(reservation['Instances'])
        print(f"  ✓ Total de instâncias: {total_instances}")
        
        # Testar outras operações EC2
        regions = ec2.describe_regions()
        print(f"  ✓ Regiões disponíveis: {len(regions['Regions'])}")
        
        volumes = ec2.describe_volumes()
        print(f"  ✓ Volumes EBS: {len(volumes['Volumes'])}")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'UnauthorizedOperation':
            print("  ✗ Acesso negado ao EC2")
        else:
            print(f"  ✗ Erro no EC2: {error_code}")
    except Exception as e:
        print(f"  ✗ Erro inesperado no EC2: {e}")
    print()
    
    # Teste 3: S3 - Buckets
    print("🪣 SERVIÇO S3:")
    try:
        s3 = session.client('s3')
        buckets = s3.list_buckets()
        print(f"  ✓ Total de buckets: {len(buckets['Buckets'])}")
        
        for bucket in buckets['Buckets']:
            print(f"    - {bucket['Name']} (criado em {bucket['CreationDate']})")
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDenied':
            print("  ✗ Acesso negado ao S3")
        else:
            print(f"  ✗ Erro no S3: {error_code}")
    except Exception as e:
        print(f"  ✗ Erro inesperado no S3: {e}")
    print()
    
    # Teste 4: IAM - Usuários
    print("👤 SERVIÇO IAM:")
    try:
        iam = session.client('iam')
        
        # Informações do usuário atual
        user = iam.get_user()
        print(f"  ✓ Usuário atual: {user['User']['UserName']}")
        
        # Políticas anexadas ao usuário
        policies = iam.list_attached_user_policies(UserName=user['User']['UserName'])
        print(f"  ✓ Políticas anexadas: {len(policies['AttachedPolicies'])}")
        for policy in policies['AttachedPolicies']:
            print(f"    - {policy['PolicyName']}")
            
        # Grupos do usuário
        groups = iam.get_groups_for_user(UserName=user['User']['UserName'])
        print(f"  ✓ Grupos: {len(groups['Groups'])}")
        for group in groups['Groups']:
            print(f"    - {group['GroupName']}")
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDenied':
            print("  ✗ Acesso negado ao IAM")
        else:
            print(f"  ✗ Erro no IAM: {error_code}")
    except Exception as e:
        print(f"  ✗ Erro inesperado no IAM: {e}")
    print()
    
    # Teste 5: Lambda - Funções
    print("⚡ SERVIÇO LAMBDA:")
    try:
        lambda_client = session.client('lambda')
        functions = lambda_client.list_functions()
        print(f"  ✓ Total de funções: {len(functions['Functions'])}")
        
        for func in functions['Functions']:
            print(f"    - {func['FunctionName']} ({func['Runtime']})")
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDenied':
            print("  ✗ Acesso negado ao Lambda")
        else:
            print(f"  ✗ Erro no Lambda: {error_code}")
    except Exception as e:
        print(f"  ✗ Erro inesperado no Lambda: {e}")
    print()
    
    # Teste 6: CloudWatch - Logs
    print("📊 SERVIÇO CLOUDWATCH:")
    try:
        cloudwatch = session.client('cloudwatch')
        metrics = cloudwatch.list_metrics(MaxRecords=10)
        print(f"  ✓ Métricas disponíveis: {len(metrics['Metrics'])}")
        
        logs = session.client('logs')
        log_groups = logs.describe_log_groups(limit=10)
        print(f"  ✓ Grupos de logs: {len(log_groups['logGroups'])}")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDenied':
            print("  ✗ Acesso negado ao CloudWatch")
        else:
            print(f"  ✗ Erro no CloudWatch: {error_code}")
    except Exception as e:
        print(f"  ✗ Erro inesperado no CloudWatch: {e}")
    print()
    
    print("=" * 60)
    print("TESTE CONCLUÍDO")
    print("=" * 60)

if __name__ == "__main__":
    test_aws_permissions()
