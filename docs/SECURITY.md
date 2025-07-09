# 🔐 Guia de Segurança do AWS Multi-Account Agent

## 🛡️ **Visão Geral de Segurança**

A segurança é uma prioridade fundamental no AWS Multi-Account Agent. Este documento detalha todas as medidas de segurança implementadas, configurações recomendadas e melhores práticas.

---

## 🔑 **Gerenciamento de Credenciais**

### 🔒 **Armazenamento Seguro**

#### **Criptografia de Credenciais**
```python
# Todas as credenciais são criptografadas usando AES-256-GCM
ENCRYPTION_CONFIG = {
    "algorithm": "AES-256-GCM",
    "key_derivation": "PBKDF2",
    "iterations": 100000,
    "salt_length": 32
}
```

#### **Keyring do Sistema**
- Integração com o keyring nativo do OS
- Credenciais não são armazenadas em texto plano
- Suporte para macOS Keychain, Windows Credential Store, Linux Secret Service

```python
from aws_agent.core.security import CredentialManager

# Armazenamento seguro
cred_manager = CredentialManager()
cred_manager.store_credentials("account-name", {
    "access_key": "AKIA...",
    "secret_key": "wJalrXUt..."
})
```

### 🔄 **Rotação Automática**

#### **Tokens de Sessão**
```python
# Configuração de rotação automática
SESSION_CONFIG = {
    "auto_refresh": True,
    "refresh_threshold": 300,  # 5 minutos antes da expiração
    "max_session_duration": 3600  # 1 hora
}
```

#### **Detecção de Expiração**
```python
class SessionManager:
    def is_token_expired(self, token):
        """Verifica se o token está prestes a expirar"""
        expiry = token.get('Expiration')
        if expiry:
            remaining = (expiry - datetime.utcnow()).total_seconds()
            return remaining < self.refresh_threshold
        return True
```

---

## 🚨 **Controle de Acesso**

### 🔐 **Validação de Permissões**

#### **Verificação Prévia**
```python
class PermissionValidator:
    def validate_action(self, service, action, resource=None):
        """Valida se a ação é permitida antes da execução"""
        required_permissions = self.get_required_permissions(service, action)
        current_permissions = self.get_current_permissions()
        
        for permission in required_permissions:
            if not self.has_permission(current_permissions, permission, resource):
                raise PermissionDeniedError(f"Permissão negada: {permission}")
```

#### **Princípio do Menor Privilégio**
```python
# Exemplo de validação granular
PERMISSION_MATRIX = {
    "s3": {
        "list_buckets": ["s3:ListAllMyBuckets"],
        "create_bucket": ["s3:CreateBucket"],
        "upload_object": ["s3:PutObject", "s3:PutObjectAcl"],
        "delete_object": ["s3:DeleteObject"]
    },
    "ec2": {
        "list_instances": ["ec2:DescribeInstances"],
        "start_instance": ["ec2:StartInstances"],
        "stop_instance": ["ec2:StopInstances"]
    }
}
```

### 🔍 **Auditoria de Ações**

#### **Log de Auditoria**
```python
class AuditLogger:
    def log_action(self, user, action, resource, result):
        """Registra todas as ações para auditoria"""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user": user,
            "action": action,
            "resource": resource,
            "result": result,
            "ip_address": self.get_client_ip(),
            "user_agent": self.get_user_agent()
        }
        
        # Criptografar e armazenar
        encrypted_entry = self.encrypt_audit_entry(audit_entry)
        self.store_audit_log(encrypted_entry)
```

---

## 🔒 **Proteção de Dados**

### 🛡️ **Criptografia em Trânsito**

#### **TLS 1.3 Forçado**
```python
import ssl
from urllib3.util.ssl_ import create_urllib3_context

# Configuração SSL/TLS segura
def create_secure_context():
    context = create_urllib3_context()
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
    return context
```

#### **Verificação de Certificados**
```python
# Sempre verificar certificados SSL
BOTO3_CONFIG = {
    "use_ssl": True,
    "verify": True,  # Verificar certificados
    "check_hostname": True
}
```

### 🧹 **Sanitização de Logs**

#### **Redação de Informações Sensíveis**
```python
import re

class LogSanitizer:
    SENSITIVE_PATTERNS = [
        r'AKIA[0-9A-Z]{16}',  # AWS Access Key
        r'[A-Za-z0-9/+=]{40}',  # AWS Secret Key
        r'password["\']?\s*[:=]\s*["\']?[^\s,"\']+',  # Senhas
        r'token["\']?\s*[:=]\s*["\']?[^\s,"\']+',  # Tokens
    ]
    
    def sanitize_log(self, log_message):
        """Remove informações sensíveis dos logs"""
        for pattern in self.SENSITIVE_PATTERNS:
            log_message = re.sub(pattern, '[REDACTED]', log_message, flags=re.IGNORECASE)
        return log_message
```

