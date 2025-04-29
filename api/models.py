"""
Modelos SQLAlchemy para o banco de dados
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from datetime import datetime

from .db import Base

class User(Base):
    """Modelo para usuários"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relacionamentos
    cameras = relationship("Camera", back_populates="owner", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.username}>"

class Camera(Base):
    """Modelo para câmeras"""
    __tablename__ = "cameras"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    ip_address = Column(String, nullable=True)
    rtsp_url = Column(String, nullable=True)
    model = Column(String, nullable=True)
    manufacturer = Column(String, nullable=True)
    port = Column(Integer, default=80)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)
    location = Column(String, nullable=True)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    connector_type = Column(String, default="rtsp")
    detection_enabled = Column(Boolean, default=True)
    detection_confidence = Column(Float, default=0.5)
    detection_objects = Column(JSONB, default=lambda: ["person", "car", "bicycle"])
    detection_zones = Column(JSONB, nullable=True)
    detection_settings = Column(JSONB, nullable=True)
    ai_settings = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    owner = relationship("User", back_populates="cameras")
    events = relationship("DetectionEvent", back_populates="camera", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Camera {self.name}>"

class DetectionEvent(Base):
    """Modelo para eventos de detecção"""
    __tablename__ = "detection_events"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    camera_id = Column(String, ForeignKey("cameras.id"), nullable=False)
    event_type = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    detected_class = Column(String, nullable=False)
    bounding_box = Column(JSONB, nullable=True)
    image_path = Column(String, nullable=True)
    video_path = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    camera = relationship("Camera", back_populates="events")
    
    def __repr__(self):
        return f"<DetectionEvent {self.id}>" 
    def __repr__(self):
        return f"<DetectionEvent {self.id}>" 