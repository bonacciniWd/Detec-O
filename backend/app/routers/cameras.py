from fastapi import APIRouter, Depends, HTTPException, status, Body, Path, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from ..database import get_db
from ..models.models import Camera, CameraSettings
from ..dependencies import get_current_user
from pydantic import BaseModel, validator
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/v1/cameras", tags=["cameras"])

class CameraBase(BaseModel):
    name: str
    location: Optional[str] = None
    rtsp_url: str
    model_name: Optional[str] = "yolov8n"

class CameraCreate(CameraBase):
    pass

class CameraResponse(CameraBase):
    id: str
    status: str
    is_recording: bool
    created_at: datetime
    
    class Config:
        orm_mode = True

@router.get("", response_model=List[Dict[str, Any]])
async def list_cameras(
    page: int = Query(1, ge=1, description="Página atual"),
    limit: int = Query(10, ge=1, le=100, description="Itens por página"),
    search: Optional[str] = Query(None, description="Termo de busca para nome ou localização"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista todas as câmeras do usuário atual."""
    # Construir a query base
    query = db.query(Camera).filter(Camera.user_id == current_user["id"])
    
    # Aplicar filtro de busca se fornecido
    if search:
        query = query.filter(
            (Camera.name.contains(search)) | 
            (Camera.location.contains(search))
        )
    
    # Calcular total para paginação
    total = query.count()
    
    # Aplicar paginação
    query = query.order_by(Camera.created_at.desc()).offset((page - 1) * limit).limit(limit)
    
    # Executar a consulta
    cameras = query.all()
    
    # Formatar resposta
    result = []
    for camera in cameras:
        # Obter configurações da câmera
        settings = db.query(CameraSettings).filter(CameraSettings.camera_id == camera.id).first()
        
        # Se não houver configurações, criar valores padrão
        confidence_threshold = 0.5
        detection_classes = ["person", "car", "animal"]
        
        if settings:
            confidence_threshold = settings.confidence_threshold
            detection_classes = settings.detection_classes
        
        # Formatar resposta para cada câmera
        camera_data = {
            "id": camera.id,
            "name": camera.name,
            "location": camera.location,
            "status": camera.status,
            "rtsp_url": camera.rtsp_url,
            "is_recording": camera.is_recording,
            "model_name": camera.model_name,
            "created_at": camera.created_at,
            "detection_settings": {
                "confidence_threshold": confidence_threshold,
                "detection_classes": detection_classes
            }
        }
        
        result.append(camera_data)
    
    # Adicionar metadados de paginação
    return {
        "items": result,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit  # Cálculo de total de páginas
    }

@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_camera(
    camera_data: CameraCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cria uma nova câmera para o usuário atual."""
    # Criar câmera
    new_camera = Camera(
        id=str(uuid.uuid4()),
        user_id=current_user["id"],
        name=camera_data.name,
        location=camera_data.location,
        rtsp_url=camera_data.rtsp_url,
        model_name=camera_data.model_name,
        status="offline",  # Inicia offline
        is_recording=False,
        is_active=True
    )
    
    db.add(new_camera)
    
    # Criar configurações padrão para a câmera
    camera_settings = CameraSettings(
        id=str(uuid.uuid4()),
        camera_id=new_camera.id,
        confidence_threshold=0.5,
        min_detection_interval=1,
        motion_sensitivity=0.3,
        detection_classes=["person", "car", "animal"],
        notifications_enabled=True,
        save_all_frames=False
    )
    
    db.add(camera_settings)
    db.commit()
    db.refresh(new_camera)
    db.refresh(camera_settings)
    
    # Formatar resposta
    return {
        "id": new_camera.id,
        "name": new_camera.name,
        "location": new_camera.location,
        "status": new_camera.status,
        "rtsp_url": new_camera.rtsp_url,
        "is_recording": new_camera.is_recording,
        "model_name": new_camera.model_name,
        "created_at": new_camera.created_at,
        "detection_settings": {
            "confidence_threshold": camera_settings.confidence_threshold,
            "detection_classes": camera_settings.detection_classes
        },
        "message": "Câmera criada com sucesso"
    }

@router.get("/{camera_id}", response_model=Dict[str, Any])
async def get_camera(
    camera_id: str = Path(..., description="ID da câmera"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtém detalhes de uma câmera específica."""
    # Buscar a câmera
    camera = db.query(Camera).filter(
        Camera.id == camera_id,
        Camera.user_id == current_user["id"]
    ).first()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Câmera não encontrada ou não pertence ao usuário atual"
        )
    
    # Buscar configurações
    settings = db.query(CameraSettings).filter(CameraSettings.camera_id == camera.id).first()
    
    # Formatar resposta
    result = {
        "id": camera.id,
        "name": camera.name,
        "location": camera.location,
        "status": camera.status,
        "rtsp_url": camera.rtsp_url,
        "is_recording": camera.is_recording,
        "model_name": camera.model_name,
        "created_at": camera.created_at,
        "detection_settings": {
            "confidence_threshold": settings.confidence_threshold if settings else 0.5,
            "min_detection_interval": settings.min_detection_interval if settings else 1,
            "motion_sensitivity": settings.motion_sensitivity if settings else 0.3,
            "detection_classes": settings.detection_classes if settings else ["person", "car", "animal"],
            "notifications_enabled": settings.notifications_enabled if settings else True,
            "save_all_frames": settings.save_all_frames if settings else False,
            "detection_zone": settings.detection_zone if settings else None
        }
    }
    
    return result

@router.put("/{camera_id}", response_model=Dict[str, Any])
async def update_camera(
    camera_data: Dict[str, Any] = Body(...),
    camera_id: str = Path(..., description="ID da câmera"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Atualiza uma câmera existente."""
    # Buscar a câmera
    camera = db.query(Camera).filter(
        Camera.id == camera_id,
        Camera.user_id == current_user["id"]
    ).first()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Câmera não encontrada ou não pertence ao usuário atual"
        )
    
    # Atualizar campos principais da câmera
    if "name" in camera_data:
        camera.name = camera_data["name"]
    
    if "location" in camera_data:
        camera.location = camera_data["location"]
    
    if "rtsp_url" in camera_data:
        camera.rtsp_url = camera_data["rtsp_url"]
    
    if "model_name" in camera_data:
        camera.model_name = camera_data["model_name"]
    
    if "is_recording" in camera_data:
        camera.is_recording = camera_data["is_recording"]
    
    # Atualizar configurações se fornecidas
    if "detection_settings" in camera_data:
        settings = db.query(CameraSettings).filter(CameraSettings.camera_id == camera.id).first()
        
        if not settings:
            # Criar configurações se não existirem
            settings = CameraSettings(
                id=str(uuid.uuid4()),
                camera_id=camera.id
            )
            db.add(settings)
        
        detection_settings = camera_data["detection_settings"]
        
        if "confidence_threshold" in detection_settings:
            settings.confidence_threshold = detection_settings["confidence_threshold"]
        
        if "min_detection_interval" in detection_settings:
            settings.min_detection_interval = detection_settings["min_detection_interval"]
        
        if "motion_sensitivity" in detection_settings:
            settings.motion_sensitivity = detection_settings["motion_sensitivity"]
        
        if "detection_classes" in detection_settings:
            settings.detection_classes = detection_settings["detection_classes"]
        
        if "notifications_enabled" in detection_settings:
            settings.notifications_enabled = detection_settings["notifications_enabled"]
        
        if "save_all_frames" in detection_settings:
            settings.save_all_frames = detection_settings["save_all_frames"]
        
        if "detection_zone" in detection_settings:
            settings.detection_zone = detection_settings["detection_zone"]
    
    # Salvar alterações
    camera.updated_at = datetime.now()
    db.commit()
    
    # Recarregar para obter valores atualizados
    db.refresh(camera)
    settings = db.query(CameraSettings).filter(CameraSettings.camera_id == camera.id).first()
    
    # Formatar resposta
    result = {
        "id": camera.id,
        "name": camera.name,
        "location": camera.location,
        "status": camera.status,
        "rtsp_url": camera.rtsp_url,
        "is_recording": camera.is_recording,
        "model_name": camera.model_name,
        "created_at": camera.created_at,
        "updated_at": camera.updated_at,
        "detection_settings": {
            "confidence_threshold": settings.confidence_threshold if settings else 0.5,
            "min_detection_interval": settings.min_detection_interval if settings else 1,
            "motion_sensitivity": settings.motion_sensitivity if settings else 0.3,
            "detection_classes": settings.detection_classes if settings else ["person", "car", "animal"],
            "notifications_enabled": settings.notifications_enabled if settings else True,
            "save_all_frames": settings.save_all_frames if settings else False,
            "detection_zone": settings.detection_zone if settings else None
        },
        "message": "Câmera atualizada com sucesso"
    }
    
    return result

@router.delete("/{camera_id}", response_model=Dict[str, Any])
async def delete_camera(
    camera_id: str = Path(..., description="ID da câmera"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove uma câmera."""
    # Buscar a câmera
    camera = db.query(Camera).filter(
        Camera.id == camera_id,
        Camera.user_id == current_user["id"]
    ).first()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Câmera não encontrada ou não pertence ao usuário atual"
        )
    
    # Excluir a câmera (as configurações serão excluídas em cascata)
    db.delete(camera)
    db.commit()
    
    return {
        "message": "Câmera removida com sucesso",
        "id": camera_id
    }

@router.get("/{camera_id}/settings", response_model=Dict[str, Any])
async def get_camera_settings(
    camera_id: str = Path(..., description="ID da câmera"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtém as configurações de detecção de uma câmera."""
    # Verificar se a câmera existe e pertence ao usuário
    camera = db.query(Camera).filter(
        Camera.id == camera_id,
        Camera.user_id == current_user["id"]
    ).first()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Câmera não encontrada ou não pertence ao usuário atual"
        )
    
    # Buscar configurações
    settings = db.query(CameraSettings).filter(CameraSettings.camera_id == camera.id).first()
    
    # Se não houver configurações, retornar valores padrão
    if not settings:
        return {
            "confidence_threshold": 0.5,
            "min_detection_interval": 1,
            "motion_sensitivity": 0.3,
            "detection_classes": ["person", "car", "animal"],
            "notifications_enabled": True,
            "save_all_frames": False,
            "detection_zone": None
        }
    
    # Retornar configurações
    return {
        "confidence_threshold": settings.confidence_threshold,
        "min_detection_interval": settings.min_detection_interval,
        "motion_sensitivity": settings.motion_sensitivity,
        "detection_classes": settings.detection_classes,
        "notifications_enabled": settings.notifications_enabled,
        "save_all_frames": settings.save_all_frames,
        "detection_zone": settings.detection_zone
    }

@router.put("/{camera_id}/settings", response_model=Dict[str, Any])
async def update_camera_settings(
    settings_data: Dict[str, Any] = Body(...),
    camera_id: str = Path(..., description="ID da câmera"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Atualiza as configurações de detecção de uma câmera."""
    # Verificar se a câmera existe e pertence ao usuário
    camera = db.query(Camera).filter(
        Camera.id == camera_id,
        Camera.user_id == current_user["id"]
    ).first()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Câmera não encontrada ou não pertence ao usuário atual"
        )
    
    # Buscar ou criar configurações
    settings = db.query(CameraSettings).filter(CameraSettings.camera_id == camera.id).first()
    
    if not settings:
        settings = CameraSettings(
            id=str(uuid.uuid4()),
            camera_id=camera.id
        )
        db.add(settings)
    
    # Atualizar configurações
    if "confidence_threshold" in settings_data:
        settings.confidence_threshold = settings_data["confidence_threshold"]
    
    if "min_detection_interval" in settings_data:
        settings.min_detection_interval = settings_data["min_detection_interval"]
    
    if "motion_sensitivity" in settings_data:
        settings.motion_sensitivity = settings_data["motion_sensitivity"]
    
    if "detection_classes" in settings_data:
        settings.detection_classes = settings_data["detection_classes"]
    
    if "notifications_enabled" in settings_data:
        settings.notifications_enabled = settings_data["notifications_enabled"]
    
    if "save_all_frames" in settings_data:
        settings.save_all_frames = settings_data["save_all_frames"]
    
    if "detection_zone" in settings_data:
        settings.detection_zone = settings_data["detection_zone"]
    
    # Salvar alterações
    db.commit()
    db.refresh(settings)
    
    # Retornar configurações atualizadas
    return {
        "confidence_threshold": settings.confidence_threshold,
        "min_detection_interval": settings.min_detection_interval,
        "motion_sensitivity": settings.motion_sensitivity,
        "detection_classes": settings.detection_classes,
        "notifications_enabled": settings.notifications_enabled,
        "save_all_frames": settings.save_all_frames,
        "detection_zone": settings.detection_zone,
        "message": "Configurações atualizadas com sucesso"
    } 