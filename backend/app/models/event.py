from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class EventBase(BaseModel):
    """Modelo base para eventos de detecção."""
    camera_id: str = Field(..., description="ID da câmera que capturou o evento")
    event_type: str = Field(..., description="Tipo de evento (ex: pessoa, veículo, animal)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confiança da detecção (0-1)")
    timestamp: datetime = Field(..., description="Data e hora da detecção")
    image_path: str = Field(..., description="Caminho para a imagem capturada")
    bounding_boxes: List[Dict[str, Any]] = Field(..., description="Coordenadas dos objetos detectados")
    metadata: Dict[str, Any] = Field(default={}, description="Metadados adicionais sobre o evento")
    
    # Classificação por cores
    severity: str = Field("blue", description="Severidade do evento (red, yellow, blue)")

class EventCreate(EventBase):
    """Modelo para criação de eventos."""
    pass

class EventInDB(EventBase):
    """Modelo para eventos armazenados no banco."""
    user_id: str
    feedback: Optional[str] = None  # true_positive, false_positive, uncertain
    
class EventResponse(EventInDB):
    """Modelo de resposta para eventos."""
    id: str
    camera_name: Optional[str] = None
    camera_location: Optional[str] = None

class EventList(BaseModel):
    """Modelo para listagem paginada de eventos."""
    items: List[EventResponse]
    total: int
    page: int
    pages: int 