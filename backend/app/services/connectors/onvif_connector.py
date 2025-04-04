"""
Conector para dispositivos compatíveis com ONVIF.

Este módulo implementa um conector para dispositivos que suportam o protocolo ONVIF,
que é um padrão aberto para comunicação entre dispositivos de vídeo IP.
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
import aiohttp
import asyncio
from zeep import Client
from zeep.asyncio import AsyncTransport
from urllib.parse import urlparse

from .base import BaseConnector, ConnectorError, DeviceInfo, StreamInfo
from .factory import register_connector


@register_connector("onvif")
class OnvifConnector(BaseConnector):
    """Conector para dispositivos compatíveis com ONVIF."""
    
    def __init__(self, ip_address: str, port: int, username: str, password: str, **kwargs):
        """
        Inicializa o conector ONVIF.
        
        Args:
            ip_address: Endereço IP do dispositivo
            port: Porta para conexão ONVIF (geralmente 80)
            username: Nome de usuário para autenticação
            password: Senha para autenticação
            **kwargs: Parâmetros adicionais
        """
        super().__init__(ip_address, port, username, password, **kwargs)
        self.device_service = None
        self.media_service = None
        self.ptz_service = None
        self.event_service = None
        self.device_mgmt_service = None
        
        # URLs de serviço
        self.device_service_url = f"http://{ip_address}:{port}/onvif/device_service"
        self.device_xaddr = None
        self.media_xaddr = None
        self.ptz_xaddr = None
        self.event_xaddr = None
        
        # Configuração
        self.wsdl_dir = kwargs.get('wsdl_dir', './wsdl')
        self.timeout = kwargs.get('timeout', 10)
    
    async def _create_onvif_client(self, url: str) -> Client:
        """
        Cria um cliente ONVIF para um serviço específico.
        
        Args:
            url: URL do serviço ONVIF
            
        Returns:
            Client: Cliente ONVIF configurado
            
        Raises:
            ConnectorError: Se não for possível criar o cliente
        """
        try:
            session = aiohttp.ClientSession()
            transport = AsyncTransport(session=session)
            wsdl = f"{self.wsdl_dir}/device.wsdl"
            
            client = Client(
                wsdl=wsdl,
                transport=transport,
                wsse={"username": self.username, "password": self.password}
            )
            
            return client
        except Exception as e:
            raise ConnectorError(f"Erro ao criar cliente ONVIF: {str(e)}")
    
    async def connect(self) -> bool:
        """
        Conecta ao dispositivo ONVIF.
        
        Returns:
            bool: True se a conexão foi bem-sucedida
            
        Raises:
            ConnectorError: Se ocorrer um erro durante a conexão
        """
        try:
            # Criar cliente para o serviço de dispositivo
            self.device_client = await self._create_onvif_client(self.device_service_url)
            
            # Obter capacidades do dispositivo
            capabilities = await self.device_client.service.GetCapabilities()
            
            # Armazenar URLs dos serviços
            if hasattr(capabilities, 'Device') and capabilities.Device:
                self.device_xaddr = capabilities.Device.XAddr
            
            if hasattr(capabilities, 'Media') and capabilities.Media:
                self.media_xaddr = capabilities.Media.XAddr
            
            if hasattr(capabilities, 'PTZ') and capabilities.PTZ:
                self.ptz_xaddr = capabilities.PTZ.XAddr
            
            if hasattr(capabilities, 'Events') and capabilities.Events:
                self.event_xaddr = capabilities.Events.XAddr
            
            # Criar clientes para os outros serviços
            if self.media_xaddr:
                self.media_client = await self._create_onvif_client(self.media_xaddr)
            
            if self.ptz_xaddr:
                self.ptz_client = await self._create_onvif_client(self.ptz_xaddr)
            
            if self.event_xaddr:
                self.event_client = await self._create_onvif_client(self.event_xaddr)
            
            self.is_connected = True
            return True
        
        except Exception as e:
            self.is_connected = False
            raise ConnectorError(f"Erro ao conectar ao dispositivo ONVIF: {str(e)}")
    
    async def disconnect(self) -> bool:
        """
        Desconecta do dispositivo ONVIF.
        
        Returns:
            bool: True se a desconexão foi bem-sucedida
        """
        try:
            # Fechar sessões
            if hasattr(self, 'device_client') and self.device_client:
                if hasattr(self.device_client.transport, 'session'):
                    await self.device_client.transport.session.close()
            
            if hasattr(self, 'media_client') and self.media_client:
                if hasattr(self.media_client.transport, 'session'):
                    await self.media_client.transport.session.close()
            
            if hasattr(self, 'ptz_client') and self.ptz_client:
                if hasattr(self.ptz_client.transport, 'session'):
                    await self.ptz_client.transport.session.close()
            
            if hasattr(self, 'event_client') and self.event_client:
                if hasattr(self.event_client.transport, 'session'):
                    await self.event_client.transport.session.close()
            
            self.is_connected = False
            return True
        
        except Exception as e:
            raise ConnectorError(f"Erro ao desconectar do dispositivo ONVIF: {str(e)}")
    
    async def get_device_info(self) -> DeviceInfo:
        """
        Obtém informações sobre o dispositivo ONVIF.
        
        Returns:
            DeviceInfo: Informações sobre o dispositivo
            
        Raises:
            ConnectorError: Se ocorrer um erro ao obter as informações
        """
        if not self.is_connected:
            await self.connect()
        
        try:
            # Obter informações do dispositivo
            device_info = await self.device_client.service.GetDeviceInformation()
            
            # Criar objeto DeviceInfo
            info = DeviceInfo(
                id=str(uuid.uuid4()),  # Gerar ID único
                name=getattr(device_info, 'FriendlyName', device_info.Manufacturer),
                model=device_info.Model,
                manufacturer=device_info.Manufacturer,
                ip_address=self.ip_address,
                port=self.port,
                firmware=device_info.FirmwareVersion,
                serial_number=getattr(device_info, 'SerialNumber', None),
                status="online",
                last_seen=datetime.now()
            )
            
            # Armazenar informações do dispositivo
            self.device_info = info
            
            # Obter número de canais/profiles
            if self.media_client:
                try:
                    profiles = await self.media_client.service.GetProfiles()
                    info.channels = len(profiles)
                except:
                    info.channels = 0
            
            # Obter capacidades
            info.capabilities = {
                "ptz": self.ptz_xaddr is not None,
                "events": self.event_xaddr is not None,
                "media": self.media_xaddr is not None
            }
            
            return info
        
        except Exception as e:
            raise ConnectorError(f"Erro ao obter informações do dispositivo ONVIF: {str(e)}")
    
    async def list_streams(self) -> List[StreamInfo]:
        """
        Lista todos os streams disponíveis no dispositivo ONVIF.
        
        Returns:
            List[StreamInfo]: Lista de informações sobre os streams
            
        Raises:
            ConnectorError: Se ocorrer um erro ao listar os streams
        """
        if not self.is_connected:
            await self.connect()
        
        if not self.media_client:
            raise ConnectorError("Serviço de mídia não disponível")
        
        try:
            # Obter perfis de mídia
            profiles = await self.media_client.service.GetProfiles()
            
            # Criar lista de streams
            streams = []
            
            for idx, profile in enumerate(profiles):
                # Obter URI do stream
                stream_setup = {
                    'Stream': 'RTP-Unicast',
                    'Transport': {'Protocol': 'RTSP', 'Tunnel': None}
                }
                
                uri = await self.media_client.service.GetStreamUri(stream_setup, profile.token)
                
                # Obter informações de vídeo
                video_config = None
                if hasattr(profile, 'VideoEncoderConfiguration') and profile.VideoEncoderConfiguration:
                    video_config = profile.VideoEncoderConfiguration
                
                # Verificar se suporta PTZ
                ptz_capable = False
                if self.ptz_client and hasattr(profile, 'PTZConfiguration') and profile.PTZConfiguration:
                    ptz_capable = True
                
                # Verificar se suporta áudio
                audio_capable = False
                if hasattr(profile, 'AudioEncoderConfiguration') and profile.AudioEncoderConfiguration:
                    audio_capable = True
                
                # Criar objeto StreamInfo
                stream_info = StreamInfo(
                    id=profile.token,
                    name=profile.Name,
                    url=uri.Uri,
                    type="rtsp",
                    channel=idx,
                    resolution=f"{video_config.Resolution.Width}x{video_config.Resolution.Height}" if video_config else None,
                    fps=video_config.RateControl.FrameRateLimit if video_config and hasattr(video_config, 'RateControl') else None,
                    encoding=video_config.Encoding if video_config else None,
                    ptz_capable=ptz_capable,
                    audio_capable=audio_capable,
                    device_id=self.device_info.id if self.device_info else None
                )
                
                streams.append(stream_info)
            
            return streams
        
        except Exception as e:
            raise ConnectorError(f"Erro ao listar streams ONVIF: {str(e)}")
    
    async def get_stream_url(self, channel_id: str) -> str:
        """
        Obtém a URL para um stream específico.
        
        Args:
            channel_id: ID do canal (token do perfil)
            
        Returns:
            str: URL do stream
            
        Raises:
            ConnectorError: Se ocorrer um erro ao obter a URL
        """
        if not self.is_connected:
            await self.connect()
        
        if not self.media_client:
            raise ConnectorError("Serviço de mídia não disponível")
        
        try:
            # Configuração do stream
            stream_setup = {
                'Stream': 'RTP-Unicast',
                'Transport': {'Protocol': 'RTSP', 'Tunnel': None}
            }
            
            # Obter URI do stream
            uri = await self.media_client.service.GetStreamUri(stream_setup, channel_id)
            
            return uri.Uri
        
        except Exception as e:
            raise ConnectorError(f"Erro ao obter URL do stream ONVIF: {str(e)}")
    
    async def snapshot(self, channel_id: str) -> bytes:
        """
        Obtém uma imagem instantânea de um stream.
        
        Args:
            channel_id: ID do canal (token do perfil)
            
        Returns:
            bytes: Dados da imagem
            
        Raises:
            ConnectorError: Se ocorrer um erro ao obter a imagem
        """
        if not self.is_connected:
            await self.connect()
        
        if not self.media_client:
            raise ConnectorError("Serviço de mídia não disponível")
        
        try:
            # Obter URI da imagem
            uri = await self.media_client.service.GetSnapshotUri(channel_id)
            
            # Baixar a imagem
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(self.username, self.password)
                async with session.get(uri.Uri, auth=auth, timeout=self.timeout) as response:
                    if response.status != 200:
                        raise ConnectorError(f"Erro ao obter snapshot: HTTP {response.status}")
                    
                    return await response.read()
        
        except Exception as e:
            raise ConnectorError(f"Erro ao obter snapshot ONVIF: {str(e)}")
    
    async def discover_devices(network: str = "192.168.1.0/24", timeout: int = 5) -> List[Dict[str, Any]]:
        """
        Descobre dispositivos ONVIF na rede.
        
        Args:
            network: Rede a ser escaneada (formato CIDR)
            timeout: Tempo limite em segundos
            
        Returns:
            List[Dict[str, Any]]: Lista de dispositivos encontrados
        """
        # Implementação da descoberta WS-Discovery
        # Este é um placeholder - uma implementação real usaria WS-Discovery
        # que é um protocolo complexo para descoberta de serviços web
        
        return []  # Implementação pendente 