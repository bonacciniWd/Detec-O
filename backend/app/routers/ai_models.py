from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import logging
from pathlib import Path as FilePath

from ..dependencies import get_db, get_current_user
from ..models.user import User
from ..models.camera import AIModel, AIModelCreate, AIModelUpdate, AIModelInDB

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


@router.get("/models", response_model=List[AIModelInDB])
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


@router.get("/models/{model_id}", response_model=AIModelInDB)
async def get_model(
    model_id: int = Path(..., description="ID do modelo"),
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


@router.post("/models", response_model=AIModelInDB)
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


@router.put("/models/{model_id}", response_model=AIModelInDB)
async def update_model(
    model_id: int = Path(..., description="ID do modelo"),
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
    model_id: int = Path(..., description="ID do modelo"),
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