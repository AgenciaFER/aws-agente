"""
Serviço IAM para gerenciamento de usuários, grupos, roles e políticas
"""

import boto3
from botocore.exceptions import ClientError
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from .base import BaseAWSService


class IAMService(BaseAWSService):
    """
    Serviço para operações com AWS IAM
    """
    
    def __init__(self, session: boto3.Session, region: str = "us-east-1"):
        super().__init__(session, region)
        self.client = session.client('iam', region_name=region)
        self.resource = session.resource('iam', region_name=region)
    
    @property
    def service_name(self) -> str:
        """Nome do serviço AWS"""
        return 'iam'
    
    def list_resources(self, resource_type: str = 'users', **kwargs) -> List[Dict[str, Any]]:
        """
        Lista recursos IAM
        
        Args:
            resource_type: Tipo de recurso ('users', 'groups', 'roles', 'policies')
            **kwargs: Parâmetros específicos do recurso
            
        Returns:
            Lista de recursos
        """
        if resource_type == 'users':
            return self.list_users(**kwargs)
        elif resource_type == 'groups':
            return self.list_groups(**kwargs)
        elif resource_type == 'roles':
            return self.list_roles(**kwargs)
        elif resource_type == 'policies':
            return self.list_policies(**kwargs)
        else:
            raise ValueError(f"Tipo de recurso '{resource_type}' não suportado")
    
    def get_resource_details(self, resource_id: str, resource_type: str = 'user', **kwargs) -> Optional[Dict[str, Any]]:
        """
        Obtém detalhes de um recurso específico
        
        Args:
            resource_id: ID do recurso (nome do usuário, grupo, role, etc.)
            resource_type: Tipo de recurso ('user', 'group', 'role', 'policy')
            **kwargs: Parâmetros específicos
            
        Returns:
            Detalhes do recurso ou None se não encontrado
        """
        if resource_type == 'user':
            return self.get_user_details(resource_id)
        elif resource_type == 'group':
            return self.get_group_details(resource_id)
        elif resource_type == 'role':
            return self.get_role_details(resource_id)
        elif resource_type == 'policy':
            return self.get_policy_details(resource_id)
        else:
            raise ValueError(f"Tipo de recurso '{resource_type}' não suportado")
    
    def list_users(self, path_prefix: str = "/") -> List[Dict[str, Any]]:
        """
        Lista usuários IAM
        
        Args:
            path_prefix: Prefixo do caminho para filtrar usuários
            
        Returns:
            Lista de usuários
        """
        try:
            response = self.client.list_users(PathPrefix=path_prefix)
            users = []
            
            for user in response['Users']:
                user_info = {
                    'username': user['UserName'],
                    'user_id': user['UserId'],
                    'arn': user['Arn'],
                    'path': user['Path'],
                    'create_date': user['CreateDate'],
                    'password_last_used': user.get('PasswordLastUsed')
                }
                users.append(user_info)
                
            return users
            
        except ClientError as e:
            self.logger.error(f"Erro ao listar usuários: {e}")
            return []
    
    def create_user(self, username: str, path: str = "/") -> bool:
        """
        Cria um novo usuário IAM
        
        Args:
            username: Nome do usuário
            path: Caminho do usuário
            
        Returns:
            True se criado com sucesso
        """
        try:
            self.client.create_user(UserName=username, Path=path)
            self.logger.info(f"Usuário '{username}' criado com sucesso")
            return True
            
        except ClientError as e:
            self.logger.error(f"Erro ao criar usuário '{username}': {e}")
            return False
    
    def delete_user(self, username: str, force: bool = False) -> bool:
        """
        Remove um usuário IAM
        
        Args:
            username: Nome do usuário
            force: Se True, remove políticas e grupos primeiro
            
        Returns:
            True se removido com sucesso
        """
        try:
            if force:
                # Remove políticas anexadas
                self._detach_user_policies(username)
                # Remove usuário de grupos
                self._remove_user_from_groups(username)
                # Remove chaves de acesso
                self._delete_user_access_keys(username)
                # Remove perfis de login
                self._delete_user_login_profile(username)
            
            self.client.delete_user(UserName=username)
            self.logger.info(f"Usuário '{username}' removido com sucesso")
            return True
            
        except ClientError as e:
            self.logger.error(f"Erro ao remover usuário '{username}': {e}")
            return False
    
    def list_groups(self, path_prefix: str = "/") -> List[Dict[str, Any]]:
        """
        Lista grupos IAM
        
        Args:
            path_prefix: Prefixo do caminho para filtrar grupos
            
        Returns:
            Lista de grupos
        """
        try:
            response = self.client.list_groups(PathPrefix=path_prefix)
            groups = []
            
            for group in response['Groups']:
                group_info = {
                    'group_name': group['GroupName'],
                    'group_id': group['GroupId'],
                    'arn': group['Arn'],
                    'path': group['Path'],
                    'create_date': group['CreateDate']
                }
                groups.append(group_info)
                
            return groups
            
        except ClientError as e:
            self.logger.error(f"Erro ao listar grupos: {e}")
            return []
    
    def create_group(self, group_name: str, path: str = "/") -> bool:
        """
        Cria um novo grupo IAM
        
        Args:
            group_name: Nome do grupo
            path: Caminho do grupo
            
        Returns:
            True se criado com sucesso
        """
        try:
            self.client.create_group(GroupName=group_name, Path=path)
            self.logger.info(f"Grupo '{group_name}' criado com sucesso")
            return True
            
        except ClientError as e:
            self.logger.error(f"Erro ao criar grupo '{group_name}': {e}")
            return False
    
    def delete_group(self, group_name: str, force: bool = False) -> bool:
        """
        Remove um grupo IAM
        
        Args:
            group_name: Nome do grupo
            force: Se True, remove políticas e usuários primeiro
            
        Returns:
            True se removido com sucesso
        """
        try:
            if force:
                # Remove políticas anexadas
                self._detach_group_policies(group_name)
                # Remove usuários do grupo
                self._remove_users_from_group(group_name)
            
            self.client.delete_group(GroupName=group_name)
            self.logger.info(f"Grupo '{group_name}' removido com sucesso")
            return True
            
        except ClientError as e:
            self.logger.error(f"Erro ao remover grupo '{group_name}': {e}")
            return False
    
    def list_roles(self, path_prefix: str = "/") -> List[Dict[str, Any]]:
        """
        Lista roles IAM
        
        Args:
            path_prefix: Prefixo do caminho para filtrar roles
            
        Returns:
            Lista de roles
        """
        try:
            response = self.client.list_roles(PathPrefix=path_prefix)
            roles = []
            
            for role in response['Roles']:
                role_info = {
                    'role_name': role['RoleName'],
                    'role_id': role['RoleId'],
                    'arn': role['Arn'],
                    'path': role['Path'],
                    'create_date': role['CreateDate'],
                    'assume_role_policy_document': role.get('AssumeRolePolicyDocument'),
                    'max_session_duration': role.get('MaxSessionDuration')
                }
                roles.append(role_info)
                
            return roles
            
        except ClientError as e:
            self.logger.error(f"Erro ao listar roles: {e}")
            return []
    
    def create_role(self, role_name: str, assume_role_policy: Dict[str, Any],
                   path: str = "/", description: str = "") -> bool:
        """
        Cria uma nova role IAM
        
        Args:
            role_name: Nome da role
            assume_role_policy: Documento de política de confiança
            path: Caminho da role
            description: Descrição da role
            
        Returns:
            True se criada com sucesso
        """
        try:
            params = {
                'RoleName': role_name,
                'AssumeRolePolicyDocument': json.dumps(assume_role_policy),
                'Path': path
            }
            
            if description:
                params['Description'] = description
            
            self.client.create_role(**params)
            self.logger.info(f"Role '{role_name}' criada com sucesso")
            return True
            
        except ClientError as e:
            self.logger.error(f"Erro ao criar role '{role_name}': {e}")
            return False
    
    def delete_role(self, role_name: str, force: bool = False) -> bool:
        """
        Remove uma role IAM
        
        Args:
            role_name: Nome da role
            force: Se True, remove políticas anexadas primeiro
            
        Returns:
            True se removida com sucesso
        """
        try:
            if force:
                # Remove políticas anexadas
                self._detach_role_policies(role_name)
                # Remove perfis de instância
                self._remove_role_from_instance_profiles(role_name)
            
            self.client.delete_role(RoleName=role_name)
            self.logger.info(f"Role '{role_name}' removida com sucesso")
            return True
            
        except ClientError as e:
            self.logger.error(f"Erro ao remover role '{role_name}': {e}")
            return False
    
    def list_policies(self, scope: str = "Local", only_attached: bool = False) -> List[Dict[str, Any]]:
        """
        Lista políticas IAM
        
        Args:
            scope: Escopo das políticas ("Local", "AWS", "All")
            only_attached: Se True, apenas políticas anexadas
            
        Returns:
            Lista de políticas
        """
        try:
            params = {'Scope': scope}
            if only_attached:
                params['OnlyAttached'] = True
            
            response = self.client.list_policies(**params)
            policies = []
            
            for policy in response['Policies']:
                policy_info = {
                    'policy_name': policy['PolicyName'],
                    'policy_id': policy['PolicyId'],
                    'arn': policy['Arn'],
                    'path': policy['Path'],
                    'create_date': policy['CreateDate'],
                    'update_date': policy['UpdateDate'],
                    'attachment_count': policy.get('AttachmentCount', 0),
                    'permissions_boundary_usage_count': policy.get('PermissionsBoundaryUsageCount', 0),
                    'is_attachable': policy.get('IsAttachable', False)
                }
                policies.append(policy_info)
                
            return policies
            
        except ClientError as e:
            self.logger.error(f"Erro ao listar políticas: {e}")
            return []
    
    def create_policy(self, policy_name: str, policy_document: Dict[str, Any],
                     path: str = "/", description: str = "") -> Optional[str]:
        """
        Cria uma nova política IAM
        
        Args:
            policy_name: Nome da política
            policy_document: Documento da política
            path: Caminho da política
            description: Descrição da política
            
        Returns:
            ARN da política criada ou None se erro
        """
        try:
            params = {
                'PolicyName': policy_name,
                'PolicyDocument': json.dumps(policy_document),
                'Path': path
            }
            
            if description:
                params['Description'] = description
            
            response = self.client.create_policy(**params)
            policy_arn = response['Policy']['Arn']
            
            self.logger.info(f"Política '{policy_name}' criada com sucesso")
            return policy_arn
            
        except ClientError as e:
            self.logger.error(f"Erro ao criar política '{policy_name}': {e}")
            return None
    
    def delete_policy(self, policy_arn: str) -> bool:
        """
        Remove uma política IAM
        
        Args:
            policy_arn: ARN da política
            
        Returns:
            True se removida com sucesso
        """
        try:
            self.client.delete_policy(PolicyArn=policy_arn)
            self.logger.info(f"Política '{policy_arn}' removida com sucesso")
            return True
            
        except ClientError as e:
            self.logger.error(f"Erro ao remover política '{policy_arn}': {e}")
            return False
    
    def attach_user_policy(self, username: str, policy_arn: str) -> bool:
        """
        Anexa uma política a um usuário
        
        Args:
            username: Nome do usuário
            policy_arn: ARN da política
            
        Returns:
            True se anexada com sucesso
        """
        try:
            self.client.attach_user_policy(
                UserName=username,
                PolicyArn=policy_arn
            )
            self.logger.info(f"Política '{policy_arn}' anexada ao usuário '{username}'")
            return True
            
        except ClientError as e:
            self.logger.error(f"Erro ao anexar política ao usuário: {e}")
            return False
    
    def detach_user_policy(self, username: str, policy_arn: str) -> bool:
        """
        Desanexa uma política de um usuário
        
        Args:
            username: Nome do usuário
            policy_arn: ARN da política
            
        Returns:
            True se desanexada com sucesso
        """
        try:
            self.client.detach_user_policy(
                UserName=username,
                PolicyArn=policy_arn
            )
            self.logger.info(f"Política '{policy_arn}' desanexada do usuário '{username}'")
            return True
            
        except ClientError as e:
            self.logger.error(f"Erro ao desanexar política do usuário: {e}")
            return False
    
    def create_access_key(self, username: str) -> Optional[Dict[str, str]]:
        """
        Cria uma chave de acesso para um usuário
        
        Args:
            username: Nome do usuário
            
        Returns:
            Dicionário com access_key_id e secret_access_key
        """
        try:
            response = self.client.create_access_key(UserName=username)
            access_key = response['AccessKey']
            
            self.logger.info(f"Chave de acesso criada para usuário '{username}'")
            return {
                'access_key_id': access_key['AccessKeyId'],
                'secret_access_key': access_key['SecretAccessKey']
            }
            
        except ClientError as e:
            self.logger.error(f"Erro ao criar chave de acesso: {e}")
            return None
    
    def delete_access_key(self, username: str, access_key_id: str) -> bool:
        """
        Remove uma chave de acesso
        
        Args:
            username: Nome do usuário
            access_key_id: ID da chave de acesso
            
        Returns:
            True se removida com sucesso
        """
        try:
            self.client.delete_access_key(
                UserName=username,
                AccessKeyId=access_key_id
            )
            self.logger.info(f"Chave de acesso '{access_key_id}' removida")
            return True
            
        except ClientError as e:
            self.logger.error(f"Erro ao remover chave de acesso: {e}")
            return False
    
    def get_user_policies(self, username: str) -> List[Dict[str, Any]]:
        """
        Obtém políticas anexadas a um usuário
        
        Args:
            username: Nome do usuário
            
        Returns:
            Lista de políticas
        """
        try:
            # Políticas gerenciadas
            managed_response = self.client.list_attached_user_policies(UserName=username)
            managed_policies = [
                {
                    'policy_name': policy['PolicyName'],
                    'policy_arn': policy['PolicyArn'],
                    'type': 'managed'
                }
                for policy in managed_response['AttachedPolicies']
            ]
            
            # Políticas inline
            inline_response = self.client.list_user_policies(UserName=username)
            inline_policies = [
                {
                    'policy_name': policy_name,
                    'policy_arn': None,
                    'type': 'inline'
                }
                for policy_name in inline_response['PolicyNames']
            ]
            
            return managed_policies + inline_policies
            
        except ClientError as e:
            self.logger.error(f"Erro ao obter políticas do usuário: {e}")
            return []
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """
        Obtém informações do usuário atual
        
        Returns:
            Informações do usuário atual
        """
        try:
            response = self.client.get_user()
            user = response['User']
            
            return {
                'username': user['UserName'],
                'user_id': user['UserId'],
                'arn': user['Arn'],
                'path': user['Path'],
                'create_date': user['CreateDate'],
                'password_last_used': user.get('PasswordLastUsed')
            }
            
        except ClientError as e:
            self.logger.error(f"Erro ao obter usuário atual: {e}")
            return None
    
    def get_account_summary(self) -> Dict[str, Any]:
        """
        Obtém resumo da conta
        
        Returns:
            Resumo da conta
        """
        try:
            response = self.client.get_account_summary()
            return response['SummaryMap']
            
        except ClientError as e:
            self.logger.error(f"Erro ao obter resumo da conta: {e}")
            return {}
    
    def _detach_user_policies(self, username: str) -> None:
        """Remove todas as políticas de um usuário"""
        try:
            # Remove políticas gerenciadas
            response = self.client.list_attached_user_policies(UserName=username)
            for policy in response['AttachedPolicies']:
                self.client.detach_user_policy(
                    UserName=username,
                    PolicyArn=policy['PolicyArn']
                )
            
            # Remove políticas inline
            response = self.client.list_user_policies(UserName=username)
            for policy_name in response['PolicyNames']:
                self.client.delete_user_policy(
                    UserName=username,
                    PolicyName=policy_name
                )
                
        except ClientError as e:
            self.logger.error(f"Erro ao remover políticas do usuário: {e}")
    
    def _remove_user_from_groups(self, username: str) -> None:
        """Remove usuário de todos os grupos"""
        try:
            response = self.client.get_groups_for_user(UserName=username)
            for group in response['Groups']:
                self.client.remove_user_from_group(
                    GroupName=group['GroupName'],
                    UserName=username
                )
        except ClientError as e:
            self.logger.error(f"Erro ao remover usuário dos grupos: {e}")
    
    def _delete_user_access_keys(self, username: str) -> None:
        """Remove todas as chaves de acesso do usuário"""
        try:
            response = self.client.list_access_keys(UserName=username)
            for key in response['AccessKeyMetadata']:
                self.client.delete_access_key(
                    UserName=username,
                    AccessKeyId=key['AccessKeyId']
                )
        except ClientError as e:
            self.logger.error(f"Erro ao remover chaves de acesso: {e}")
    
    def _delete_user_login_profile(self, username: str) -> None:
        """Remove perfil de login do usuário"""
        try:
            self.client.delete_login_profile(UserName=username)
        except ClientError as e:
            if e.response['Error']['Code'] != 'NoSuchEntity':
                self.logger.error(f"Erro ao remover perfil de login: {e}")
    
    def _detach_group_policies(self, group_name: str) -> None:
        """Remove todas as políticas de um grupo"""
        try:
            response = self.client.list_attached_group_policies(GroupName=group_name)
            for policy in response['AttachedPolicies']:
                self.client.detach_group_policy(
                    GroupName=group_name,
                    PolicyArn=policy['PolicyArn']
                )
        except ClientError as e:
            self.logger.error(f"Erro ao remover políticas do grupo: {e}")
    
    def _remove_users_from_group(self, group_name: str) -> None:
        """Remove todos os usuários de um grupo"""
        try:
            response = self.client.get_group(GroupName=group_name)
            for user in response['Users']:
                self.client.remove_user_from_group(
                    GroupName=group_name,
                    UserName=user['UserName']
                )
        except ClientError as e:
            self.logger.error(f"Erro ao remover usuários do grupo: {e}")
    
    def _detach_role_policies(self, role_name: str) -> None:
        """Remove todas as políticas de uma role"""
        try:
            response = self.client.list_attached_role_policies(RoleName=role_name)
            for policy in response['AttachedPolicies']:
                self.client.detach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy['PolicyArn']
                )
        except ClientError as e:
            self.logger.error(f"Erro ao remover políticas da role: {e}")
    
    def _remove_role_from_instance_profiles(self, role_name: str) -> None:
        """Remove role de todos os perfis de instância"""
        try:
            response = self.client.list_instance_profiles_for_role(RoleName=role_name)
            for profile in response['InstanceProfiles']:
                self.client.remove_role_from_instance_profile(
                    InstanceProfileName=profile['InstanceProfileName'],
                    RoleName=role_name
                )
        except ClientError as e:
            self.logger.error(f"Erro ao remover role dos perfis de instância: {e}")
