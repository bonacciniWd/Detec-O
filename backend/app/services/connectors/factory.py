"""
Fábrica para criação de conectores.

Este módulo define a fábrica que cria instâncias dos diferentes tipos de conectores
de acordo com o tipo especificado.
"""

from typing import Dict, Any, Type, Optional, List, Callable
from .base import BaseConnector

# Dicionário global para armazenar os tipos de conectores registrados
REGISTERED_CONNECTORS: Dict[str, Type[BaseConnector]] = {}


def register_connector(connector_type: str):
    """
    Decorador para registrar uma classe de conector na fábrica.
    
    Args:
        connector_type: Tipo de conector (ex: 'hikvision', 'dahua', 'onvif')
    
    Returns:
        Callable: Decorador
    """
    def decorator(cls: Type[BaseConnector]) -> Type[BaseConnector]:
        if connector_type in REGISTERED_CONNECTORS:
            raise ValueError(f"Conector com tipo '{connector_type}' já registrado")
        
        REGISTERED_CONNECTORS[connector_type] = cls
        cls.connector_type = connector_type
        return cls
    
    return decorator


class ConnectorFactory:
    """Fábrica para criação de instâncias de conectores."""
    
    @staticmethod
    def get_connector_types() -> List[str]:
        """
        Obtém a lista de tipos de conectores registrados.
        
        Returns:
            List[str]: Lista de tipos de conectores disponíveis
        """
        return list(REGISTERED_CONNECTORS.keys())
    
    @staticmethod
    def create_connector(
        connector_type: str,
        ip_address: str,
        port: int,
        username: str,
        password: str,
        **kwargs
    ) -> Optional[BaseConnector]:
        """
        Cria uma instância de um conector específico.
        
        Args:
            connector_type: Tipo de conector a ser criado
            ip_address: Endereço IP do dispositivo
            port: Porta para conexão
            username: Nome de usuário para autenticação
            password: Senha para autenticação
            **kwargs: Parâmetros adicionais específicos do conector
        
        Returns:
            BaseConnector: Instância do conector
            
        Raises:
            ValueError: Se o tipo de conector não estiver registrado
        """
        if connector_type not in REGISTERED_CONNECTORS:
            raise ValueError(f"Tipo de conector '{connector_type}' não registrado")
        
        connector_class = REGISTERED_CONNECTORS[connector_type]
        return connector_class(ip_address, port, username, password, **kwargs)
    
    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> Optional[BaseConnector]:
        """
        Cria uma instância de um conector a partir de uma configuração.
        
        Args:
            config: Dicionário de configuração com os parâmetros necessários
                   (deve conter pelo menos 'type', 'ip_address', 'port', 'username', 'password')
        
        Returns:
            BaseConnector: Instância do conector
            
        Raises:
            ValueError: Se a configuração for inválida ou o tipo de conector não estiver registrado
        """
        required_fields = ['type', 'ip_address', 'port', 'username', 'password']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Campo obrigatório '{field}' ausente na configuração")
        
        # Extrair campos principais
        connector_type = config.pop('type')
        ip_address = config.pop('ip_address')
        port = config.pop('port')
        username = config.pop('username')
        password = config.pop('password')
        
        # Os demais campos são passados como kwargs
        return ConnectorFactory.create_connector(
            connector_type, ip_address, port, username, password, **config
        ) 