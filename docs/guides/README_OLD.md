# AWS Multi-Account Agent

## Visão Geral

O AWS Multi-Account Agent é uma ferramenta robusta e segura para gerenciar múltiplas contas AWS através de uma interface unificada. Permite armazenar credenciais de forma criptografada e alternar entre diferentes contas AWS facilmente.

## Características Principais

- 🔐 **Armazenamento Seguro**: Credenciais criptografadas localmente
- 🔄 **Multi-Account**: Suporte para múltiplas contas AWS
- 🛠️ **SDK Oficial**: Utiliza boto3 (SDK oficial da AWS)
- 📋 **Interface CLI**: Interface de linha de comando intuitiva
- 📚 **Documentação Completa**: Documentação detalhada de todos os recursos
- 🧪 **Testes**: Suite completa de testes automatizados

## Serviços AWS Suportados

### Core Services
- EC2 (Elastic Compute Cloud)
- S3 (Simple Storage Service)
- IAM (Identity and Access Management)
- RDS (Relational Database Service)
- Lambda (Serverless Computing)

### Advanced Services
- CloudFormation
- VPC (Virtual Private Cloud)
- ECS/EKS (Container Services)
- CloudWatch
- SNS/SQS (Messaging Services)

## Instalação

```bash
# Clone o repositório
git clone <repository-url>
cd aws-multi-account-agent

# Instale as dependências
pip install -r requirements.txt

# Execute a configuração inicial
python setup.py install
```

## Uso Básico

```bash
# Iniciar o agente
python -m aws_agent

# Adicionar uma nova conta AWS
python -m aws_agent add-account

# Listar contas configuradas
python -m aws_agent list-accounts

# Conectar a uma conta específica
python -m aws_agent connect --account my-account
```

## Estrutura do Projeto

```
aws-multi-account-agent/
├── src/
│   └── aws_agent/
│       ├── __init__.py
│       ├── cli/
│       ├── core/
│       ├── services/
│       └── utils/
├── tests/
├── docs/
├── examples/
├── requirements.txt
├── setup.py
└── README.md
```

## Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Faça commit das mudanças
4. Faça push para a branch
5. Abra um Pull Request

## Licença

Este projeto está licenciado sob a MIT License - veja o arquivo LICENSE para detalhes.

## Segurança

- Todas as credenciais são criptografadas usando AES-256
- Chaves de criptografia são armazenadas de forma segura usando keyring
- Suporte para MFA (Multi-Factor Authentication)
- Logs de auditoria para todas as operações

## Suporte

Para suporte, abra uma issue no GitHub ou consulte a documentação em `docs/`.

---

**Versão**: 1.0.0
**Autor**: AWS Multi-Account Agent Team
**Data**: Julho 2025
