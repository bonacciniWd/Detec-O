from fastapi import APIRouter, Depends, HTTPException, status, Path, Query, Body, File, UploadFile
from typing import List, Optional, Dict, Any
from ..db.database import get_database
from ..models.detection_settings import (
    DetectionSettingsCreate, 
    DetectionSettingsUpdate,
    DetectionSettingsResponse,
    DetectionZone
)
from ..services.auth import get_current_user, get_current_active_user
from ..models.user import User
from ..services.detection_service import DetectionService, detection_service
from bson import ObjectId
from datetime import datetime
import uuid
import json

# Criar o router
router = APIRouter(
    prefix="/api/v1/detection-settings",
    tags=["detection_settings"],
    responses={404: {"description": "Not found"}},
)

# Banco de dados simulado para configurações
SETTINGS_DB = []

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

@router.get("/", response_model=dict)
async def get_detection_settings(
    current_user: dict = Depends(get_current_user)
):
    """
    Obtém as configurações de detecção do usuário atual.
    Se não existirem configurações, retorna as configurações padrão.
    """
    # Buscar configurações do usuário atual
    user_settings = next((settings for settings in SETTINGS_DB 
                         if settings["user_id"] == current_user["id"]), None)
    
    # Se não existir, criar configurações padrão
    if not user_settings:
        settings_id = str(uuid.uuid4())
        now = datetime.now()
        
        user_settings = {
            "id": settings_id,
            "user_id": current_user["id"],
            "detection_interval": 10,  # Intervalo entre detecções em segundos
            "confidence_threshold": 0.5,  # Limiar de confiança para detecções
            "sensitivity": "medium",  # Sensibilidade do detector (low, medium, high)
            "notify_on_detection": True,  # Notificar quando uma detecção ocorrer
            "detect_people": True,  # Detectar pessoas
            "detect_weapons": True,  # Detectar armas
            "detect_vehicles": False,  # Detectar veículos
            "detect_animals": False,  # Detectar animais
            "detect_suspicious": True,  # Detectar comportamento suspeito
            "created_at": now,
            "updated_at": now
        }
        
        # Adicionar ao banco de dados simulado
        SETTINGS_DB.append(user_settings)
    
    return user_settings

@router.put("/", response_model=dict)
async def update_detection_settings(
    settings: Dict = Body(..., description="Configurações de detecção a serem atualizadas"),
    current_user: dict = Depends(get_current_user)
):
    """
    Atualiza as configurações de detecção do usuário atual.
    """
    # Verificar campos obrigatórios
    required_fields = [
        "detection_interval", "confidence_threshold", "sensitivity", 
        "notify_on_detection", "detect_people", "detect_weapons"
    ]
    
    for field in required_fields:
        if field not in settings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Campo obrigatório ausente: {field}"
            )
    
    # Validar valores
    if settings["detection_interval"] < 1 or settings["detection_interval"] > 3600:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Intervalo de detecção deve estar entre 1 e 3600 segundos"
        )
    
    if settings["confidence_threshold"] < 0.1 or settings["confidence_threshold"] > 1.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limiar de confiança deve estar entre 0.1 e 1.0"
        )
    
    if settings["sensitivity"] not in ["low", "medium", "high"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sensibilidade deve ser 'low', 'medium' ou 'high'"
        )
    
    # Buscar configurações existentes do usuário
    settings_idx = None
    for idx, s in enumerate(SETTINGS_DB):
        if s["user_id"] == current_user["id"]:
            settings_idx = idx
            break
    
    now = datetime.now()
    
    if settings_idx is not None:
        # Atualizar configurações existentes
        for key, value in settings.items():
            SETTINGS_DB[settings_idx][key] = value
        
        # Atualizar timestamp
        SETTINGS_DB[settings_idx]["updated_at"] = now
        
        return SETTINGS_DB[settings_idx]
    else:
        # Criar novas configurações
        settings_id = str(uuid.uuid4())
        
        new_settings = {
            "id": settings_id,
            "user_id": current_user["id"],
            "created_at": now,
            "updated_at": now,
            **settings
        }
        
        # Adicionar ao banco de dados simulado
        SETTINGS_DB.append(new_settings)
        
        return new_settings

