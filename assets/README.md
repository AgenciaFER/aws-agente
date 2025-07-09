# 🎨 ASSETS

Esta pasta contém recursos estáticos do projeto:

## 📂 Estrutura

### 🌐 html/
Arquivos HTML do projeto:
- `demo_page.html` - Página de demonstração principal
- `index.html` - Página inicial

### 🎨 css/
Arquivos CSS (preparado para futuras adições):
- Estilos customizados
- Temas responsivos

### 🖼️ images/
Imagens do projeto (preparado para futuras adições):
- Logos
- Screenshots
- Diagramas

## 🚀 Como usar

Os assets podem ser referenciados nos scripts:

```python
# Carregar página HTML
html_path = Path("assets/html/demo_page.html")
with open(html_path, 'r') as f:
    html_content = f.read()
```

## 📝 Notas

- Todos os arquivos HTML são responsivos
- Preparado para expansão com mais assets
- Manter organização por tipo de arquivo
