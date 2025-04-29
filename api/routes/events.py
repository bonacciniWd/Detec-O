"""
Rotas para gerenciamento de eventos de detecção
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from api import models, schemas, security
from api.db import get_db

router = APIRouter(prefix="/events", tags=["events"])

@router.get("/", response_model=List[schemas.DetectionEventResponse])
async def get_events(
    camera_id: Optional[str] = None,
    event_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Obtém a lista de eventos de detecção com filtros opcionais.
    Converte objetos SQLAlchemy em dicts para evitar erros de serialização.
    """
    # Iniciar query base
    query = db.query(models.DetectionEvent).join(
        models.Camera, models.DetectionEvent.camera_id == models.Camera.id
    ).filter(
        models.Camera.owner_id == current_user.id
    )
    
    # Aplicar filtros se fornecidos
    if camera_id:
        query = query.filter(models.DetectionEvent.camera_id == camera_id)
    
    if event_type:
        query = query.filter(models.DetectionEvent.event_type == event_type)
    
    if start_date:
        query = query.filter(models.DetectionEvent.timestamp >= start_date)
    
    if end_date:
        query = query.filter(models.DetectionEvent.timestamp <= end_date)
    
    # Ordenar por data/hora, mais recentes primeiro
    query = query.order_by(models.DetectionEvent.timestamp.desc())
    
    # Paginar resultados
    events_db = query.offset(skip).limit(limit).all()
    
    # WORKAROUND: Converter para lista de dicionários
    events_list = []
    for event in events_db:
        event_dict = {
            field: getattr(event, field) 
            for field in schemas.DetectionEventResponse.__fields__ 
            if hasattr(event, field)
        }
        events_list.append(event_dict)
        
    return events_list

@router.get("/{event_id}", response_model=schemas.DetectionEventResponse)
async def get_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Obtém detalhes de um evento específico
    """
    # Buscar evento com verificação de permissão
    event = db.query(models.DetectionEvent).join(
        models.Camera, models.DetectionEvent.camera_id == models.Camera.id
    ).filter(
        models.DetectionEvent.id == event_id,
        models.Camera.owner_id == current_user.id
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado"
        )
    
    return event

@router.post("/", response_model=schemas.DetectionEventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event: schemas.DetectionEventCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Cria um novo evento de detecção (para testes ou uso interno)
    """
    # Verificar se a câmera existe e pertence ao usuário
    camera = db.query(models.Camera).filter(
        models.Camera.id == event.camera_id,
        models.Camera.owner_id == current_user.id
    ).first()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Câmera não encontrada ou não pertence ao usuário"
        )
    
    # Criar novo evento
    db_event = models.DetectionEvent(**event.dict())
    
    # Adicionar ao banco de dados
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    return db_event

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Remove um evento específico
    """
    # Buscar evento com verificação de permissão
    event = db.query(models.DetectionEvent).join(
        models.Camera, models.DetectionEvent.camera_id == models.Camera.id
    ).filter(
        models.DetectionEvent.id == event_id,
        models.Camera.owner_id == current_user.id
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado"
        )
    
    # Remover evento
    db.delete(event)
    db.commit()
    
    return None

@router.get("/stats", response_model=dict)
async def get_event_stats(
    days: int = 7,
    camera_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Obtém estatísticas dos eventos (contagem por tipo, severidade, etc.)
    """
    # Definir período
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Iniciar query base
    query = db.query(models.DetectionEvent).join(
        models.Camera, models.DetectionEvent.camera_id == models.Camera.id
    ).filter(
        models.Camera.owner_id == current_user.id,
        models.DetectionEvent.timestamp >= start_date,
        models.DetectionEvent.timestamp <= end_date
    )
    
    # Filtrar por câmera se especificado
    if camera_id:
        query = query.filter(models.DetectionEvent.camera_id == camera_id)
    
    # Buscar todos os eventos no período
    events = query.all()
    
    # Calcular estatísticas
    total_count = len(events)
    
    # Contagem por tipo de evento
    event_types = {}
    for event in events:
        event_type = event.event_type
        event_types[event_type] = event_types.get(event_type, 0) + 1
    
    # Outras estatísticas (implementar conforme necessário)
    
    return {
        "total_count": total_count,
        "period_days": days,
        "start_date": start_date,
        "end_date": end_date,
        "by_type": event_types
    } 