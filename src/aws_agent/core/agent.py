"""
AWS Agent - Classe principal do agente

Este módulo contém a classe principal do agente AWS que coordena
todas as operações e serviços disponíveis.
"""

import logging
from typing import Dict, List, Optional, Any, Type
from datetime import datetime
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from .config import get_config
from .account_manager import AccountManager, AWSCredentials
from ..services.base import BaseAWSService
from ..services.ec2 import EC2Service
from ..services.s3 import S3Service
from ..services.iam import IAMService
from ..services.lambda_service import LambdaService


class AWSAgent:
    """
    Classe principal do AWS Agent
    
    Coordena todas as operações do agente, incluindo gerenciamento de contas,
    conexões AWS e execução de operações nos serviços.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa o AWS Agent
        
        Args:
            config_path: Caminho para arquivo de configuração personalizado
        """
        self.config = get_config()
        self.account_manager = AccountManager(config_path)
        self.current_account: Optional[str] = None
        self.current_session: Optional[boto3.Session] = None
        self.services: Dict[str, BaseAWSService] = {}
        self.logger = self._setup_logging()
        
        # Registra serviços disponíveis
        self._register_services()
    
    def _setup_logging(self) -> logging.Logger:
        """
        Configura sistema de logging
        
        Returns:
            Logger configurado
        """
        logger = logging.getLogger('aws_agent')
        logger.setLevel(getattr(logging, self.config.log_level))

        # Evita adicionar múltiplos handlers se o logger já foi configurado
        if not logger.handlers:
            # Garante que o diretório de logs existe
            self.config.log_path.parent.mkdir(parents=True, exist_ok=True)

            # Handler para arquivo
            file_handler = logging.FileHandler(self.config.log_path)
            file_handler.setLevel(logging.DEBUG)

            # Handler para console
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, self.config.log_level))

            # Formatação
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

            # Evita propagação duplicada para o root logger
            logger.propagate = False

        return logger
    
    def _register_services(self) -> None:
        """Registra serviços AWS disponíveis"""
        # Registra serviços apenas quando há uma sessão ativa
        if self.current_session:
            self.services['ec2'] = EC2Service(self.current_session, self.get_current_region())
            self.services['s3'] = S3Service(self.current_session, self.get_current_region())
            self.services['iam'] = IAMService(self.current_session, self.get_current_region())
            self.services['lambda'] = LambdaService(self.current_session, self.get_current_region())
    
    def get_current_region(self) -> str:
        """Obtém a região atual da sessão"""
        if self.current_session:
            return self.current_session.region_name
        return self.config.default_region
    
    def add_account(self, account_name: str, access_key_id: str, 
                   secret_access_key: str, region: str = "us-east-1",
                   session_token: Optional[str] = None,
                   profile_name: Optional[str] = None,
                   mfa_serial: Optional[str] = None,
                   role_arn: Optional[str] = None,
                   external_id: Optional[str] = None) -> bool:
        """
        Adiciona uma nova conta AWS
        
        Args:
            account_name: Nome amigável da conta
            access_key_id: AWS Access Key ID
            secret_access_key: AWS Secret Access Key
            region: Região AWS padrão
            session_token: Token de sessão (para MFA)
            profile_name: Nome do perfil AWS
            mfa_serial: Número serial do dispositivo MFA
            role_arn: ARN da role para assume
            external_id: ID externo para assume role
            
        Returns:
            True se conta adicionada com sucesso
        """
        try:
            credentials = AWSCredentials(
                access_key_id=access_key_id,
                secret_access_key=secret_access_key,
                session_token=session_token,
                region=region,
                account_name=account_name,
                profile_name=profile_name or account_name,
                mfa_serial=mfa_serial,
                role_arn=role_arn,
                external_id=external_id
            )
            
            success = self.account_manager.add_account(account_name, credentials)
            
            if success:
                self.logger.info(f"Conta '{account_name}' adicionada com sucesso")
            else:
                self.logger.error(f"Falha ao adicionar conta '{account_name}'")
            
            return success
        
        except Exception as e:
            self.logger.error(f"Erro ao adicionar conta '{account_name}': {e}")
            return False
    
    def remove_account(self, account_name: str) -> bool:
        """
        Remove uma conta AWS
        
        Args:
            account_name: Nome da conta a ser removida
            
        Returns:
            True se removida com sucesso
        """
        try:
            # Se a conta atual está sendo removida, desconecta
            if self.current_account == account_name:
                self.disconnect()
            
            success = self.account_manager.remove_account(account_name)
            
            if success:
                self.logger.info(f"Conta '{account_name}' removida com sucesso")
            else:
                self.logger.error(f"Falha ao remover conta '{account_name}'")
            
            return success
        
        except Exception as e:
            self.logger.error(f"Erro ao remover conta '{account_name}': {e}")
            return False
    
    def list_accounts(self) -> List[Dict[str, Any]]:
        """
        Lista todas as contas disponíveis
        
        Returns:
            Lista com informações das contas
        """
        try:
            accounts = []
            for account_name in self.account_manager.list_accounts():
                account_info = self.account_manager.get_account_info(account_name)
                if account_info:
                    account_info['is_current'] = (account_name == self.current_account)
                    accounts.append(account_info)
            
            return accounts
        
        except Exception as e:
            self.logger.error(f"Erro ao listar contas: {e}")
            return []
    
    def connect(self, account_name: str) -> bool:
        """
        Conecta a uma conta AWS específica
        
        Args:
            account_name: Nome da conta para conectar
            
        Returns:
            True se conectado com sucesso
        """
        try:
            credentials = self.account_manager.get_account(account_name)
            if credentials is None:
                self.logger.error(f"Conta '{account_name}' não encontrada")
                return False
            
            # Verifica se credenciais expiraram
            if credentials.is_expired:
                self.logger.error(f"Credenciais da conta '{account_name}' expiraram")
                return False
            
            # Cria sessão boto3
            self.current_session = boto3.Session(
                aws_access_key_id=credentials.access_key_id,
                aws_secret_access_key=credentials.secret_access_key,
                aws_session_token=credentials.session_token,
                region_name=credentials.region
            )
            
            # Valida conexão
            if self._validate_connection():
                self.current_account = account_name
                self.account_manager.update_last_used(account_name)
                
                # Registra serviços após conexão bem-sucedida
                self._register_services()
                
                self.logger.info(f"Conectado à conta '{account_name}' com sucesso")
                return True
            else:
                self.logger.error(f"Falha na validação da conexão com '{account_name}'")
                self.current_session = None
                return False
        
        except Exception as e:
            self.logger.error(f"Erro ao conectar à conta '{account_name}': {e}")
            self.current_session = None
            return False
    
    def disconnect(self) -> None:
        """Desconecta da conta atual"""
        if self.current_account:
            self.logger.info(f"Desconectando da conta '{self.current_account}'")
            self.current_account = None
            self.current_session = None
            self.services.clear()  # Limpa serviços registrados
    
    def _validate_connection(self) -> bool:
        """
        Valida a conexão atual
        
        Returns:
            True se conexão válida
        """
        try:
            if self.current_session is None:
                return False
            
            sts_client = self.current_session.client('sts')
            sts_client.get_caller_identity()
            return True
        
        except (ClientError, NoCredentialsError):
            return False
        except Exception as e:
            self.logger.error(f"Erro na validação da conexão: {e}")
            return False
    
    def get_current_account_info(self) -> Optional[Dict[str, Any]]:
        """
        Obtém informações da conta atual
        
        Returns:
            Informações da conta atual ou None se não conectado
        """
        if not self.current_account:
            return None
        
        try:
            sts_client = self.current_session.client('sts')
            response = sts_client.get_caller_identity()
            
            account_info = self.account_manager.get_account_info(self.current_account)
            if account_info:
                account_info.update({
                    'current_user_id': response.get('UserId'),
                    'current_arn': response.get('Arn'),
                    'session_valid': True
                })
            
            return account_info
        
        except Exception as e:
            self.logger.error(f"Erro ao obter informações da conta atual: {e}")
            return None
    
    def get_session(self) -> Optional[boto3.Session]:
        """
        Obtém a sessão boto3 atual
        
        Returns:
            Sessão boto3 ou None se não conectado
        """
        return self.current_session
    
    def get_client(self, service_name: str, region: Optional[str] = None) -> Optional[Any]:
        """
        Obtém cliente AWS para um serviço específico
        
        Args:
            service_name: Nome do serviço AWS
            region: Região específica (opcional)
            
        Returns:
            Cliente AWS ou None se não conectado
        """
        if self.current_session is None:
            self.logger.error("Nenhuma sessão ativa. Conecte-se a uma conta primeiro.")
            return None
        
        try:
            return self.current_session.client(service_name, region_name=region)
        except Exception as e:
            self.logger.error(f"Erro ao criar cliente para '{service_name}': {e}")
            return None
    
    def get_resource(self, service_name: str, region: Optional[str] = None) -> Optional[Any]:
        """
        Obtém resource AWS para um serviço específico
        
        Args:
            service_name: Nome do serviço AWS
            region: Região específica (opcional)
            
        Returns:
            Resource AWS ou None se não conectado
        """
        if self.current_session is None:
            self.logger.error("Nenhuma sessão ativa. Conecte-se a uma conta primeiro.")
            return None
        
        try:
            return self.current_session.resource(service_name, region_name=region)
        except Exception as e:
            self.logger.error(f"Erro ao criar resource para '{service_name}': {e}")
            return None
    
    def execute_operation(self, service_name: str, operation: str, **kwargs) -> Any:
        """
        Executa operação em um serviço AWS
        
        Args:
            service_name: Nome do serviço
            operation: Nome da operação
            **kwargs: Argumentos da operação
            
        Returns:
            Resultado da operação
        """
        if self.current_session is None:
            raise ValueError("Nenhuma sessão ativa. Conecte-se a uma conta primeiro.")
        
        if service_name not in self.services:
            raise ValueError(f"Serviço '{service_name}' não encontrado")
        
        service = self.services[service_name]
        
        if not hasattr(service, operation):
            raise ValueError(f"Operação '{operation}' não encontrada no serviço '{service_name}'")
        
        try:
            self.logger.info(f"Executando {service_name}.{operation}")
            result = getattr(service, operation)(**kwargs)
            self.logger.info(f"Operação {service_name}.{operation} concluída com sucesso")
            return result
        
        except Exception as e:
            self.logger.error(f"Erro ao executar {service_name}.{operation}: {e}")
            raise
    
    def get_available_services(self) -> List[str]:
        """
        Obtém lista de serviços disponíveis
        
        Returns:
            Lista de nomes dos serviços
        """
        return list(self.services.keys())
    
    def get_service_operations(self, service_name: str) -> List[str]:
        """
        Obtém operações disponíveis para um serviço
        
        Args:
            service_name: Nome do serviço
            
        Returns:
            Lista de operações disponíveis
        """
        if service_name not in self.services:
            return []
        
        service = self.services[service_name]
        return [method for method in dir(service) 
                if not method.startswith('_') and callable(getattr(service, method))]
    
    def cleanup_expired_credentials(self) -> List[str]:
        """
        Remove credenciais expiradas
        
        Returns:
            Lista de contas removidas
        """
        expired = self.account_manager.cleanup_expired_credentials()
        if expired:
            self.logger.info(f"Credenciais expiradas removidas: {expired}")
        return expired
    
    def backup_configuration(self, backup_path: Optional[str] = None) -> bool:
        """
        Faz backup da configuração
        
        Args:
            backup_path: Caminho para o backup
            
        Returns:
            True se backup criado com sucesso
        """
        try:
            from pathlib import Path
            path = Path(backup_path) if backup_path else None
            success = self.account_manager.backup_accounts(path)
            
            if success:
                self.logger.info("Backup da configuração criado com sucesso")
            else:
                self.logger.error("Falha ao criar backup da configuração")
            
            return success
        
        except Exception as e:
            self.logger.error(f"Erro ao criar backup: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Obtém status atual do agente
        
        Returns:
            Status do agente
        """
        return {
            'current_account': self.current_account,
            'connected': self.current_session is not None,
            'total_accounts': len(self.account_manager.list_accounts()),
            'available_services': len(self.services),
            'config_path': str(self.config.config_dir),
            'log_level': self.config.log_level,
            'version': self.config.version,
            'uptime': datetime.now().isoformat()
        }
