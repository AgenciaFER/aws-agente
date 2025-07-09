"""
Serviço Lambda para gerenciamento de funções serverless
"""

import boto3
from botocore.exceptions import ClientError
from typing import Dict, List, Optional, Any
import json
import base64
import zipfile
import io
from pathlib import Path

from .base import BaseAWSService


class LambdaService(BaseAWSService):
    """
    Serviço para operações com AWS Lambda
    """
    
    def __init__(self, session: boto3.Session, region: str = "us-east-1"):
        super().__init__(session, region)
        self.client = session.client('lambda', region_name=region)
    
    @property
    def service_name(self) -> str:
        """Nome do serviço AWS"""
        return 'lambda'
    
    def list_resources(self, resource_type: str = 'functions', **kwargs) -> List[Dict[str, Any]]:
        """
        Lista recursos Lambda
        
        Args:
            resource_type: Tipo de recurso ('functions', 'layers', 'event_source_mappings')
            **kwargs: Parâmetros específicos do recurso
            
        Returns:
            Lista de recursos
        """
        if resource_type == 'functions':
            return self.list_functions(**kwargs)
        elif resource_type == 'layers':
            return self.list_layers(**kwargs)
        elif resource_type == 'event_source_mappings':
            function_name = kwargs.get('function_name')
            if not function_name:
                raise ValueError("function_name é obrigatório para listar event source mappings")
            return self.list_event_source_mappings(function_name)
        else:
            raise ValueError(f"Tipo de recurso '{resource_type}' não suportado")
    
    def get_resource_details(self, resource_id: str, resource_type: str = 'function', **kwargs) -> Optional[Dict[str, Any]]:
        """
        Obtém detalhes de um recurso específico
        
        Args:
            resource_id: ID do recurso (nome da função, ARN da layer, etc.)
            resource_type: Tipo de recurso ('function', 'layer', 'event_source_mapping')
            **kwargs: Parâmetros específicos
            
        Returns:
            Detalhes do recurso ou None se não encontrado
        """
        if resource_type == 'function':
            return self.get_function_details(resource_id)
        elif resource_type == 'layer':
            return self.get_layer_details(resource_id)
        elif resource_type == 'event_source_mapping':
            return self.get_event_source_mapping_details(resource_id)
        else:
            raise ValueError(f"Tipo de recurso '{resource_type}' não suportado")
    
    def list_functions(self) -> List[Dict[str, Any]]:
        """
        Lista todas as funções Lambda
        
        Returns:
            Lista de funções
        """
        try:
            response = self.client.list_functions()
            functions = []
            
            for func in response['Functions']:
                function_info = {
                    'function_name': func['FunctionName'],
                    'function_arn': func['FunctionArn'],
                    'runtime': func['Runtime'],
                    'role': func['Role'],
                    'handler': func['Handler'],
                    'code_size': func['CodeSize'],
                    'description': func.get('Description', ''),
                    'timeout': func['Timeout'],
                    'memory_size': func['MemorySize'],
                    'last_modified': func['LastModified'],
                    'code_sha256': func['CodeSha256'],
                    'version': func['Version'],
                    'environment': func.get('Environment', {}).get('Variables', {}),
                    'layers': func.get('Layers', [])
                }
                functions.append(function_info)
                
            return functions
            
        except ClientError as e:
            self.logger.error(f"Erro ao listar funções: {e}")
            return []
    
    def create_function(self, function_name: str, runtime: str, role: str,
                       handler: str, code: Dict[str, Any], 
                       description: str = "", timeout: int = 3,
                       memory_size: int = 128, environment: Optional[Dict[str, str]] = None,
                       layers: Optional[List[str]] = None) -> Optional[str]:
        """
        Cria uma nova função Lambda
        
        Args:
            function_name: Nome da função
            runtime: Runtime (python3.9, nodejs18.x, etc.)
            role: ARN da role IAM
            handler: Handler da função
            code: Código da função (ZipFile ou S3)
            description: Descrição da função
            timeout: Timeout em segundos
            memory_size: Memória em MB
            environment: Variáveis de ambiente
            layers: Lista de ARNs de layers
            
        Returns:
            ARN da função criada ou None se erro
        """
        try:
            params = {
                'FunctionName': function_name,
                'Runtime': runtime,
                'Role': role,
                'Handler': handler,
                'Code': code,
                'Description': description,
                'Timeout': timeout,
                'MemorySize': memory_size,
                'Publish': True
            }
            
            if environment:
                params['Environment'] = {'Variables': environment}
                
            if layers:
                params['Layers'] = layers
            
            response = self.client.create_function(**params)
            function_arn = response['FunctionArn']
            
            self.logger.info(f"Função '{function_name}' criada com sucesso")
            return function_arn
            
        except ClientError as e:
            self.logger.error(f"Erro ao criar função '{function_name}': {e}")
            return None
    
    def delete_function(self, function_name: str) -> bool:
        """
        Remove uma função Lambda
        
        Args:
            function_name: Nome da função
            
        Returns:
            True se removida com sucesso
        """
        try:
            self.client.delete_function(FunctionName=function_name)
            self.logger.info(f"Função '{function_name}' removida com sucesso")
            return True
            
        except ClientError as e:
            self.logger.error(f"Erro ao remover função '{function_name}': {e}")
            return False
    
    def invoke_function(self, function_name: str, payload: Dict[str, Any] = None,
                       invocation_type: str = "RequestResponse") -> Optional[Dict[str, Any]]:
        """
        Invoca uma função Lambda
        
        Args:
            function_name: Nome da função
            payload: Dados para enviar à função
            invocation_type: Tipo de invocação (RequestResponse, Event, DryRun)
            
        Returns:
            Resposta da função ou None se erro
        """
        try:
            params = {
                'FunctionName': function_name,
                'InvocationType': invocation_type
            }
            
            if payload:
                params['Payload'] = json.dumps(payload)
            
            response = self.client.invoke(**params)
            
            result = {
                'status_code': response['StatusCode'],
                'executed_version': response.get('ExecutedVersion'),
                'log_result': response.get('LogResult'),
                'payload': None
            }
            
            if 'Payload' in response:
                payload_data = response['Payload'].read()
                if payload_data:
                    result['payload'] = json.loads(payload_data)
            
            return result
            
        except ClientError as e:
            self.logger.error(f"Erro ao invocar função '{function_name}': {e}")
            return None
    
    def update_function_code(self, function_name: str, code: Dict[str, Any]) -> bool:
        """
        Atualiza o código de uma função
        
        Args:
            function_name: Nome da função
            code: Novo código (ZipFile ou S3)
            
        Returns:
            True se atualizado com sucesso
        """
        try:
            params = {
                'FunctionName': function_name,
                **code
            }
            
            self.client.update_function_code(**params)
            self.logger.info(f"Código da função '{function_name}' atualizado")
            return True
            
        except ClientError as e:
            self.logger.error(f"Erro ao atualizar código da função: {e}")
            return False
    
    def update_function_configuration(self, function_name: str, **kwargs) -> bool:
        """
        Atualiza configuração de uma função
        
        Args:
            function_name: Nome da função
            **kwargs: Parâmetros de configuração
            
        Returns:
            True se atualizado com sucesso
        """
        try:
            params = {'FunctionName': function_name}
            params.update(kwargs)
            
            self.client.update_function_configuration(**params)
            self.logger.info(f"Configuração da função '{function_name}' atualizada")
            return True
            
        except ClientError as e:
            self.logger.error(f"Erro ao atualizar configuração da função: {e}")
            return False
    
    def get_function(self, function_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtém informações detalhadas de uma função
        
        Args:
            function_name: Nome da função
            
        Returns:
            Informações da função ou None se erro
        """
        try:
            response = self.client.get_function(FunctionName=function_name)
            
            function_info = {
                'configuration': response['Configuration'],
                'code': response['Code'],
                'tags': response.get('Tags', {})
            }
            
            return function_info
            
        except ClientError as e:
            self.logger.error(f"Erro ao obter função '{function_name}': {e}")
            return None
    
    def list_versions(self, function_name: str) -> List[Dict[str, Any]]:
        """
        Lista versões de uma função
        
        Args:
            function_name: Nome da função
            
        Returns:
            Lista de versões
        """
        try:
            response = self.client.list_versions_by_function(FunctionName=function_name)
            versions = []
            
            for version in response['Versions']:
                version_info = {
                    'version': version['Version'],
                    'function_arn': version['FunctionArn'],
                    'code_sha256': version['CodeSha256'],
                    'last_modified': version['LastModified'],
                    'description': version.get('Description', '')
                }
                versions.append(version_info)
                
            return versions
            
        except ClientError as e:
            self.logger.error(f"Erro ao listar versões da função: {e}")
            return []
    
    def publish_version(self, function_name: str, description: str = "") -> Optional[str]:
        """
        Publica uma nova versão da função
        
        Args:
            function_name: Nome da função
            description: Descrição da versão
            
        Returns:
            Número da versão ou None se erro
        """
        try:
            params = {'FunctionName': function_name}
            if description:
                params['Description'] = description
            
            response = self.client.publish_version(**params)
            version = response['Version']
            
            self.logger.info(f"Versão '{version}' da função '{function_name}' publicada")
            return version
            
        except ClientError as e:
            self.logger.error(f"Erro ao publicar versão da função: {e}")
            return None
    
    def list_aliases(self, function_name: str) -> List[Dict[str, Any]]:
        """
        Lista aliases de uma função
        
        Args:
            function_name: Nome da função
            
        Returns:
            Lista de aliases
        """
        try:
            response = self.client.list_aliases(FunctionName=function_name)
            aliases = []
            
            for alias in response['Aliases']:
                alias_info = {
                    'name': alias['Name'],
                    'function_version': alias['FunctionVersion'],
                    'description': alias.get('Description', ''),
                    'routing_config': alias.get('RoutingConfig', {}),
                    'revision_id': alias.get('RevisionId')
                }
                aliases.append(alias_info)
                
            return aliases
            
        except ClientError as e:
            self.logger.error(f"Erro ao listar aliases da função: {e}")
            return []
    
    def create_alias(self, function_name: str, name: str, function_version: str,
                    description: str = "") -> bool:
        """
        Cria um alias para uma função
        
        Args:
            function_name: Nome da função
            name: Nome do alias
            function_version: Versão da função
            description: Descrição do alias
            
        Returns:
            True se criado com sucesso
        """
        try:
            params = {
                'FunctionName': function_name,
                'Name': name,
                'FunctionVersion': function_version
            }
            
            if description:
                params['Description'] = description
            
            self.client.create_alias(**params)
            self.logger.info(f"Alias '{name}' criado para função '{function_name}'")
            return True
            
        except ClientError as e:
            self.logger.error(f"Erro ao criar alias: {e}")
            return False
    
    def delete_alias(self, function_name: str, name: str) -> bool:
        """
        Remove um alias
        
        Args:
            function_name: Nome da função
            name: Nome do alias
            
        Returns:
            True se removido com sucesso
        """
        try:
            self.client.delete_alias(FunctionName=function_name, Name=name)
            self.logger.info(f"Alias '{name}' removido da função '{function_name}'")
            return True
            
        except ClientError as e:
            self.logger.error(f"Erro ao remover alias: {e}")
            return False
    
    def list_event_source_mappings(self, function_name: str = None) -> List[Dict[str, Any]]:
        """
        Lista mapeamentos de origem de eventos
        
        Args:
            function_name: Nome da função (opcional)
            
        Returns:
            Lista de mapeamentos
        """
        try:
            params = {}
            if function_name:
                params['FunctionName'] = function_name
            
            response = self.client.list_event_source_mappings(**params)
            mappings = []
            
            for mapping in response['EventSourceMappings']:
                mapping_info = {
                    'uuid': mapping['UUID'],
                    'event_source_arn': mapping.get('EventSourceArn'),
                    'function_name': mapping['FunctionName'],
                    'last_modified': mapping['LastModified'],
                    'last_processing_result': mapping.get('LastProcessingResult'),
                    'state': mapping['State'],
                    'state_transition_reason': mapping.get('StateTransitionReason')
                }
                mappings.append(mapping_info)
                
            return mappings
            
        except ClientError as e:
            self.logger.error(f"Erro ao listar mapeamentos de eventos: {e}")
            return []
    
    def create_event_source_mapping(self, event_source_arn: str, function_name: str,
                                   starting_position: str = "LATEST",
                                   batch_size: int = 100) -> Optional[str]:
        """
        Cria um mapeamento de origem de eventos
        
        Args:
            event_source_arn: ARN da origem do evento
            function_name: Nome da função
            starting_position: Posição inicial (LATEST, TRIM_HORIZON)
            batch_size: Tamanho do lote
            
        Returns:
            UUID do mapeamento ou None se erro
        """
        try:
            response = self.client.create_event_source_mapping(
                EventSourceArn=event_source_arn,
                FunctionName=function_name,
                StartingPosition=starting_position,
                BatchSize=batch_size
            )
            
            uuid = response['UUID']
            self.logger.info(f"Mapeamento de eventos criado: {uuid}")
            return uuid
            
        except ClientError as e:
            self.logger.error(f"Erro ao criar mapeamento de eventos: {e}")
            return None
    
    def delete_event_source_mapping(self, uuid: str) -> bool:
        """
        Remove um mapeamento de origem de eventos
        
        Args:
            uuid: UUID do mapeamento
            
        Returns:
            True se removido com sucesso
        """
        try:
            self.client.delete_event_source_mapping(UUID=uuid)
            self.logger.info(f"Mapeamento de eventos removido: {uuid}")
            return True
            
        except ClientError as e:
            self.logger.error(f"Erro ao remover mapeamento de eventos: {e}")
            return False
    
    def get_function_logs(self, function_name: str, start_time: str = None,
                         end_time: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtém logs de uma função (através do CloudWatch Logs)
        
        Args:
            function_name: Nome da função
            start_time: Tempo de início (ISO format)
            end_time: Tempo de fim (ISO format)
            limit: Limite de eventos
            
        Returns:
            Lista de eventos de log
        """
        try:
            # Usar CloudWatch Logs para obter logs da função
            logs_client = self.session.client('logs', region_name=self.region)
            log_group_name = f"/aws/lambda/{function_name}"
            
            # Listar streams de log
            streams_response = logs_client.describe_log_streams(
                logGroupName=log_group_name,
                orderBy='LastEventTime',
                descending=True,
                limit=10
            )
            
            events = []
            for stream in streams_response['logStreams']:
                stream_name = stream['logStreamName']
                
                params = {
                    'logGroupName': log_group_name,
                    'logStreamName': stream_name,
                    'limit': limit
                }
                
                if start_time:
                    from datetime import datetime
                    start_timestamp = int(datetime.fromisoformat(start_time).timestamp() * 1000)
                    params['startTime'] = start_timestamp
                
                if end_time:
                    end_timestamp = int(datetime.fromisoformat(end_time).timestamp() * 1000)
                    params['endTime'] = end_timestamp
                
                events_response = logs_client.get_log_events(**params)
                
                for event in events_response['events']:
                    events.append({
                        'timestamp': event['timestamp'],
                        'message': event['message'],
                        'log_stream': stream_name
                    })
                    
                if len(events) >= limit:
                    break
            
            return events[:limit]
            
        except ClientError as e:
            self.logger.error(f"Erro ao obter logs da função: {e}")
            return []
    
    def create_zip_from_code(self, code_string: str, handler_file: str = "lambda_function.py") -> bytes:
        """
        Cria um arquivo ZIP a partir de código Python
        
        Args:
            code_string: Código Python como string
            handler_file: Nome do arquivo principal
            
        Returns:
            Bytes do arquivo ZIP
        """
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(handler_file, code_string)
        
        zip_buffer.seek(0)
        return zip_buffer.read()
    
    def create_zip_from_directory(self, directory_path: str) -> bytes:
        """
        Cria um arquivo ZIP a partir de um diretório
        
        Args:
            directory_path: Caminho do diretório
            
        Returns:
            Bytes do arquivo ZIP
        """
        zip_buffer = io.BytesIO()
        directory = Path(directory_path)
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(directory)
                    zip_file.write(file_path, arcname)
        
        zip_buffer.seek(0)
        return zip_buffer.read()
    
    def add_permission(self, function_name: str, statement_id: str, 
                      action: str, principal: str, source_arn: str = None) -> bool:
        """
        Adiciona permissão para invocar a função
        
        Args:
            function_name: Nome da função
            statement_id: ID único da declaração
            action: Ação a permitir (lambda:InvokeFunction)
            principal: Principal (serviço ou conta)
            source_arn: ARN da origem (opcional)
            
        Returns:
            True se adicionada com sucesso
        """
        try:
            params = {
                'FunctionName': function_name,
                'StatementId': statement_id,
                'Action': action,
                'Principal': principal
            }
            
            if source_arn:
                params['SourceArn'] = source_arn
            
            self.client.add_permission(**params)
            self.logger.info(f"Permissão adicionada à função '{function_name}'")
            return True
            
        except ClientError as e:
            self.logger.error(f"Erro ao adicionar permissão: {e}")
            return False
    
    def remove_permission(self, function_name: str, statement_id: str) -> bool:
        """
        Remove permissão de uma função
        
        Args:
            function_name: Nome da função
            statement_id: ID da declaração
            
        Returns:
            True se removida com sucesso
        """
        try:
            self.client.remove_permission(
                FunctionName=function_name,
                StatementId=statement_id
            )
            self.logger.info(f"Permissão removida da função '{function_name}'")
            return True
            
        except ClientError as e:
            self.logger.error(f"Erro ao remover permissão: {e}")
            return False
