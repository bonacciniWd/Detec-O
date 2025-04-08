from sqlalchemy import Column, String, Float, DateTime, JSON, Boolean, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from ..database import Base

def generate_uuid():
    """Gera um UUID único como string"""
    return str(uuid4())

class AIModel(Base):
    __tablename__ = "ai_models"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    file_path = Column(String, nullable=False)
    classes = Column(JSON, default=lambda: [])
    size_mb = Column(Float, nullable=True)
    speed_rating = Column(String, nullable=True)
    
    # Metadados
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class CameraAISettings(Base):
    __tablename__ = "camera_ai_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id", ondelete="CASCADE"))
    ai_model_id = Column(String, ForeignKey("ai_models.id"))
    confidence_threshold = Column(Float, default=0.4)
    enabled = Column(Boolean, default=True)
    target_classes = Column(JSON, default=lambda: ["person"])
    
    # Relacionamento com câmera e modelo de IA
    camera = relationship("Camera", back_populates="ai_settings")
    ai_model = relationship("AIModel")
    
    # Metadados
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class DetectionEvent(Base):
    __tablename__ = "detection_events"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id", ondelete="SET NULL"), nullable=True)
    ai_model_id = Column(String, ForeignKey("ai_models.id", ondelete="SET NULL"), nullable=True)
    event_type = Column(String, nullable=False)  # movimento, objeto, pessoa, etc
    confidence = Column(Float)
    detected_class = Column(String)
    bounding_box = Column(JSON)  # [x, y, w, h]
    image_path = Column(String, nullable=True)  # Caminho para imagem salva
    video_path = Column(String, nullable=True)  # Caminho para vídeo salvo
    timestamp = Column(DateTime, default=datetime.now, index=True)
    
    # Relacionamentos
    camera = relationship("Camera")
    ai_model = relationship("AIModel")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    
    # Permissões
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # Metadados
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime, nullable=True)
    
    # Relacionamentos
    # cameras = relationship("Camera", back_populates="owner") 