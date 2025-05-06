"""
Modelos SQLAlchemy para o banco de dados
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB, BYTEA
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
    settings = Column(JSONB, nullable=True)  # Campo para configurações gerais do usuário
    
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
    video_path = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Nova coluna para relacionar com a pessoa detectada (se houver)
    detected_person_id = Column(String, ForeignKey("persons.id"), nullable=True)

    # Campos de Feedback
    feedback_status = Column(String, nullable=True) # e.g., 'true_positive', 'false_positive', 'uncertain'
    feedback_notes = Column(Text, nullable=True)
    feedback_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    feedback_timestamp = Column(DateTime, nullable=True)
    
    # Relacionamentos
    camera = relationship("Camera", back_populates="events")
    snapshots = relationship("EventSnapshot", back_populates="event", cascade="all, delete-orphan")
    feedback_user = relationship("User") # Relacionamento para buscar o usuário que deu feedback
    detected_person = relationship("Person") # Relacionamento para buscar a pessoa detectada
    
    def __repr__(self):
        return f"<DetectionEvent {self.id}>"

class EventSnapshot(Base):
    """Modelo para armazenar caminhos de snapshots associados a um evento."""
    __tablename__ = "event_snapshots"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String, ForeignKey("detection_events.id"), nullable=False)
    snapshot_path = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False) # Timestamp exato do frame
    
    # Relacionamento inverso
    event = relationship("DetectionEvent", back_populates="snapshots")
    
    def __repr__(self):
        return f"<EventSnapshot {self.id} for Event {self.event_id}>"

# --- Novos Modelos ---

class Person(Base):
    """Modelo para Pessoas reconhecidas pelo sistema."""
    __tablename__ = "persons"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True, index=True, default='default')
    class_group = Column(String, nullable=True) # Nova coluna para Classe/Turma
    thumbnail_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamento com embeddings faciais
    face_embeddings = relationship("FaceEmbedding", back_populates="person", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Person {self.name} ({self.id})>"

class FaceEmbedding(Base):
    """Modelo para armazenar embeddings faciais associados a uma Pessoa."""
    __tablename__ = "face_embeddings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    person_id = Column(String, ForeignKey("persons.id"), nullable=False, index=True)
    embedding = Column(BYTEA, nullable=False) # Vetor de embedding como bytes
    label = Column(String, nullable=True) # Rótulo opcional (e.g., 'frontal', 'perfil', 'oculos')
    source_image_path = Column(String, nullable=True) # Caminho da imagem original usada
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relacionamento inverso
    person = relationship("Person", back_populates="face_embeddings")

    def __repr__(self):
        return f"<FaceEmbedding {self.id} for Person {self.person_id}>" 