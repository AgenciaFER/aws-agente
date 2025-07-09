#!/usr/bin/env python3
"""
Script para criar um website S3 com a página HTML
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from aws_agent.core.agent import AWSAgent
from rich.console import Console
import time
import json

console = Console()

def create_s3_website():
    """Cria um website S3 com a página HTML"""
    
    console.print("🌐 CRIANDO WEBSITE S3", style="bold blue")
    console.print("=" * 50)
    
    # Conectar ao AWS Agent
    agent = AWSAgent()
    
    try:
        if agent.connect('marcos'):
            console.print("✅ Conectado à conta AWS", style="green")
            
            s3_service = agent.services.get('s3')
            if s3_service:
                # Criar bucket para website
                website_bucket = f"marcos-website-{int(time.time())}"
                console.print(f"\n📦 Criando bucket para website: {website_bucket}")
                
                if s3_service.create_bucket(website_bucket):
                    console.print("✅ Bucket criado com sucesso!", style="green")
                    
                    # Fazer upload da página HTML
                    console.print("\n📤 Fazendo upload da página HTML...")
                    
                    # Ler o arquivo HTML
                    with open('index.html', 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    
                    # Upload do arquivo
                    s3_client = s3_service.client
                    
                    s3_client.put_object(
                        Bucket=website_bucket,
                        Key='index.html',
                        Body=html_content,
                        ContentType='text/html',
                        CacheControl='no-cache'
                    )
                    console.print("✅ index.html enviado!", style="green")
                    
                    # Criar uma página 404 personalizada
                    error_html = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>404 - Página não encontrada</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            text-align: center; 
            padding: 50px;
            background: #f0f0f0;
        }
        .error { 
            color: #e74c3c; 
            font-size: 2em; 
            margin-bottom: 20px;
        }
        a { 
            color: #3498db; 
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="error">404 - Página não encontrada</div>
    <p>A página que você procura não existe.</p>
    <p><a href="/">Voltar para a página inicial</a></p>
</body>
</html>'''
                    
                    s3_client.put_object(
                        Bucket=website_bucket,
                        Key='error.html',
                        Body=error_html,
                        ContentType='text/html'
                    )
                    console.print("✅ error.html enviado!", style="green")
                    
                    # Configurar website hosting
                    console.print("\n🌐 Configurando website hosting...")
                    
                    website_config = {
                        'IndexDocument': {'Suffix': 'index.html'},
                        'ErrorDocument': {'Key': 'error.html'}
                    }
                    
                    try:
                        s3_client.put_bucket_website(
                            Bucket=website_bucket,
                            WebsiteConfiguration=website_config
                        )
                        console.print("✅ Website hosting configurado!", style="green")
                    except Exception as e:
                        console.print(f"⚠️  Erro ao configurar website: {e}", style="yellow")
                    
                    # Configurar política pública para leitura
                    console.print("\n🔓 Configurando acesso público...")
                    
                    bucket_policy = {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Sid": "PublicReadGetObject",
                                "Effect": "Allow",
                                "Principal": "*",
                                "Action": "s3:GetObject",
                                "Resource": f"arn:aws:s3:::{website_bucket}/*"
                            }
                        ]
                    }
                    
                    try:
                        s3_client.put_bucket_policy(
                            Bucket=website_bucket,
                            Policy=json.dumps(bucket_policy)
                        )
                        console.print("✅ Política pública configurada!", style="green")
                    except Exception as e:
                        console.print(f"⚠️  Erro ao configurar política: {e}", style="yellow")
                        console.print("   Você pode configurar manualmente no console AWS", style="dim")
                    
                    # Gerar URLs de acesso
                    console.print("\n🔗 URLs de acesso:")
                    
                    # URL do website S3
                    website_url = f"http://{website_bucket}.s3-website-us-east-1.amazonaws.com"
                    console.print(f"   🌐 Website URL: [bold cyan]{website_url}[/bold cyan]")
                    
                    # URL direta do objeto
                    object_url = f"https://{website_bucket}.s3.amazonaws.com/index.html"
                    console.print(f"   📄 Objeto URL: [bold blue]{object_url}[/bold blue]")
                    
                    # Testar acesso
                    console.print("\n🧪 Testando acesso...")
                    
                    try:
                        import requests
                        
                        # Tentar acessar o website
                        response = requests.get(website_url, timeout=10)
                        if response.status_code == 200:
                            console.print("✅ Website acessível!", style="green")
                        else:
                            console.print(f"⚠️  Status: {response.status_code}", style="yellow")
                    except Exception as e:
                        console.print(f"⚠️  Não foi possível testar automaticamente: {e}", style="yellow")
                        console.print("   Tente acessar manualmente as URLs acima", style="dim")
                    
                    # Abrir no navegador
                    console.print("\n🚀 Abrindo no navegador...")
                    
                    try:
                        import webbrowser
                        webbrowser.open(website_url)
                        console.print("✅ Navegador aberto!", style="green")
                    except Exception as e:
                        console.print(f"⚠️  Erro ao abrir navegador: {e}", style="yellow")
                        console.print(f"   Acesse manualmente: {website_url}", style="cyan")
                    
                    # Resumo final
                    console.print("\n" + "=" * 50)
                    console.print("🎉 [bold green]WEBSITE CRIADO COM SUCESSO![/bold green]")
                    console.print("=" * 50)
                    console.print(f"📦 Bucket: [bold]{website_bucket}[/bold]")
                    console.print(f"🌐 URL: [bold cyan]{website_url}[/bold cyan]")
                    console.print(f"📄 Arquivos: index.html, error.html")
                    console.print(f"🔓 Acesso: Público (somente leitura)")
                    
                    return website_url
                    
                else:
                    console.print("❌ Falha ao criar bucket", style="red")
                    return None
            else:
                console.print("❌ Serviço S3 não disponível", style="red")
                return None
        else:
            console.print("❌ Falha na conexão", style="red")
            return None
    
    except Exception as e:
        console.print(f"❌ Erro: {e}", style="red")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        agent.disconnect()

if __name__ == "__main__":
    website_url = create_s3_website()
    
    if website_url:
        print(f"\n🌐 Acesse seu website em: {website_url}")
    else:
        print("\n❌ Falha ao criar website")