### 🔐 **Validação de Entrada**

#### **Schemas Pydantic**
```python
from pydantic import BaseModel, validator, SecretStr
from typing import Optional

class AWSCredentials(BaseModel):
    access_key_id: str
    secret_access_key: SecretStr
    session_token: Optional[SecretStr] = None
    region: str = "us-east-1"
    
    @validator('access_key_id')
    def validate_access_key_format(cls, v):
        if not re.match(r'^AKIA[0-9A-Z]{16}$', v):
            raise ValueError('Formato de Access Key inválido')
        return v
    
    @validator('secret_access_key')
    def validate_secret_key_format(cls, v):
        if len(v.get_secret_value()) != 40:
            raise ValueError('Formato de Secret Key inválido')
        return v
```

---

## 🛡️ **Configuração de Segurança**

### 📋 **Arquivo de Configuração**
```yaml
# config/security.yaml
security:
  # Configurações de criptografia
  encryption:
    algorithm: "AES-256-GCM"
    key_derivation: "PBKDF2"
    iterations: 100000
    salt_length: 32
  
  # Configurações de sessão
  session:
    timeout: 3600  # 1 hora
    max_retries: 3
    lockout_time: 900  # 15 minutos após falhas
    auto_refresh: true
    refresh_threshold: 300  # 5 minutos
  
  # Configurações de auditoria
  audit:
    enabled: true
    log_level: "INFO"
    retention_days: 90
    encrypt_logs: true
    
  # Configurações de validação
  validation:
    strict_mode: true
    validate_permissions: true
    check_resource_existence: true
    
  # Configurações de rede
  network:
    force_tls: true
    min_tls_version: "1.3"
    verify_certificates: true
    timeout: 30
```

### 🔧 **Configuração Programática**
```python
from aws_agent.core.security import SecurityConfig

# Configuração programática de segurança
security_config = SecurityConfig(
    encryption_algorithm="AES-256-GCM",
    session_timeout=3600,
    audit_enabled=True,
    strict_validation=True
)
```

---

## 🔍 **Monitoramento e Auditoria**

### 📊 **Métricas de Segurança**

#### **Monitoramento em Tempo Real**
```python
class SecurityMonitor:
    def __init__(self):
        self.failed_attempts = {}
        self.active_sessions = {}
        self.suspicious_activities = []
    
    def track_failed_login(self, user, ip_address):
        """Rastreia tentativas de login falhadas"""
        key = f"{user}:{ip_address}"
        self.failed_attempts[key] = self.failed_attempts.get(key, 0) + 1
        
        if self.failed_attempts[key] >= 3:
            self.trigger_lockout(user, ip_address)
    
    def detect_anomalies(self, action, user, timestamp):
        """Detecta atividades anômalas"""
        if self.is_unusual_activity(action, user, timestamp):
            self.suspicious_activities.append({
                "user": user,
                "action": action,
                "timestamp": timestamp,
                "risk_level": self.calculate_risk_level(action)
            })
```

### 📈 **Relatórios de Segurança**

#### **Relatório Automático**
```python
class SecurityReporter:
    def generate_security_report(self):
        """Gera relatório de segurança automático"""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "failed_logins": self.count_failed_logins(),
            "active_sessions": self.count_active_sessions(),
            "permission_violations": self.count_permission_violations(),
            "suspicious_activities": len(self.suspicious_activities),
            "compliance_score": self.calculate_compliance_score()
        }
        
        return report
```

---

## 🚨 **Resposta a Incidentes**

### 🔒 **Lockout Automático**

#### **Bloqueio por Falhas de Autenticação**
```python
class SecurityLockout:
    def __init__(self, max_attempts=3, lockout_duration=900):
        self.max_attempts = max_attempts
        self.lockout_duration = lockout_duration
        self.failed_attempts = {}
        self.locked_accounts = {}
    
    def is_account_locked(self, user):
        """Verifica se conta está bloqueada"""
        if user in self.locked_accounts:
            lockout_time = self.locked_accounts[user]
            if time.time() - lockout_time < self.lockout_duration:
                return True
            else:
                del self.locked_accounts[user]
        return False
    
    def trigger_lockout(self, user):
        """Bloqueia conta por segurança"""
        self.locked_accounts[user] = time.time()
        self.send_security_alert(user)
```

### 📧 **Alertas de Segurança**

#### **Notificações Automáticas**
```python
class SecurityAlerts:
    def send_security_alert(self, alert_type, details):
        """Envia alertas de segurança"""
        alert = {
            "type": alert_type,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details,
            "severity": self.calculate_severity(alert_type)
        }
        
        # Enviar por múltiplos canais
        self.send_email_alert(alert)
        self.send_slack_alert(alert)
        self.log_security_event(alert)
```

---

## 🧪 **Testes de Segurança**

