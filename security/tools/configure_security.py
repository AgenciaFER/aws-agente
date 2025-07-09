#!/usr/bin/env python3
"""
Script de Configuração de Segurança do AWS Multi-Account Agent
============================================================

Este script configura todas as medidas de segurança recomendadas
para o ambiente de produção.
"""

import os
import sys
import yaml
import json
import subprocess
from pathlib import Path
from typing import Dict, Any

class SecurityConfigurator:
    """Configurador de segurança para o AWS Multi-Account Agent"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.config_dir = self.project_root / "config"
        self.security_dir = self.project_root / "security"
        
        # Criar diretórios se não existirem
        self.config_dir.mkdir(exist_ok=True)
        self.security_dir.mkdir(exist_ok=True)
    
    def configure_production_security(self):
        """Configura segurança para produção"""
        print("🔐 Configurando segurança para produção...")
        
        # 1. Configurar arquivo de segurança
        self.create_security_config()
        
        # 2. Configurar permissões de arquivos
        self.set_file_permissions()
        
        # 3. Configurar criptografia
        self.setup_encryption()
        
        # 4. Configurar logs seguros
        self.configure_secure_logging()
        
        # 5. Configurar auditoria
        self.configure_audit_logging()
        
        # 6. Configurar alertas de segurança
        self.configure_security_alerts()
        
        # 7. Instalar ferramentas de segurança
        self.install_security_tools()
        
        print("✅ Configuração de segurança concluída!")
    
    def create_security_config(self):
        """Cria arquivo de configuração de segurança"""
        print("📄 Criando arquivo de configuração de segurança...")
        
        security_config = {
            "security": {
                "encryption": {
                    "algorithm": "AES-256-GCM",
                    "key_derivation": "PBKDF2",
                    "iterations": 150000,
                    "salt_length": 32
                },
                "session": {
                    "timeout": 1800,  # 30 minutos
                    "max_retries": 2,
                    "lockout_time": 1800,  # 30 minutos
                    "auto_refresh": True,
                    "refresh_threshold": 300  # 5 minutos
                },
                "audit": {
                    "enabled": True,
                    "log_level": "INFO",
                    "retention_days": 365,
                    "encrypt_logs": True,
                    "sanitize_logs": True
                },
                "validation": {
                    "strict_mode": True,
                    "validate_permissions": True,
                    "check_resource_existence": True,
                    "require_mfa": False  # Pode ser habilitado se necessário
                },
                "network": {
                    "force_tls": True,
                    "min_tls_version": "1.3",
                    "verify_certificates": True,
                    "timeout": 30
                },
                "monitoring": {
                    "failed_login_threshold": 3,
                    "suspicious_activity_detection": True,
                    "real_time_alerts": True,
                    "metrics_collection": True
                }
            }
        }
        
        security_file = self.config_dir / "security.yaml"
        with open(security_file, 'w') as f:
            yaml.dump(security_config, f, default_flow_style=False, indent=2)
        
        print(f"✅ Arquivo de segurança criado: {security_file}")
    
    def set_file_permissions(self):
        """Define permissões seguras para arquivos"""
        print("🔒 Configurando permissões de arquivos...")
        
        if os.name == 'posix':  # Unix/Linux/macOS
            sensitive_files = [
                "config/security.yaml",
                "config/default.yaml",
                "config/accounts.json"
            ]
            
            for file_path in sensitive_files:
                full_path = self.project_root / file_path
                if full_path.exists():
                    # Definir permissões 600 (rw para owner, nada para outros)
                    os.chmod(full_path, 0o600)
                    print(f"✅ Permissões definidas para {file_path}")
            
            # Permissões para diretórios
            sensitive_dirs = [
                "config",
                "security",
                "logs"
            ]
            
            for dir_path in sensitive_dirs:
                full_path = self.project_root / dir_path
                if full_path.exists():
                    # Definir permissões 700 (rwx para owner, nada para outros)
                    os.chmod(full_path, 0o700)
                    print(f"✅ Permissões definidas para diretório {dir_path}")
        else:
            print("⚠️  Configuração de permissões não suportada no Windows")
    
    def setup_encryption(self):
        """Configura sistema de criptografia"""
        print("🔐 Configurando sistema de criptografia...")
        
        # Criar arquivo de configuração de criptografia
        encryption_config = {
            "encryption": {
                "default_algorithm": "AES-256-GCM",
                "key_derivation": {
                    "method": "PBKDF2",
                    "iterations": 150000,
                    "salt_length": 32,
                    "hash_algorithm": "SHA-256"
                },
                "secure_random": {
                    "use_system_random": True,
                    "entropy_sources": ["os.urandom", "secrets"]
                }
            }
        }
        
        encryption_file = self.security_dir / "encryption.yaml"
        with open(encryption_file, 'w') as f:
            yaml.dump(encryption_config, f, default_flow_style=False, indent=2)
        
        print(f"✅ Configuração de criptografia criada: {encryption_file}")
    
    def configure_secure_logging(self):
        """Configura sistema de logs seguros"""
        print("📝 Configurando sistema de logs seguros...")
        
        # Criar diretório de logs
        logs_dir = self.project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Configuração de logging
        logging_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "secure": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                },
                "audit": {
                    "format": "%(asctime)s - AUDIT - %(levelname)s - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                }
            },
            "handlers": {
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": str(logs_dir / "aws-agent.log"),
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5,
                    "formatter": "secure",
                    "level": "INFO"
                },
                "audit": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": str(logs_dir / "audit.log"),
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 10,
                    "formatter": "audit",
                    "level": "INFO"
                },
                "security": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": str(logs_dir / "security.log"),
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 10,
                    "formatter": "audit",
                    "level": "WARNING"
                }
            },
            "loggers": {
                "aws_agent": {
                    "handlers": ["file", "audit"],
                    "level": "INFO",
                    "propagate": False
                },
                "aws_agent.security": {
                    "handlers": ["security"],
                    "level": "WARNING",
                    "propagate": False
                }
            }
        }
        
        logging_file = self.config_dir / "logging.yaml"
        with open(logging_file, 'w') as f:
            yaml.dump(logging_config, f, default_flow_style=False, indent=2)
        
        print(f"✅ Configuração de logging criada: {logging_file}")
    
    def configure_audit_logging(self):
        """Configura auditoria de ações"""
        print("🔍 Configurando auditoria de ações...")
        
        audit_config = {
            "audit": {
                "enabled": True,
                "log_all_actions": True,
                "log_failed_attempts": True,
                "log_permission_checks": True,
                "retention_policy": {
                    "days": 365,
                    "archive_after_days": 90,
                    "compression": True
                },
                "alerts": {
                    "failed_login_threshold": 3,
                    "suspicious_activity_patterns": [
                        "multiple_failed_logins",
                        "unusual_access_patterns",
                        "privilege_escalation_attempts"
                    ]
                }
            }
        }
        
        audit_file = self.security_dir / "audit.yaml"
        with open(audit_file, 'w') as f:
            yaml.dump(audit_config, f, default_flow_style=False, indent=2)
        
        print(f"✅ Configuração de auditoria criada: {audit_file}")
    
    def configure_security_alerts(self):
        """Configura alertas de segurança"""
        print("🚨 Configurando alertas de segurança...")
        
        alerts_config = {
            "alerts": {
                "channels": {
                    "email": {
                        "enabled": True,
                        "smtp_server": "smtp.gmail.com",
                        "smtp_port": 587,
                        "use_tls": True,
                        "sender": "security@exemplo.com",
                        "recipients": ["admin@exemplo.com"]
                    },
                    "slack": {
                        "enabled": False,
                        "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
                    },
                    "webhook": {
                        "enabled": False,
                        "url": "https://your-webhook-endpoint.com/alerts"
                    }
                },
                "severity_levels": {
                    "low": ["info", "debug"],
                    "medium": ["warning"],
                    "high": ["error"],
                    "critical": ["critical", "security_breach"]
                },
                "rate_limiting": {
                    "enabled": True,
                    "max_alerts_per_hour": 10,
                    "cooldown_period": 300  # 5 minutos
                }
            }
        }
        
        alerts_file = self.security_dir / "alerts.yaml"
        with open(alerts_file, 'w') as f:
            yaml.dump(alerts_config, f, default_flow_style=False, indent=2)
        
        print(f"✅ Configuração de alertas criada: {alerts_file}")
    
    def install_security_tools(self):
        """Instala ferramentas de segurança"""
        print("🛠️ Instalando ferramentas de segurança...")
        
        security_tools = [
            "bandit",       # Security linter
            "safety",       # Dependency vulnerability scanner
            "pip-audit",    # Python package auditor
        ]
        
        for tool in security_tools:
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", tool
                ], check=True, capture_output=True)
                print(f"✅ {tool} instalado com sucesso")
            except subprocess.CalledProcessError:
                print(f"❌ Falha ao instalar {tool}")
    
    def create_security_scripts(self):
        """Cria scripts de segurança adicionais"""
        print("📜 Criando scripts de segurança...")
        
        # Script de verificação de compliance
        compliance_script = """#!/usr/bin/env python3
