from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
import uuid

from ..database import Base

class CameraBase(BaseModel):
    """Modelo base para câmeras."""
    name: str = Field(..., description="Nome da câmera")
    ip_address: str = Field(..., description="Endereço IP da câmera")
    port: int = Field(80, description="Porta da câmera")
    username: Optional[str] = Field(None, description="Nome de usuário para autenticação")
    password: Optional[str] = Field(None, description="Senha para autenticação")
    location: Optional[str] = Field(None, description="Localização física da câmera")
    connector_type: str = Field("onvif", description="Tipo de conector (onvif, hikvision, etc)")
    manufacturer: Optional[str] = Field(None, description="Fabricante da câmera")
    model: Optional[str] = Field(None, description="Modelo da câmera")

class CameraCreate(CameraBase):
    """Modelo para criação de câmeras."""
    user_id: str = Field(..., description="ID do usuário que possui a câmera")

class CameraUpdate(BaseModel):
    """Modelo para atualização de câmeras."""
    name: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    location: Optional[str] = None
    connector_type: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None

class CameraInDB(CameraBase):
    """Modelo para câmeras armazenadas no banco."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

class CameraOut(CameraBase):
    """Modelo para retorno de câmeras."""
    id: str
    status: str = Field("offline", description="Status da câmera (online, offline)")
    last_connection: Optional[datetime] = None
    detection_enabled: bool = Field(True, description="Se a detecção está habilitada para a câmera")

class AISettingsBase(BaseModel):
    """Modelo base para configurações de IA."""
    enabled: bool = Field(True, description="Se o processamento de IA está habilitado")
    model_id: Optional[str] = Field(None, description="ID do modelo de IA a ser usado")
    confidence_threshold: float = Field(0.4, description="Limiar de confiança para detecções (0.0-1.0)")
    use_gpu: bool = Field(True, description="Se deve usar GPU para processamento")
    enable_tracking: bool = Field(True, description="Se deve rastrear objetos entre frames")

class AISettingsCreate(AISettingsBase):
    """Modelo para criação de configurações de IA."""
    camera_id: str

class AISettingsUpdate(AISettingsBase):
    """Modelo para atualização de configurações de IA."""
    pass

class AISettingsInDB(AISettingsBase):
    """Modelo para configurações de IA armazenadas no banco."""
    id: str
    camera_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

class AIModelBase(BaseModel):
    """Modelo base para modelos de IA."""
    name: str = Field(..., description="Nome do modelo")
    description: Optional[str] = Field(None, description="Descrição do modelo")
    file_path: str = Field(..., description="Caminho para o arquivo do modelo")
    classes: List[str] = Field([], description="Classes que o modelo pode detectar")
    size_mb: Optional[float] = Field(None, description="Tamanho do modelo em MB")
    speed_rating: Optional[str] = Field(None, description="Classificação de velocidade do modelo")

class AIModelCreate(AIModelBase):
    """Modelo para criação de modelos de IA."""
    pass

class AIModelUpdate(BaseModel):
    """Modelo para atualização de modelos de IA."""
    name: Optional[str] = None
    description: Optional[str] = None
    file_path: Optional[str] = None
    classes: Optional[List[str]] = None
    size_mb: Optional[float] = None
    speed_rating: Optional[str] = None

class AIModelInDB(AIModelBase):
    """Modelo para modelos de IA armazenados no banco."""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

class Camera(Base):
    """
    Modelo de dados para câmeras no sistema.
    
    Armazena informações sobre as câmeras conectadas, incluindo
    configurações de conexão e preferências de detecção.
    """
    __tablename__ = "cameras"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    model = Column(String, nullable=True)
    manufacturer = Column(String, nullable=True)
    ip_address = Column(String, nullable=False)
    port = Column(Integer, default=80)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)
    location = Column(String, nullable=True)
    
    # Configuração de conexão e streams
    connector_type = Column(String, default="onvif")  # onvif, hikvision, dahua, etc.
    config = Column(JSON, default={})
    status = Column(String, default="offline")  # online, offline, error, etc.
    last_connection = Column(DateTime, nullable=True)
    
    # Configuração de detecção
    detection_enabled = Column(Boolean, default=True)
    detection_confidence = Column(Float, default=0.5)
    detection_objects = Column(JSON, default=["person", "car"])
    detection_zones = Column(JSON, default=[])  # Zonas de detecção na imagem
    detection_schedule = Column(JSON, default={})  # Programação para detecção
    
    # Configuração de IA
    ai_enabled = Column(Boolean, default=True)
    ai_model_id = Column(String, nullable=True)  # Referência ao modelo de IA a ser usado
    ai_confidence_threshold = Column(Float, default=0.4)
    ai_use_gpu = Column(Boolean, default=True)
    ai_enable_tracking = Column(Boolean, default=True)
    
    # Configuração de notificações
    notifications_enabled = Column(Boolean, default=True)
    notification_settings = Column(JSON, default={})
    
    # Metadados
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relações
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="cameras")
    events = relationship("Event", back_populates="camera", cascade="all, delete-orphan")

class AIModel(Base):
    """
    Modelo de dados para modelos de IA.
    
    Armazena informações sobre os modelos de IA disponíveis.
    """
    __tablename__ = "ai_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    file_path = Column(String, nullable=False)
    classes = Column(JSON, default=[])
    size_mb = Column(Float, nullable=True)
    speed_rating = Column(String, nullable=True)
    
    # Metadados
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now) 