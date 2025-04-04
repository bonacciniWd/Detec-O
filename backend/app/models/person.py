from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship

from ..database import Base

# Classe SQLAlchemy para o banco de dados
class Person(Base):
    """Modelo SQLAlchemy para pessoas."""
    __tablename__ = "persons"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, default="default")
    user_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    face_count = Column(Integer, default=0)
    face_encodings = Column(Text, default="[]")  # JSON serializado como texto

# Classes Pydantic para validação e API

class PersonBase(BaseModel):
    """Modelo base para pessoas reconhecíveis pelo sistema."""
    name: str = Field(..., description="Nome da pessoa")
    description: Optional[str] = Field(None, description="Descrição ou observações sobre a pessoa")
    category: str = Field("default", description="Categoria da pessoa (colaborador, visitante, etc)")
    
class PersonCreate(PersonBase):
    """Modelo para criação de pessoa."""
    face_image: str = Field(..., description="Imagem de face em formato base64")
    
class PersonUpdate(BaseModel):
    """Modelo para atualização de pessoa."""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    
class FaceEncodingCreate(BaseModel):
    """Modelo para criar/adicionar uma nova codificação facial para pessoa existente."""
    person_id: str = Field(..., description="ID da pessoa à qual a face pertence")
    face_image: str = Field(..., description="Imagem da face em formato base64")
    label: Optional[str] = Field(None, description="Rótulo opcional para esta face (ex: 'perfil', 'óculos')")
    
class FaceEncoding(BaseModel):
    """Modelo para armazenar codificação facial."""
    id: str
    person_id: str
    created_at: datetime
    label: Optional[str] = None
    thumbnail_url: Optional[str] = None
    
class PersonInDB(PersonBase):
    """Modelo para pessoa armazenada no banco."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    face_count: int = Field(0, description="Quantidade de faces cadastradas para esta pessoa")
    face_encodings: List[FaceEncoding] = Field([], description="Codificações faciais desta pessoa")
    
class PersonResponse(PersonBase):
    """Modelo de resposta para pessoas."""
    id: str
    created_at: datetime
    updated_at: datetime
    face_count: int
    thumbnail_url: Optional[str] = None
    
class PersonList(BaseModel):
    """Modelo para listagem paginada de pessoas."""
    items: List[PersonResponse]
    total: int
    page: int
    pages: int
    
class FaceMatchResult(BaseModel):
    """Resultado de uma correspondência facial."""
    person_id: str
    person_name: str
    match_confidence: float
    thumbnail_url: Optional[str] = None
    category: str 