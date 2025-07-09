"""
Serviço S3 para gerenciamento de buckets e objetos
"""

import boto3
from botocore.exceptions import ClientError
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
from pathlib import Path

from .base import BaseAWSService


class S3Service(BaseAWSService):
    """
    Serviço para operações com Amazon S3
    """
    
    def __init__(self, session: boto3.Session, region: str = "us-east-1"):
        super().__init__(session, region)
        self.client = session.client('s3', region_name=region)
        self.resource = session.resource('s3', region_name=region)
    
    @property
    def service_name(self) -> str:
        """Nome do serviço AWS"""
        return 's3'
    
    def list_resources(self, resource_type: str = 'buckets', **kwargs) -> List[Dict[str, Any]]:
        """
        Lista recursos S3
        
        Args:
            resource_type: Tipo de recurso ('buckets', 'objects')
            **kwargs: Parâmetros específicos do recurso
            
        Returns:
            Lista de recursos
        """
        if resource_type == 'buckets':
            return self.list_buckets()
        elif resource_type == 'objects':
            bucket_name = kwargs.get('bucket_name')
            if not bucket_name:
                raise ValueError("bucket_name é obrigatório para listar objetos")
            return self.list_objects(bucket_name, **kwargs)
        else:
            raise ValueError(f"Tipo de recurso '{resource_type}' não suportado")
    
    def get_resource_details(self, resource_id: str, resource_type: str = 'bucket', **kwargs) -> Optional[Dict[str, Any]]:
        """
        Obtém detalhes de um recurso específico
        
        Args:
            resource_id: ID do recurso (nome do bucket ou chave do objeto)
            resource_type: Tipo de recurso ('bucket', 'object')
            **kwargs: Parâmetros específicos
            
        Returns:
            Detalhes do recurso ou None se não encontrado
        """
        if resource_type == 'bucket':
            return self.get_bucket_details(resource_id)
        elif resource_type == 'object':
            bucket_name = kwargs.get('bucket_name')
            if not bucket_name:
                raise ValueError("bucket_name é obrigatório para detalhes do objeto")
            return self.get_object_details(bucket_name, resource_id)
        else:
            raise ValueError(f"Tipo de recurso '{resource_type}' não suportado")
    
    def list_buckets(self) -> List[Dict[str, Any]]:
        """
        Lista todos os buckets S3
        
        Returns:
            Lista de buckets
        """
        try:
            response = self.client.list_buckets()
            buckets = []
            
            for bucket in response['Buckets']:
                bucket_info = {
                    'name': bucket['Name'],
                    'creation_date': bucket['CreationDate'],
                    'region': self._get_bucket_region(bucket['Name'])
                }
                buckets.append(bucket_info)
                
            return buckets
        except ClientError as e:
            self.logger.error(f"Erro ao listar buckets: {e}")
            return []
    
    def create_bucket(self, bucket_name: str, region: Optional[str] = None) -> bool:
        """
        Cria um novo bucket S3
        
        Args:
            bucket_name: Nome do bucket
            region: Região onde criar o bucket
            
        Returns:
            True se criado com sucesso
        """
        try:
            region = region or self.region
            
            if region == 'us-east-1':
                # us-east-1 é a região padrão, não precisa especificar
                self.client.create_bucket(Bucket=bucket_name)
            else:
                self.client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': region}
                )
            
            self.logger.info(f"Bucket '{bucket_name}' criado com sucesso")
            return True
            
        except ClientError as e:
            self.logger.error(f"Erro ao criar bucket '{bucket_name}': {e}")
            return False
    
    def delete_bucket(self, bucket_name: str, force: bool = False) -> bool:
        """
        Remove um bucket S3
        
        Args:
            bucket_name: Nome do bucket
            force: Se True, remove todos os objetos antes de deletar
            
        Returns:
            True se removido com sucesso
        """
        try:
            if force:
                # Remove todos os objetos primeiro
                self.empty_bucket(bucket_name)
            
            self.client.delete_bucket(Bucket=bucket_name)
            self.logger.info(f"Bucket '{bucket_name}' removido com sucesso")
            return True
            
        except ClientError as e:
            self.logger.error(f"Erro ao remover bucket '{bucket_name}': {e}")
            return False
    
    def empty_bucket(self, bucket_name: str) -> bool:
        """
        Remove todos os objetos de um bucket
        
        Args:
            bucket_name: Nome do bucket
            
        Returns:
            True se esvaziado com sucesso
        """
        try:
            bucket = self.resource.Bucket(bucket_name)
            bucket.objects.all().delete()
            
            # Remove versões se versionamento estiver habilitado
            bucket.object_versions.all().delete()
            
            self.logger.info(f"Bucket '{bucket_name}' esvaziado com sucesso")
            return True
            
        except ClientError as e:
            self.logger.error(f"Erro ao esvaziar bucket '{bucket_name}': {e}")
            return False
    
    def list_objects(self, bucket_name: str, prefix: str = "", 
                    max_keys: int = 1000) -> List[Dict[str, Any]]:
        """
        Lista objetos em um bucket
        
        Args:
            bucket_name: Nome do bucket
            prefix: Prefixo para filtrar objetos
            max_keys: Número máximo de objetos a retornar
            
        Returns:
            Lista de objetos
        """
        try:
            response = self.client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            objects = []
            for obj in response.get('Contents', []):
                object_info = {
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'etag': obj['ETag'],
                    'storage_class': obj.get('StorageClass', 'STANDARD')
                }
                objects.append(object_info)
                
            return objects
            
        except ClientError as e:
            self.logger.error(f"Erro ao listar objetos no bucket '{bucket_name}': {e}")
            return []
    
    def upload_file(self, file_path: str, bucket_name: str, 
                   object_key: Optional[str] = None) -> bool:
        """
        Faz upload de um arquivo para S3
        
        Args:
            file_path: Caminho do arquivo local
            bucket_name: Nome do bucket
            object_key: Chave do objeto (se None, usa o nome do arquivo)
            
        Returns:
            True se upload foi bem-sucedido
        """
        try:
            object_key = object_key or Path(file_path).name
            
            self.client.upload_file(file_path, bucket_name, object_key)
            self.logger.info(f"Arquivo '{file_path}' enviado para '{bucket_name}/{object_key}'")
            return True
            
        except ClientError as e:
            self.logger.error(f"Erro ao fazer upload do arquivo: {e}")
            return False
    
    def download_file(self, bucket_name: str, object_key: str, 
                     file_path: str) -> bool:
        """
        Faz download de um objeto do S3
        
        Args:
            bucket_name: Nome do bucket
            object_key: Chave do objeto
            file_path: Caminho local para salvar o arquivo
            
        Returns:
            True se download foi bem-sucedido
        """
        try:
            # Cria diretório se não existir
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            self.client.download_file(bucket_name, object_key, file_path)
            self.logger.info(f"Arquivo '{bucket_name}/{object_key}' baixado para '{file_path}'")
            return True
            
        except ClientError as e:
            self.logger.error(f"Erro ao fazer download do arquivo: {e}")
            return False
    
    def delete_object(self, bucket_name: str, object_key: str) -> bool:
        """
        Remove um objeto do S3
        
        Args:
            bucket_name: Nome do bucket
            object_key: Chave do objeto
            
        Returns:
            True se removido com sucesso
        """
        try:
            self.client.delete_object(Bucket=bucket_name, Key=object_key)
            self.logger.info(f"Objeto '{bucket_name}/{object_key}' removido")
            return True
            
        except ClientError as e:
            self.logger.error(f"Erro ao remover objeto: {e}")
            return False
    
    def get_object_info(self, bucket_name: str, object_key: str) -> Optional[Dict[str, Any]]:
        """
        Obtém informações detalhadas sobre um objeto
        
        Args:
            bucket_name: Nome do bucket
            object_key: Chave do objeto
            
        Returns:
            Informações do objeto ou None se não encontrado
        """
        try:
            response = self.client.head_object(Bucket=bucket_name, Key=object_key)
            
            return {
                'key': object_key,
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'etag': response['ETag'],
                'content_type': response.get('ContentType', 'unknown'),
                'metadata': response.get('Metadata', {}),
                'storage_class': response.get('StorageClass', 'STANDARD')
            }
            
        except ClientError as e:
            self.logger.error(f"Erro ao obter informações do objeto: {e}")
            return None
    
    def get_bucket_policy(self, bucket_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtém a política de um bucket
        
        Args:
            bucket_name: Nome do bucket
            
        Returns:
            Política do bucket ou None se não houver
        """
        try:
            response = self.client.get_bucket_policy(Bucket=bucket_name)
            import json
            return json.loads(response['Policy'])
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
                return None
            self.logger.error(f"Erro ao obter política do bucket: {e}")
            return None
    
    def set_bucket_policy(self, bucket_name: str, policy: Dict[str, Any]) -> bool:
        """
        Define a política de um bucket
        
        Args:
            bucket_name: Nome do bucket
            policy: Política a ser aplicada
            
        Returns:
            True se aplicada com sucesso
        """
        try:
            import json
            policy_json = json.dumps(policy)
            
            self.client.put_bucket_policy(
                Bucket=bucket_name,
                Policy=policy_json
            )
            
            self.logger.info(f"Política aplicada ao bucket '{bucket_name}'")
            return True
            
        except ClientError as e:
            self.logger.error(f"Erro ao definir política do bucket: {e}")
            return False
    
    def generate_presigned_url(self, bucket_name: str, object_key: str,
                              expiration: int = 3600, 
                              method: str = 'get_object') -> Optional[str]:
        """
        Gera URL pré-assinada para um objeto
        
        Args:
            bucket_name: Nome do bucket
            object_key: Chave do objeto
            expiration: Tempo de expiração em segundos
            method: Método HTTP ('get_object' ou 'put_object')
            
        Returns:
            URL pré-assinada ou None se erro
        """
        try:
            url = self.client.generate_presigned_url(
                method,
                Params={'Bucket': bucket_name, 'Key': object_key},
                ExpiresIn=expiration
            )
            
            return url
            
        except ClientError as e:
            self.logger.error(f"Erro ao gerar URL pré-assinada: {e}")
            return None
    
    def _get_bucket_region(self, bucket_name: str) -> str:
        """
        Obtém a região de um bucket
        
        Args:
            bucket_name: Nome do bucket
            
        Returns:
            Região do bucket
        """
        try:
            response = self.client.get_bucket_location(Bucket=bucket_name)
            region = response['LocationConstraint']
            return region or 'us-east-1'  # us-east-1 retorna None
            
        except ClientError:
            return 'unknown'
    
    def get_bucket_versioning(self, bucket_name: str) -> Dict[str, Any]:
        """
        Obtém status de versionamento do bucket
        
        Args:
            bucket_name: Nome do bucket
            
        Returns:
            Status de versionamento
        """
        try:
            response = self.client.get_bucket_versioning(Bucket=bucket_name)
            return {
                'status': response.get('Status', 'Disabled'),
                'mfa_delete': response.get('MfaDelete', 'Disabled')
            }
            
        except ClientError as e:
            self.logger.error(f"Erro ao obter versionamento do bucket: {e}")
            return {'status': 'Unknown', 'mfa_delete': 'Unknown'}
    
    def set_bucket_versioning(self, bucket_name: str, enabled: bool = True) -> bool:
        """
        Define o versionamento do bucket
        
        Args:
            bucket_name: Nome do bucket
            enabled: Se True, habilita versionamento
            
        Returns:
            True se configurado com sucesso
        """
        try:
            status = 'Enabled' if enabled else 'Suspended'
            
            self.client.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={'Status': status}
            )
            
            self.logger.info(f"Versionamento do bucket '{bucket_name}' definido como {status}")
            return True
            
        except ClientError as e:
            self.logger.error(f"Erro ao definir versionamento do bucket: {e}")
            return False
