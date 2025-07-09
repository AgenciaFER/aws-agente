"""
Services module do AWS Agent - Módulos dos serviços AWS
"""

from .base import BaseAWSService
from .ec2 import EC2Service
from .s3 import S3Service
from .iam import IAMService
from .lambda_service import LambdaService

__all__ = [
    'BaseAWSService',
    'EC2Service',
    'S3Service',
    'IAMService',
    'LambdaService'
]

# Mapeamento de serviços disponíveis
AVAILABLE_SERVICES = {
    'ec2': EC2Service,
    's3': S3Service,
    'iam': IAMService,
    'lambda': LambdaService
}
