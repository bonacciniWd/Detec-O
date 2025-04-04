"""
Conector para dispositivos Hikvision (DVRs, NVRs e câmeras IP).

Este módulo implementa um conector específico para dispositivos da Hikvision,
utilizando a API ISAPI fornecida pelo fabricante.
"""

import uuid
import time
import asyncio
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import datetime
import aiohttp
from urllib.parse import quote

from .base import BaseConnector, ConnectorError, DeviceInfo, StreamInfo
from .factory import register_connector


@register_connector("hikvision")
class HikvisionConnector(BaseConnector):
    """Conector para dispositivos Hikvision."""
    
    def __init__(self, ip_address: str, port: int, username: str, password: str, **kwargs):
        """
        Inicializa o conector Hikvision.
        
        Args:
            ip_address: Endereço IP do dispositivo
            port: Porta para conexão (padrão: 80)
            username: Nome de usuário para autenticação
            password: Senha para autenticação
            **kwargs: Parâmetros adicionais
                - use_https: Usar HTTPS em vez de HTTP (padrão: False)
                - timeout: Tempo limite em segundos (padrão: 10)
                - rtsp_port: Porta RTSP (padrão: 554)
        """
        super().__init__(ip_address, port, username, password, **kwargs)
        
        # Configurações
        self.use_https = kwargs.get('use_https', False)
        self.timeout = kwargs.get('timeout', 10)
        self.rtsp_port = kwargs.get('rtsp_port', 554)
        
        # Construir URL base
        protocol = "https" if self.use_https else "http"
        self.base_url = f"{protocol}://{ip_address}:{port}"
        self.isapi_url = f"{self.base_url}/ISAPI"
        
        # Para autenticação digest
        self.auth = aiohttp.BasicAuth(username, password)
        
        # Sessão HTTP
        self.session = None
    
    async def connect(self) -> bool:
        """
        Conecta ao dispositivo Hikvision.
        
        Returns:
            bool: True se a conexão foi bem-sucedida
            
        Raises:
            ConnectorError: Se ocorrer um erro durante a conexão
        """
        try:
            # Criar sessão HTTP
            self.session = aiohttp.ClientSession(auth=self.auth)
            
            # Verificar conexão com um request simples
            async with self.session.get(
                f"{self.isapi_url}/System/deviceInfo", 
                timeout=self.timeout,
                ssl=False if self.use_https else None
            ) as response:
                if response.status != 200:
                    raise ConnectorError(f"Erro ao conectar: HTTP {response.status}")
                
                # Analisar resposta XML
                xml_text = await response.text()
                try:
                    root = ET.fromstring(xml_text)
                except ET.ParseError:
                    raise ConnectorError("Resposta XML inválida")
            
            self.is_connected = True
            return True
        
        except aiohttp.ClientError as e:
            self.is_connected = False
            raise ConnectorError(f"Erro ao conectar: {str(e)}")
        
        except Exception as e:
            self.is_connected = False
            raise ConnectorError(f"Erro ao conectar ao dispositivo Hikvision: {str(e)}")
    
    async def disconnect(self) -> bool:
        """
        Desconecta do dispositivo Hikvision.
        
        Returns:
            bool: True se a desconexão foi bem-sucedida
        """
        try:
            if self.session:
                await self.session.close()
            
            self.is_connected = False
            return True
        
        except Exception as e:
            raise ConnectorError(f"Erro ao desconectar do dispositivo Hikvision: {str(e)}")
    
    async def get_device_info(self) -> DeviceInfo:
        """
        Obtém informações sobre o dispositivo Hikvision.
        
        Returns:
            DeviceInfo: Informações sobre o dispositivo
            
        Raises:
            ConnectorError: Se ocorrer um erro ao obter as informações
        """
        if not self.is_connected:
            await self.connect()
        
        try:
            # Obter informações do dispositivo
            async with self.session.get(
                f"{self.isapi_url}/System/deviceInfo", 
                timeout=self.timeout,
                ssl=False if self.use_https else None
            ) as response:
                if response.status != 200:
                    raise ConnectorError(f"Erro ao obter informações: HTTP {response.status}")
                
                # Analisar resposta XML
                xml_text = await response.text()
                root = ET.fromstring(xml_text)
                
                # Extrair campos relevantes
                device_name = root.findtext("deviceName", "Unknown Device")
                model = root.findtext("model", "Unknown Model")
                serial_number = root.findtext("serialNumber", None)
                firmware_version = root.findtext("firmwareVersion", None)
                firmware_released_date = root.findtext("firmwareReleasedDate", None)
                
                # Número de canais (importante para DVRs/NVRs)
                num_channels = 1  # Padrão para câmeras
                
                # Verificar se é um DVR/NVR com múltiplos canais
                try:
                    async with self.session.get(
                        f"{self.isapi_url}/ContentMgmt/InputProxy/channels", 
                        timeout=self.timeout,
                        ssl=False if self.use_https else None
                    ) as channels_response:
                        if channels_response.status == 200:
                            channels_xml = await channels_response.text()
                            channels_root = ET.fromstring(channels_xml)
                            channels = channels_root.findall(".//InputProxyChannel")
                            if channels:
                                num_channels = len(channels)
                except:
                    # Ignorar erros ao tentar determinar número de canais
                    pass
                
                # Criar objeto DeviceInfo
                device_info = DeviceInfo(
                    id=str(uuid.uuid4()),
                    name=device_name,
                    model=model,
                    manufacturer="Hikvision",
                    ip_address=self.ip_address,
                    port=self.port,
                    firmware=firmware_version,
                    serial_number=serial_number,
                    channels=num_channels,
                    status="online",
                    last_seen=datetime.now(),
                    capabilities={
                        "ptz": False,  # Será determinado para cada canal
                        "audio": True,
                        "recording": True,
                    }
                )
                
                # Armazenar informações do dispositivo
                self.device_info = device_info
                
                return device_info
        
        except aiohttp.ClientError as e:
            raise ConnectorError(f"Erro de rede ao obter informações: {str(e)}")
        
        except Exception as e:
            raise ConnectorError(f"Erro ao obter informações do dispositivo Hikvision: {str(e)}")
    
    async def list_streams(self) -> List[StreamInfo]:
        """
        Lista todos os streams disponíveis no dispositivo Hikvision.
        
        Returns:
            List[StreamInfo]: Lista de informações sobre os streams
            
        Raises:
            ConnectorError: Se ocorrer um erro ao listar os streams
        """
        if not self.is_connected:
            await self.connect()
        
        if not self.device_info:
            await self.get_device_info()
        
        streams = []
        
        try:
            # Verificar se é uma câmera única ou um DVR/NVR
            if self.device_info.channels <= 1:
                # Dispositivo é uma câmera única
                # Adicionar streams principal e secundário
                main_stream = StreamInfo(
                    id="1",
                    name="Main Stream",
                    url=f"rtsp://{self.username}:{self.password}@{self.ip_address}:{self.rtsp_port}/Streaming/Channels/101",
                    type="rtsp",
                    channel=1,
                    resolution=None,  # Não podemos determinar sem consulta adicional
                    fps=None,
                    encoding="H.264",
                    ptz_capable=False,  # Pode ser atualizado com consulta adicional
                    audio_capable=True,
                    device_id=self.device_info.id
                )
                
                sub_stream = StreamInfo(
                    id="2",
                    name="Sub Stream",
                    url=f"rtsp://{self.username}:{self.password}@{self.ip_address}:{self.rtsp_port}/Streaming/Channels/102",
                    type="rtsp",
                    channel=1,
                    resolution=None,
                    fps=None,
                    encoding="H.264",
                    ptz_capable=False,
                    audio_capable=True,
                    device_id=self.device_info.id
                )
                
                streams.extend([main_stream, sub_stream])
            
            else:
                # Dispositivo é um DVR/NVR
                # Consultar canais disponíveis
                async with self.session.get(
                    f"{self.isapi_url}/ContentMgmt/InputProxy/channels", 
                    timeout=self.timeout,
                    ssl=False if self.use_https else None
                ) as response:
                    if response.status != 200:
                        raise ConnectorError(f"Erro ao listar canais: HTTP {response.status}")
                    
                    xml_text = await response.text()
                    root = ET.fromstring(xml_text)
                    
                    # Procurar todos os canais
                    channels = root.findall(".//InputProxyChannel")
                    
                    for channel in channels:
                        channel_id = channel.findtext("id", "")
                        if not channel_id:
                            continue
                        
                        # Extrair número do canal a partir do ID (formato típico: "ip_1_1")
                        channel_num = channel_id.split("_")[-1]
                        if not channel_num.isdigit():
                            channel_num = "1"
                        
                        channel_name = channel.findtext("name", f"Camera {channel_num}")
                        
                        # Verificar capacidade PTZ
                        ptz_capable = False
                        try:
                            async with self.session.get(
                                f"{self.isapi_url}/PTZCtrl/channels/{channel_id}/capabilities", 
                                timeout=self.timeout,
                                ssl=False if self.use_https else None
                            ) as ptz_response:
                                if ptz_response.status == 200:
                                    ptz_capable = True
                        except:
                            # Ignorar erros ao verificar capacidade PTZ
                            pass
                        
                        # Adicionar streams principal e secundário para o canal
                        main_stream = StreamInfo(
                            id=f"{channel_num}_1",
                            name=f"{channel_name} - Main",
                            url=f"rtsp://{self.username}:{self.password}@{self.ip_address}:{self.rtsp_port}/Streaming/Channels/{channel_num}01",
                            type="rtsp",
                            channel=int(channel_num),
                            resolution=None,
                            fps=None,
                            encoding="H.264",
                            ptz_capable=ptz_capable,
                            audio_capable=True,
                            device_id=self.device_info.id
                        )
                        
                        sub_stream = StreamInfo(
                            id=f"{channel_num}_2",
                            name=f"{channel_name} - Sub",
                            url=f"rtsp://{self.username}:{self.password}@{self.ip_address}:{self.rtsp_port}/Streaming/Channels/{channel_num}02",
                            type="rtsp",
                            channel=int(channel_num),
                            resolution=None,
                            fps=None,
                            encoding="H.264",
                            ptz_capable=ptz_capable,
                            audio_capable=True,
                            device_id=self.device_info.id
                        )
                        
                        streams.extend([main_stream, sub_stream])
            
            return streams
        
        except Exception as e:
            raise ConnectorError(f"Erro ao listar streams Hikvision: {str(e)}")
    
    async def get_stream_url(self, channel_id: str) -> str:
        """
        Obtém a URL para um stream específico.
        
        Args:
            channel_id: ID do canal (formato: "CANAL_STREAM", ex: "1_1" para canal 1, stream principal)
            
        Returns:
            str: URL do stream
            
        Raises:
            ConnectorError: Se ocorrer um erro ao obter a URL
        """
        try:
            # Extrair número do canal e tipo de stream
            parts = channel_id.split("_")
            if len(parts) != 2:
                raise ConnectorError(f"ID de canal inválido: {channel_id}")
            
            channel_num = parts[0]
            stream_type = parts[1]
            
            # Validar
            if not channel_num.isdigit() or not stream_type.isdigit():
                raise ConnectorError(f"ID de canal inválido: {channel_id}")
            
            # Construir URL
            url = f"rtsp://{self.username}:{self.password}@{self.ip_address}:{self.rtsp_port}/Streaming/Channels/{channel_num}0{stream_type}"
            
            return url
        
        except Exception as e:
            raise ConnectorError(f"Erro ao obter URL do stream Hikvision: {str(e)}")
    
    async def snapshot(self, channel_id: str) -> bytes:
        """
        Obtém uma imagem instantânea de um canal.
        
        Args:
            channel_id: ID do canal (formato: "CANAL_STREAM", ex: "1_1")
            
        Returns:
            bytes: Dados da imagem
            
        Raises:
            ConnectorError: Se ocorrer um erro ao obter a imagem
        """
        if not self.is_connected:
            await self.connect()
        
        try:
            # Extrair número do canal
            parts = channel_id.split("_")
            channel_num = parts[0]
            
            # URL para snapshot
            url = f"{self.base_url}/ISAPI/Streaming/channels/{channel_num}01/picture"
            
            # Obter snapshot
            async with self.session.get(
                url, 
                timeout=self.timeout,
                ssl=False if self.use_https else None
            ) as response:
                if response.status != 200:
                    raise ConnectorError(f"Erro ao obter snapshot: HTTP {response.status}")
                
                return await response.read()
        
        except Exception as e:
            raise ConnectorError(f"Erro ao obter snapshot Hikvision: {str(e)}")
    
    @staticmethod
    async def scan_network(subnet: str, port: int = 80, timeout: float = 0.5) -> List[Dict[str, Any]]:
        """
        Escaneia a rede em busca de dispositivos Hikvision.
        
        Args:
            subnet: Endereço de rede (formato: "192.168.1")
            port: Porta a ser verificada (padrão: 80)
            timeout: Tempo limite em segundos para cada tentativa
            
        Returns:
            List[Dict[str, Any]]: Lista de dispositivos encontrados
        """
        devices = []
        
        # Tenta se conectar a cada IP na sub-rede
        for i in range(1, 255):
            ip = f"{subnet}.{i}"
            
            try:
                # Verificar se responde na porta especificada
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(ip, port),
                    timeout=timeout
                )
                
                writer.close()
                await writer.wait_closed()
                
                # Verificar se é um dispositivo Hikvision
                url = f"http://{ip}/ISAPI/System/deviceInfo"
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.get(url, timeout=timeout) as response:
                            if response.status == 401:  # Autenticação necessária (típico para Hikvision)
                                devices.append({
                                    "ip": ip,
                                    "port": port,
                                    "type": "hikvision",
                                    "requires_auth": True
                                })
                            elif response.status == 200:
                                # Sucesso sem autenticação (raro)
                                xml_text = await response.text()
                                if "<deviceType>" in xml_text and "<model>" in xml_text:
                                    devices.append({
                                        "ip": ip,
                                        "port": port,
                                        "type": "hikvision",
                                        "requires_auth": False
                                    })
                    except:
                        # Se houve timeout ou outro erro, ignore
                        pass
            
            except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
                # Ignora erros de timeout e conexão recusada
                pass
        
        return devices 