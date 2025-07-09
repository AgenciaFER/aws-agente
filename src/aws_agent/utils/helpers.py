"""
Utilitários para o AWS Agent

Este módulo contém funções utilitárias compartilhadas entre os componentes
do agente AWS, incluindo validação, formatação e helpers diversos.
"""

import re
import json
import yaml
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone
from pathlib import Path


def validate_aws_account_id(account_id: str) -> bool:
    """
    Valida formato de Account ID AWS
    
    Args:
        account_id: ID da conta para validar
        
    Returns:
        True se válido
    """
    if not account_id:
        return False
    
    # Account ID deve ter 12 dígitos
    return re.match(r'^\d{12}$', account_id) is not None


def validate_aws_region(region: str) -> bool:
    """
    Valida formato de região AWS
    
    Args:
        region: Região para validar
        
    Returns:
        True se válido
    """
    if not region:
        return False
    
    # Formato: us-east-1, eu-west-1, ap-southeast-1, etc.
    return re.match(r'^[a-z]{2}-[a-z]+-\d+$', region) is not None


def validate_aws_arn(arn: str) -> bool:
    """
    Valida formato de ARN AWS
    
    Args:
        arn: ARN para validar
        
    Returns:
        True se válido
    """
    if not arn:
        return False
    
    # Formato: arn:partition:service:region:account-id:resource
    pattern = r'^arn:([^:]+):([^:]+):([^:]*):([^:]*):(.+)$'
    return re.match(pattern, arn) is not None


def parse_aws_arn(arn: str) -> Optional[Dict[str, str]]:
    """
    Faz parse de um ARN AWS
    
    Args:
        arn: ARN para fazer parse
        
    Returns:
        Dicionário com componentes do ARN ou None se inválido
    """
    if not validate_aws_arn(arn):
        return None
    
    parts = arn.split(':', 5)
    
    return {
        'arn': arn,
        'partition': parts[1],
        'service': parts[2],
        'region': parts[3],
        'account_id': parts[4],
        'resource': parts[5]
    }


def format_datetime(dt: Optional[datetime]) -> str:
    """
    Formata datetime para string legível
    
    Args:
        dt: Datetime para formatar
        
    Returns:
        String formatada ou 'N/A' se None
    """
    if dt is None:
        return 'N/A'
    
    # Converte para UTC se não tiver timezone
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.strftime('%Y-%m-%d %H:%M:%S UTC')


def parse_datetime(dt_str: str) -> Optional[datetime]:
    """
    Converte string para datetime
    
    Args:
        dt_str: String de datetime
        
    Returns:
        Datetime ou None se inválido
    """
    if not dt_str or dt_str == 'N/A':
        return None
    
    # Tenta vários formatos
    formats = [
        '%Y-%m-%d %H:%M:%S UTC',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    
    return None


def format_size(size_bytes: int) -> str:
    """
    Formata tamanho em bytes para string legível
    
    Args:
        size_bytes: Tamanho em bytes
        
    Returns:
        String formatada (ex: '1.5 GB')
    """
    if size_bytes == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.1f} {units[unit_index]}"


def format_currency(amount: float, currency: str = 'USD') -> str:
    """
    Formata valor monetário
    
    Args:
        amount: Valor
        currency: Moeda (padrão: USD)
        
    Returns:
        String formatada
    """
    if currency == 'USD':
        return f"${amount:.2f}"
    else:
        return f"{amount:.2f} {currency}"


def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Obtém valor de dicionário de forma segura
    
    Args:
        data: Dicionário
        key: Chave (pode usar notação de ponto para chaves aninhadas)
        default: Valor padrão
        
    Returns:
        Valor ou padrão se não encontrado
    """
    if not data or not key:
        return default
    
    keys = key.split('.')
    current = data
    
    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return default
    
    return current


def deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Faz merge profundo de dois dicionários
    
    Args:
        dict1: Primeiro dicionário
        dict2: Segundo dicionário
        
    Returns:
        Dicionário com merge
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Carrega arquivo JSON
    
    Args:
        file_path: Caminho do arquivo
        
    Returns:
        Conteúdo do arquivo ou None se erro
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def save_json_file(file_path: Path, data: Dict[str, Any]) -> bool:
    """
    Salva dados em arquivo JSON
    
    Args:
        file_path: Caminho do arquivo
        data: Dados para salvar
        
    Returns:
        True se salvo com sucesso
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def load_yaml_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Carrega arquivo YAML
    
    Args:
        file_path: Caminho do arquivo
        
    Returns:
        Conteúdo do arquivo ou None se erro
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception:
        return None


