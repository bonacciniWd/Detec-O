"""
Roteador para descoberta e gerenciamento de dispositivos de vídeo (DVRs, NVRs, câmeras IP).

Este módulo fornece endpoints para:
1. Descoberta automática de dispositivos na rede
2. Conexão e gerenciamento de dispositivos
3. Listagem e acesso a streams de vídeo
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Body, Response
from fastapi.security import OAuth2PasswordBearer
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
import asyncio
import logging
import time

from ..auth.dependencies import get_current_user
from ..models.user import User
from ..models.camera import Camera
from ..services.connectors.discovery import discover_devices
from ..services.connectors.factory import ConnectorFactory, register_connector
from ..services.connectors.base import ConnectorError
from ..database import get_db
from sqlalchemy.orm import Session

# Modelos de dados para API

class SubnetInfo(BaseModel):
    subnet: str = Field(..., description="Subnet in CIDR notation (e.g. 192.168.1.0/24)")
    description: Optional[str] = Field(None, description="Optional description")

class DiscoveryRequest(BaseModel):
    discovery_methods: List[str] = Field(default=["auto"], description="Discovery methods to use")
    subnets: Optional[List[str]] = Field(None, description="List of subnets to scan")
    timeout: float = Field(default=5.0, description="Timeout in seconds")

class DeviceDiscoveryResult(BaseModel):
    id: str = Field(..., description="Unique ID for the discovered device")
    ip_address: str = Field(..., description="IP address")
    port: int = Field(..., description="Port number")
    device_type: str = Field(..., description="Type of device (onvif, hikvision, dahua, etc.)")
    name: Optional[str] = Field(None, description="Device name if available")
    model: Optional[str] = Field(None, description="Device model if available")
    manufacturer: Optional[str] = Field(None, description="Manufacturer if available")
    requires_auth: bool = Field(default=True, description="Whether authentication is required")
    discovery_method: str = Field(..., description="Method used to discover this device")
    discovered_at: datetime = Field(..., description="When the device was discovered")
    status: str = Field(..., description="Device status (discovered, online, etc.)")

class ConnectDeviceRequest(BaseModel):
    ip_address: str = Field(..., description="Device IP address")
    port: int = Field(..., description="Device port")
    device_type: str = Field(..., description="Device type (onvif, hikvision, dahua, etc.)")
    username: str = Field(..., description="Username for authentication")
    password: str = Field(..., description="Password for authentication")
    name: Optional[str] = Field(None, description="Custom name for the device")
    rtsp_port: Optional[int] = Field(None, description="RTSP port (if different from default)")
    use_https: Optional[bool] = Field(False, description="Use HTTPS instead of HTTP")
    additional_params: Optional[Dict[str, Any]] = Field(None, description="Additional connector parameters")

class StreamInfo(BaseModel):
    id: str = Field(..., description="Stream ID")
    name: str = Field(..., description="Stream name")
    url: str = Field(..., description="Stream URL")
    type: str = Field(..., description="Stream type (rtsp, http, etc.)")
    channel: int = Field(..., description="Channel number")
    resolution: Optional[str] = Field(None, description="Stream resolution if available")
    fps: Optional[int] = Field(None, description="Frames per second if available")
    encoding: Optional[str] = Field(None, description="Video encoding (H.264, H.265, etc.)")
    ptz_capable: bool = Field(default=False, description="Whether PTZ is supported")
    audio_capable: bool = Field(default=False, description="Whether audio is supported")
    device_id: str = Field(..., description="ID of the device this stream belongs to")

class DeviceInfo(BaseModel):
    id: str = Field(..., description="Device ID")
    name: str = Field(..., description="Device name")
    model: Optional[str] = Field(None, description="Device model")
    manufacturer: str = Field(..., description="Device manufacturer")
    ip_address: str = Field(..., description="IP address")
    port: int = Field(..., description="Port")
    firmware: Optional[str] = Field(None, description="Firmware version")
    serial_number: Optional[str] = Field(None, description="Serial number")
    channels: int = Field(default=1, description="Number of channels")
    status: str = Field(..., description="Device status")
    last_seen: Optional[datetime] = Field(None, description="When the device was last seen")
    capabilities: Dict[str, Any] = Field(default_factory=dict, description="Device capabilities")

class AISettingsBase(BaseModel):
    enabled: bool
    model_id: Optional[str]
    confidence_threshold: float
    use_gpu: bool
    enable_tracking: bool

class AISettingsUpdate(BaseModel):
    enabled: bool
    model_id: Optional[str]
    confidence_threshold: float
    use_gpu: bool
    enable_tracking: bool

# Cache temporário para dispositivos descobertos
# Na implementação real, isso deve ser movido para um armazenamento persistente ou Redis
discovered_devices: Dict[str, Any] = {}
connected_devices: Dict[str, Any] = {}

# Configurar router
router = APIRouter(prefix="/devices", tags=["devices"])

# Rotas para descoberta e gerenciamento de dispositivos

@router.post("/discover", response_model=List[DeviceDiscoveryResult])
async def discover_network_devices(
    discovery_request: DiscoveryRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Descobre dispositivos de vídeo na rede local.
    
    Inicia uma tarefa em segundo plano para descobrir dispositivos e retorna
    dispositivos já descobertos anteriormente enquanto a busca continua.
    """
    # Iniciar descoberta em segundo plano
    background_tasks.add_task(
        run_discovery, 
        discovery_request.discovery_methods, 
        discovery_request.subnets,
        discovery_request.timeout
    )
    
    # Retornar dispositivos já descobertos
    results = []
    for device_id, device in discovered_devices.items():
        # Converter para o modelo de resposta
        try:
            result = DeviceDiscoveryResult(
                id=device_id,
                ip_address=device["ip"],
                port=device["port"],
                device_type=device.get("device_type", "unknown"),
                name=device.get("device_name"),
                model=device.get("model"),
                manufacturer=get_manufacturer_for_type(device.get("device_type", "unknown")),
                requires_auth=device.get("requires_auth", True),
                discovery_method=device.get("discovery_method", "unknown"),
                discovered_at=datetime.fromisoformat(device["discovered_at"]) 
                    if isinstance(device["discovered_at"], str) 
                    else device["discovered_at"],
                status=device.get("status", "discovered")
            )
            results.append(result)
        except Exception as e:
            logging.error(f"Erro ao converter dispositivo descoberto: {str(e)}")
    
    return results

