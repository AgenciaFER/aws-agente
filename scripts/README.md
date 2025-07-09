# 📁 SCRIPTS

Esta pasta contém scripts organizados por categoria:

## 📂 Estrutura

### 🎬 demo/
Scripts de demonstração do sistema:
- `demo.py` - Demonstração principal
- `serve_demo.py` - Servidor para páginas de demo
- `upload_demo_page.py` - Upload de páginas de demonstração
- `upload_demo_simple.py` - Upload simplificado
- `final_demo.py` - Demonstração final

### 🔧 utilities/
Scripts utilitários para operações AWS:
- `configure_public_access.py` - Configuração de acesso público S3
- `create_s3_website.py` - Criação de websites S3
- `relatorio_s3_marcos.py` - Relatório de buckets S3
- `website_summary.py` - Resumo de websites

### 🛠️ maintenance/
Scripts de manutenção do projeto:
- `prepare_for_github.py` - Preparação para GitHub
- `o_que_ele_realmente_faz.py` - Explicação do projeto
- `RESUMO_FINAL.py` - Resumo final do projeto

### 📦 setup/
Scripts de configuração e instalação:
- (Pasta preparada para futuros scripts de setup)

## 🚀 Como usar

Cada script pode ser executado individualmente:

```bash
# Executar demonstração
python scripts/demo/demo.py

# Criar website S3
python scripts/utilities/create_s3_website.py

# Preparar para GitHub
python scripts/maintenance/prepare_for_github.py
```

## 📝 Notas

- Todos os scripts mantêm sua funcionalidade original
- Imports podem precisar ser ajustados para a nova estrutura
- Documentação individual disponível em cada script
