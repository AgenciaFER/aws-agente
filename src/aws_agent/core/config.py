"""
Configuração principal do AWS Agent

Este módulo gerencia as configurações do agente AWS, incluindo
configurações de aplicação, caminhos de arquivos e validação.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class Config(BaseModel):
    """
    Classe principal de configuração do AWS Agent
    
    Attributes:
        app_name: Nome da aplicação
        version: Versão da aplicação
        config_dir: Diretório de configuração
        credentials_file: Arquivo de credenciais criptografadas
        log_level: Nível de log
        log_file: Arquivo de log
        encryption_key_name: Nome da chave de criptografia no keyring
        default_region: Região AWS padrão
        session_timeout: Timeout da sessão em segundos
    """
    
    app_name: str = Field(default="aws-multi-account-agent")
    version: str = Field(default="1.0.0")
    config_dir: Path = Field(default_factory=lambda: Path.home() / ".aws-agent")
    credentials_file: str = Field(default="credentials.encrypted")
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="aws-agent.log")
    encryption_key_name: str = Field(default="aws-agent-encryption-key")
    default_region: str = Field(default="us-east-1")
    session_timeout: int = Field(default=3600)
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Valida o nível de log"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()
    
    @field_validator('session_timeout')
    @classmethod
    def validate_session_timeout(cls, v):
        """Valida o timeout da sessão"""
        if v < 60 or v > 86400:  # 1 minuto a 24 horas
            raise ValueError('Session timeout must be between 60 and 86400 seconds')
        return v
    
    @property
    def credentials_path(self) -> Path:
        """Caminho completo para o arquivo de credenciais"""
        return self.config_dir / self.credentials_file
    
    @property
    def log_path(self) -> Path:
        """Caminho completo para o arquivo de log"""
        return self.config_dir / self.log_file
    
    def ensure_directories(self) -> None:
        """Garante que os diretórios necessários existam"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        (self.config_dir / "logs").mkdir(parents=True, exist_ok=True)
        (self.config_dir / "backups").mkdir(parents=True, exist_ok=True)
    
    def load_from_file(self, config_file: Optional[Path] = None) -> None:
        """
        Carrega configurações de um arquivo YAML
        
        Args:
            config_file: Caminho para o arquivo de configuração
        """
        if config_file is None:
            config_file = self.config_dir / "config.yaml"
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if data:
                        for key, value in data.items():
                            if hasattr(self, key):
                                setattr(self, key, value)
            except Exception as e:
                print(f"Erro ao carregar configuração: {e}")
    
    def save_to_file(self, config_file: Optional[Path] = None) -> None:
        """
        Salva configurações em um arquivo YAML
        
        Args:
            config_file: Caminho para o arquivo de configuração
        """
        if config_file is None:
            config_file = self.config_dir / "config.yaml"
        
        self.ensure_directories()
        
        # Converte Path para string para serialização YAML
        config_data = self.dict()
        config_data['config_dir'] = str(self.config_dir)
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            print(f"Erro ao salvar configuração: {e}")
    
    def get_env_config(self) -> Dict[str, Any]:
        """
        Obtém configurações de variáveis de ambiente
        
        Returns:
            Dict com configurações encontradas nas variáveis de ambiente
        """
        env_config = {}
        
        # Mapeamento de variáveis de ambiente
        env_mapping = {
            'AWS_AGENT_CONFIG_DIR': 'config_dir',
            'AWS_AGENT_LOG_LEVEL': 'log_level',
            'AWS_AGENT_DEFAULT_REGION': 'default_region',
            'AWS_AGENT_SESSION_TIMEOUT': 'session_timeout',
        }
        
        for env_var, config_key in env_mapping.items():
            value = os.getenv(env_var)
            if value:
                # Conversão de tipos quando necessário
                if config_key == 'session_timeout':
                    try:
                        value = int(value)
                    except ValueError:
                        continue
                elif config_key == 'config_dir':
                    value = Path(value)
                
                env_config[config_key] = value
        
        return env_config
    
    def update_from_env(self) -> None:
        """Atualiza configurações com valores de variáveis de ambiente"""
        env_config = self.get_env_config()
        for key, value in env_config.items():
            setattr(self, key, value)
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True
    )


# Instância global da configuração
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """
    Obtém a instância global da configuração
    
    Returns:
        Instância da configuração
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
        _config_instance.update_from_env()
        _config_instance.load_from_file()
        _config_instance.ensure_directories()
    return _config_instance


def reset_config() -> None:
    """Reset da configuração global (útil para testes)"""
    global _config_instance
    _config_instance = None
