"""
Testes para o módulo core do AWS Agent
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os

from aws_agent.core.config import Config, get_config, reset_config
from aws_agent.core.account_manager import AccountManager, AWSCredentials
from aws_agent.core.agent import AWSAgent


class TestConfig:
    """Testes para a classe Config"""
    
    def test_config_default_values(self):
        """Testa valores padrão da configuração"""
        config = Config()
        assert config.app_name == "aws-multi-account-agent"
        assert config.version == "1.0.0"
        assert config.log_level == "INFO"
        assert config.default_region == "us-east-1"
        assert config.session_timeout == 3600
    
    def test_config_validation_log_level(self):
        """Testa validação do nível de log"""
        # Nível válido
        config = Config(log_level="DEBUG")
        assert config.log_level == "DEBUG"
        
        # Nível inválido
        with pytest.raises(ValueError, match="Log level must be one of"):
            Config(log_level="INVALID")
    
    def test_config_validation_session_timeout(self):
        """Testa validação do timeout da sessão"""
        # Timeout válido
        config = Config(session_timeout=1800)
        assert config.session_timeout == 1800
        
        # Timeout muito baixo
        with pytest.raises(ValueError, match="Session timeout must be between"):
            Config(session_timeout=30)
        
        # Timeout muito alto
        with pytest.raises(ValueError, match="Session timeout must be between"):
            Config(session_timeout=100000)
    
    def test_config_paths(self):
        """Testa propriedades de caminho"""
        config = Config()
        assert config.credentials_path == config.config_dir / config.credentials_file
        assert config.log_path == config.config_dir / config.log_file
    
    def test_ensure_directories(self):
        """Testa criação de diretórios"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config(config_dir=Path(temp_dir) / "test_aws_agent")
            config.ensure_directories()
            
            assert config.config_dir.exists()
            assert (config.config_dir / "logs").exists()
            assert (config.config_dir / "backups").exists()


class TestAWSCredentials:
    """Testes para a classe AWSCredentials"""
    
    def test_aws_credentials_creation(self):
        """Testa criação de credenciais AWS"""
        creds = AWSCredentials(
            access_key_id="test_access_key",
            secret_access_key="test_secret_key",
            region="us-west-2",
            account_id="123456789012",
            profile_name="test_profile"
        )
        
        assert creds.access_key_id == "test_access_key"
        assert creds.secret_access_key == "test_secret_key"
        assert creds.region == "us-west-2"
        assert creds.account_id == "123456789012"
        assert creds.profile_name == "test_profile"
    
    def test_aws_credentials_to_dict(self):
        """Testa conversão para dicionário"""
        creds = AWSCredentials(
            access_key_id="test_access_key",
            secret_access_key="test_secret_key",
            region="us-west-2",
            account_id="123456789012",
            profile_name="test_profile"
        )
        
        creds_dict = creds.to_dict()
        
        # Verificar campos essenciais
        assert creds_dict["access_key_id"] == "test_access_key"
        assert creds_dict["secret_access_key"] == "test_secret_key"
        assert creds_dict["region"] == "us-west-2"
        assert creds_dict["account_id"] == "123456789012"
        assert creds_dict["profile_name"] == "test_profile"
        assert creds_dict["session_token"] is None
        assert creds_dict["account_name"] == ""
        assert creds_dict["mfa_serial"] is None
        assert creds_dict["role_arn"] is None
        assert creds_dict["external_id"] is None
        assert creds_dict["last_used"] is None
        assert creds_dict["expires_at"] is None
        
        # Verificar se created_at está presente e é uma string ISO
        assert "created_at" in creds_dict
        assert isinstance(creds_dict["created_at"], str)


class TestAccountManager:
    """Testes para a classe AccountManager"""
    
    def test_account_manager_initialization(self):
        """Testa inicialização do AccountManager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config(config_dir=Path(temp_dir) / "test_aws_agent")
            manager = AccountManager(config.credentials_path)
            
            assert manager.config == get_config()
            assert manager._accounts == {}
    
    @patch('aws_agent.core.account_manager.keyring')
    def test_account_manager_encryption_key(self, mock_keyring):
        """Testa geração de chave de criptografia"""
        mock_keyring.get_password.return_value = None
        mock_keyring.set_password.return_value = None
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config(config_dir=Path(temp_dir) / "test_aws_agent")
            manager = AccountManager(config.credentials_path)
            
            # Primeira chamada deve gerar uma nova chave
            key1 = manager._get_encryption_key()
            mock_keyring.set_password.assert_called_once()
            
            # Segunda chamada deve retornar a chave existente
            mock_keyring.get_password.return_value = key1
            mock_keyring.set_password.reset_mock()
            
            key2 = manager._get_encryption_key()
            assert key1 == key2
            mock_keyring.set_password.assert_not_called()


class TestAWSAgent:
    """Testes para a classe AWSAgent"""
    
    def test_aws_agent_initialization(self):
        """Testa inicialização do AWSAgent"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config(config_dir=Path(temp_dir) / "test_aws_agent")
            agent = AWSAgent(config.credentials_path)
            
            assert agent.config == get_config()
            assert agent.current_account is None
            assert agent.current_session is None
            assert agent.services == {}
    
    def test_aws_agent_is_connected(self):
        """Testa verificação de conexão"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config(config_dir=Path(temp_dir) / "test_aws_agent")
            agent = AWSAgent(config.credentials_path)
            
            # Não conectado inicialmente
            status = agent.get_status()
            assert not status["connected"]
            
            # Simula conexão
            agent.current_account = "test_account"
            agent.current_session = MagicMock()
            status = agent.get_status()
            assert status["connected"]
    
    def test_aws_agent_get_account_info(self):
        """Testa obtenção de informações da conta"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config(config_dir=Path(temp_dir) / "test_aws_agent")
            agent = AWSAgent(config.credentials_path)
            
            # Sem conta conectada
            info = agent.get_current_account_info()
            assert info is None
            
            # Com conta conectada (mock)
            agent.current_account = "test_account"
            agent.current_session = MagicMock()
            mock_sts_client = MagicMock()
            mock_sts_client.get_caller_identity.return_value = {
                'UserId': 'test_user',
                'Arn': 'arn:aws:iam::123456789012:user/test_user'
            }
            agent.current_session.client.return_value = mock_sts_client
            
            # Mock account manager
            agent.account_manager.get_account_info = MagicMock(return_value={
                'account_name': 'test_account',
                'account_id': '123456789012'
            })
            
            info = agent.get_current_account_info()
            assert info is not None
            assert info['current_user_id'] == 'test_user'
            assert info['session_valid'] is True
    
    def test_aws_agent_disconnect(self):
        """Testa desconexão"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config(config_dir=Path(temp_dir) / "test_aws_agent")
            agent = AWSAgent(config.credentials_path)
            
            # Simula conexão
            agent.current_account = "test_account"
            agent.current_session = MagicMock()
            agent.services = {"ec2": MagicMock()}
            
            # Desconecta
            agent.disconnect()
            
            assert agent.current_account is None
            assert agent.current_session is None
            assert agent.services == {}


class TestGetConfig:
    """Testes para a função get_config"""
    
    def test_get_config_singleton(self):
        """Testa padrão singleton da configuração"""
        config1 = get_config()
        config2 = get_config()
        
        assert config1 is config2
    
    def test_reset_config(self):
        """Testa reset da configuração"""
        config1 = get_config()
        reset_config()
        config2 = get_config()
        
        assert config1 is not config2
