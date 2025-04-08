from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import logging
from pathlib import Path as FilePath

from ..dependencies import get_db, get_current_user
from ..models.user import User
from ..models.models import AIModel
from ..models.camera import CameraAISettings
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(
    prefix="/api/v1/ai",
    tags=["ai"],
    responses={404: {"description": "Not found"}},
)

# Diretório para modelos
MODELS_DIR = FilePath("models")

# Garantir que o diretório existe
if not MODELS_DIR.exists():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Esquemas Pydantic para API
class AIModelBase(BaseModel):
    name: str
    description: Optional[str] = None
    file_path: str
    classes: List[str] = []
    size_mb: Optional[float] = None
    speed_rating: Optional[str] = None

class AIModelCreate(AIModelBase):
    pass

class AIModelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    file_path: Optional[str] = None
    classes: Optional[List[str]] = None
    size_mb: Optional[float] = None
    speed_rating: Optional[str] = None

class AIModelResponse(AIModelBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

@router.get("/models", response_model=List[AIModelResponse])
async def list_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Lista todos os modelos de IA disponíveis.
    """
    try:
        models = db.query(AIModel).offset(skip).limit(limit).all()
        
        # Se não houver modelos, cadastre pelo menos o YOLOv8n como padrão
        if len(models) == 0:
            default_model = AIModel(
                name="YOLOv8n",
                description="Modelo leve para detecção de objetos baseado em YOLOv8",
                file_path=str(MODELS_DIR / "yolov8n.pt"),
                classes=["person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat"],
                size_mb=6.2,
                speed_rating="Rápido"
            )
            db.add(default_model)
            db.commit()
            db.refresh(default_model)
            models = [default_model]
        
        return models
    except Exception as e:
        logging.error(f"Erro ao listar modelos: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao listar modelos")


@router.get("/models/{model_id}", response_model=AIModelResponse)
async def get_model(
    model_id: str = Path(..., description="ID do modelo"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtém um modelo específico pelo ID.
    """
    try:
        model = db.query(AIModel).filter(AIModel.id == model_id).first()
        if not model:
            raise HTTPException(status_code=404, detail="Modelo não encontrado")
        return model
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Erro ao obter modelo: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao obter modelo")


@router.post("/models", response_model=AIModelResponse)
async def create_model(
    model_data: AIModelCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cria um novo modelo no sistema.
    
    Este endpoint é para administradores registrarem manualmente modelos.
    Os modelos reais precisam ser colocados na pasta 'models/'.
    """
    try:
        # Verificar se o arquivo do modelo existe
        file_path = FilePath(model_data.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=400, detail="Arquivo do modelo não encontrado")
        
        # Criar novo modelo
        new_model = AIModel(
            name=model_data.name,
            description=model_data.description,
            file_path=model_data.file_path,
            classes=model_data.classes,
            size_mb=model_data.size_mb,
            speed_rating=model_data.speed_rating
        )
        
        db.add(new_model)
        db.commit()
        db.refresh(new_model)
        
        return new_model
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Erro ao criar modelo: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao criar modelo")


@router.put("/models/{model_id}", response_model=AIModelResponse)
async def update_model(
    model_id: str = Path(..., description="ID do modelo"),
    model_data: AIModelUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Atualiza um modelo existente.
    """
    try:
        model = db.query(AIModel).filter(AIModel.id == model_id).first()
        if not model:
            raise HTTPException(status_code=404, detail="Modelo não encontrado")
        
        # Atualizar campos
        for key, value in model_data.dict(exclude_unset=True).items():
            setattr(model, key, value)
        
        db.commit()
        db.refresh(model)
        
        return model
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Erro ao atualizar modelo: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao atualizar modelo")


@router.delete("/models/{model_id}", status_code=204)
async def delete_model(
    model_id: str = Path(..., description="ID do modelo"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove um modelo do sistema.
    
    Apenas remove o registro, não exclui o arquivo.
    """
    try:
        model = db.query(AIModel).filter(AIModel.id == model_id).first()
        if not model:
            raise HTTPException(status_code=404, detail="Modelo não encontrado")
        
        # Não permitir excluir o modelo padrão se for o único
        if db.query(AIModel).count() <= 1:
            raise HTTPException(status_code=400, detail="Não é possível excluir o único modelo disponível")
        
        db.delete(model)
        db.commit()
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Erro ao excluir modelo: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao excluir modelo")

# Endpoints para configurações de IA por câmera
class AISettingsBase(BaseModel):
    enabled: bool = True
    model_id: Optional[str] = None
    confidence_threshold: float = 0.4
    use_gpu: bool = True
    enable_tracking: bool = True

class AISettingsUpdate(AISettingsBase):
    pass

class AISettingsResponse(AISettingsBase):
    id: str
    camera_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

@router.get("/cameras/{camera_id}/settings", response_model=AISettingsResponse)
async def get_camera_ai_settings(
    camera_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtém as configurações de IA para uma câmera específica.
    """
    try:
        settings = db.query(CameraAISettings).filter(CameraAISettings.camera_id == camera_id).first()
        
        if not settings:
            # Criar configurações padrão
            model = db.query(AIModel).first()
            model_id = model.id if model else None
            
            settings = CameraAISettings(
                camera_id=camera_id,
                model_id=model_id,
                enabled=True,
                confidence_threshold=0.4,
                use_gpu=True,
                enable_tracking=True
            )
            
            db.add(settings)
            db.commit()
            db.refresh(settings)
        
        return settings
    except Exception as e:
        logging.error(f"Erro ao obter configurações de IA: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao obter configurações de IA")

@router.put("/cameras/{camera_id}/settings", response_model=AISettingsResponse)
async def update_camera_ai_settings(
    camera_id: str,
    settings_data: AISettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Atualiza as configurações de IA para uma câmera específica.
    """
    try:
        settings = db.query(CameraAISettings).filter(CameraAISettings.camera_id == camera_id).first()
        
        if not settings:
            # Criar configurações padrão
            settings = CameraAISettings(
                camera_id=camera_id,
                model_id=settings_data.model_id,
                enabled=settings_data.enabled,
                confidence_threshold=settings_data.confidence_threshold,
                use_gpu=settings_data.use_gpu,
                enable_tracking=settings_data.enable_tracking
            )
            
            db.add(settings)
        else:
            # Atualizar campos
            for key, value in settings_data.dict().items():
                setattr(settings, key, value)
        
        db.commit()
        db.refresh(settings)
        
        return settings
    except Exception as e:
        logging.error(f"Erro ao atualizar configurações de IA: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao atualizar configurações de IA") 