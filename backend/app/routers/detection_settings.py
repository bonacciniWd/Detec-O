from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from typing import List, Optional, Dict, Any
from ..db.database import get_database
from ..models.detection_settings import (
    DetectionSettingsCreate, 
    DetectionSettingsUpdate,
    DetectionSettingsResponse
)
from ..auth.dependencies import get_current_user
from ..models.user import User
from ..services.detection_service import DetectionService
from bson import ObjectId
from datetime import datetime

router = APIRouter(
    prefix="/api/v1/detection-settings",
    tags=["detection settings"]
)

@router.post("/", response_model=DetectionSettingsResponse)
async def create_detection_settings(
    settings: DetectionSettingsCreate,
    camera_id: Optional[str] = Query(None, description="ID da câmera (None para configuração global)"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Cria nova configuração de detecção para o usuário.
    Se camera_id for fornecido, a configuração será específica para aquela câmera.
    Caso contrário, será uma configuração global para todas as câmeras do usuário.
    """
    try:
        # Verificar se já existe configuração para esta câmera/global
        query = {
            "user_id": str(current_user["_id"]),
        }
        
        if camera_id:
            # Verificar se a câmera existe
            camera = await db.cameras.find_one({
                "_id": ObjectId(camera_id),
                "user_id": current_user["_id"]
            })
            
            if not camera:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Câmera não encontrada"
                )
                
            query["camera_id"] = camera_id
        else:
            query["camera_id"] = None
        
        existing_settings = await db.detection_settings.find_one(query)
        
        if existing_settings:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Configuração de detecção já existe para este usuário/câmera. Use o endpoint PUT para atualizar."
            )
        
        # Preparar dados para salvar
        settings_data = settings.dict()
        settings_data["user_id"] = str(current_user["_id"])
        settings_data["camera_id"] = camera_id
        settings_data["created_at"] = datetime.utcnow()
        
        # Salvar configuração
        result = await db.detection_settings.insert_one(settings_data)
        
        # Obter a configuração criada
        created_settings = await db.detection_settings.find_one({"_id": result.inserted_id})
        created_settings["id"] = str(created_settings.pop("_id"))
        
        return created_settings
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar configuração de detecção: {str(e)}"
        )

@router.get("/", response_model=List[DetectionSettingsResponse])
async def get_all_detection_settings(
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Obtém todas as configurações de detecção do usuário."""
    try:
        settings_cursor = db.detection_settings.find({
            "user_id": str(current_user["_id"])
        })
        
        settings_list = []
        async for settings in settings_cursor:
            settings["id"] = str(settings.pop("_id"))
            settings_list.append(settings)
        
        return settings_list
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar configurações de detecção: {str(e)}"
        )

@router.get("/{settings_id}", response_model=DetectionSettingsResponse)
async def get_detection_settings_by_id(
    settings_id: str = Path(..., description="ID da configuração"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Obtém uma configuração de detecção específica pelo ID."""
    try:
        settings = await db.detection_settings.find_one({
            "_id": ObjectId(settings_id),
            "user_id": str(current_user["_id"])
        })
        
        if not settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Configuração de detecção não encontrada"
            )
        
        settings["id"] = str(settings.pop("_id"))
        return settings
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar configuração de detecção: {str(e)}"
        )

@router.get("/camera/{camera_id}", response_model=DetectionSettingsResponse)
async def get_detection_settings_by_camera(
    camera_id: str = Path(..., description="ID da câmera"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Obtém configuração de detecção para uma câmera específica."""
    try:
        # Verificar se a câmera existe
        camera = await db.cameras.find_one({
            "_id": ObjectId(camera_id),
            "user_id": current_user["_id"]
        })
        
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Câmera não encontrada"
            )
        
        # Buscar configuração específica da câmera
        settings = await db.detection_settings.find_one({
            "camera_id": camera_id,
            "user_id": str(current_user["_id"])
        })
        
        # Se não encontrar configuração específica, buscar configuração global
        if not settings:
            settings = await db.detection_settings.find_one({
                "camera_id": None,
                "user_id": str(current_user["_id"])
            })
            
            if not settings:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Nenhuma configuração de detecção encontrada para esta câmera ou global"
                )
        
        settings["id"] = str(settings.pop("_id"))
        return settings
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar configuração de detecção: {str(e)}"
        )

