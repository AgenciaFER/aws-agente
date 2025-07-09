#!/usr/bin/env python3
"""
Script para tentar configurar acesso público usando ACLs
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from aws_agent.core.agent import AWSAgent
from rich.console import Console
import boto3
from botocore.exceptions import ClientError

console = Console()

def configure_public_access():
    """Tenta configurar acesso público usando diferentes métodos"""
    
    console.print("🔧 CONFIGURANDO ACESSO PÚBLICO", style="bold blue")
    console.print("=" * 50)
    
    # Conectar ao AWS Agent
    agent = AWSAgent()
    bucket_name = "marcos-website-1752027952"  # Bucket criado anteriormente
    
    try:
        if agent.connect('marcos'):
            console.print("✅ Conectado à conta AWS", style="green")
            
            s3_service = agent.services.get('s3')
            if s3_service:
                s3_client = s3_service.client
                
                # Método 1: Tentar configurar ACL do bucket
                console.print("\n📋 Método 1: Configurando ACL do bucket...")
                try:
                    s3_client.put_bucket_acl(
                        Bucket=bucket_name,
                        ACL='public-read'
                    )
                    console.print("✅ ACL do bucket configurada!", style="green")
                except ClientError as e:
                    console.print(f"⚠️  Erro ACL bucket: {e.response['Error']['Code']}", style="yellow")
                
                # Método 2: Configurar ACL dos objetos individualmente
                console.print("\n📄 Método 2: Configurando ACL dos objetos...")
                
                objects = ['index.html', 'error.html']
                for obj_key in objects:
                    try:
                        s3_client.put_object_acl(
                            Bucket=bucket_name,
                            Key=obj_key,
                            ACL='public-read'
                        )
                        console.print(f"✅ ACL configurada para {obj_key}", style="green")
                    except ClientError as e:
                        console.print(f"⚠️  Erro ACL {obj_key}: {e.response['Error']['Code']}", style="yellow")
                
                # Método 3: Gerar URL pré-assinada para teste
                console.print("\n🔗 Método 3: Gerando URL pré-assinada...")
                try:
                    presigned_url = s3_client.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': bucket_name, 'Key': 'index.html'},
                        ExpiresIn=3600  # 1 hora
                    )
                    console.print(f"✅ URL pré-assinada gerada!", style="green")
                    console.print(f"   [cyan]{presigned_url}[/cyan]")
                except Exception as e:
                    console.print(f"❌ Erro URL pré-assinada: {e}", style="red")
                
                # Método 4: Verificar configurações de Block Public Access
                console.print("\n🚫 Método 4: Verificando Block Public Access...")
                try:
                    block_config = s3_client.get_public_access_block(Bucket=bucket_name)
                    config = block_config['PublicAccessBlockConfiguration']
                    
                    console.print("   Configurações atuais:")
                    console.print(f"   - BlockPublicAcls: {config.get('BlockPublicAcls', False)}")
                    console.print(f"   - IgnorePublicAcls: {config.get('IgnorePublicAcls', False)}")
                    console.print(f"   - BlockPublicPolicy: {config.get('BlockPublicPolicy', False)}")
                    console.print(f"   - RestrictPublicBuckets: {config.get('RestrictPublicBuckets', False)}")
                    
                    # Tentar desabilitar Block Public Access
                    console.print("\n   Tentando desabilitar Block Public Access...")
                    try:
                        s3_client.put_public_access_block(
                            Bucket=bucket_name,
                            PublicAccessBlockConfiguration={
                                'BlockPublicAcls': False,
                                'IgnorePublicAcls': False,
                                'BlockPublicPolicy': False,
                                'RestrictPublicBuckets': False
                            }
                        )
                        console.print("   ✅ Block Public Access desabilitado!", style="green")
                        
                        # Tentar novamente a política pública
                        console.print("\n   Tentando aplicar política pública novamente...")
                        bucket_policy = {
                            "Version": "2012-10-17",
                            "Statement": [
                                {
                                    "Sid": "PublicReadGetObject",
                                    "Effect": "Allow",
                                    "Principal": "*",
                                    "Action": "s3:GetObject",
                                    "Resource": f"arn:aws:s3:::{bucket_name}/*"
                                }
                            ]
                        }
                        
                        import json
                        s3_client.put_bucket_policy(
                            Bucket=bucket_name,
                            Policy=json.dumps(bucket_policy)
                        )
                        console.print("   ✅ Política pública aplicada!", style="green")
                        
                    except ClientError as e:
                        console.print(f"   ⚠️  Erro: {e.response['Error']['Code']}", style="yellow")
                        
                except ClientError as e:
                    if e.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
                        console.print("   ℹ️  Nenhuma configuração de Block Public Access encontrada", style="blue")
                    else:
                        console.print(f"   ⚠️  Erro: {e.response['Error']['Code']}", style="yellow")
                
                # Teste final de acesso
                console.print("\n🧪 Teste final de acesso...")
                
                website_url = f"http://{bucket_name}.s3-website-us-east-1.amazonaws.com"
                object_url = f"https://{bucket_name}.s3.amazonaws.com/index.html"
                
                try:
                    import requests
                    
                    # Testar website URL
                    response = requests.get(website_url, timeout=10)
                    console.print(f"   Website URL: Status {response.status_code}")
                    
                    # Testar object URL
                    response = requests.get(object_url, timeout=10)
                    console.print(f"   Object URL: Status {response.status_code}")
                    
                    if response.status_code == 200:
                        console.print("   ✅ Acesso público funcionando!", style="green")
                    
                except Exception as e:
                    console.print(f"   ⚠️  Erro no teste: {e}", style="yellow")
                
                # URLs finais
                console.print("\n🔗 URLs para teste:")
                console.print(f"   🌐 Website: [bold cyan]{website_url}[/bold cyan]")
                console.print(f"   📄 Objeto: [bold blue]{object_url}[/bold blue]")
                if 'presigned_url' in locals():
                    console.print(f"   🔑 Pré-assinada: [bold green]{presigned_url[:80]}...[/bold green]")
                
                # Abrir no navegador
                console.print("\n🚀 Abrindo URLs no navegador...")
                try:
                    import webbrowser
                    webbrowser.open(website_url)
                    console.print("✅ Navegador aberto!", style="green")
                except Exception as e:
                    console.print(f"⚠️  Erro ao abrir navegador: {e}", style="yellow")
        
        else:
            console.print("❌ Falha na conexão", style="red")
    
    except Exception as e:
        console.print(f"❌ Erro geral: {e}", style="red")
        import traceback
        traceback.print_exc()
    
    finally:
        agent.disconnect()

if __name__ == "__main__":
    configure_public_access()
