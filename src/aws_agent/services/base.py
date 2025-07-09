"""
Classe base para serviços AWS

Este módulo contém a classe base que todos os serviços AWS devem implementar,
fornecendo funcionalidades comuns como logging, validação e tratamento de erros.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
import boto3
from botocore.exceptions import ClientError, NoCredentialsError


class BaseAWSService(ABC):
    """
    Classe base para todos os serviços AWS
    
    Fornece funcionalidades comuns como logging, validação de sessão,
    tratamento de erros e métodos utilitários.
    """
    
    def __init__(self, session: boto3.Session, region: Optional[str] = None):
        """
        Inicializa o serviço AWS
        
        Args:
            session: Sessão boto3 autenticada
            region: Região AWS específica (opcional)
        """
        self.session = session
        self.region = region or session.region_name
        self.logger = logging.getLogger(f'aws_agent.{self.__class__.__name__}')
        
        # Clientes serão criados sob demanda
        self._clients: Dict[str, Any] = {}
        self._resources: Dict[str, Any] = {}
    
    @property
    @abstractmethod
    def service_name(self) -> str:
        """Nome do serviço AWS (ex: 'ec2', 's3', 'iam')"""
        pass
    
    def get_client(self, service: Optional[str] = None, region: Optional[str] = None) -> Any:
        """
        Obtém cliente AWS para o serviço
        
        Args:
            service: Nome do serviço (usa service_name se não especificado)
            region: Região específica (usa self.region se não especificado)
            
        Returns:
            Cliente AWS
        """
        service = service or self.service_name
        region = region or self.region
        
        cache_key = f"{service}_{region}"
        
        if cache_key not in self._clients:
            try:
                self._clients[cache_key] = self.session.client(service, region_name=region)
            except Exception as e:
                self.logger.error(f"Erro ao criar cliente {service}: {e}")
                raise
        
        return self._clients[cache_key]
    
    def get_resource(self, service: Optional[str] = None, region: Optional[str] = None) -> Any:
        """
        Obtém resource AWS para o serviço
        
        Args:
            service: Nome do serviço (usa service_name se não especificado)
            region: Região específica (usa self.region se não especificado)
            
        Returns:
            Resource AWS
        """
        service = service or self.service_name
        region = region or self.region
        
        cache_key = f"{service}_{region}"
        
        if cache_key not in self._resources:
            try:
                self._resources[cache_key] = self.session.resource(service, region_name=region)
            except Exception as e:
                self.logger.error(f"Erro ao criar resource {service}: {e}")
                raise
        
        return self._resources[cache_key]
    
    def handle_aws_error(self, error: ClientError, operation: str) -> None:
        """
        Trata erros AWS de forma padronizada
        
        Args:
            error: Erro do cliente AWS
            operation: Nome da operação que falhou
        """
        error_code = error.response.get('Error', {}).get('Code', 'Unknown')
        error_message = error.response.get('Error', {}).get('Message', str(error))
        
        self.logger.error(f"Erro AWS em {operation}: {error_code} - {error_message}")
        
        # Mapeamento de erros comuns
        error_mapping = {
            'AccessDenied': 'Acesso negado. Verifique as permissões.',
            'InvalidParameterValue': 'Parâmetro inválido fornecido.',
            'ResourceNotFound': 'Recurso não encontrado.',
            'ThrottlingException': 'Limite de taxa excedido. Tente novamente.',
            'UnauthorizedOperation': 'Operação não autorizada.',
            'ValidationError': 'Erro de validação nos parâmetros.',
        }
        
        user_message = error_mapping.get(error_code, f"Erro AWS: {error_message}")
        raise ValueError(user_message)
    
    def validate_session(self) -> bool:
        """
        Valida se a sessão está ativa e funcional
        
        Returns:
            True se sessão válida
        """
        try:
            sts_client = self.session.client('sts')
            sts_client.get_caller_identity()
            return True
        except (ClientError, NoCredentialsError) as e:
            self.logger.error(f"Sessão inválida: {e}")
            return False
    
    def paginate_results(self, operation: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Executa operação com paginação automática
        
        Args:
            operation: Nome da operação
            **kwargs: Parâmetros da operação
            
        Returns:
            Lista com todos os resultados paginados
        """
        client = self.get_client()
        
        try:
            paginator = client.get_paginator(operation)
            results = []
            
            for page in paginator.paginate(**kwargs):
                # Determina a chave de resultados baseada na operação
                result_key = self._get_result_key(operation)
                if result_key and result_key in page:
                    results.extend(page[result_key])
                else:
                    # Se não conseguir determinar a chave, adiciona a página inteira
                    results.append(page)
            
            return results
        
        except ClientError as e:
            self.handle_aws_error(e, operation)
            return []
        except Exception as e:
            self.logger.error(f"Erro na paginação de {operation}: {e}")
            raise
    
    def _get_result_key(self, operation: str) -> Optional[str]:
        """
        Determina a chave de resultados para uma operação
        
        Args:
            operation: Nome da operação
            
        Returns:
            Chave de resultados ou None se não encontrada
        """
        # Mapeamento comum de operações para chaves de resultado
        result_key_mapping = {
            'describe_instances': 'Reservations',
            'describe_volumes': 'Volumes',
            'describe_security_groups': 'SecurityGroups',
            'list_buckets': 'Buckets',
            'list_objects_v2': 'Contents',
            'list_users': 'Users',
            'list_roles': 'Roles',
            'list_policies': 'Policies',
            'describe_db_instances': 'DBInstances',
            'list_functions': 'Functions',
        }
        
        return result_key_mapping.get(operation)
    
    def get_account_id(self) -> Optional[str]:
        """
        Obtém ID da conta AWS atual
        
        Returns:
            ID da conta ou None se não conseguir obter
        """
        try:
            sts_client = self.session.client('sts')
            response = sts_client.get_caller_identity()
            return response.get('Account')
        except Exception as e:
            self.logger.error(f"Erro ao obter ID da conta: {e}")
            return None
    
    def get_current_region(self) -> str:
        """
        Obtém região atual
        
        Returns:
            Nome da região atual
        """
        return self.region
    
    def list_available_regions(self) -> List[str]:
        """
        Lista regiões disponíveis para o serviço
        
        Returns:
            Lista de regiões disponíveis
        """
        try:
            client = self.get_client()
            response = client.describe_regions()
            return [region['RegionName'] for region in response['Regions']]
        except Exception as e:
            self.logger.debug(f"Não foi possível listar regiões para {self.service_name}: {e}")
            # Retorna regiões padrão se não conseguir obter dinamicamente
            return [
                'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
                'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-central-1',
                'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1',
                'sa-east-1'
            ]
    
    def format_tags(self, tags: List[Dict[str, str]]) -> Dict[str, str]:
        """
        Formata tags AWS para dicionário
        
        Args:
            tags: Lista de tags no formato AWS
            
        Returns:
            Dicionário com tags formatadas
        """
        if not tags:
            return {}
        
        return {tag['Key']: tag['Value'] for tag in tags}
    
    def format_tags_for_aws(self, tags: Dict[str, str]) -> List[Dict[str, str]]:
        """
        Formata tags para formato AWS
        
        Args:
            tags: Dicionário com tags
            
        Returns:
            Lista de tags no formato AWS
        """
        if not tags:
            return []
        
        return [{'Key': key, 'Value': value} for key, value in tags.items()]
    
    def wait_for_state(self, waiter_name: str, **kwargs) -> bool:
        """
        Aguarda até que um recurso atinja um estado específico
        
        Args:
            waiter_name: Nome do waiter
            **kwargs: Parâmetros do waiter
            
        Returns:
            True se estado atingido com sucesso
        """
        try:
            client = self.get_client()
            waiter = client.get_waiter(waiter_name)
            waiter.wait(**kwargs)
            return True
        except Exception as e:
            self.logger.error(f"Erro ao aguardar estado {waiter_name}: {e}")
            return False
    
    @abstractmethod
    def list_resources(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Lista recursos do serviço
        
        Args:
            **kwargs: Parâmetros específicos do serviço
            
        Returns:
            Lista de recursos
        """
        pass
    
    @abstractmethod
    def get_resource_details(self, resource_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Obtém detalhes de um recurso específico
        
        Args:
            resource_id: ID do recurso
            **kwargs: Parâmetros específicos do serviço
            
        Returns:
            Detalhes do recurso ou None se não encontrado
        """
        pass
