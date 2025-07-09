"""
AWS Multi-Account Agent

Um agente AWS completo para gerenciamento de múltiplas contas com credenciais seguras.
"""

__version__ = "1.0.0"
__author__ = "AWS Multi-Account Agent Team"
__email__ = "team@aws-agent.com"
__description__ = "Agente AWS para gerenciamento de múltiplas contas com credenciais seguras"

from aws_agent.core.agent import AWSAgent
from aws_agent.core.account_manager import AccountManager
from aws_agent.core.config import Config

__all__ = [
    "AWSAgent",
    "AccountManager", 
    "Config",
    "__version__",
    "__author__",
    "__email__",
    "__description__",
]
