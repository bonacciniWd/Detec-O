"""
Modelos Pydantic para validação e serialização
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime

# ---- Schemas para Usuários ----

class UserBase(BaseModel):
    """Modelo base para usuários"""
    username: str
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    """Modelo para criação de usuários"""
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    """Modelo para login de usuários"""
    username: str
    password: str

class UserResponse(UserBase):
    """Modelo para resposta de usuários"""
    id: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True  # Para compatibilidade com SQLAlchemy

class UserUpdate(BaseModel):
    """Modelo para atualização de usuários"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None

# ---- Schemas para Autenticação ----

class Token(BaseModel):
    """Modelo para token de acesso"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400  # 24 horas em segundos

class TokenPayload(BaseModel):
    """Modelo para payload do token"""
    sub: Optional[str] = None
    exp: Optional[int] = None

# ---- Schemas para Câmeras ----

class CameraBase(BaseModel):
    """Modelo base para entrada de dados de câmeras (conexão local)."""
    name: str = Field(..., description="Nome descritivo da câmera")
    # Campos para conexão local
    ip_address: str = Field(..., description="Endereço IP local da câmera/NVR")
    rtsp_port: int = Field(default=554, description="Porta RTSP da câmera/NVR (geralmente 554)")
    rtsp_path: str = Field(..., description="Caminho do stream RTSP (ex: /cam/realmonitor?channel=1&subtype=0)")
    # Credenciais (opcionais)
    username: Optional[str] = Field(default=None, description="Usuário para autenticação RTSP (se necessário)")
    password: Optional[str] = Field(default=None, description="Senha para autenticação RTSP (se necessário)")
    # Campos adicionais 
    location: Optional[str] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    connector_type: Optional[str] = "rtsp" 
    detection_enabled: Optional[bool] = True
    detection_confidence: Optional[float] = 0.5
    detection_objects: Optional[List[str]] = ["person", "car", "bicycle"]

class CameraCreate(CameraBase):
    """Modelo para criação de câmeras (herda de CameraBase)"""
    pass

class CameraResponse(BaseModel):
    """Modelo para resposta de câmeras (reflete models.Camera)."""
    id: str
    name: str
    owner_id: str
    ip_address: Optional[str] = None 
    port: Optional[int] = None 
    rtsp_url: Optional[str] = None 
    username: Optional[str] = None 
    location: Optional[str] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    connector_type: Optional[str] = None
    detection_enabled: Optional[bool] = None
    detection_confidence: Optional[float] = None
    detection_objects: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    last_event_image_path: Optional[str] = None
    
    class Config:
        from_attributes = True 

class CameraUpdate(BaseModel):
    """Modelo para atualização de câmeras (geralmente campos não-conexão)"""
    name: Optional[str] = None
    location: Optional[str] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    connector_type: Optional[str] = None
    detection_enabled: Optional[bool] = None
    detection_confidence: Optional[float] = None
    detection_objects: Optional[List[str]] = None

# ---- Schemas para Configurações de Detecção ----

class DetectionSettingsBase(BaseModel):
    enabled: bool = True
    confidence_threshold: float = Field(default=0.5, ge=0.1, le=1.0)
    iou_threshold: float = Field(default=0.45, ge=0.1, le=1.0)
    detect_objects: bool = True
    # detect_behaviors: bool = False # Comentado se não for usar agora
    detection_interval: int = Field(default=5, ge=1) # Em frames
    # alert_on_detection: bool = True # Comentado se não for usar agora
    object_classes: List[str] = ["person", "car", "bicycle"] # Classes padrão
    # behavior_classes: List[str] = [] # Comentado se não for usar agora

class DetectionSettingsResponse(DetectionSettingsBase):
    # Poderia adicionar campos extras se necessário ao retornar
    camera_id: str
    
    class Config:
        from_attributes = True

class DetectionSettingsUpdate(DetectionSettingsBase):
    # Todos os campos são opcionais na atualização (PATCH), 
    # mas para PUT, o frontend deve enviar todos.
    pass

# ---- Schemas para Eventos de Detecção ----

class DetectionEventBase(BaseModel):
    """Modelo base para eventos de detecção"""
    event_type: str
    confidence: float
    detected_class: str
    bounding_box: Optional[Dict[str, float]] = None
    image_path: Optional[str] = None
    video_path: Optional[str] = None

class DetectionEventCreate(DetectionEventBase):
    """Modelo para criação de eventos de detecção"""
    camera_id: str

class DetectionEventResponse(DetectionEventBase):
    """Modelo para resposta de eventos de detecção"""
    id: str
    camera_id: str
    timestamp: datetime
    
    class Config:
        from_attributes = True 

# ---- Schemas para Configurações de IA ----

class AISettingsBase(BaseModel):
    enabled: bool = True
    model_id: Optional[str] = "yolov8n.pt" # Exemplo de ID/nome padrão
    confidence_threshold: float = Field(default=0.4, ge=0.1, le=0.9)
    use_gpu: bool = True
    enable_tracking: bool = False # Tracking pode ser pesado, desativado por padrão

class AISettingsResponse(AISettingsBase):
    camera_id: str

    class Config:
        from_attributes = True

class AISettingsUpdate(BaseModel):
    # Permitir atualização parcial (PATCH pode ser melhor, mas PUT é mais simples por ora)
    enabled: Optional[bool] = None
    model_id: Optional[str] = None 
    confidence_threshold: Optional[float] = Field(default=None, ge=0.1, le=0.9)
    use_gpu: Optional[bool] = None
    enable_tracking: Optional[bool] = None 

# ---- Schemas para Status de Processamento ----

class ProcessorStatus(BaseModel):
    camera_id: str
    is_running: bool
    rtsp_url: Optional[str] = None
    last_error: Optional[str] = None
    # Adicionar outros campos se get_status() retornar mais infos 