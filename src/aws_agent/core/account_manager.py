"""
Gerenciador de contas AWS

Este módulo gerencia as credenciais de múltiplas contas AWS de forma segura,
incluindo criptografia, armazenamento e validação de credenciais.
"""

import json
import keyring
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from pydantic import BaseModel, Field, validator

from .config import get_config


@dataclass
class AWSCredentials:
    """
    Classe para representar credenciais AWS
    
    Attributes:
        access_key_id: AWS Access Key ID
        secret_access_key: AWS Secret Access Key
        session_token: AWS Session Token (opcional, para MFA)
        region: Região AWS preferida
        account_id: ID da conta AWS
        account_name: Nome amigável da conta
        profile_name: Nome do perfil AWS
        mfa_serial: Número serial do dispositivo MFA (opcional)
        role_arn: ARN da role para assume (opcional)
        external_id: ID externo para assume role (opcional)
        created_at: Data de criação das credenciais
        last_used: Data da última utilização
        expires_at: Data de expiração (para temporary credentials)
    """
    
    access_key_id: str
    secret_access_key: str
    session_token: Optional[str] = None
    region: str = "us-east-1"
    account_id: Optional[str] = None
    account_name: str = ""
    profile_name: str = ""
    mfa_serial: Optional[str] = None
    role_arn: Optional[str] = None
    external_id: Optional[str] = None
    created_at: datetime = None
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Inicialização pós-criação"""
        if self.created_at is None:
            self.created_at = datetime.now()
    
    @property
    def is_expired(self) -> bool:
        """Verifica se as credenciais expiraram"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    @property
    def is_temporary(self) -> bool:
        """Verifica se são credenciais temporárias"""
        return self.session_token is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para serialização"""
        data = asdict(self)
        # Converte datetime para ISO string
        for field in ['created_at', 'last_used', 'expires_at']:
            if data[field] is not None:
                data[field] = data[field].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AWSCredentials':
        """Cria instância a partir de dicionário"""
        # Converte ISO string para datetime
        for field in ['created_at', 'last_used', 'expires_at']:
            if data.get(field):
                data[field] = datetime.fromisoformat(data[field])
        return cls(**data)


class AccountManager:
    """
    Gerenciador de contas AWS
    
    Responsável por gerenciar credenciais de múltiplas contas AWS de forma segura,
    incluindo criptografia, armazenamento e validação.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Inicializa o gerenciador de contas
        
        Args:
            config_path: Caminho para o arquivo de configuração
        """
        self.config = get_config()
        self.config_path = config_path or self.config.credentials_path
        self._accounts: Dict[str, AWSCredentials] = {}
        self._encryption_key: Optional[bytes] = None
        
        # Carrega contas existentes
        self._load_accounts()
    
    def _get_encryption_key(self) -> bytes:
        """
        Obtém ou gera a chave de criptografia
        
        Returns:
            Chave de criptografia
        """
        if self._encryption_key is None:
            # Tenta obter a chave do keyring
            key_str = keyring.get_password("aws-agent", self.config.encryption_key_name)
            
            if key_str is None:
                # Gera nova chave
                key = Fernet.generate_key()
                keyring.set_password("aws-agent", self.config.encryption_key_name, key.decode())
                self._encryption_key = key
            else:
                self._encryption_key = key_str.encode()
        
        return self._encryption_key
    
    def _encrypt_data(self, data: str) -> bytes:
        """
        Criptografa dados
        
        Args:
            data: Dados para criptografar
            
        Returns:
            Dados criptografados
        """
        key = self._get_encryption_key()
        f = Fernet(key)
        return f.encrypt(data.encode())
    
    def _decrypt_data(self, encrypted_data: bytes) -> str:
        """
        Descriptografa dados
        
        Args:
            encrypted_data: Dados criptografados
            
        Returns:
            Dados descriptografados
        """
        key = self._get_encryption_key()
        f = Fernet(key)
        return f.decrypt(encrypted_data).decode()
    
    def _load_accounts(self) -> None:
        """Carrega contas do arquivo criptografado"""
        if not self.config_path.exists():
            return
        
        try:
            with open(self.config_path, 'rb') as f:
                encrypted_data = f.read()
            
            if encrypted_data:
                decrypted_data = self._decrypt_data(encrypted_data)
                accounts_data = json.loads(decrypted_data)
                
                for account_name, account_data in accounts_data.items():
                    self._accounts[account_name] = AWSCredentials.from_dict(account_data)
        
        except Exception as e:
            print(f"Erro ao carregar contas: {e}")
    
    def _save_accounts(self) -> None:
        """Salva contas no arquivo criptografado"""
        try:
            # Prepara dados para serialização
            accounts_data = {}
            for account_name, credentials in self._accounts.items():
                accounts_data[account_name] = credentials.to_dict()
            
            # Criptografa e salva
            data_str = json.dumps(accounts_data, indent=2)
            encrypted_data = self._encrypt_data(data_str)
            
            # Garante que o diretório existe
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'wb') as f:
                f.write(encrypted_data)
        
        except Exception as e:
            print(f"Erro ao salvar contas: {e}")
            raise
    
    def add_account(self, account_name: str, credentials: AWSCredentials) -> bool:
        """
        Adiciona uma nova conta
        
        Args:
            account_name: Nome da conta
            credentials: Credenciais da conta
            
        Returns:
            True se adicionada com sucesso
        """
        try:
            # Valida credenciais
            if self.validate_credentials(credentials):
                # Obtém informações da conta
                account_info = self._get_account_info(credentials)
                if account_info:
                    credentials.account_id = account_info.get('account_id')
                    credentials.account_name = account_name
                
                self._accounts[account_name] = credentials
                self._save_accounts()
                return True
            else:
                print(f"Credenciais inválidas para a conta: {account_name}")
                return False
        
        except Exception as e:
            print(f"Erro ao adicionar conta {account_name}: {e}")
            return False
    
    def remove_account(self, account_name: str) -> bool:
        """
        Remove uma conta
        
        Args:
            account_name: Nome da conta a ser removida
            
        Returns:
            True se removida com sucesso
        """
        try:
            if account_name in self._accounts:
                del self._accounts[account_name]
                self._save_accounts()
                return True
            else:
                print(f"Conta não encontrada: {account_name}")
                return False
        
        except Exception as e:
            print(f"Erro ao remover conta {account_name}: {e}")
            return False
    
    def get_account(self, account_name: str) -> Optional[AWSCredentials]:
        """
        Obtém credenciais de uma conta
        
        Args:
            account_name: Nome da conta
            
        Returns:
            Credenciais da conta ou None se não encontrada
        """
        return self._accounts.get(account_name)
    
    def list_accounts(self) -> List[str]:
        """
        Lista todas as contas disponíveis
        
        Returns:
            Lista com nomes das contas
        """
        return list(self._accounts.keys())
    
    def get_account_info(self, account_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtém informações detalhadas de uma conta
        
        Args:
            account_name: Nome da conta
            
        Returns:
            Informações da conta ou None se não encontrada
        """
        credentials = self.get_account(account_name)
        if credentials is None:
            return None
        
        return {
            'account_name': account_name,
            'account_id': credentials.account_id,
            'region': credentials.region,
            'profile_name': credentials.profile_name,
            'is_temporary': credentials.is_temporary,
            'is_expired': credentials.is_expired,
            'created_at': credentials.created_at.isoformat() if credentials.created_at else None,
            'last_used': credentials.last_used.isoformat() if credentials.last_used else None,
            'expires_at': credentials.expires_at.isoformat() if credentials.expires_at else None,
            'has_mfa': credentials.mfa_serial is not None,
            'has_role': credentials.role_arn is not None,
        }
    
    def validate_credentials(self, credentials: AWSCredentials) -> bool:
        """
        Valida credenciais AWS
        
        Args:
            credentials: Credenciais para validar
            
        Returns:
            True se válidas
        """
        try:
            # Cria cliente STS para validar credenciais
            session = boto3.Session(
                aws_access_key_id=credentials.access_key_id,
                aws_secret_access_key=credentials.secret_access_key,
                aws_session_token=credentials.session_token,
                region_name=credentials.region
            )
            
            sts_client = session.client('sts')
            
            # Tenta obter identidade
            response = sts_client.get_caller_identity()
            
            # Atualiza informações da conta
            credentials.account_id = response.get('Account')
            
            return True
        
        except (ClientError, NoCredentialsError) as e:
            print(f"Erro de validação: {e}")
            return False
        except Exception as e:
            print(f"Erro inesperado na validação: {e}")
            return False
    
    def _get_account_info(self, credentials: AWSCredentials) -> Optional[Dict[str, Any]]:
        """
        Obtém informações da conta AWS
        
        Args:
            credentials: Credenciais da conta
            
        Returns:
            Informações da conta ou None em caso de erro
        """
        try:
            session = boto3.Session(
                aws_access_key_id=credentials.access_key_id,
                aws_secret_access_key=credentials.secret_access_key,
                aws_session_token=credentials.session_token,
                region_name=credentials.region
            )
            
            sts_client = session.client('sts')
            response = sts_client.get_caller_identity()
            
            return {
                'account_id': response.get('Account'),
                'user_id': response.get('UserId'),
                'arn': response.get('Arn'),
            }
        
        except Exception as e:
            print(f"Erro ao obter informações da conta: {e}")
            return None
    
    def update_last_used(self, account_name: str) -> None:
        """
        Atualiza timestamp de última utilização
        
        Args:
            account_name: Nome da conta
        """
        if account_name in self._accounts:
            self._accounts[account_name].last_used = datetime.now()
            self._save_accounts()
    
    def cleanup_expired_credentials(self) -> List[str]:
        """
        Remove credenciais expiradas
        
        Returns:
            Lista de contas removidas
        """
        expired_accounts = []
        
        for account_name, credentials in list(self._accounts.items()):
            if credentials.is_expired:
                expired_accounts.append(account_name)
                del self._accounts[account_name]
        
        if expired_accounts:
            self._save_accounts()
        
        return expired_accounts
    
    def backup_accounts(self, backup_path: Optional[Path] = None) -> bool:
        """
        Faz backup das contas
        
        Args:
            backup_path: Caminho para o backup
            
        Returns:
            True se backup criado com sucesso
        """
        try:
            if backup_path is None:
                backup_path = self.config.config_dir / "backups" / f"accounts_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.encrypted"
            
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copia arquivo de credenciais
            if self.config_path.exists():
                with open(self.config_path, 'rb') as src:
                    with open(backup_path, 'wb') as dst:
                        dst.write(src.read())
                return True
            
            return False
        
        except Exception as e:
            print(f"Erro ao fazer backup: {e}")
            return False
    
    def restore_accounts(self, backup_path: Path) -> bool:
        """
        Restaura contas a partir de backup
        
        Args:
            backup_path: Caminho do backup
            
        Returns:
            True se restaurado com sucesso
        """
        try:
            if backup_path.exists():
                # Faz backup do arquivo atual
                if self.config_path.exists():
                    self.backup_accounts()
                
                # Restaura backup
                with open(backup_path, 'rb') as src:
                    with open(self.config_path, 'wb') as dst:
                        dst.write(src.read())
                
                # Recarrega contas
                self._accounts.clear()
                self._load_accounts()
                
                return True
            
            return False
        
        except Exception as e:
            print(f"Erro ao restaurar backup: {e}")
            return False
