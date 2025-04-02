from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from typing import List, Optional
from ..db.database import get_database
from ..models.event import EventResponse, EventList
from ..models.feedback import FeedbackCreate, FeedbackResponse
from ..auth.dependencies import get_current_user
from ..models.user import User
from bson import ObjectId
from datetime import datetime, timedelta

router = APIRouter(
    prefix="/api/v1/events",
    tags=["events"]
)

@router.get("/", response_model=EventList)
async def get_events(
    days: int = Query(7, description="Eventos dos últimos X dias"),
    camera_id: Optional[str] = Query(None, description="Filtrar por câmera específica"),
    page: int = Query(1, ge=1, description="Número da página"),
    limit: int = Query(10, ge=1, le=100, description="Itens por página"),
    event_type: Optional[str] = Query(None, description="Filtrar por tipo de evento"),
    min_confidence: Optional[float] = Query(None, ge=0, le=1, description="Confiança mínima"),
    feedback: Optional[str] = Query(None, description="Filtrar por tipo de feedback"),
    date_start: Optional[str] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    date_end: Optional[str] = Query(None, description="Data final (YYYY-MM-DD)"),
    severity: Optional[str] = Query(None, description="Filtrar por severidade (red, yellow, blue)"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    # Calculando a data limite baseada nos dias
    date_limit = datetime.utcnow() - timedelta(days=days)
    
    # Construindo a query para MongoDB
    query = {
        "timestamp": {"$gte": date_limit},
        "user_id": current_user["_id"]  # Apenas eventos do usuário atual
    }
    
    # Adicionando filtros opcionais
    if camera_id:
        query["camera_id"] = ObjectId(camera_id)
    
    if event_type:
        query["event_type"] = event_type
    
    if min_confidence is not None:
        query["confidence"] = {"$gte": min_confidence}
    
    if date_start:
        try:
            start_date = datetime.strptime(date_start, "%Y-%m-%d")
            if "timestamp" in query:
                query["timestamp"]["$gte"] = start_date
            else:
                query["timestamp"] = {"$gte": start_date}
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de data inicial inválido. Use YYYY-MM-DD")
    
    if date_end:
        try:
            # Ajustar para o final do dia
            end_date = datetime.strptime(date_end, "%Y-%m-%d") + timedelta(days=1, microseconds=-1)
            if "timestamp" in query:
                query["timestamp"]["$lte"] = end_date
            else:
                query["timestamp"] = {"$lte": end_date}
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de data final inválido. Use YYYY-MM-DD")
    
    if feedback:
        if feedback == "none":
            # Eventos sem feedback
            query["feedback"] = {"$exists": False}
        else:
            # Filtrar pelo valor específico
            query["feedback"] = feedback
    
    if severity:
        query["severity"] = severity
    
    # Calculando paginação
    skip = (page - 1) * limit
    
    # Contando total de eventos
    total_events = await db.events.count_documents(query)
    
    # Buscando eventos com paginação e ordenando por data
    events_cursor = db.events.find(query).sort("timestamp", -1).skip(skip).limit(limit)
    events = []
    
    async for event in events_cursor:
        # Convertendo ID do ObjectId para string
        event["id"] = str(event.pop("_id"))
        
        # Convertendo outros ObjectIds
        if "camera_id" in event:
            event["camera_id"] = str(event["camera_id"])
        
        # Adicionando informações da câmera se disponível
        if "camera_id" in event:
            camera = await db.cameras.find_one({"_id": ObjectId(event["camera_id"])})
            if camera:
                event["camera_name"] = camera.get("name")
                event["camera_location"] = camera.get("location")
        
        events.append(event)
    
    return {
        "items": events,
        "total": total_events,
        "page": page,
        "pages": (total_events + limit - 1) // limit  # Ceiling division
    }

@router.get("/{event_id}", response_model=EventResponse)
async def get_event_by_id(
    event_id: str = Path(..., description="ID do evento"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    try:
        # Buscando evento
        event = await db.events.find_one({
            "_id": ObjectId(event_id),
            "user_id": current_user["_id"]  # Garantir que pertence ao usuário atual
        })
        
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento não encontrado"
            )
        
        # Convertendo ID do ObjectId para string
        event["id"] = str(event.pop("_id"))
        
        # Convertendo outros ObjectIds
        if "camera_id" in event:
            event["camera_id"] = str(event["camera_id"])
        
        # Adicionando informações da câmera se disponível
        if "camera_id" in event:
            camera = await db.cameras.find_one({"_id": ObjectId(event["camera_id"])})
            if camera:
                event["camera_name"] = camera.get("name")
                event["camera_location"] = camera.get("location")
        
        return event
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar evento: {str(e)}"
        )

@router.post("/{event_id}/feedback", response_model=FeedbackResponse)
async def create_event_feedback(
    event_id: str = Path(..., description="ID do evento"),
    feedback: FeedbackCreate = None,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Adiciona feedback a um evento de detecção.
    O feedback pode ser:
    - true_positive: O evento foi detectado corretamente
    - false_positive: O evento foi detectado incorretamente
    - uncertain: Não está claro se o evento foi detectado corretamente
    """
    try:
        # Verificar se o evento existe e pertence ao usuário
        event = await db.events.find_one({
            "_id": ObjectId(event_id),
            "user_id": current_user["_id"]
        })
        
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento não encontrado"
            )
        
        # Verificar se já existe feedback para este evento
        existing_feedback = await db.feedback.find_one({
            "event_id": event_id,
            "user_id": str(current_user["_id"])
        })
        
        feedback_data = feedback.dict()
        feedback_data["event_id"] = event_id
        feedback_data["user_id"] = str(current_user["_id"])
        feedback_data["created_at"] = datetime.utcnow()
        
        if existing_feedback:
            # Atualizar feedback existente
            feedback_data["updated_at"] = datetime.utcnow()
            await db.feedback.update_one(
                {"_id": existing_feedback["_id"]},
                {"$set": feedback_data}
            )
            
            # Obter o feedback atualizado
            updated_feedback = await db.feedback.find_one({"_id": existing_feedback["_id"]})
            updated_feedback["id"] = str(updated_feedback.pop("_id"))
            
            # Atualizar o campo de feedback no evento
            await db.events.update_one(
                {"_id": ObjectId(event_id)},
                {"$set": {"feedback": feedback.feedback_value}}
            )
            
            return updated_feedback
        else:
            # Criar novo feedback
            result = await db.feedback.insert_one(feedback_data)
            
            # Obter o feedback criado
            created_feedback = await db.feedback.find_one({"_id": result.inserted_id})
            created_feedback["id"] = str(created_feedback.pop("_id"))
            
            # Atualizar o campo de feedback no evento
            await db.events.update_one(
                {"_id": ObjectId(event_id)},
                {"$set": {"feedback": feedback.feedback_value}}
            )
            
            return created_feedback
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar feedback: {str(e)}"
        )

@router.get("/{event_id}/feedback", response_model=FeedbackResponse)
async def get_event_feedback(
    event_id: str = Path(..., description="ID do evento"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Obtém o feedback associado a um evento."""
    try:
        # Verificar se o evento existe e pertence ao usuário
        event = await db.events.find_one({
            "_id": ObjectId(event_id),
            "user_id": current_user["_id"]
        })
        
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento não encontrado"
            )
        
        # Buscar o feedback
        feedback = await db.feedback.find_one({
            "event_id": event_id,
            "user_id": str(current_user["_id"])
        })
        
        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback não encontrado para este evento"
            )
        
        # Converter ObjectId para string
        feedback["id"] = str(feedback.pop("_id"))
        
        return feedback
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar feedback: {str(e)}"
        )

@router.delete("/{event_id}/feedback", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event_feedback(
    event_id: str = Path(..., description="ID do evento"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Remove o feedback associado a um evento."""
    try:
        # Verificar se o evento existe e pertence ao usuário
        event = await db.events.find_one({
            "_id": ObjectId(event_id),
            "user_id": current_user["_id"]
        })
        
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento não encontrado"
            )
        
        # Remover o feedback
        result = await db.feedback.delete_one({
            "event_id": event_id,
            "user_id": str(current_user["_id"])
        })
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback não encontrado para este evento"
            )
        
        # Remover o campo de feedback do evento
        await db.events.update_one(
            {"_id": ObjectId(event_id)},
            {"$unset": {"feedback": ""}}
        )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao remover feedback: {str(e)}"
        ) 