@router.get("/discovery-status", response_model=Dict[str, Any])
async def get_discovery_status(current_user: User = Depends(get_current_user)):
    """
    Retorna o status atual da descoberta de dispositivos.
    
    Inclui dispositivos descobertos e informações sobre a operação em andamento.
    """
    return {
        "discovery_running": is_discovery_running(),
        "devices_count": len(discovered_devices),
        "last_discovery": get_last_discovery_time()
    }

@router.post("/connect", response_model=DeviceInfo)
async def connect_to_device(
    connect_request: ConnectDeviceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Conecta a um dispositivo, obtém informações e salva no banco de dados.
    
    Ao conectar com sucesso, o dispositivo é automaticamente adicionado aos
    dispositivos do usuário atual.
    """
    try:
        # Criar objeto de configuração do conector
        config = {
            "ip_address": connect_request.ip_address,
            "port": connect_request.port,
            "username": connect_request.username,
            "password": connect_request.password,
            "type": connect_request.device_type
        }
        
        # Adicionar parâmetros opcionais
        if connect_request.rtsp_port:
            config["rtsp_port"] = connect_request.rtsp_port
        
        if connect_request.use_https:
            config["use_https"] = connect_request.use_https
        
        if connect_request.additional_params:
            config.update(connect_request.additional_params)
        
        # Criar conector
        connector = ConnectorFactory.create_from_config(config)
        
        # Conectar ao dispositivo
        await connector.connect()
        
        # Obter informações do dispositivo
        device_info = await connector.get_device_info()
        
        # Se o nome foi fornecido, substituir o original
        if connect_request.name:
            device_info.name = connect_request.name
        
        # Salvar informações do dispositivo
        # Verificar se o dispositivo já existe para este usuário
        existing_camera = db.query(Camera).filter(
            Camera.ip_address == connect_request.ip_address,
            Camera.user_id == current_user.id
        ).first()
        
        if existing_camera:
            # Atualizar dispositivo existente
            existing_camera.name = device_info.name
            existing_camera.model = device_info.model
            existing_camera.manufacturer = device_info.manufacturer
            existing_camera.port = connect_request.port
            existing_camera.username = connect_request.username
            existing_camera.password = connect_request.password
            existing_camera.connector_type = connect_request.device_type
            existing_camera.status = "online"
            existing_camera.last_connection = datetime.now()
            
            # Serializar configurações adicionais
            config_dict = {
                "rtsp_port": connect_request.rtsp_port,
                "use_https": connect_request.use_https
            }
            if connect_request.additional_params:
                config_dict.update(connect_request.additional_params)
            
            existing_camera.config = config_dict
            
            db.commit()
            db.refresh(existing_camera)
            
            device_id = str(existing_camera.id)
        else:
            # Criar novo dispositivo
            new_camera = Camera(
                name=device_info.name,
                model=device_info.model or "Unknown",
                manufacturer=device_info.manufacturer,
                ip_address=connect_request.ip_address,
                port=connect_request.port,
                username=connect_request.username,
                password=connect_request.password,
                connector_type=connect_request.device_type,
                status="online",
                last_connection=datetime.now(),
                user_id=current_user.id
            )
            
            # Serializar configurações adicionais
            config_dict = {
                "rtsp_port": connect_request.rtsp_port,
                "use_https": connect_request.use_https
            }
            if connect_request.additional_params:
                config_dict.update(connect_request.additional_params)
            
            new_camera.config = config_dict
            
            db.add(new_camera)
            db.commit()
            db.refresh(new_camera)
            
            device_id = str(new_camera.id)
        
        # Atualizar ID com o do banco de dados
        device_info.id = device_id
        
        # Adicionar dispositivo ao cache de dispositivos conectados
        connected_devices[device_id] = connector
        
        # Desconectar após uso
        await connector.disconnect()
        
        return device_info
    
    except ConnectorError as e:
        raise HTTPException(status_code=400, detail=f"Erro ao conectar: {str(e)}")
    
    except Exception as e:
        logging.error(f"Erro ao conectar ao dispositivo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao conectar ao dispositivo")

@router.get("/", response_model=List[DeviceInfo])
async def list_user_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lista todos os dispositivos do usuário atual.
    """
    try:
        # Buscar câmeras do usuário
        user_cameras = db.query(Camera).filter(Camera.user_id == current_user.id).all()
        
        # Converter para modelo de resposta
        results = []
        for camera in user_cameras:
            device_info = DeviceInfo(
                id=str(camera.id),
                name=camera.name,
                model=camera.model,
                manufacturer=camera.manufacturer,
                ip_address=camera.ip_address,
                port=camera.port,
                firmware=camera.config.get("firmware"),
                serial_number=camera.config.get("serial_number"),
                channels=camera.config.get("channels", 1),
                status=camera.status,
                last_seen=camera.last_connection,
                capabilities=camera.config.get("capabilities", {})
            )
            results.append(device_info)
        
        return results
    
    except Exception as e:
        logging.error(f"Erro ao listar dispositivos: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao listar dispositivos")

@router.get("/{device_id}", response_model=DeviceInfo)
async def get_device_info(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtém informações detalhadas sobre um dispositivo específico.
    """
    try:
        # Buscar câmera do usuário
        camera = db.query(Camera).filter(
            Camera.id == device_id,
            Camera.user_id == current_user.id
        ).first()
        
        if not camera:
            raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
        
        # Converter para modelo de resposta
        device_info = DeviceInfo(
            id=str(camera.id),
            name=camera.name,
            model=camera.model,
            manufacturer=camera.manufacturer,
            ip_address=camera.ip_address,
            port=camera.port,
            firmware=camera.config.get("firmware"),
            serial_number=camera.config.get("serial_number"),
            channels=camera.config.get("channels", 1),
            status=camera.status,
            last_seen=camera.last_connection,
            capabilities=camera.config.get("capabilities", {})
        )
        
        return device_info
    
    except HTTPException:
        raise
    
    except Exception as e:
        logging.error(f"Erro ao obter informações do dispositivo: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao obter informações do dispositivo")

@router.get("/{device_id}/streams", response_model=List[StreamInfo])
async def list_device_streams(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lista todos os streams disponíveis em um dispositivo específico.
    """
    try:
        # Verificar propriedade da câmera
        camera = db.query(Camera).filter(
            Camera.id == device_id,
            Camera.user_id == current_user.id
        ).first()
        
        if not camera:
            raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
        
        # Configurar conector
        config = {
            "ip_address": camera.ip_address,
            "port": camera.port,
            "username": camera.username,
            "password": camera.password,
            "type": camera.connector_type
        }
        
        # Adicionar configurações extras
        if camera.config:
            config.update(camera.config)
        
        # Criar conector
        connector = ConnectorFactory.create_from_config(config)
        
        # Conectar e listar streams
        await connector.connect()
        streams = await connector.list_streams()
        await connector.disconnect()
        
        # Converter para modelo de resposta
        results = []
        for stream in streams:
            stream_info = StreamInfo(
                id=stream.id,
                name=stream.name,
                url=stream.url,
                type=stream.type,
                channel=stream.channel,
                resolution=stream.resolution,
                fps=stream.fps,
                encoding=stream.encoding,
                ptz_capable=stream.ptz_capable,
                audio_capable=stream.audio_capable,
                device_id=device_id
            )
            results.append(stream_info)
        
        return results
    
    except ConnectorError as e:
        raise HTTPException(status_code=400, detail=f"Erro ao listar streams: {str(e)}")
    
    except HTTPException:
        raise
    
    except Exception as e:
        logging.error(f"Erro ao listar streams: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao listar streams")

@router.get("/{device_id}/snapshot/{stream_id}", response_class=Response)
async def get_stream_snapshot(
    device_id: str,
    stream_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtém uma imagem instantânea de um stream específico.
    
    Retorna a imagem como um arquivo binário.
    """
    try:
        # Verificar propriedade da câmera
        camera = db.query(Camera).filter(
            Camera.id == device_id,
            Camera.user_id == current_user.id
        ).first()
        
        if not camera:
            raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
        
        # Configurar conector
        config = {
            "ip_address": camera.ip_address,
            "port": camera.port,
            "username": camera.username,
            "password": camera.password,
            "type": camera.connector_type
        }
        
        # Adicionar configurações extras
        if camera.config:
            config.update(camera.config)
        
        # Criar conector
        connector = ConnectorFactory.create_from_config(config)
        
        # Conectar e obter snapshot
        await connector.connect()
        
        try:
            image_data = await connector.snapshot(stream_id)
            
            # Atualizar timestamp da última conexão
            camera.last_connection = datetime.now()
            camera.status = "online"
            db.commit()
            
            # Retornar a imagem como resposta binária
            return Response(
                content=image_data,
                media_type="image/jpeg"
            )
        finally:
            # Garantir que desconectamos mesmo em caso de erro
            await connector.disconnect()
    
    except ConnectorError as e:
        logging.error(f"Erro ao obter snapshot: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Erro ao obter snapshot: {str(e)}")
    
    except HTTPException:
        raise
    
    except Exception as e:
        logging.error(f"Erro ao obter snapshot: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao obter snapshot")

# Novo endpoint para obter snapshot com cache (para atualização periódica)
@router.get("/{device_id}/cached-snapshot/{stream_id}", response_class=Response)
async def get_cached_stream_snapshot(
    device_id: str,
    stream_id: str,
    max_age: int = Query(30, description="Idade máxima do cache em segundos"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtém uma imagem instantânea de um stream específico, com suporte a cache.
    
    Se houver um snapshot recente no cache (conforme definido por max_age), o cache é usado.
    Caso contrário, um novo snapshot é obtido.
    
    Args:
        device_id: ID do dispositivo
        stream_id: ID do stream
        max_age: Idade máxima do cache em segundos (padrão: 30)
    
    Returns:
        Imagem em formato JPEG
    """
    # Cache de snapshots (para dispositivo_stream -> (timestamp, dados))
    # Normalmente, isso seria implementado com Redis em produção
    global snapshot_cache
    if 'snapshot_cache' not in globals():
        snapshot_cache = {}
    
    cache_key = f"{device_id}_{stream_id}"
    
    # Verificar se há cache válido
    if cache_key in snapshot_cache:
        timestamp, image_data = snapshot_cache[cache_key]
        age = time.time() - timestamp
        
        if age < max_age:
            # Retornar do cache
            return Response(
                content=image_data,
                media_type="image/jpeg",
                headers={"X-Cache": "HIT", "X-Cache-Age": str(int(age))}
            )
    
    # Nenhum cache válido, obter novo snapshot
    try:
        # Verificar propriedade da câmera
        camera = db.query(Camera).filter(
            Camera.id == device_id,
            Camera.user_id == current_user.id
        ).first()
        
        if not camera:
            raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
        
        # Configurar conector
        config = {
            "ip_address": camera.ip_address,
            "port": camera.port,
            "username": camera.username,
            "password": camera.password,
            "type": camera.connector_type
        }
        
        # Adicionar configurações extras
        if camera.config:
            config.update(camera.config)
        
        # Criar conector
        connector = ConnectorFactory.create_from_config(config)
        
        # Conectar e obter snapshot
        await connector.connect()
        
        try:
            image_data = await connector.snapshot(stream_id)
            
            # Atualizar timestamp da última conexão
            camera.last_connection = datetime.now()
            camera.status = "online"
            db.commit()
            
            # Armazenar no cache
            snapshot_cache[cache_key] = (time.time(), image_data)
            
            # Retornar a imagem como resposta binária
            return Response(
                content=image_data,
                media_type="image/jpeg",
                headers={"X-Cache": "MISS"}
            )
        finally:
            # Garantir que desconectamos mesmo em caso de erro
            await connector.disconnect()
    
    except ConnectorError as e:
        logging.error(f"Erro ao obter snapshot: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Erro ao obter snapshot: {str(e)}")
    
    except HTTPException:
        raise
    
    except Exception as e:
        logging.error(f"Erro ao obter snapshot: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao obter snapshot")

@router.get("/{device_id}/ai-settings", response_model=AISettingsBase)
async def get_camera_ai_settings(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtém as configurações de IA para uma câmera específica.
    """
    try:
        # Verificar se a câmera existe e pertence ao usuário
        camera = db.query(Camera).filter(
            Camera.id == device_id,
            Camera.user_id == current_user.id
        ).first()
        
        if not camera:
            raise HTTPException(status_code=404, detail="Câmera não encontrada")
        
        # Retornar configurações de IA
        return {
            "enabled": camera.ai_enabled,
            "model_id": camera.ai_model_id,
            "confidence_threshold": camera.ai_confidence_threshold,
            "use_gpu": camera.ai_use_gpu,
            "enable_tracking": camera.ai_enable_tracking
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Erro ao obter configurações de IA: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao obter configurações de IA")

@router.put("/{device_id}/ai-settings", response_model=AISettingsBase)
async def update_camera_ai_settings(
    device_id: str,
    settings: AISettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Atualiza as configurações de IA para uma câmera específica.
    """
    try:
        # Verificar se a câmera existe e pertence ao usuário
        camera = db.query(Camera).filter(
            Camera.id == device_id,
            Camera.user_id == current_user.id
        ).first()
        
        if not camera:
            raise HTTPException(status_code=404, detail="Câmera não encontrada")
        
        # Verificar se o modelo existe, caso seja especificado
        if settings.model_id:
            model = db.query(AIModel).filter(AIModel.id == settings.model_id).first()
            if not model:
                raise HTTPException(status_code=404, detail="Modelo de IA não encontrado")
        
        # Atualizar configurações
        camera.ai_enabled = settings.enabled
        if settings.model_id:
            camera.ai_model_id = settings.model_id
        camera.ai_confidence_threshold = settings.confidence_threshold
        camera.ai_use_gpu = settings.use_gpu
        camera.ai_enable_tracking = settings.enable_tracking
        
        db.commit()
        db.refresh(camera)
        
        # Retornar configurações atualizadas
        return {
            "enabled": camera.ai_enabled,
            "model_id": camera.ai_model_id,
            "confidence_threshold": camera.ai_confidence_threshold,
            "use_gpu": camera.ai_use_gpu,
            "enable_tracking": camera.ai_enable_tracking
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Erro ao atualizar configurações de IA: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao atualizar configurações de IA")

# Funções de utilidade

def get_manufacturer_for_type(device_type: str) -> str:
    """Determina o fabricante com base no tipo de dispositivo."""
    if device_type == "hikvision":
        return "Hikvision"
    elif device_type == "dahua":
        return "Dahua"
    elif device_type == "onvif":
        return "Generic ONVIF"
    else:
        return "Unknown"

# Variáveis de controle de descoberta
discovery_running = False
last_discovery_time = None

def is_discovery_running() -> bool:
    """Verifica se a descoberta está em andamento."""
    global discovery_running
    return discovery_running

def get_last_discovery_time() -> Optional[datetime]:
    """Retorna o momento da última descoberta."""
    global last_discovery_time
    return last_discovery_time

async def run_discovery(methods: List[str], subnets: Optional[List[str]], timeout: float):
    """Executa a descoberta em segundo plano."""
    global discovery_running, last_discovery_time, discovered_devices
    
    if discovery_running:
        return
    
    try:
        discovery_running = True
        
        # Executar descoberta
        devices = await discover_devices(
            discovery_methods=methods,
            subnets=subnets,
            timeout=timeout
        )
        
        # Atualizar cache de dispositivos descobertos
        for device in devices:
            device_id = str(uuid.uuid4())
            device["id"] = device_id
            discovered_devices[device_id] = device
        
        last_discovery_time = datetime.now()
    
    except Exception as e:
        logging.error(f"Erro durante descoberta: {str(e)}")
    
    finally:
        discovery_running = False 