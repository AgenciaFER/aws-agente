#!/usr/bin/env python3
"""
Criar servidor local para testar a página HTML
"""
import http.server
import socketserver
import webbrowser
from pathlib import Path
import threading
import time

def serve_page():
    """Servir a página HTML localmente"""
    print("🌐 Iniciando servidor local para testar a página...")
    
    # Mudar para o diretório do projeto
    import os
    os.chdir(Path(__file__).parent)
    
    # Configurar servidor HTTP
    PORT = 8000
    Handler = http.server.SimpleHTTPRequestHandler
    
    # Procurar uma porta disponível
    for port in range(8000, 8010):
        try:
            with socketserver.TCPServer(("", port), Handler) as httpd:
                print(f"✓ Servidor iniciado na porta {port}")
                print(f"🔗 URL local: http://localhost:{port}/demo_page.html")
                
                # Abrir no navegador após um breve delay
                def open_browser():
                    time.sleep(2)
                    webbrowser.open(f"http://localhost:{port}/demo_page.html")
                
                browser_thread = threading.Thread(target=open_browser)
                browser_thread.daemon = True
                browser_thread.start()
                
                print("\\n🎉 Página aberta no navegador!")
                print("⚠️  Pressione Ctrl+C para parar o servidor\\n")
                
                try:
                    httpd.serve_forever()
                except KeyboardInterrupt:
                    print("\\n🛑 Servidor interrompido")
                    httpd.shutdown()
                    break
                    
        except OSError:
            continue
    else:
        print("❌ Não foi possível encontrar uma porta disponível")

if __name__ == "__main__":
    serve_page()