@router.get("/global", response_model=DetectionSettingsResponse)
async def get_global_detection_settings(
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Obtém configuração global de detecção do usuário."""
    try:
        settings = await db.detection_settings.find_one({
            "camera_id": None,
            "user_id": str(current_user["_id"])
        })
        
        if not settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Configuração global de detecção não encontrada"
            )
        
        settings["id"] = str(settings.pop("_id"))
        return settings
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar configuração global de detecção: {str(e)}"
        )

@router.put("/{settings_id}", response_model=DetectionSettingsResponse)
async def update_detection_settings(
    settings_id: str = Path(..., description="ID da configuração"),
    settings: DetectionSettingsCreate = None,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Atualiza uma configuração de detecção pelo ID."""
    try:
        # Verificar se a configuração existe
        existing_settings = await db.detection_settings.find_one({
            "_id": ObjectId(settings_id),
            "user_id": str(current_user["_id"])
        })
        
        if not existing_settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Configuração de detecção não encontrada"
            )
        
        # Preparar dados para atualização
        settings_data = settings.dict()
        settings_data["updated_at"] = datetime.utcnow()
        
        # Atualizar configuração
        await db.detection_settings.update_one(
            {"_id": ObjectId(settings_id)},
            {"$set": settings_data}
        )
        
        # Obter a configuração atualizada
        updated_settings = await db.detection_settings.find_one({"_id": ObjectId(settings_id)})
        updated_settings["id"] = str(updated_settings.pop("_id"))
        
        return updated_settings
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar configuração de detecção: {str(e)}"
        )

@router.patch("/{settings_id}", response_model=DetectionSettingsResponse)
async def patch_detection_settings(
    settings_id: str = Path(..., description="ID da configuração"),
    settings: DetectionSettingsUpdate = None,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Atualiza parcialmente uma configuração de detecção pelo ID."""
    try:
        # Verificar se a configuração existe
        existing_settings = await db.detection_settings.find_one({
            "_id": ObjectId(settings_id),
            "user_id": str(current_user["_id"])
        })
        
        if not existing_settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Configuração de detecção não encontrada"
            )
        
        # Preparar dados para atualização (apenas campos não nulos)
        settings_data = {k: v for k, v in settings.dict().items() if v is not None}
        if settings_data:
            settings_data["updated_at"] = datetime.utcnow()
            
            # Atualizar configuração
            await db.detection_settings.update_one(
                {"_id": ObjectId(settings_id)},
                {"$set": settings_data}
            )
        
        # Obter a configuração atualizada
        updated_settings = await db.detection_settings.find_one({"_id": ObjectId(settings_id)})
        updated_settings["id"] = str(updated_settings.pop("_id"))
        
        return updated_settings
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar configuração de detecção: {str(e)}"
        )

@router.delete("/{settings_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_detection_settings(
    settings_id: str = Path(..., description="ID da configuração"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Remove uma configuração de detecção pelo ID."""
    try:
        # Verificar se a configuração existe
        existing_settings = await db.detection_settings.find_one({
            "_id": ObjectId(settings_id),
            "user_id": str(current_user["_id"])
        })
        
        if not existing_settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Configuração de detecção não encontrada"
            )
        
        # Remover configuração
        await db.detection_settings.delete_one({"_id": ObjectId(settings_id)})
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao remover configuração de detecção: {str(e)}"
        )

@router.get("/statistics", response_model=Dict[str, Any])
async def get_detection_statistics(
    days: int = Query(30, description="Estatísticas dos últimos X dias"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Obtém estatísticas sobre a eficácia do sistema de detecção,
    incluindo a taxa de precisão baseada nos feedbacks dos usuários.
    """
    try:
        # Criar instância do serviço de detecção
        detection_service = DetectionService(db)
        
        # Obter estatísticas
        stats = await detection_service.get_detection_statistics(
            user_id=str(current_user["_id"]),
            days=days
        )
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter estatísticas de detecção: {str(e)}"
        )

@router.get("/potential-threats", response_model=Dict[str, Any])
async def get_potential_threats(
    days: int = Query(7, description="Ameaças dos últimos X dias"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Lista eventos que podem representar ameaças potenciais,
    como objetos que podem ser confundidos com armas ou comportamentos suspeitos.
    """
    try:
        # Consulta para eventos potencialmente perigosos
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = {
            "user_id": current_user["_id"],
            "timestamp": {"$gte": cutoff_date},
            "$or": [
                {"potential_threat": True},
                {"metadata.is_potential_threat": True},
                {"metadata.is_weapon": True},
                {"metadata.is_suspicious": True},
                {"metadata.potential_aggression": True}
            ]
        }
        
        # Buscar eventos
        events_cursor = db.events.find(query).sort("timestamp", -1)
        potential_threats = []
        
        async for event in events_cursor:
            # Convertendo ID do ObjectId para string
            event["id"] = str(event.pop("_id"))
            
            # Convertendo outros ObjectIds
            if "camera_id" in event:
                event["camera_id"] = str(event["camera_id"])
            
            # Adicionando informações da câmera
            if "camera_id" in event:
                camera = await db.cameras.find_one({"_id": ObjectId(event["camera_id"])})
                if camera:
                    event["camera_name"] = camera.get("name")
                    event["camera_location"] = camera.get("location")
            
            potential_threats.append(event)
        
        return {
            "items": potential_threats,
            "total": len(potential_threats),
            "period_days": days
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar ameaças potenciais: {str(e)}"
        ) 