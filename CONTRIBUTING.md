# Contributing to AWS Multi-Account Agent

🎉 Obrigado por considerar contribuir para o AWS Multi-Account Agent! 

## 🚀 Como Contribuir

### 🔧 Configuração do Ambiente de Desenvolvimento

1. **Fork** o repositório
2. **Clone** seu fork localmente
3. **Configure** o ambiente:

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/aws-multi-account-agent.git
cd aws-multi-account-agent

# Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instale dependências
pip install -r requirements.txt
pip install -e .

# Instale dependências de desenvolvimento
pip install pytest pytest-cov black flake8 mypy bandit safety
```

### 🎯 Tipos de Contribuição

Aceitamos os seguintes tipos de contribuições:

- 🐛 **Bug fixes**
- ✨ **Novas features**
- 📚 **Documentação**
- 🧪 **Testes**
- 🔐 **Melhorias de segurança**
- 🚀 **Otimizações de performance**

### 📋 Processo de Contribuição

1. **Crie uma branch** para sua feature/fix:
   ```bash
   git checkout -b feature/nome-da-feature
   # ou
   git checkout -b fix/nome-do-bug
   ```

2. **Desenvolva** sua mudança:
   - Escreva código limpo e bem documentado
   - Adicione testes para novas funcionalidades
   - Siga as convenções de código do projeto
   - Atualize documentação se necessário

3. **Teste** suas mudanças:
   ```bash
   # Executar testes
   pytest tests/ -v
   
   # Verificar cobertura
   pytest tests/ --cov=aws_agent --cov-report=html
   
   # Verificar estilo
   black src/
   flake8 src/
   
   # Verificar tipos
   mypy src/
   
   # Verificar segurança
   bandit -r src/
   safety check
   ```

4. **Commit** suas mudanças:
   ```bash
   git add .
   git commit -m "feat: adiciona nova funcionalidade X"
   ```

5. **Push** para seu fork:
   ```bash
   git push origin feature/nome-da-feature
   ```

6. **Abra** um Pull Request

## 📝 Convenções de Código

### 🐍 Python Style Guide

- Seguimos o **PEP 8** para estilo de código
- Usamos **Black** para formatação automática
- Limitamos linhas a **88 caracteres** (padrão do Black)
- Usamos **type hints** sempre que possível
- Documentamos funções com **docstrings**

### 📊 Exemplo de Função Bem Documentada

```python
def create_bucket(
    self,
    bucket_name: str,
    region: str = "us-east-1",
    encryption: bool = True
) -> Dict[str, Any]:
    """
    Cria um novo bucket S3 com configurações de segurança.
    
    Args:
        bucket_name: Nome do bucket a ser criado
        region: Região AWS onde criar o bucket
        encryption: Se deve habilitar criptografia
    
    Returns:
        Dict com informações do bucket criado
    
    Raises:
        BucketAlreadyExistsError: Se o bucket já existir
        PermissionError: Se não houver permissões suficientes
    
    Example:
        >>> s3_service = S3Service(session)
        >>> result = s3_service.create_bucket("my-bucket")
        >>> print(result["bucket_name"])
        my-bucket
    """
    # Implementação...
```

### 🧪 Convenções de Testes

- Testes devem estar no diretório `tests/`
- Nomes de arquivos de teste: `test_*.py`
- Nomes de funções de teste: `test_*`
- Use fixtures para setup/teardown
- Mock chamadas externas (AWS APIs)

```python
import pytest
from unittest.mock import Mock, patch
from aws_agent.services.s3 import S3Service

class TestS3Service:
    @pytest.fixture
    def s3_service(self):
        mock_session = Mock()
        return S3Service(mock_session)
    
    @patch('boto3.client')
    def test_create_bucket_success(self, mock_client, s3_service):
        # Arrange
        mock_client.return_value.create_bucket.return_value = {
            'Location': 'us-east-1'
        }
        
        # Act
        result = s3_service.create_bucket('test-bucket')
        
        # Assert
        assert result['bucket_name'] == 'test-bucket'
        mock_client.return_value.create_bucket.assert_called_once()
```

### 📝 Convenções de Commit

Usamos **Conventional Commits** para mensagens de commit:

```
<type>(<scope>): <description>

<body>

<footer>
```

**Tipos:**
- `feat`: Nova funcionalidade
- `fix`: Correção de bug
- `docs`: Documentação
- `style`: Formatação
- `refactor`: Refatoração
- `test`: Testes
- `chore`: Tarefas de manutenção
- `security`: Melhorias de segurança

**Exemplos:**
```bash
feat(s3): adiciona suporte para website hosting
fix(ec2): corrige listagem de instâncias
docs(security): atualiza guia de segurança
security(auth): implementa rotação de tokens
```

## 🔐 Considerações de Segurança

### 🛡️ Diretrizes de Segurança

1. **Nunca** commite credenciais ou informações sensíveis
2. **Sempre** valide entrada do usuário
3. **Use** criptografia para dados sensíveis
4. **Implemente** auditoria para ações críticas
5. **Siga** o princípio do menor privilégio

### 🚨 Reportando Vulnerabilidades

Para vulnerabilidades de segurança:
1. **NÃO** abra um issue público
2. **Envie** email para: security@exemplo.com
3. **Use** criptografia GPG se possível
4. **Aguarde** nossa resposta antes de disclosure público

## 📋 Checklist de Pull Request

Antes de abrir um PR, verifique:

### ✅ Código
- [ ] Código segue as convenções do projeto
- [ ] Mudanças são bem documentadas
- [ ] Não há credenciais hardcoded
- [ ] Type hints foram adicionados
- [ ] Docstrings foram adicionadas/atualizadas

### 🧪 Testes
- [ ] Testes foram adicionados para novas funcionalidades
- [ ] Todos os testes passam
- [ ] Cobertura de testes é mantida (>90%)
- [ ] Testes de segurança passam

### 📚 Documentação
- [ ] README foi atualizado se necessário
- [ ] Documentação da API foi atualizada
- [ ] Exemplos foram adicionados/atualizados
- [ ] Changelog foi atualizado

### 🔐 Segurança
- [ ] Auditoria de segurança passou
- [ ] Verificação de vulnerabilidades passou
- [ ] Nenhuma informação sensível foi exposta
- [ ] Validação de entrada foi implementada

## 🏆 Reconhecimento

Todos os contribuidores serão reconhecidos:

- **Contributors** serão listados no README
- **Major contributors** terão menção especial
- **Security contributors** no hall of fame de segurança

## 📞 Contato

Dúvidas sobre contribuição:
- **GitHub Issues**: Para discussões técnicas
- **Email**: dev@exemplo.com
- **Discord**: [Link do servidor](https://discord.gg/exemplo)

## 📄 Licença

Ao contribuir, você concorda que suas contribuições serão licenciadas sob a **MIT License**.

---

**Obrigado por contribuir para o AWS Multi-Account Agent!** 🚀
