#!/usr/bin/env python3
"""
Script de Auditoria de Segurança do AWS Multi-Account Agent
==========================================================

Este script executa uma auditoria completa de segurança,
verificando configurações, permissões e vulnerabilidades.
"""

import os
import sys
import json
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Adicionar o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

class SecurityAuditor:
    """Auditor de segurança para o AWS Multi-Account Agent"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.audit_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
            "vulnerabilities": [],
            "recommendations": [],
            "compliance_score": 0
        }
    
    def run_full_audit(self) -> Dict[str, Any]:
        """Executa auditoria completa de segurança"""
        print("🔍 Iniciando auditoria de segurança...")
        
        # Verificações de segurança
        self.check_file_permissions()
        self.check_credential_storage()
        self.check_code_vulnerabilities()
        self.check_dependencies()
        self.check_configuration_security()
        self.check_logging_security()
        self.check_network_security()
        self.check_encryption_usage()
        
        # Calcular score de compliance
        self.calculate_compliance_score()
        
        # Gerar relatório
        self.generate_security_report()
        
        return self.audit_results
    
    def check_file_permissions(self):
        """Verifica permissões de arquivos sensíveis"""
        print("🔒 Verificando permissões de arquivos...")
        
        sensitive_files = [
            "config/accounts.json",
            "config/default.yaml",
            ".env",
            "credentials.json"
        ]
        
        issues = []
        for file_path in sensitive_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                # Verificar permissões no Unix
                if os.name == 'posix':
                    stat = full_path.stat()
                    # Verificar se arquivo não é legível por outros
                    if stat.st_mode & 0o044:  # Outros podem ler
                        issues.append(f"Arquivo {file_path} é legível por outros usuários")
                    # Verificar se arquivo não é executável
                    if stat.st_mode & 0o111:  # Arquivo executável
                        issues.append(f"Arquivo {file_path} é executável (desnecessário)")
        
        self.audit_results["checks"]["file_permissions"] = {
            "status": "PASS" if not issues else "FAIL",
            "issues": issues,
            "recommendation": "Defina permissões 600 para arquivos sensíveis"
        }
    
    def check_credential_storage(self):
        """Verifica armazenamento seguro de credenciais"""
        print("🔐 Verificando armazenamento de credenciais...")
        
        issues = []
        
        # Verificar se não há credenciais hardcoded
        for py_file in self.project_root.glob("**/*.py"):
            if py_file.is_file():
                try:
                    content = py_file.read_text(encoding='utf-8')
                except UnicodeDecodeError:
                    # Pular arquivos com encoding inválido
                    continue
                
                # Padrões de credenciais AWS
                patterns = [
                    r"AKIA[0-9A-Z]{16}",  # AWS Access Key
                    r"aws_access_key_id\s*=\s*['\"][^'\"]+['\"]",
                    r"aws_secret_access_key\s*=\s*['\"][^'\"]+['\"]",
                    r"password\s*=\s*['\"][^'\"]+['\"]"
                ]
                
                import re
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        issues.append(f"Possível credencial hardcoded em {py_file}")
        
        # Verificar se keyring está sendo usado
        keyring_usage = False
        for py_file in self.project_root.glob("**/*.py"):
            if py_file.is_file():
                try:
                    content = py_file.read_text(encoding='utf-8')
                    if "keyring" in content or "cryptography" in content:
                        keyring_usage = True
                        break
                except UnicodeDecodeError:
                    continue
        
        if not keyring_usage:
            issues.append("Sistema de keyring não está sendo utilizado")
        
        self.audit_results["checks"]["credential_storage"] = {
            "status": "PASS" if not issues else "FAIL",
            "issues": issues,
            "recommendation": "Use keyring e criptografia para armazenar credenciais"
        }
    
    def check_code_vulnerabilities(self):
        """Verifica vulnerabilidades no código usando bandit"""
        print("🚨 Verificando vulnerabilidades no código...")
        
        try:
            # Executar bandit
            result = subprocess.run([
                sys.executable, "-m", "bandit", "-r", "src/", "-f", "json"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            vulnerabilities = []
            if result.returncode == 0:
                bandit_output = json.loads(result.stdout)
                vulnerabilities = bandit_output.get("results", [])
            
            self.audit_results["checks"]["code_vulnerabilities"] = {
                "status": "PASS" if not vulnerabilities else "FAIL",
                "vulnerabilities": len(vulnerabilities),
                "details": vulnerabilities[:5],  # Primeiras 5
                "recommendation": "Corrija vulnerabilidades encontradas pelo bandit"
            }
            
        except Exception as e:
            self.audit_results["checks"]["code_vulnerabilities"] = {
                "status": "ERROR",
                "error": str(e),
                "recommendation": "Instale bandit: pip install bandit"
            }
    
    def check_dependencies(self):
        """Verifica vulnerabilidades em dependências"""
        print("📦 Verificando dependências vulneráveis...")
        
        try:
            # Verificar safety
            result = subprocess.run([
                sys.executable, "-m", "safety", "check", "--json"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            vulnerabilities = []
            if result.returncode != 0:
                try:
                    safety_output = json.loads(result.stdout)
                    vulnerabilities = safety_output
                except:
                    pass
            
            self.audit_results["checks"]["dependencies"] = {
                "status": "PASS" if not vulnerabilities else "FAIL",
                "vulnerabilities": len(vulnerabilities),
                "details": vulnerabilities[:3],  # Primeiras 3
                "recommendation": "Atualize dependências vulneráveis"
            }
            
        except Exception as e:
            self.audit_results["checks"]["dependencies"] = {
                "status": "ERROR",
                "error": str(e),
                "recommendation": "Instale safety: pip install safety"
            }
    
    def check_configuration_security(self):
        """Verifica configurações de segurança"""
        print("⚙️ Verificando configurações de segurança...")
        
        issues = []
        
        # Verificar se arquivo de configuração existe
        config_file = self.project_root / "config" / "default.yaml"
        if not config_file.exists():
            issues.append("Arquivo de configuração padrão não encontrado")
        else:
            import yaml
            try:
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                
                # Verificar configurações de segurança
                security_config = config.get('security', {})
                
                # Verificar algoritmo de criptografia
                encryption = security_config.get('encryption', {})
                if encryption.get('algorithm') != 'AES-256':
                    issues.append("Algoritmo de criptografia não é AES-256")
                
                # Verificar timeout de sessão
                if config.get('aws', {}).get('session_timeout', 0) > 3600:
                    issues.append("Timeout de sessão muito longo (> 1 hora)")
                
                # Verificar nível de log
                if config.get('logging', {}).get('level') == 'DEBUG':
                    issues.append("Nível de log DEBUG em produção pode vazar informações")
                
            except Exception as e:
                issues.append(f"Erro ao ler configuração: {e}")
        
        self.audit_results["checks"]["configuration"] = {
            "status": "PASS" if not issues else "FAIL",
            "issues": issues,
            "recommendation": "Corrija configurações de segurança"
        }
    
    def check_logging_security(self):
        """Verifica configuração de logs"""
        print("📝 Verificando configuração de logs...")
        
        issues = []
        
        # Verificar se logs estão sendo sanitizados
        log_files = list(self.project_root.glob("**/*.py"))
        sanitization_found = False
        
        for py_file in log_files:
            if py_file.is_file():
                try:
                    content = py_file.read_text(encoding='utf-8')
                    if "sanitize" in content.lower() or "redact" in content.lower():
                        sanitization_found = True
                        break
                except UnicodeDecodeError:
                    continue
        
        if not sanitization_found:
            issues.append("Sistema de sanitização de logs não encontrado")
        
        # Verificar se logs estão sendo armazenados com segurança
        log_dir = self.project_root / "logs"
        if log_dir.exists():
            for log_file in log_dir.glob("*.log"):
                if os.name == 'posix':
                    stat = log_file.stat()
                    if stat.st_mode & 0o044:  # Outros podem ler
                        issues.append(f"Log {log_file.name} é legível por outros")
        
        self.audit_results["checks"]["logging"] = {
            "status": "PASS" if not issues else "FAIL",
            "issues": issues,
            "recommendation": "Implemente sanitização e proteja arquivos de log"
        }
    
    def check_network_security(self):
        """Verifica configurações de rede"""
        print("🌐 Verificando configurações de rede...")
        
        issues = []
        
        # Verificar uso de HTTPS/TLS
        for py_file in self.project_root.glob("**/*.py"):
            if py_file.is_file():
                content = py_file.read_text()
                
                # Verificar uso de HTTP inseguro
                if "http://" in content and "localhost" not in content:
                    issues.append(f"Uso de HTTP inseguro em {py_file}")
                
                # Verificar desabilitação de verificação SSL
                if "verify=False" in content or "ssl._create_unverified_context" in content:
                    issues.append(f"Verificação SSL desabilitada em {py_file}")
        
        self.audit_results["checks"]["network"] = {
            "status": "PASS" if not issues else "FAIL",
            "issues": issues,
            "recommendation": "Use HTTPS e sempre verifique certificados SSL"
        }
    
    def check_encryption_usage(self):
        """Verifica uso de criptografia"""
        print("🔒 Verificando uso de criptografia...")
        
        issues = []
        encryption_found = False
        
        # Verificar uso de bibliotecas de criptografia
        for py_file in self.project_root.glob("**/*.py"):
            if py_file.is_file():
                content = py_file.read_text()
                
                crypto_imports = [
                    "cryptography",
                    "hashlib",
                    "secrets",
                    "Crypto"
                ]
                
                for crypto_lib in crypto_imports:
                    if crypto_lib in content:
                        encryption_found = True
                        break
        
        if not encryption_found:
            issues.append("Nenhuma biblioteca de criptografia encontrada")
        
        # Verificar uso de algoritmos seguros
        for py_file in self.project_root.glob("**/*.py"):
            if py_file.is_file():
                content = py_file.read_text()
                
                # Verificar algoritmos inseguros
                insecure_algos = ["MD5", "SHA1", "DES", "RC4"]
                for algo in insecure_algos:
                    if algo in content:
                        issues.append(f"Algoritmo inseguro {algo} encontrado em {py_file}")
        
        self.audit_results["checks"]["encryption"] = {
            "status": "PASS" if not issues else "FAIL",
            "issues": issues,
            "recommendation": "Use criptografia forte (AES-256, SHA-256)"
        }
    
    def calculate_compliance_score(self):
        """Calcula score de compliance"""
        total_checks = len(self.audit_results["checks"])
        passed_checks = sum(1 for check in self.audit_results["checks"].values() 
                          if check["status"] == "PASS")
        
        self.audit_results["compliance_score"] = (passed_checks / total_checks) * 100
    
    def generate_security_report(self):
        """Gera relatório de segurança"""
        print("📊 Gerando relatório de segurança...")
        
        # Salvar relatório JSON
        report_file = self.project_root / "security" / "security-audit-report.json"
        with open(report_file, 'w') as f:
            json.dump(self.audit_results, f, indent=2)
        
        # Gerar relatório HTML
        html_report = self.generate_html_report()
        html_file = self.project_root / "security" / "security-audit-report.html"
        with open(html_file, 'w') as f:
            f.write(html_report)
        
        print(f"✅ Relatório salvo em: {report_file}")
        print(f"🌐 Relatório HTML salvo em: {html_file}")
    
    def generate_html_report(self) -> str:
        """Gera relatório HTML"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Security Audit Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
                .score {{ font-size: 24px; font-weight: bold; }}
                .pass {{ color: #27ae60; }}
                .fail {{ color: #e74c3c; }}
                .error {{ color: #f39c12; }}
                .check {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
                .issues {{ background: #f8f9fa; padding: 10px; margin: 5px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔐 Security Audit Report</h1>
                <p>Generated: {self.audit_results['timestamp']}</p>
                <p class="score">Compliance Score: {self.audit_results['compliance_score']:.1f}%</p>
            </div>
            
            <h2>Security Checks</h2>
        """
        
        for check_name, check_data in self.audit_results["checks"].items():
            status_class = check_data["status"].lower()
            html += f"""
            <div class="check">
                <h3>{check_name.replace('_', ' ').title()}</h3>
                <p class="{status_class}">Status: {check_data["status"]}</p>
                
                {f'<div class="issues"><strong>Issues:</strong><ul>' + 
                 ''.join(f'<li>{issue}</li>' for issue in check_data.get("issues", [])) + 
                 '</ul></div>' if check_data.get("issues") else ''}
                
                <p><strong>Recommendation:</strong> {check_data.get("recommendation", "N/A")}</p>
            </div>
            """
        
        html += """
            </body>
        </html>
        """
        
        return html
    
    def print_summary(self):
        """Imprime resumo da auditoria"""
        print("\n" + "="*60)
        print("🔍 RESUMO DA AUDITORIA DE SEGURANÇA")
        print("="*60)
        
        print(f"📊 Score de Compliance: {self.audit_results['compliance_score']:.1f}%")
        
        total_checks = len(self.audit_results["checks"])
        passed = sum(1 for check in self.audit_results["checks"].values() 
                    if check["status"] == "PASS")
        failed = sum(1 for check in self.audit_results["checks"].values() 
                    if check["status"] == "FAIL")
        errors = sum(1 for check in self.audit_results["checks"].values() 
                    if check["status"] == "ERROR")
        
        print(f"✅ Verificações aprovadas: {passed}/{total_checks}")
        print(f"❌ Verificações falhadas: {failed}/{total_checks}")
        print(f"⚠️  Verificações com erro: {errors}/{total_checks}")
        
        if failed > 0:
            print("\\n🚨 Verificações que falharam:")
            for check_name, check_data in self.audit_results["checks"].items():
                if check_data["status"] == "FAIL":
                    print(f"  • {check_name.replace('_', ' ').title()}")
                    for issue in check_data.get("issues", []):
                        print(f"    - {issue}")
        
        # Recomendações prioritárias
        print("\\n💡 Recomendações prioritárias:")
        priority_recommendations = [
            "Corrija vulnerabilidades encontradas pelo bandit",
            "Use keyring e criptografia para armazenar credenciais",
            "Defina permissões 600 para arquivos sensíveis",
            "Implemente sanitização e proteja arquivos de log"
        ]
        
        for rec in priority_recommendations:
            print(f"  • {rec}")
        
        print("\\n" + "="*60)

def main():
    """Função principal"""
    print("🔐 AWS Multi-Account Agent - Security Audit")
    print("="*50)
    
    auditor = SecurityAuditor()
    results = auditor.run_full_audit()
    
    auditor.print_summary()
    
    # Sair com código de erro se compliance < 80%
    if results["compliance_score"] < 80:
        print("\\n❌ Compliance score abaixo do mínimo (80%)")
        sys.exit(1)
    else:
        print("\\n✅ Auditoria de segurança concluída com sucesso!")
        sys.exit(0)

if __name__ == "__main__":
    main()
