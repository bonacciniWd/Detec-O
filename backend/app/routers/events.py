from fastapi import APIRouter, Depends, HTTPException, status, Body, Path, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import Dict, List, Optional, Any
from ..database import get_db
from ..models.models import Event, Camera
from ..dependencies import get_current_user
from pydantic import BaseModel
from datetime import datetime, timedelta
import uuid

router = APIRouter(prefix="/api/v1/events", tags=["events"])

class EventBase(BaseModel):
    event_type: str
    camera_id: str
    confidence: float
    severity: str
    image_path: Optional[str] = None
    video_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class EventCreate(EventBase):
    pass

class EventResponse(EventBase):
    id: str
    timestamp: datetime
    is_false_positive: bool
    feedback: Optional[str] = None
    
    class Config:
        orm_mode = True

@router.get("", response_model=Dict[str, Any])
async def list_events(
    page: int = Query(1, ge=1, description="Página atual"),
    limit: int = Query(10, ge=1, le=100, description="Itens por página"),
    start_date: Optional[datetime] = Query(None, description="Data de início do filtro"),
    end_date: Optional[datetime] = Query(None, description="Data final do filtro"),
    camera_id: Optional[str] = Query(None, description="Filtrar por ID da câmera"),
    event_type: Optional[str] = Query(None, description="Tipo de evento (pessoa, veículo, etc.)"),
    severity: Optional[str] = Query(None, description="Severidade do evento (red, yellow, blue)"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Confiança mínima"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista eventos detectados com suporte a filtragem."""
    # Construir a query base
    query = db.query(Event).filter(Event.user_id == current_user["id"])
    
    # Aplicar filtros
    if start_date:
        query = query.filter(Event.timestamp >= start_date)
    
    if end_date:
        query = query.filter(Event.timestamp <= end_date)
    
    if camera_id:
        query = query.filter(Event.camera_id == camera_id)
    
    if event_type:
        query = query.filter(Event.event_type == event_type)
    
    if severity:
        query = query.filter(Event.severity == severity)
    
    if min_confidence:
        query = query.filter(Event.confidence >= min_confidence)
    
    # Calcular total para paginação
    total = query.count()
    
    # Aplicar ordenação e paginação
    query = query.order_by(desc(Event.timestamp)).offset((page - 1) * limit).limit(limit)
    
    # Executar consulta
    events = query.all()
    
    # Carregar informações da câmera para cada evento
    result = []
    for event in events:
        camera = db.query(Camera).filter(Camera.id == event.camera_id).first()
        
        camera_name = "Câmera Desconhecida"
        camera_location = "Local Desconhecido"
        
        if camera:
            camera_name = camera.name
            camera_location = camera.location
        
        # Criar dicionário para o evento
        event_data = {
            "id": event.id,
            "camera_id": event.camera_id,
            "camera_name": camera_name,
            "camera_location": camera_location,
            "event_type": event.event_type,
            "confidence": event.confidence,
            "severity": event.severity,
            "timestamp": event.timestamp,
            "image_path": event.image_path,
            "video_path": event.video_path,
            "metadata": event.metadata,
            "is_false_positive": event.is_false_positive,
            "feedback": event.feedback
        }
        
        result.append(event_data)
    
    # Adicionar metadados de paginação
    return {
        "items": result,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if total > 0 else 1  # Cálculo de total de páginas
    }

@router.get("/summary", response_model=Dict[str, Any])
async def get_events_summary(
    days: int = Query(7, ge=1, le=30, description="Número de dias para resumo"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtém um resumo dos eventos recentes."""
    # Calcular data de início
    start_date = datetime.now() - timedelta(days=days)
    
    # Consulta para eventos totais no período
    total_events = db.query(Event).filter(
        Event.user_id == current_user["id"],
        Event.timestamp >= start_date
    ).count()
    
    # Consulta para contagem por severidade
    red_events = db.query(Event).filter(
        Event.user_id == current_user["id"],
        Event.timestamp >= start_date,
        Event.severity == "red"
    ).count()
    
    yellow_events = db.query(Event).filter(
        Event.user_id == current_user["id"],
        Event.timestamp >= start_date,
        Event.severity == "yellow"
    ).count()
    
    blue_events = db.query(Event).filter(
        Event.user_id == current_user["id"],
        Event.timestamp >= start_date,
        Event.severity == "blue"
    ).count()
    
    # Consulta para contagem por tipo
    person_events = db.query(Event).filter(
        Event.user_id == current_user["id"],
        Event.timestamp >= start_date,
        Event.event_type == "person"
    ).count()
    
    vehicle_events = db.query(Event).filter(
        Event.user_id == current_user["id"],
        Event.timestamp >= start_date,
        Event.event_type == "vehicle"
    ).count()
    
    animal_events = db.query(Event).filter(
        Event.user_id == current_user["id"],
        Event.timestamp >= start_date,
        Event.event_type == "animal"
    ).count()
    
    # Consulta para eventos por câmera
    camera_events = db.query(
        Camera.id, 
        Camera.name, 
        db.func.count(Event.id).label("event_count")
    ).join(
        Event, 
        and_(
            Event.camera_id == Camera.id,
            Event.timestamp >= start_date,
            Event.user_id == current_user["id"]
        )
    ).group_by(
        Camera.id
    ).order_by(
        desc("event_count")
    ).limit(5).all()
    
    # Preparar lista de câmeras com mais eventos
    top_cameras = []
    for camera_id, camera_name, event_count in camera_events:
        top_cameras.append({
            "camera_id": camera_id,
            "camera_name": camera_name,
            "event_count": event_count
        })
    
    # Retornar resumo
    return {
        "period_days": days,
        "total_events": total_events,
        "by_severity": {
            "red": red_events,
            "yellow": yellow_events,
            "blue": blue_events
        },
        "by_type": {
            "person": person_events,
            "vehicle": vehicle_events,
            "animal": animal_events
        },
        "top_cameras": top_cameras
    }

@router.get("/{event_id}", response_model=Dict[str, Any])
async def get_event(
    event_id: str = Path(..., description="ID do evento"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtém detalhes de um evento específico."""
    # Buscar o evento
    event = db.query(Event).filter(
        Event.id == event_id,
        Event.user_id == current_user["id"]
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado ou não pertence ao usuário atual"
        )
    
    # Buscar informações da câmera
    camera = db.query(Camera).filter(Camera.id == event.camera_id).first()
    
    camera_name = "Câmera Desconhecida"
    camera_location = "Local Desconhecido"
    
    if camera:
        camera_name = camera.name
        camera_location = camera.location
    
    # Formatar resposta
    return {
        "id": event.id,
        "camera_id": event.camera_id,
        "camera_name": camera_name,
        "camera_location": camera_location,
        "event_type": event.event_type,
        "confidence": event.confidence,
        "severity": event.severity,
        "timestamp": event.timestamp,
        "image_path": event.image_path,
        "video_path": event.video_path,
        "metadata": event.metadata,
        "is_false_positive": event.is_false_positive,
        "feedback": event.feedback,
        "feedback_comment": event.feedback_comment
    }

@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cria um novo evento de detecção."""
    # Verificar se a câmera existe e pertence ao usuário
    camera = db.query(Camera).filter(
        Camera.id == event_data.camera_id,
        Camera.user_id == current_user["id"]
    ).first()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Câmera não encontrada ou não pertence ao usuário atual"
        )
    
    # Validar severity
    valid_severities = ["red", "yellow", "blue"]
    if event_data.severity not in valid_severities:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Severidade inválida. Deve ser uma das seguintes: {', '.join(valid_severities)}"
        )
    
    # Criar evento
    new_event = Event(
        id=str(uuid.uuid4()),
        user_id=current_user["id"],
        camera_id=event_data.camera_id,
        event_type=event_data.event_type,
        confidence=event_data.confidence,
        severity=event_data.severity,
        timestamp=datetime.now(),
        image_path=event_data.image_path,
        video_path=event_data.video_path,
        metadata=event_data.metadata,
        is_false_positive=False
    )
    
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    
    # Formatar resposta
    return {
        "id": new_event.id,
        "camera_id": new_event.camera_id,
        "camera_name": camera.name,
        "camera_location": camera.location,
        "event_type": new_event.event_type,
        "confidence": new_event.confidence,
        "severity": new_event.severity,
        "timestamp": new_event.timestamp,
        "image_path": new_event.image_path,
        "video_path": new_event.video_path,
        "metadata": new_event.metadata,
        "is_false_positive": new_event.is_false_positive,
        "message": "Evento criado com sucesso"
    }

@router.put("/{event_id}/feedback", response_model=Dict[str, Any])
async def provide_event_feedback(
    feedback_data: Dict[str, Any] = Body(...),
    event_id: str = Path(..., description="ID do evento"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fornece feedback para um evento (verdadeiro ou falso positivo)."""
    # Buscar o evento
    event = db.query(Event).filter(
        Event.id == event_id,
        Event.user_id == current_user["id"]
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado ou não pertence ao usuário atual"
        )
    
    # Verificar campos obrigatórios
    if "feedback" not in feedback_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campo 'feedback' é obrigatório"
        )
    
    valid_feedback = ["true_positive", "false_positive", "uncertain"]
    if feedback_data["feedback"] not in valid_feedback:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Feedback inválido. Deve ser um dos seguintes: {', '.join(valid_feedback)}"
        )
    
    # Atualizar feedback
    event.feedback = feedback_data["feedback"]
    event.is_false_positive = (feedback_data["feedback"] == "false_positive")
    
    if "comment" in feedback_data:
        event.feedback_comment = feedback_data["comment"]
    
    db.commit()
    
    return {
        "id": event.id,
        "feedback": event.feedback,
        "is_false_positive": event.is_false_positive,
        "feedback_comment": event.feedback_comment,
        "message": "Feedback registrado com sucesso"
    } 