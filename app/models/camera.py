from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, Float
from sqlalchemy.orm import relationship
from ..database import Base

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
    
    # Adicionar campo para o proprietário da câmera
    owner = Column(String, nullable=False)
    
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
    
    # Relacionamentos
    ai_settings = relationship("CameraAISettings", back_populates="camera", cascade="all, delete-orphan") 