### 🔍 **Testes Automatizados**

#### **Testes de Penetração**
```python
class SecurityTests:
    def test_credential_encryption(self):
        """Testa se credenciais estão criptografadas"""
        cred_manager = CredentialManager()
        
        # Armazenar credencial
        cred_manager.store_credentials("test", {"key": "value"})
        
        # Verificar se está criptografada no storage
        raw_data = cred_manager.get_raw_storage_data("test")
        assert "value" not in raw_data
        
    def test_session_timeout(self):
        """Testa timeout de sessão"""
        session = SessionManager()
        
        # Simular sessão expirada
        expired_session = session.create_session()
        time.sleep(session.timeout + 1)
        
        assert session.is_session_expired(expired_session)
        
    def test_permission_validation(self):
        """Testa validação de permissões"""
        validator = PermissionValidator()
        
        # Deve falhar sem permissões
        with pytest.raises(PermissionDeniedError):
            validator.validate_action("s3", "delete_bucket")
```

### 🔒 **Vulnerability Scanning**

#### **Bandit Security Scanner**
```bash
# Executar scan de segurança
bandit -r src/ -f json -o security-report.json

# Verificar vulnerabilidades conhecidas
safety check --json
```

---

## 📋 **Compliance e Conformidade**

### ✅ **Frameworks Suportados**

#### **OWASP Top 10**
- [x] A01:2021 - Broken Access Control
- [x] A02:2021 - Cryptographic Failures  
- [x] A03:2021 - Injection
- [x] A04:2021 - Insecure Design
- [x] A05:2021 - Security Misconfiguration
- [x] A06:2021 - Vulnerable Components
- [x] A07:2021 - Identification and Authentication Failures
- [x] A08:2021 - Software and Data Integrity Failures
- [x] A09:2021 - Security Logging and Monitoring Failures
- [x] A10:2021 - Server-Side Request Forgery

#### **AWS Well-Architected Security Pillar**
- [x] Identity and Access Management
- [x] Detective Controls
- [x] Infrastructure Protection
- [x] Data Protection in Transit and at Rest
- [x] Incident Response

### 📊 **Compliance Checklist**

```python
class ComplianceChecker:
    def run_compliance_check(self):
        """Executa verificação de compliance"""
        checks = {
            "credential_encryption": self.check_credential_encryption(),
            "session_management": self.check_session_management(),
            "audit_logging": self.check_audit_logging(),
            "permission_validation": self.check_permission_validation(),
            "network_security": self.check_network_security()
        }
        
        compliance_score = sum(checks.values()) / len(checks) * 100
        return compliance_score, checks
```

---

## 🛡️ **Hardening e Configuração**

### 🔧 **Configuração Recomendada**

#### **Ambiente de Produção**
```yaml
# config/production-security.yaml
security:
  encryption:
    algorithm: "AES-256-GCM"
    key_derivation: "PBKDF2"
    iterations: 150000  # Maior para produção
    
  session:
    timeout: 1800  # 30 minutos
    max_retries: 2
    lockout_time: 1800  # 30 minutos
    
  audit:
    enabled: true
    log_level: "DEBUG"
    retention_days: 365  # 1 ano
    encrypt_logs: true
    
  validation:
    strict_mode: true
    validate_permissions: true
    check_resource_existence: true
    require_mfa: true  # Requer MFA
```

### 🔐 **Integração com AWS IAM**

#### **Roles e Policies Recomendadas**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::my-secure-bucket",
        "arn:aws:s3:::my-secure-bucket/*"
      ],
      "Condition": {
        "StringEquals": {
          "s3:x-amz-server-side-encryption": "AES256"
        }
      }
    }
  ]
}
```

---

## 🚀 **Melhores Práticas**

### 🔑 **Gestão de Credenciais**
1. **Nunca hardcode credenciais** no código
2. **Use AWS IAM Roles** sempre que possível
3. **Implemente rotação regular** de credenciais
4. **Use MFA** para operações críticas
5. **Monitore uso** de credenciais

### 🔒 **Controle de Acesso**
1. **Aplique o princípio do menor privilégio**
2. **Valide permissões** antes de cada operação
3. **Implemente auditoria** completa
4. **Use timeouts** apropriados
5. **Monitore atividades** suspeitas

### 📝 **Monitoramento**
1. **Ative logs** de auditoria
2. **Monitore métricas** de segurança
3. **Configure alertas** automáticos
4. **Faça reviews** regulares
5. **Documente incidentes**

---

## 📞 **Contato de Segurança**

Para reportar vulnerabilidades de segurança:
- **Email**: security@exemplo.com
- **GPG Key**: [Chave Pública](security-key.asc)
- **Responsible Disclosure**: 90 dias

---

*Este documento deve ser revisado regularmente e atualizado conforme novas ameaças e melhores práticas de segurança.*
