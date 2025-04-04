"""
Classes base para conectores de DVRs, NVRs e câmeras IP.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


class ConnectorError(Exception):
    """Exceção para erros específicos de conectores."""
    pass


@dataclass
class DeviceInfo:
    """Classe para armazenar informações sobre um dispositivo conectado."""
    
    id: str
    name: str
    model: str
    manufacturer: str
    ip_address: str
    port: int
    firmware: Optional[str] = None
    serial_number: Optional[str] = None
    channels: int = 0
    status: str = "unknown"
    last_seen: Optional[datetime] = None
    capabilities: Optional[Dict[str, Any]] = None


@dataclass
class StreamInfo:
    """Classe para armazenar informações sobre um stream de vídeo."""
    
    id: str
    name: str
    url: str
    type: str  # 'rtsp', 'http', 'onvif', etc.
    channel: int
    resolution: Optional[str] = None
    fps: Optional[int] = None
    encoding: Optional[str] = None
    ptz_capable: bool = False
    audio_capable: bool = False
    device_id: Optional[str] = None


class BaseConnector(ABC):
    """Classe base para todos os conectores de dispositivos."""
    
    connector_type: str = "generic"
    
    def __init__(self, ip_address: str, port: int, username: str, password: str, **kwargs):
        """
        Inicializa o conector.
        
        Args:
            ip_address: Endereço IP do dispositivo
            port: Porta para conexão
            username: Nome de usuário para autenticação
            password: Senha para autenticação
            **kwargs: Parâmetros adicionais específicos do conector
        """
        self.ip_address = ip_address
        self.port = port
        self.username = username
        self.password = password
        self.config = kwargs
        self.is_connected = False
        self.device_info = None
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Conecta ao dispositivo.
        
        Returns:
            bool: True se a conexão foi bem-sucedida, False caso contrário
        
        Raises:
            ConnectorError: Se ocorrer um erro durante a conexão
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Desconecta do dispositivo.
        
        Returns:
            bool: True se a desconexão foi bem-sucedida, False caso contrário
        """
        pass
    
    @abstractmethod
    async def get_device_info(self) -> DeviceInfo:
        """
        Obtém informações sobre o dispositivo.
        
        Returns:
            DeviceInfo: Informações sobre o dispositivo
        
        Raises:
            ConnectorError: Se ocorrer um erro ao obter as informações
        """
        pass
    
    @abstractmethod
    async def list_streams(self) -> List[StreamInfo]:
        """
        Lista todos os streams disponíveis no dispositivo.
        
        Returns:
            List[StreamInfo]: Lista de informações sobre os streams
        
        Raises:
            ConnectorError: Se ocorrer um erro ao listar os streams
        """
        pass
    
    @abstractmethod
    async def get_stream_url(self, channel_id: str) -> str:
        """
        Obtém a URL para um stream específico.
        
        Args:
            channel_id: ID do canal (stream)
            
        Returns:
            str: URL do stream
            
        Raises:
            ConnectorError: Se ocorrer um erro ao obter a URL
        """
        pass
    
    async def test_connection(self) -> bool:
        """
        Testa a conexão com o dispositivo.
        
        Returns:
            bool: True se a conexão está ativa, False caso contrário
        """
        try:
            if not self.is_connected:
                return await self.connect()
            return True
        except Exception:
            return False
    
    def __str__(self) -> str:
        """
        Retorna uma representação em string do conector.
        
        Returns:
            str: Representação em string
        """
        return f"{self.connector_type} Connector ({self.ip_address}:{self.port})" 