\"\"\"
Script de verificação de compliance
\"\"\"
import sys
import subprocess
from pathlib import Path

def check_compliance():
    \"\"\"Verifica compliance de segurança\"\"\"
    project_root = Path(__file__).parent.parent
    
    # Executar auditoria
    result = subprocess.run([
        sys.executable, str(project_root / "security" / "audit.py")
    ], capture_output=True, text=True)
    
    return result.returncode == 0

if __name__ == "__main__":
    if check_compliance():
        print("✅ Compliance verificado com sucesso")
        sys.exit(0)
    else:
        print("❌ Falha na verificação de compliance")
        sys.exit(1)
"""
        
        compliance_file = self.security_dir / "compliance_check.py"
        with open(compliance_file, 'w') as f:
            f.write(compliance_script)
        
        # Tornar executável
        if os.name == 'posix':
            os.chmod(compliance_file, 0o755)
        
        print(f"✅ Script de compliance criado: {compliance_file}")
    
    def generate_security_checklist(self):
        """Gera checklist de segurança"""
        print("📋 Gerando checklist de segurança...")
        
        checklist = """# 🔐 Security Checklist - AWS Multi-Account Agent

## 📋 Configuração Inicial

### 🔑 Credenciais
- [ ] Credenciais não estão hardcoded no código
- [ ] Keyring do sistema está configurado
- [ ] Criptografia AES-256 está habilitada
- [ ] Rotação automática de tokens configurada