@router.get("/camera/{camera_id}", response_model=dict)
async def get_camera_detection_settings(
    camera_id: str = Path(..., description="ID da câmera"),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtém as configurações de detecção específicas de uma câmera.
    Se não existirem configurações específicas, retorna as configurações globais do usuário.
    """
    # Verificar câmeras existentes do usuário
    from .cameras import CAMERA_DB
    camera = next((cam for cam in CAMERA_DB 
                   if cam["id"] == camera_id and cam["user_id"] == current_user["id"]), None)
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Câmera não encontrada ou não pertence ao usuário atual"
        )
    
    # Buscar configurações específicas da câmera
    camera_settings = next((settings for settings in SETTINGS_DB 
                           if settings.get("camera_id") == camera_id), None)
    
    # Se não existir, retornar configurações globais do usuário
    if not camera_settings:
        return await get_detection_settings(current_user)
    
    return camera_settings

@router.put("/camera/{camera_id}", response_model=dict)
async def update_camera_detection_settings(
    camera_id: str = Path(..., description="ID da câmera"),
    settings: Dict = Body(..., description="Configurações de detecção a serem atualizadas"),
    current_user: dict = Depends(get_current_user)
):
    """
    Atualiza as configurações de detecção específicas de uma câmera.
    """
    # Verificar câmeras existentes do usuário
    from .cameras import CAMERA_DB
    camera = next((cam for cam in CAMERA_DB 
                   if cam["id"] == camera_id and cam["user_id"] == current_user["id"]), None)
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Câmera não encontrada ou não pertence ao usuário atual"
        )
    
    # Verificar campos obrigatórios
    required_fields = [
        "detection_interval", "confidence_threshold", "sensitivity", 
        "notify_on_detection", "detect_people", "detect_weapons"
    ]
    
    for field in required_fields:
        if field not in settings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Campo obrigatório ausente: {field}"
            )
    
    # Validar valores
    if settings["detection_interval"] < 1 or settings["detection_interval"] > 3600:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Intervalo de detecção deve estar entre 1 e 3600 segundos"
        )
    
    if settings["confidence_threshold"] < 0.1 or settings["confidence_threshold"] > 1.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limiar de confiança deve estar entre 0.1 e 1.0"
        )
    
    if settings["sensitivity"] not in ["low", "medium", "high"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sensibilidade deve ser 'low', 'medium' ou 'high'"
        )
    
    # Buscar configurações existentes da câmera
    settings_idx = None
    for idx, s in enumerate(SETTINGS_DB):
        if s.get("camera_id") == camera_id:
            settings_idx = idx
            break
    
    now = datetime.now()
    
    if settings_idx is not None:
        # Atualizar configurações existentes
        for key, value in settings.items():
            SETTINGS_DB[settings_idx][key] = value
        
        # Atualizar timestamp
        SETTINGS_DB[settings_idx]["updated_at"] = now
        
        return SETTINGS_DB[settings_idx]
    else:
        # Criar novas configurações específicas para a câmera
        settings_id = str(uuid.uuid4())
        
        new_settings = {
            "id": settings_id,
            "user_id": current_user["id"],
            "camera_id": camera_id,
            "created_at": now,
            "updated_at": now,
            **settings
        }
        
        # Adicionar ao banco de dados simulado
        SETTINGS_DB.append(new_settings)
        
        return new_settings

@router.delete("/camera/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera_detection_settings(
    camera_id: str = Path(..., description="ID da câmera"),
    current_user: dict = Depends(get_current_user)
):
    """
    Exclui as configurações de detecção específicas de uma câmera.
    A câmera passará a usar as configurações globais do usuário.
    """
    # Verificar câmeras existentes do usuário
    from .cameras import CAMERA_DB
    camera = next((cam for cam in CAMERA_DB 
                   if cam["id"] == camera_id and cam["user_id"] == current_user["id"]), None)
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Câmera não encontrada ou não pertence ao usuário atual"
        )
    
    # Buscar configurações específicas da câmera
    settings_idx = None
    for idx, s in enumerate(SETTINGS_DB):
        if s.get("camera_id") == camera_id and s["user_id"] == current_user["id"]:
            settings_idx = idx
            break
    
    if settings_idx is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configurações específicas não encontradas para esta câmera"
        )
    
    # Remover configurações
    SETTINGS_DB.pop(settings_idx)
    
    return 

# Endpoint para obter as configurações de detecção de uma câmera
@router.get("/cameras/{camera_id}/settings", response_model=DetectionSettingsResponse)
async def get_camera_detection_settings(
    camera_id: str = Path(..., description="ID da câmera"),
    current_user: User = Depends(get_current_active_user)
):
    """Obtém as configurações de detecção para uma câmera específica."""
    settings = await detection_service.get_settings(current_user.id, camera_id)
    if not settings:
        raise HTTPException(status_code=404, detail="Configurações não encontradas")
    return settings

# Endpoint para atualizar as configurações de detecção de uma câmera
@router.put("/cameras/{camera_id}/settings", response_model=DetectionSettingsResponse)
async def update_camera_detection_settings(
    settings_update: DetectionSettingsUpdate,
    camera_id: str = Path(..., description="ID da câmera"),
    current_user: User = Depends(get_current_active_user)
):
    """Atualiza as configurações de detecção para uma câmera específica."""
    updated_settings = await detection_service.update_settings(
        current_user.id, camera_id, settings_update
    )
    if not updated_settings:
        raise HTTPException(status_code=404, detail="Configurações não encontradas ou não puderam ser atualizadas")
    return updated_settings

# Endpoint para gerenciar zonas de detecção

# Obter todas as zonas de detecção para uma câmera
@router.get("/cameras/{camera_id}/detection-zones", response_model=List[DetectionZone])
async def get_detection_zones(
    camera_id: str = Path(..., description="ID da câmera"),
    current_user: User = Depends(get_current_active_user)
):
    """Obtém todas as zonas de detecção configuradas para uma câmera."""
    settings = await detection_service.get_settings(current_user.id, camera_id)
    if not settings:
        raise HTTPException(status_code=404, detail="Configurações não encontradas")
    
    return settings.detection_zones

# Adicionar uma nova zona de detecção
@router.post("/cameras/{camera_id}/detection-zones", response_model=DetectionZone)
async def add_detection_zone(
    zone: DetectionZone,
    camera_id: str = Path(..., description="ID da câmera"),
    current_user: User = Depends(get_current_active_user)
):
    """Adiciona uma nova zona de detecção para uma câmera."""
    settings = await detection_service.get_settings(current_user.id, camera_id)
    if not settings:
        raise HTTPException(status_code=404, detail="Configurações não encontradas")
    
    # Adicionar zona à lista de zonas
    update_data = DetectionSettingsUpdate(
        detection_zones=settings.detection_zones + [zone]
    )
    
    updated_settings = await detection_service.update_settings(
        current_user.id, camera_id, update_data
    )
    
    return zone

# Atualizar uma zona de detecção existente
@router.put("/cameras/{camera_id}/detection-zones/{zone_id}", response_model=DetectionZone)
async def update_detection_zone(
    zone_update: DetectionZone,
    camera_id: str = Path(..., description="ID da câmera"),
    zone_id: str = Path(..., description="ID da zona de detecção"),
    current_user: User = Depends(get_current_active_user)
):
    """Atualiza uma zona de detecção existente."""
    settings = await detection_service.get_settings(current_user.id, camera_id)
    if not settings:
        raise HTTPException(status_code=404, detail="Configurações não encontradas")
    
    # Verificar se a zona existe
    zone_index = next((i for i, z in enumerate(settings.detection_zones) if z.id == zone_id), None)
    if zone_index is None:
        raise HTTPException(status_code=404, detail="Zona de detecção não encontrada")
    
    # Atualizar a zona
    updated_zones = settings.detection_zones.copy()
    updated_zones[zone_index] = zone_update
    
    update_data = DetectionSettingsUpdate(detection_zones=updated_zones)
    updated_settings = await detection_service.update_settings(
        current_user.id, camera_id, update_data
    )
    
    return zone_update

# Excluir uma zona de detecção
@router.delete("/cameras/{camera_id}/detection-zones/{zone_id}", response_model=dict)
async def delete_detection_zone(
    camera_id: str = Path(..., description="ID da câmera"),
    zone_id: str = Path(..., description="ID da zona de detecção"),
    current_user: User = Depends(get_current_active_user)
):
    """Remove uma zona de detecção."""
    settings = await detection_service.get_settings(current_user.id, camera_id)
    if not settings:
        raise HTTPException(status_code=404, detail="Configurações não encontradas")
    
    # Filtrar a zona a ser removida
    updated_zones = [z for z in settings.detection_zones if z.id != zone_id]
    
    # Se o número de zonas não mudar, significa que a zona não foi encontrada
    if len(updated_zones) == len(settings.detection_zones):
        raise HTTPException(status_code=404, detail="Zona de detecção não encontrada")
    
    update_data = DetectionSettingsUpdate(detection_zones=updated_zones)
    updated_settings = await detection_service.update_settings(
        current_user.id, camera_id, update_data
    )
    
    return {"message": "Zona de detecção removida com sucesso"}

# Exportar zonas de detecção
@router.get("/cameras/{camera_id}/detection-zones/export")
async def export_detection_zones(
    camera_id: str = Path(..., description="ID da câmera"),
    current_user: User = Depends(get_current_active_user)
):
    """Exporta as zonas de detecção configuradas para uma câmera no formato JSON."""
    settings = await detection_service.get_settings(current_user.id, camera_id)
    if not settings:
        raise HTTPException(status_code=404, detail="Configurações não encontradas")
    
    return {
        "camera_id": camera_id,
        "detection_zones": settings.detection_zones,
        "ignore_areas": settings.ignore_areas,
        "exported_at": datetime.now().isoformat()
    }

# Importar zonas de detecção
@router.post("/cameras/{camera_id}/detection-zones/import", response_model=dict)
async def import_detection_zones(
    import_data: dict = Body(...),
    camera_id: str = Path(..., description="ID da câmera"),
    current_user: User = Depends(get_current_active_user)
):
    """Importa zonas de detecção para uma câmera a partir de um JSON exportado."""
    settings = await detection_service.get_settings(current_user.id, camera_id)
    if not settings:
        raise HTTPException(status_code=404, detail="Configurações não encontradas")
    
    # Validar os dados importados
    if "detection_zones" not in import_data:
        raise HTTPException(status_code=400, detail="Formato de importação inválido")
    
    # Atualizar as zonas de detecção
    update_data = DetectionSettingsUpdate(
        detection_zones=import_data.get("detection_zones", []),
        ignore_areas=import_data.get("ignore_areas", [])
    )
    
    updated_settings = await detection_service.update_settings(
        current_user.id, camera_id, update_data
    )
    
    return {
        "message": "Zonas de detecção importadas com sucesso",
        "detection_zones_count": len(updated_settings.detection_zones),
        "ignore_areas_count": len(updated_settings.ignore_areas)
    }

# Endpoint para obter o preview da câmera
@router.get("/cameras/{camera_id}/preview")
async def get_camera_preview(
    camera_id: str = Path(..., description="ID da câmera"),
    current_user: User = Depends(get_current_active_user)
):
    """Obtém uma imagem de preview da câmera para configuração de zonas."""
    # Implementação do serviço para obter a imagem da câmera
    image_path = await detection_service.get_camera_preview(current_user.id, camera_id)
    if not image_path:
        raise HTTPException(status_code=404, detail="Preview da câmera não disponível")
    
    # A lógica para retornar a imagem depende da implementação do serviço
    # Pode retornar um arquivo ou um redirecionamento para uma URL
    return {"preview_url": image_path} 