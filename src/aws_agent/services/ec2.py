"""
Serviço EC2 para o AWS Agent

Este módulo implementa todas as operações relacionadas ao Amazon EC2,
incluindo gerenciamento de instâncias, volumes, security groups e VPCs.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

from .base import BaseAWSService
from ..utils.helpers import format_datetime, format_size, safe_get


class EC2Service(BaseAWSService):
    """
    Serviço para gerenciar recursos Amazon EC2
    
    Fornece operações para instâncias, volumes, security groups,
    key pairs e outros recursos EC2.
    """
    
    @property
    def service_name(self) -> str:
        """Nome do serviço AWS"""
        return 'ec2'
    
    def list_resources(self, resource_type: str = 'instances', **kwargs) -> List[Dict[str, Any]]:
        """
        Lista recursos EC2
        
        Args:
            resource_type: Tipo de recurso ('instances', 'volumes', 'security_groups', etc.)
            **kwargs: Parâmetros específicos do recurso
            
        Returns:
            Lista de recursos
        """
        if resource_type == 'instances':
            return self.list_instances(**kwargs)
        elif resource_type == 'volumes':
            return self.list_volumes(**kwargs)
        elif resource_type == 'security_groups':
            return self.list_security_groups(**kwargs)
        elif resource_type == 'key_pairs':
            return self.list_key_pairs(**kwargs)
        elif resource_type == 'vpcs':
            return self.list_vpcs(**kwargs)
        else:
            raise ValueError(f"Tipo de recurso '{resource_type}' não suportado")
    
    def get_resource_details(self, resource_id: str, resource_type: str = 'instance', **kwargs) -> Optional[Dict[str, Any]]:
        """
        Obtém detalhes de um recurso específico
        
        Args:
            resource_id: ID do recurso
            resource_type: Tipo de recurso
            **kwargs: Parâmetros específicos
            
        Returns:
            Detalhes do recurso ou None se não encontrado
        """
        if resource_type == 'instance':
            return self.get_instance_details(resource_id)
        elif resource_type == 'volume':
            return self.get_volume_details(resource_id)
        elif resource_type == 'security_group':
            return self.get_security_group_details(resource_id)
        else:
            raise ValueError(f"Tipo de recurso '{resource_type}' não suportado")
    
    def list_instances(self, state: Optional[str] = None, instance_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Lista instâncias EC2
        
        Args:
            state: Filtrar por estado (running, stopped, terminated, etc.)
            instance_ids: Lista de IDs específicos
            
        Returns:
            Lista de instâncias formatadas
        """
        try:
            client = self.get_client()
            
            # Prepara filtros
            filters = []
            if state:
                filters.append({'Name': 'instance-state-name', 'Values': [state]})
            
            # Prepara parâmetros
            params = {}
            if filters:
                params['Filters'] = filters
            if instance_ids:
                params['InstanceIds'] = instance_ids
            
            # Executa consulta
            response = client.describe_instances(**params)
            
            instances = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instances.append(self._format_instance(instance))
            
            return instances
        
        except ClientError as e:
            self.handle_aws_error(e, 'list_instances')
            return []
    
    def get_instance_details(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém detalhes de uma instância específica
        
        Args:
            instance_id: ID da instância
            
        Returns:
            Detalhes da instância ou None se não encontrada
        """
        try:
            instances = self.list_instances(instance_ids=[instance_id])
            return instances[0] if instances else None
        
        except Exception as e:
            self.logger.error(f"Erro ao obter detalhes da instância {instance_id}: {e}")
            return None
    
    def start_instance(self, instance_id: str) -> bool:
        """
        Inicia uma instância EC2
        
        Args:
            instance_id: ID da instância
            
        Returns:
            True se operação bem-sucedida
        """
        try:
            client = self.get_client()
            
            response = client.start_instances(InstanceIds=[instance_id])
            
            if response['StartingInstances']:
                self.logger.info(f"Instância {instance_id} sendo iniciada")
                return True
            
            return False
        
        except ClientError as e:
            self.handle_aws_error(e, f'start_instance_{instance_id}')
            return False
    
    def stop_instance(self, instance_id: str, force: bool = False) -> bool:
        """
        Para uma instância EC2
        
        Args:
            instance_id: ID da instância
            force: Forçar parada
            
        Returns:
            True se operação bem-sucedida
        """
        try:
            client = self.get_client()
            
            params = {'InstanceIds': [instance_id]}
            if force:
                params['Force'] = True
            
            response = client.stop_instances(**params)
            
            if response['StoppingInstances']:
                self.logger.info(f"Instância {instance_id} sendo parada")
                return True
            
            return False
        
        except ClientError as e:
            self.handle_aws_error(e, f'stop_instance_{instance_id}')
            return False
    
    def reboot_instance(self, instance_id: str) -> bool:
        """
        Reinicia uma instância EC2
        
        Args:
            instance_id: ID da instância
            
        Returns:
            True se operação bem-sucedida
        """
        try:
            client = self.get_client()
            
            client.reboot_instances(InstanceIds=[instance_id])
            self.logger.info(f"Instância {instance_id} sendo reiniciada")
            return True
        
        except ClientError as e:
            self.handle_aws_error(e, f'reboot_instance_{instance_id}')
            return False
    
    def terminate_instance(self, instance_id: str) -> bool:
        """
        Termina uma instância EC2
        
        Args:
            instance_id: ID da instância
            
        Returns:
            True se operação bem-sucedida
        """
        try:
            client = self.get_client()
            
            response = client.terminate_instances(InstanceIds=[instance_id])
            
            if response['TerminatingInstances']:
                self.logger.info(f"Instância {instance_id} sendo terminada")
                return True
            
            return False
        
        except ClientError as e:
            self.handle_aws_error(e, f'terminate_instance_{instance_id}')
            return False
    
    def get_instance_console_output(self, instance_id: str, latest: bool = True) -> Optional[str]:
        """
        Obtém output do console da instância
        
        Args:
            instance_id: ID da instância
            latest: Obter apenas as últimas linhas
            
        Returns:
            Output do console ou None se não disponível
        """
        try:
            client = self.get_client()
            
            params = {'InstanceId': instance_id}
            if latest:
                params['Latest'] = True
            
            response = client.get_console_output(**params)
            return response.get('Output', '')
        
        except ClientError as e:
            self.handle_aws_error(e, f'get_console_output_{instance_id}')
            return None
    
    def connect_to_instance(self, instance_id: str, connection_type: str = 'ssh') -> Dict[str, Any]:
        """
        Prepara conexão para uma instância
        
        Args:
            instance_id: ID da instância
            connection_type: Tipo de conexão ('ssh', 'rdp', 'session_manager')
            
        Returns:
            Informações de conexão
        """
        try:
            instance = self.get_instance_details(instance_id)
            if not instance:
                raise ValueError(f"Instância {instance_id} não encontrada")
            
            connection_info = {
                'instance_id': instance_id,
                'instance_name': instance.get('name', 'N/A'),
                'state': instance.get('state', 'unknown'),
                'public_ip': instance.get('public_ip'),
                'private_ip': instance.get('private_ip'),
                'key_name': instance.get('key_name'),
                'platform': instance.get('platform', 'linux'),
                'connection_type': connection_type
            }
            
            # Verifica se instância está rodando
            if instance.get('state') != 'running':
                connection_info['error'] = f"Instância está no estado: {instance.get('state')}"
                return connection_info
            
            # Gera comando de conexão baseado no tipo
            if connection_type == 'ssh':
                connection_info.update(self._generate_ssh_command(instance))
            elif connection_type == 'rdp':
                connection_info.update(self._generate_rdp_command(instance))
            elif connection_type == 'session_manager':
                connection_info.update(self._generate_session_manager_command(instance))
            
            return connection_info
        
        except Exception as e:
            self.logger.error(f"Erro ao preparar conexão para {instance_id}: {e}")
            return {
                'instance_id': instance_id,
                'error': str(e)
            }
    
    def _generate_ssh_command(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """Gera comando SSH para conexão"""
        public_ip = instance.get('public_ip')
        key_name = instance.get('key_name')
        platform = instance.get('platform', 'linux')
        
        # Determina usuário padrão baseado na plataforma
        default_users = {
            'amazon': 'ec2-user',
            'ubuntu': 'ubuntu',
            'centos': 'centos',
            'rhel': 'ec2-user',
            'suse': 'ec2-user',
            'debian': 'admin',
            'linux': 'ec2-user'
        }
        
        user = default_users.get(platform.lower(), 'ec2-user')
        
        if not public_ip:
            return {'error': 'Instância não possui IP público'}
        
        if not key_name:
            return {'error': 'Instância não possui key pair associado'}
        
        ssh_command = f"ssh -i ~/.ssh/{key_name}.pem {user}@{public_ip}"
        
        return {
            'command': ssh_command,
            'user': user,
            'host': public_ip,
            'key_file': f"~/.ssh/{key_name}.pem",
            'instructions': [
                f"1. Certifique-se de que o arquivo {key_name}.pem está em ~/.ssh/",
                f"2. Execute: chmod 400 ~/.ssh/{key_name}.pem",
                f"3. Execute: {ssh_command}",
                "4. Verifique se o Security Group permite SSH (porta 22)"
            ]
        }
    
    def _generate_rdp_command(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """Gera comando RDP para conexão"""
        public_ip = instance.get('public_ip')
        
        if not public_ip:
            return {'error': 'Instância não possui IP público'}
        
        return {
            'command': f"mstsc /v:{public_ip}",
            'host': public_ip,
            'port': 3389,
            'instructions': [
                f"1. Execute: mstsc /v:{public_ip}",
                "2. Use as credenciais do Windows da instância",
                "3. Verifique se o Security Group permite RDP (porta 3389)"
            ]
        }
    
    def _generate_session_manager_command(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """Gera comando Session Manager para conexão"""
        instance_id = instance.get('instance_id')
        
        return {
            'command': f"aws ssm start-session --target {instance_id}",
            'target': instance_id,
            'instructions': [
                "1. Certifique-se de que o AWS CLI está instalado",
                "2. Certifique-se de que o Session Manager Plugin está instalado",
                f"3. Execute: aws ssm start-session --target {instance_id}",
                "4. A instância deve ter a role SSM associada"
            ]
        }
    
    def list_volumes(self, volume_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Lista volumes EBS
        
        Args:
            volume_ids: IDs específicos de volumes
            
        Returns:
            Lista de volumes formatados
        """
        try:
            client = self.get_client()
            
            params = {}
            if volume_ids:
                params['VolumeIds'] = volume_ids
            
            response = client.describe_volumes(**params)
            
            volumes = []
            for volume in response['Volumes']:
                volumes.append(self._format_volume(volume))
            
            return volumes
        
        except ClientError as e:
            self.handle_aws_error(e, 'list_volumes')
            return []
    
    def get_volume_details(self, volume_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém detalhes de um volume específico
        
        Args:
            volume_id: ID do volume
            
        Returns:
            Detalhes do volume ou None se não encontrado
        """
        try:
            volumes = self.list_volumes(volume_ids=[volume_id])
            return volumes[0] if volumes else None
        
        except Exception as e:
            self.logger.error(f"Erro ao obter detalhes do volume {volume_id}: {e}")
            return None
    
    def list_security_groups(self, group_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Lista security groups
        
        Args:
            group_ids: IDs específicos de security groups
            
        Returns:
            Lista de security groups formatados
        """
        try:
            client = self.get_client()
            
            params = {}
            if group_ids:
                params['GroupIds'] = group_ids
            
            response = client.describe_security_groups(**params)
            
            security_groups = []
            for sg in response['SecurityGroups']:
                security_groups.append(self._format_security_group(sg))
            
            return security_groups
        
        except ClientError as e:
            self.handle_aws_error(e, 'list_security_groups')
            return []
    
    def get_security_group_details(self, group_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém detalhes de um security group específico
        
        Args:
            group_id: ID do security group
            
        Returns:
            Detalhes do security group ou None se não encontrado
        """
        try:
            security_groups = self.list_security_groups(group_ids=[group_id])
            return security_groups[0] if security_groups else None
        
        except Exception as e:
            self.logger.error(f"Erro ao obter detalhes do security group {group_id}: {e}")
            return None
    
    def list_key_pairs(self) -> List[Dict[str, Any]]:
        """
        Lista key pairs
        
        Returns:
            Lista de key pairs formatados
        """
        try:
            client = self.get_client()
            
            response = client.describe_key_pairs()
            
            key_pairs = []
            for kp in response['KeyPairs']:
                key_pairs.append(self._format_key_pair(kp))
            
            return key_pairs
        
        except ClientError as e:
            self.handle_aws_error(e, 'list_key_pairs')
            return []
    
    def list_vpcs(self) -> List[Dict[str, Any]]:
        """
        Lista VPCs
        
        Returns:
            Lista de VPCs formatados
        """
        try:
            client = self.get_client()
            
            response = client.describe_vpcs()
            
            vpcs = []
            for vpc in response['Vpcs']:
                vpcs.append(self._format_vpc(vpc))
            
            return vpcs
        
        except ClientError as e:
            self.handle_aws_error(e, 'list_vpcs')
            return []
    
    def _format_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """Formata dados de instância para exibição"""
        # Extrai tags
        tags = self.format_tags(instance.get('Tags', []))
        
        # Determina plataforma
        platform = instance.get('Platform', 'linux')
        if 'windows' in instance.get('PlatformDetails', '').lower():
            platform = 'windows'
        
        return {
            'instance_id': instance['InstanceId'],
            'name': tags.get('Name', 'N/A'),
            'state': instance['State']['Name'],
            'instance_type': instance['InstanceType'],
            'platform': platform,
            'architecture': instance.get('Architecture', 'x86_64'),
            'public_ip': instance.get('PublicIpAddress'),
            'private_ip': instance.get('PrivateIpAddress'),
            'vpc_id': instance.get('VpcId'),
            'subnet_id': instance.get('SubnetId'),
            'security_groups': [sg['GroupName'] for sg in instance.get('SecurityGroups', [])],
            'key_name': instance.get('KeyName'),
            'launch_time': format_datetime(instance.get('LaunchTime')),
            'availability_zone': instance.get('Placement', {}).get('AvailabilityZone'),
            'monitoring': instance.get('Monitoring', {}).get('State', 'disabled'),
            'tags': tags,
            'raw': instance
        }
    
    def _format_volume(self, volume: Dict[str, Any]) -> Dict[str, Any]:
        """Formata dados de volume para exibição"""
        tags = self.format_tags(volume.get('Tags', []))
        
        # Informações de attachment
        attachments = volume.get('Attachments', [])
        attached_to = None
        if attachments:
            attachment = attachments[0]
            attached_to = {
                'instance_id': attachment.get('InstanceId'),
                'device': attachment.get('Device'),
                'state': attachment.get('State')
            }
        
        return {
            'volume_id': volume['VolumeId'],
            'name': tags.get('Name', 'N/A'),
            'size': volume['Size'],
            'size_formatted': format_size(volume['Size'] * 1024 * 1024 * 1024),
            'volume_type': volume['VolumeType'],
            'state': volume['State'],
            'created_time': format_datetime(volume.get('CreateTime')),
            'availability_zone': volume['AvailabilityZone'],
            'encrypted': volume.get('Encrypted', False),
            'iops': volume.get('Iops'),
            'throughput': volume.get('Throughput'),
            'attached_to': attached_to,
            'tags': tags,
            'raw': volume
        }
    
    def _format_security_group(self, sg: Dict[str, Any]) -> Dict[str, Any]:
        """Formata dados de security group para exibição"""
        tags = self.format_tags(sg.get('Tags', []))
        
        return {
            'group_id': sg['GroupId'],
            'group_name': sg['GroupName'],
            'description': sg.get('Description', ''),
            'vpc_id': sg.get('VpcId'),
            'owner_id': sg.get('OwnerId'),
            'inbound_rules': len(sg.get('IpPermissions', [])),
            'outbound_rules': len(sg.get('IpPermissionsEgress', [])),
            'tags': tags,
            'raw': sg
        }
    
    def _format_key_pair(self, kp: Dict[str, Any]) -> Dict[str, Any]:
        """Formata dados de key pair para exibição"""
        tags = self.format_tags(kp.get('Tags', []))
        
        return {
            'key_name': kp['KeyName'],
            'key_pair_id': kp.get('KeyPairId'),
            'key_type': kp.get('KeyType', 'rsa'),
            'fingerprint': kp.get('KeyFingerprint'),
            'created_time': format_datetime(kp.get('CreateTime')),
            'tags': tags,
            'raw': kp
        }
    
    def _format_vpc(self, vpc: Dict[str, Any]) -> Dict[str, Any]:
        """Formata dados de VPC para exibição"""
        tags = self.format_tags(vpc.get('Tags', []))
        
        return {
            'vpc_id': vpc['VpcId'],
            'name': tags.get('Name', 'N/A'),
            'cidr_block': vpc['CidrBlock'],
            'state': vpc['State'],
            'is_default': vpc.get('IsDefault', False),
            'dhcp_options_id': vpc.get('DhcpOptionsId'),
            'instance_tenancy': vpc.get('InstanceTenancy', 'default'),
            'tags': tags,
            'raw': vpc
        }