def save_yaml_file(file_path: Path, data: Dict[str, Any]) -> bool:
    """
    Salva dados em arquivo YAML
    
    Args:
        file_path: Caminho do arquivo
        data: Dados para salvar
        
    Returns:
        True se salvo com sucesso
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        return True
    except Exception:
        return False


def mask_sensitive_data(data: str, mask_char: str = '*', show_last: int = 4) -> str:
    """
    Mascara dados sensíveis
    
    Args:
        data: Dados para mascarar
        mask_char: Caractere para mascarar
        show_last: Quantos caracteres mostrar no final
        
    Returns:
        Dados mascarados
    """
    if not data or len(data) <= show_last:
        return mask_char * len(data) if data else ''
    
    return mask_char * (len(data) - show_last) + data[-show_last:]


def sanitize_filename(filename: str) -> str:
    """
    Sanitiza nome de arquivo removendo caracteres inválidos
    
    Args:
        filename: Nome do arquivo
        
    Returns:
        Nome sanitizado
    """
    # Remove caracteres inválidos para nomes de arquivo
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove espaços extras e pontos no final
    filename = filename.strip('. ')
    
    return filename


def truncate_string(text: str, max_length: int = 50, suffix: str = '...') -> str:
    """
    Trunca string se necessário
    
    Args:
        text: Texto para truncar
        max_length: Comprimento máximo
        suffix: Sufixo para textos truncados
        
    Returns:
        Texto truncado se necessário
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def validate_email(email: str) -> bool:
    """
    Valida formato de email
    
    Args:
        email: Email para validar
        
    Returns:
        True se válido
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def generate_unique_id(prefix: str = '') -> str:
    """
    Gera ID único
    
    Args:
        prefix: Prefixo para o ID
        
    Returns:
        ID único
    """
    import uuid
    unique_id = str(uuid.uuid4())
    
    if prefix:
        return f"{prefix}-{unique_id}"
    
    return unique_id


def retry_operation(func, max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator para retry de operações
    
    Args:
        func: Função para executar
        max_retries: Número máximo de tentativas
        delay: Delay inicial entre tentativas
        backoff: Fator de multiplicação do delay
        
    Returns:
        Decorator
    """
    def decorator(operation):
        def wrapper(*args, **kwargs):
            import time
            
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return operation(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise last_exception
            
            raise last_exception
        
        return wrapper
    
    return decorator


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Divide lista em chunks
    
    Args:
        lst: Lista para dividir
        chunk_size: Tamanho do chunk
        
    Returns:
        Lista de chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """
    Aplaina dicionário aninhado
    
    Args:
        d: Dicionário para aplainar
        parent_key: Chave pai
        sep: Separador
        
    Returns:
        Dicionário aplanado
    """
    items = []
    
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    
    return dict(items)


def is_valid_json(json_str: str) -> bool:
    """
    Verifica se string é JSON válido
    
    Args:
        json_str: String para verificar
        
    Returns:
        True se JSON válido
    """
    try:
        json.loads(json_str)
        return True
    except json.JSONDecodeError:
        return False


def format_table_data(data: List[Dict[str, Any]], columns: List[str]) -> List[List[str]]:
    """
    Formata dados para exibição em tabela
    
    Args:
        data: Dados para formatar
        columns: Colunas para incluir
        
    Returns:
        Dados formatados para tabela
    """
    if not data:
        return []
    
    rows = []
    for item in data:
        row = []
        for col in columns:
            value = safe_get(item, col, 'N/A')
            if isinstance(value, datetime):
                value = format_datetime(value)
            elif isinstance(value, bool):
                value = 'Sim' if value else 'Não'
            elif value is None:
                value = 'N/A'
            else:
                value = str(value)
            
            row.append(value)
        rows.append(row)
    
    return rows
