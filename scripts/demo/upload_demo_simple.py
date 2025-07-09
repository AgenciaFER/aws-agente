#!/usr/bin/env python3
"""
Script simplificado para fazer upload da nova página de demo para S3
"""
import boto3
import json
from pathlib import Path

def upload_demo_page():
    """Upload da página de demo para S3"""
    print("🚀 Fazendo upload da nova página de demo para S3...")
    
    try:
        # Credenciais do Marcos (do arquivo CSV)
        session = boto3.Session(
            aws_access_key_id="AKIA****************",
            aws_secret_access_key="************************************",
            region_name="us-east-1"
        )
        
        s3_client = session.client('s3')
        
        # Nome do bucket
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
            
            # Também fazer upload da página original
            s3_client.put_object(
                Bucket=bucket_name,
                Key='demo_page.html',
                Body=content.encode('utf-8'),
                ContentType='text/html'
            )
            print("✓ Upload concluído para demo_page.html")
        
        # Configurar website hosting
        print("🌐 Configurando website hosting...")
        s3_client.put_bucket_website(
            Bucket=bucket_name,
            WebsiteConfiguration={
                'IndexDocument': {'Suffix': 'index.html'},
                'ErrorDocument': {'Suffix': 'index.html'}
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
        
        s3_client.put_bucket_policy(
            Bucket=bucket_name,
            Policy=json.dumps(bucket_policy)
        )
        print("✓ Política pública aplicada")
        
        # URL do website
        website_url = f"http://{bucket_name}.s3-website-us-east-1.amazonaws.com"
        print(f"\\n🎉 Website disponível em: {website_url}")
        
        # Listar objetos no bucket
        print("\\n📋 Objetos no bucket:")
        objects = s3_client.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in objects:
            for obj in objects['Contents']:
                print(f"  - {obj['Key']} ({obj['Size']} bytes)")
        
        return website_url
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    url = upload_demo_page()
    if url:
        print("\\n✅ Upload da página de demo concluído com sucesso!")
        print(f"🔗 URL: {url}")
    else:
        print("\\n❌ Falha no upload da página")
