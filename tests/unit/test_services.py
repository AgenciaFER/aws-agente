"""
Tests for AWS services
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import boto3

from aws_agent.services.ec2 import EC2Service
from aws_agent.services.s3 import S3Service
from aws_agent.services.iam import IAMService
from aws_agent.services.lambda_service import LambdaService


class TestEC2Service(unittest.TestCase):
    """Tests for EC2Service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_session = Mock()
        self.mock_client = Mock()
        self.mock_session.client.return_value = self.mock_client
        self.service = EC2Service(self.mock_session, "us-east-1")
    
    def test_ec2_service_initialization(self):
        """Test EC2Service initialization"""
        self.assertEqual(self.service.region, "us-east-1")
        self.assertEqual(self.service.session, self.mock_session)
        self.mock_session.client.assert_called_with('ec2', region_name="us-east-1")
    
    def test_list_instances(self):
        """Test listing EC2 instances"""
        self.mock_client.describe_instances.return_value = {
            'Reservations': [
                {
                    'Instances': [
                        {
                            'InstanceId': 'i-123456789',
                            'InstanceType': 't2.micro',
                            'State': {'Name': 'running'},
                            'PublicIpAddress': '1.2.3.4',
                            'PrivateIpAddress': '10.0.0.1'
                        }
                    ]
                }
            ]
        }
        
        result = self.service.list_instances()
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['InstanceId'], 'i-123456789')
        self.assertEqual(result[0]['InstanceType'], 't2.micro')
        self.assertEqual(result[0]['State']['Name'], 'running')


class TestS3Service(unittest.TestCase):
    """Tests for S3Service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_session = Mock()
        self.mock_client = Mock()
        self.mock_session.client.return_value = self.mock_client
        self.service = S3Service(self.mock_session, "us-east-1")
    
    def test_s3_service_initialization(self):
        """Test S3Service initialization"""
        self.assertEqual(self.service.region, "us-east-1")
        self.assertEqual(self.service.session, self.mock_session)
        self.mock_session.client.assert_called_with('s3', region_name="us-east-1")
    
    def test_list_buckets(self):
        """Test listing S3 buckets"""
        self.mock_client.list_buckets.return_value = {
            'Buckets': [
                {
                    'Name': 'test-bucket',
                    'CreationDate': '2023-01-01T00:00:00Z'
                }
            ]
        }
        
        result = self.service.list_buckets()
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['Name'], 'test-bucket')


class TestIAMService(unittest.TestCase):
    """Tests for IAMService"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_session = Mock()
        self.mock_client = Mock()
        self.mock_session.client.return_value = self.mock_client
        self.service = IAMService(self.mock_session, "us-east-1")
    
    def test_iam_service_initialization(self):
        """Test IAMService initialization"""
        self.assertEqual(self.service.region, "us-east-1")
        self.assertEqual(self.service.session, self.mock_session)
        self.mock_session.client.assert_called_with('iam', region_name="us-east-1")
    
    def test_list_users(self):
        """Test listing IAM users"""
        self.mock_client.list_users.return_value = {
            'Users': [
                {
                    'UserName': 'test-user',
                    'UserId': 'AIDACKCEVSQ6C2EXAMPLE',
                    'Arn': 'arn:aws:iam::123456789012:user/test-user',
                    'CreateDate': '2023-01-01T00:00:00Z'
                }
            ]
        }
        
        result = self.service.list_users()
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['UserName'], 'test-user')


class TestLambdaService(unittest.TestCase):
    """Tests for LambdaService"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_session = Mock()
        self.mock_client = Mock()
        self.mock_session.client.return_value = self.mock_client
        self.service = LambdaService(self.mock_session, "us-east-1")
    
    def test_lambda_service_initialization(self):
        """Test LambdaService initialization"""
        self.assertEqual(self.service.region, "us-east-1")
        self.assertEqual(self.service.session, self.mock_session)
        self.mock_session.client.assert_called_with('lambda', region_name="us-east-1")
    
    def test_list_functions(self):
        """Test listing Lambda functions"""
        self.mock_client.list_functions.return_value = {
            'Functions': [
                {
                    'FunctionName': 'test-function',
                    'Runtime': 'python3.9',
                    'Role': 'arn:aws:iam::123456789012:role/lambda-role',
                    'Handler': 'lambda_function.lambda_handler',
                    'CodeSize': 1024,
                    'Description': 'Test function',
                    'Timeout': 30,
                    'MemorySize': 128,
                    'LastModified': '2023-01-01T00:00:00.000+0000'
                }
            ]
        }
        
        result = self.service.list_functions()
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['FunctionName'], 'test-function')
        self.assertEqual(result[0]['Runtime'], 'python3.9')


if __name__ == '__main__':
    unittest.main()
