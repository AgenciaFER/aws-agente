#!/usr/bin/env python3
"""
Script para fazer upload da nova página de demo para S3
"""
import sys
import os
from pathlib import Path

# Adicionar o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from aws_agent.core.config import Config
from aws_agent.core.account_manager import AccountManager
from aws_agent.services.s3 import S3Service
import boto3

def upload_demo_page():
    """Upload da página de demo para S3"""
    print("🚀 Fazendo upload da nova página de demo para S3...")
    
    try:
        # Configurar
        config = Config()
        
        # Conectar como marcos
        print("📡 Conectando como usuário marcos...")
        session = boto3.Session(
            aws_access_key_id=config.aws_access_key_id,
            aws_secret_access_key=config.aws_secret_access_key,
            region_name=config.aws_region
        )
        
        s3_client = session.client('s3')
        
        # Nome do bucket (usar o mesmo padrão de antes)
        bucket_name = "marcos-website-demo"
        
        # Verificar se o bucket existe
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"✓ Bucket '{bucket_name}' encontrado")
        except:
            print(f"📦 Criando bucket '{bucket_name}'...")
            s3_client.create_bucket(Bucket=bucket_name)
            print(f"✓ Bucket '{bucket_name}' criado")
        
        # Fazer upload da nova página
        html_file = Path("demo_page.html")
        if html_file.exists():
            print(f"📄 Fazendo upload de {html_file.name}...")
            
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            s3_client.put_object(
                Bucket=bucket_name,
                Key='index.html',
                Body=content.encode('utf-8'),
                ContentType='text/html'
            )
            print("✓ Upload concluído para index.html")
        
        # Configurar website hosting
        print("🌐 Configurando website hosting...")
        s3_client.put_bucket_website(
            Bucket=bucket_name,
            WebsiteConfiguration={
                'IndexDocument': {'Suffix': 'index.html'},
                'ErrorDocument': {'Suffix': 'error.html'}
            }
        )
        print("✓ Website hosting configurado")
        
        # Configurar política pública
        print("🔓 Configurando acesso público...")
        
        # Remover block public access
        s3_client.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': False,
                'IgnorePublicAcls': False,
                'BlockPublicPolicy': False,
                'RestrictPublicBuckets': False
            }
        )
        
        # Aplicar política pública
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
        print("✓ Política pública aplicada")
        
        # URL do website
        website_url = f"http://{bucket_name}.s3-website-us-east-1.amazonaws.com"
        print(f"\\n🎉 Website disponível em: {website_url}")
        
        return website_url
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

if __name__ == "__main__":
    url = upload_demo_page()
    if url:
        print("\\n✅ Upload da página de demo concluído com sucesso!")
        print(f"🔗 URL: {url}")
    else:
        print("\\n❌ Falha no upload da página")
