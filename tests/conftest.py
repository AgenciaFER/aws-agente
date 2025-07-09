"""
Configuração pytest para o projeto AWS Multi-Account Agent
"""
import pytest
import os
from pathlib import Path

# Adicionar src ao Python path
src_path = Path(__file__).parent / "src"
if str(src_path) not in os.sys.path:
    os.sys.path.insert(0, str(src_path))

@pytest.fixture
def aws_credentials():
    """Fixture para credenciais AWS de teste"""
    return {
        "aws_access_key_id": "test_key",
        "aws_secret_access_key": "test_secret",
        "region_name": "us-east-1"
    }

@pytest.fixture
def sample_config():
    """Fixture para configuração de exemplo"""
    return {
        "default_region": "us-east-1",
        "encryption_enabled": True,
        "session_timeout": 1800,
        "log_level": "INFO"
    }
