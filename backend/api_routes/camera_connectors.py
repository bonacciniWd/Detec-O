import requests
import logging
from typing import Dict, List, Optional, Any
from enum import Enum
import json
import base64
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

# Configurar logging
logger = logging.getLogger(__name__)

class ConnectorType(Enum):
    ONVIF = "onvif"
    HIKVISION = "hikvision"
    INTELBRAS = "intelbras"
    GENERIC = "generic"

class CameraConnector:
    """Classe base abstrata para conectores de câmeras"""
    def __init__(self, camera_config: Dict[str, Any]):
        self.camera_config = camera_config
        self.name = camera_config.get("name", "Câmera")
        self.ip = camera_config.get("ip_address", "")
        self.port = camera_config.get("port", 80)
        self.username = camera_config.get("username", "")
        self.password = camera_config.get("password", "")
        self.location = camera_config.get("location", "")
        self.connector_type = camera_config.get("connector_type", "generic")
        self.session = requests.Session()
        self.authenticated = False
        self.session_token = None

    async def connect(self) -> bool:
        """Estabelece conexão com a câmera"""
        raise NotImplementedError("Método abstrato")

    async def get_snapshot(self) -> Optional[bytes]:
        """Obtém um snapshot da câmera"""
        raise NotImplementedError("Método abstrato")

    async def get_stream_url(self, stream_type="main") -> Optional[str]:
        """Obtém URL do stream da câmera"""
        raise NotImplementedError("Método abstrato")

    async def get_device_info(self) -> Dict[str, Any]:
        """Obtém informações do dispositivo"""
        raise NotImplementedError("Método abstrato")

    async def ptz_move(self, direction: str, speed: float = 0.5) -> bool:
        """Controla o movimento PTZ da câmera"""
        raise NotImplementedError("Método abstrato")

    async def ptz_stop(self) -> bool:
        """Para o movimento PTZ da câmera"""
        raise NotImplementedError("Método abstrato")