### 🔒 Permissões
- [ ] Arquivos sensíveis com permissões 600
- [ ] Diretórios sensíveis com permissões 700
- [ ] Princípio do menor privilégio aplicado
- [ ] Validação de permissões habilitada

### 🌐 Rede
- [ ] TLS 1.3 forçado
- [ ] Verificação de certificados habilitada
- [ ] Timeouts apropriados configurados
- [ ] Proxy configurado se necessário

## 🔍 Monitoramento

### 📝 Logs
- [ ] Logging seguro configurado
- [ ] Sanitização de logs habilitada
- [ ] Retenção de logs configurada
- [ ] Criptografia de logs habilitada

### 🚨 Alertas
- [ ] Alertas de segurança configurados
- [ ] Canais de notificação configurados
- [ ] Limites de rate configurados
- [ ] Escalação automática configurada

### 🔍 Auditoria
- [ ] Auditoria de ações habilitada
- [ ] Logs de auditoria protegidos
- [ ] Retenção de auditoria configurada
- [ ] Compliance verificado

## 🛡️ Hardening

### 🔧 Configuração
- [ ] Configuração de segurança aplicada
- [ ] Timeouts de sessão configurados
- [ ] Lockout por tentativas configurado
- [ ] Validação estrita habilitada

### 🧪 Testes
- [ ] Testes de segurança executados
- [ ] Vulnerability scanning executado
- [ ] Dependency checking executado
- [ ] Penetration testing executado

## 📊 Compliance

### ✅ Frameworks
- [ ] OWASP Top 10 verificado
- [ ] AWS Well-Architected implementado
- [ ] PCI DSS (se aplicável)
- [ ] GDPR (se aplicável)

### 📈 Métricas
- [ ] Score de compliance > 80%
- [ ] Cobertura de testes > 90%
- [ ] Zero vulnerabilidades críticas
- [ ] Documentação atualizada

## 🚀 Produção

### 🔄 Deploy
- [ ] Secrets management configurado
- [ ] CI/CD pipeline seguro
- [ ] Backup de configurações
- [ ] Rollback plan definido

### 📞 Resposta a Incidentes
- [ ] Plano de resposta definido
- [ ] Contatos de emergência configurados
- [ ] Procedimentos de contenção definidos
- [ ] Comunicação de incidentes preparada

---

*Este checklist deve ser revisado antes de cada deploy em produção.*
"""
        
        checklist_file = self.security_dir / "security-checklist.md"
        with open(checklist_file, 'w') as f:
            f.write(checklist)
        
        print(f"✅ Checklist de segurança criado: {checklist_file}")
    
    def print_summary(self):
        """Imprime resumo da configuração"""
        print("\n" + "="*60)
        print("🔐 RESUMO DA CONFIGURAÇÃO DE SEGURANÇA")
        print("="*60)
        
        print("✅ Configurações criadas:")
        print("  • config/security.yaml - Configuração principal")
        print("  • config/logging.yaml - Configuração de logs")
        print("  • security/encryption.yaml - Configuração de criptografia")
        print("  • security/audit.yaml - Configuração de auditoria")
        print("  • security/alerts.yaml - Configuração de alertas")
        print("  • security/security-checklist.md - Checklist de segurança")
        
        print("\n🛠️ Ferramentas de segurança instaladas:")
        print("  • bandit - Security linter")
        print("  • safety - Dependency vulnerability scanner")
        print("  • pip-audit - Python package auditor")
        
        print("\n🔒 Permissões configuradas:")
        if os.name == 'posix':
            print("  • Arquivos sensíveis: 600 (rw-------)")
            print("  • Diretórios sensíveis: 700 (rwx------)")
        else:
            print("  • Permissões não configuradas (Windows)")
        
        print("\n📋 Próximos passos:")
        print("  1. Execute: python security/audit.py")
        print("  2. Revise: security/security-checklist.md")
        print("  3. Configure alertas em: security/alerts.yaml")
        print("  4. Teste em ambiente de produção")
        
        print("\n" + "="*60)

def main():
    """Função principal"""
    print("🔐 AWS Multi-Account Agent - Security Configuration")
    print("="*55)
    
    configurator = SecurityConfigurator()
    
    # Configurar segurança
    configurator.configure_production_security()
    
    # Criar scripts adicionais
    configurator.create_security_scripts()
    
    # Gerar checklist
    configurator.generate_security_checklist()
    
    # Imprimir resumo
    configurator.print_summary()
    
    print("\n✅ Configuração de segurança concluída com sucesso!")

if __name__ == "__main__":
    main()
