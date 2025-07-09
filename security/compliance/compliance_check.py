#!/usr/bin/env python3
"""
Script de verificação de compliance
"""
import sys
import subprocess
from pathlib import Path

def check_compliance():
    """Verifica compliance de segurança"""
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
