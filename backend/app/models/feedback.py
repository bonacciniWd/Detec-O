from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class FeedbackCreate(BaseModel):
    """Modelo para criação de feedback para um evento de detecção."""
    feedback_value: Literal['true_positive', 'false_positive', 'uncertain'] = Field(
        ...,
        description="Classificação do evento: verdadeiro positivo, falso positivo ou incerto"
    )
    comment: Optional[str] = Field(
        None,
        description="Comentário opcional sobre o evento"
    )


class FeedbackInDB(FeedbackCreate):
    """Modelo para feedback armazenado no banco de dados."""
    event_id: str = Field(..., description="ID do evento associado ao feedback")
    user_id: str = Field(..., description="ID do usuário que forneceu o feedback")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class FeedbackResponse(FeedbackInDB):
    """Modelo para resposta de feedback."""
    id: str = Field(..., description="ID único do feedback") 