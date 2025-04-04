from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, JSON, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    cameras = relationship("Camera", back_populates="user", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")

class Camera(Base):
    __tablename__ = "cameras"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    location = Column(String)
    rtsp_url = Column(String)
    status = Column(String, default="offline")  # online, offline, error
    model_name = Column(String, default="yolov8n")
    is_recording = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    user = relationship("User", back_populates="cameras")
    events = relationship("Event", back_populates="camera", cascade="all, delete-orphan")
    settings = relationship("CameraSettings", back_populates="camera", uselist=False, cascade="all, delete-orphan")

class Event(Base):
    __tablename__ = "events"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    camera_id = Column(String, ForeignKey("cameras.id"), nullable=False)
    event_type = Column(String, nullable=False)  # person, vehicle, animal, etc.
    confidence = Column(Float, nullable=False)
    severity = Column(String, nullable=False)  # red, yellow, blue
    timestamp = Column(DateTime, default=datetime.now)
    image_path = Column(String)
    video_path = Column(String)
    metadata = Column(JSON)
    is_false_positive = Column(Boolean, default=False)
    feedback = Column(String)  # true_positive, false_positive, uncertain
    feedback_comment = Column(String)
    
    # Relacionamentos
    user = relationship("User", back_populates="events")
    camera = relationship("Camera", back_populates="events")

class UserSettings(Base):
    __tablename__ = "user_settings"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Notificações
    email_notifications = Column(Boolean, default=False)
    browser_notifications = Column(Boolean, default=True)
    mobile_notifications = Column(Boolean, default=False)
    notification_frequency = Column(String, default="immediate")  # immediate, hourly, daily
    
    # Interface
    dark_mode = Column(Boolean, default=False)
    compact_view = Column(Boolean, default=False)
    show_statistics = Column(Boolean, default=True)
    highlight_detections = Column(Boolean, default=True)
    
    # Relacionamentos
    user = relationship("User", back_populates="settings")

class CameraSettings(Base):
    __tablename__ = "camera_settings"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    camera_id = Column(String, ForeignKey("cameras.id"), unique=True, nullable=False)
    
    # Configurações de detecção
    confidence_threshold = Column(Float, default=0.5)
    min_detection_interval = Column(Integer, default=1)  # segundos
    motion_sensitivity = Column(Float, default=0.3)
    
    # Classes para detectar (lista JSON)
    detection_classes = Column(JSON, default=lambda: ['person', 'car', 'animal'])
    
    # Configurações adicionais
    notifications_enabled = Column(Boolean, default=True)
    save_all_frames = Column(Boolean, default=False)
    detection_zone = Column(JSON)  # Polígono de zona de detecção
    
    # Relacionamentos
    camera = relationship("Camera", back_populates="settings") 