class IntelbrasConnector(CameraConnector):
    """Implementação do conector para câmeras Intelbras"""
    
    def __init__(self, camera_config: Dict[str, Any]):
        super().__init__(camera_config)
        self.base_url = f"http://{self.ip}:{self.port}"
        self.api_version = camera_config.get("api_version", "1.0")
        self.digest_auth = requests.auth.HTTPDigestAuth(self.username, self.password)
        
    async def connect(self) -> bool:
        """Estabelece conexão com a câmera Intelbras"""
        try:
            # Verificar se a câmera está acessível e autenticar
            url = f"{self.base_url}/cgi-bin/deviceInfo.cgi?action=getDeviceInfo"
            response = self.session.get(url, auth=self.digest_auth, timeout=10)
            
            if response.status_code == 200:
                self.authenticated = True
                logger.info(f"Conexão estabelecida com câmera Intelbras: {self.name} ({self.ip})")
                
                # Extrair informações básicas da resposta
                try:
                    device_info = self._parse_device_info(response.text)
                    self.camera_config.update({
                        "model": device_info.get("deviceType", ""),
                        "serial": device_info.get("serialNumber", ""),
                        "firmware": device_info.get("firmwareVersion", "")
                    })
                except Exception as e:
                    logger.warning(f"Erro ao processar informações do dispositivo: {str(e)}")
                
                return True
            else:
                logger.error(f"Falha na autenticação com câmera Intelbras: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao conectar com câmera Intelbras {self.name} ({self.ip}): {str(e)}")
            return False
    
    def _parse_device_info(self, info_text: str) -> Dict[str, str]:
        """Processa a resposta de texto de deviceInfo.cgi para um dicionário"""
        result = {}
        lines = info_text.strip().split('\n')
        
        for line in lines:
            if '=' in line:
                key, value = line.split('=', 1)
                result[key.strip()] = value.strip()
                
        return result
    
    async def get_snapshot(self) -> Optional[bytes]:
        """Obtém um snapshot da câmera Intelbras"""
        if not self.authenticated:
            if not await self.connect():
                return None
        
        try:
            # URL para snapshot nas câmeras Intelbras
            url = f"{self.base_url}/cgi-bin/snapshot.cgi"
            response = self.session.get(url, auth=self.digest_auth, timeout=10)
            
            if response.status_code == 200 and response.headers.get('content-type', '').startswith('image/'):
                return response.content
            else:
                logger.error(f"Erro ao obter snapshot da câmera Intelbras {self.name}: Status {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao obter snapshot da câmera Intelbras {self.name}: {str(e)}")
            self.authenticated = False  # Reset para forçar reconexão na próxima tentativa
            return None
    
    async def get_stream_url(self, stream_type="main") -> Optional[str]:
        """
        Obtém URL do stream RTSP da câmera Intelbras
        stream_type: 'main' (principal) ou 'sub' (secundário)
        """
        if not self.authenticated and not await self.connect():
            return None
            
        try:
            # Formato da URL RTSP para câmeras Intelbras
            channel = self.camera_config.get("channel", 1)
            stream_id = 0 if stream_type == "main" else 1
            
            # Construir URL RTSP padrão da Intelbras
            rtsp_url = f"rtsp://{self.username}:{self.password}@{self.ip}:{self.port}/cam/realmonitor?channel={channel}&subtype={stream_id}"
            
            return rtsp_url
            
        except Exception as e:
            logger.error(f"Erro ao obter URL do stream da câmera Intelbras {self.name}: {str(e)}")
            return None
    
    async def get_device_info(self) -> Dict[str, Any]:
        """Obtém informações detalhadas do dispositivo Intelbras"""
        if not self.authenticated and not await self.connect():
            return {}
        
        try:
            # URL para informações do dispositivo
            url = f"{self.base_url}/cgi-bin/deviceInfo.cgi?action=getDeviceInfo"
            response = self.session.get(url, auth=self.digest_auth, timeout=10)
            
            if response.status_code == 200:
                device_info = self._parse_device_info(response.text)
                
                # Formatação da resposta para o formato padrão da API
                return {
                    "manufacturer": "Intelbras",
                    "model": device_info.get("deviceType", ""),
                    "firmware_version": device_info.get("firmwareVersion", ""),
                    "serial_number": device_info.get("serialNumber", ""),
                    "hardware_id": device_info.get("hardwareId", ""),
                    "ip_address": self.ip,
                    "mac_address": device_info.get("mac", ""),
                    "channels": int(device_info.get("channelNumber", 1))
                }
            else:
                logger.error(f"Erro ao obter informações do dispositivo: {response.status_code}")
                return {"error": f"Status code: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Erro ao obter informações do dispositivo: {str(e)}")
            return {"error": str(e)}
            
    async def ptz_move(self, direction: str, speed: float = 0.5) -> bool:
        """
        Controla o movimento PTZ da câmera Intelbras
        direction: 'up', 'down', 'left', 'right'
        speed: valor de 0 a 1
        """
        if not self.authenticated and not await self.connect():
            return False
            
        # Ajustar o range de velocidade para o formato da API Intelbras (1-8)
        ptz_speed = max(1, min(8, int(speed * 8)))
        
        # Mapear direção para os comandos da API Intelbras
        direction_map = {
            "up": 0,
            "down": 1,
            "left": 2,
            "right": 3,
            "upleft": 4,
            "upright": 5,
            "downleft": 6,
            "downright": 7
        }
        
        if direction.lower() not in direction_map:
            logger.error(f"Direção PTZ inválida: {direction}")
            return False
            
        try:
            channel = self.camera_config.get("channel", 1)
            ptz_command = direction_map[direction.lower()]
            
            # URL para controle PTZ
            url = (f"{self.base_url}/cgi-bin/ptz.cgi?action=start"
                  f"&channel={channel}&code={ptz_command}&arg1=0&arg2={ptz_speed}")
                  
            response = self.session.get(url, auth=self.digest_auth, timeout=10)
            
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Erro ao controlar PTZ: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao controlar movimento PTZ: {str(e)}")
            return False
            
    async def ptz_stop(self) -> bool:
        """Para o movimento PTZ da câmera Intelbras"""
        if not self.authenticated and not await self.connect():
            return False
            
        try:
            channel = self.camera_config.get("channel", 1)
            
            # URL para parar movimento PTZ
            url = f"{self.base_url}/cgi-bin/ptz.cgi?action=stop&channel={channel}"
            response = self.session.get(url, auth=self.digest_auth, timeout=10)
            
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Erro ao parar PTZ: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao parar movimento PTZ: {str(e)}")
            return False

# Factory para criar o conector apropriado baseado no tipo
def create_camera_connector(camera_config: Dict[str, Any]) -> Optional[CameraConnector]:
    """
    Cria uma instância do conector apropriado baseado no tipo de câmera.
    Suporta ONVIF, Hikvision, Intelbras e Genérico.
    """
    connector_type = camera_config.get("connector_type", "generic").lower()
    
    if connector_type == "intelbras":
        return IntelbrasConnector(camera_config)
    elif connector_type == "hikvision":
        # Implementação para Hikvision seria aqui
        return None  # Temporariamente retorna None até ser implementado
    elif connector_type == "onvif":
        # Implementação para ONVIF seria aqui
        return None  # Temporariamente retorna None até ser implementado
    else:
        # Implementação para conector genérico seria aqui
        return None  # Temporariamente retorna None até ser implementado 