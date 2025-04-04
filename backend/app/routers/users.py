from fastapi import APIRouter, Depends, HTTPException, status, Body, Path, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from ..database import get_db
from ..models.models import User, UserSettings
from ..dependencies import get_current_user
from pydantic import BaseModel, EmailStr
from datetime import datetime

router = APIRouter(prefix="/api/v1/users", tags=["users"])

class UserSettingsModel(BaseModel):
    email_notifications: bool = False
    browser_notifications: bool = True
    mobile_notifications: bool = False
    notification_frequency: str = "immediate"
    dark_mode: bool = False
    compact_view: bool = False
    show_statistics: bool = True
    highlight_detections: bool = True

class UserSettingsResponse(BaseModel):
    notifications: Dict[str, Any]
    detection: Dict[str, Any]
    interface: Dict[str, Any]

@router.get("/{user_id}/settings", response_model=UserSettingsResponse)
async def get_user_settings(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtém as configurações do usuário."""
    # Verificar se o usuário está tentando acessar suas próprias configurações
    if user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para acessar as configurações de outro usuário"
        )
    
    # Buscar o usuário
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Buscar ou criar configurações do usuário
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    
    if not settings:
        # Criar configurações padrão
        settings = UserSettings(user_id=user_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    # Formatar resposta no formato esperado pelo frontend
    response = {
        "notifications": {
            "email": settings.email_notifications,
            "browser": settings.browser_notifications,
            "mobile": settings.mobile_notifications,
            "frequency": settings.notification_frequency
        },
        "detection": {
            "confidenceThreshold": 0.6,  # Valores padrão para detecção
            "minDetectionInterval": 30,
            "motionSensitivity": 5,
            "enableWeaponDetection": True,
            "enableFaceDetection": True,
            "enableBehaviorAnalysis": True
        },
        "interface": {
            "darkMode": settings.dark_mode,
            "compactView": settings.compact_view,
            "showStatistics": settings.show_statistics,
            "highlightDetections": settings.highlight_detections
        }
    }
    
    return response

@router.put("/{user_id}/settings", response_model=UserSettingsResponse)
async def update_user_settings(
    user_id: str,
    settings_data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Atualiza as configurações do usuário."""
    # Verificar se o usuário está tentando atualizar suas próprias configurações
    if user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para atualizar as configurações de outro usuário"
        )
    
    # Buscar o usuário
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Buscar ou criar configurações do usuário
    user_settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    
    if not user_settings:
        user_settings = UserSettings(user_id=user_id)
        db.add(user_settings)
    
    # Atualizar configurações
    if "notifications" in settings_data:
        user_settings.email_notifications = settings_data["notifications"].get("email", user_settings.email_notifications)
        user_settings.browser_notifications = settings_data["notifications"].get("browser", user_settings.browser_notifications)
        user_settings.mobile_notifications = settings_data["notifications"].get("mobile", user_settings.mobile_notifications)
        user_settings.notification_frequency = settings_data["notifications"].get("frequency", user_settings.notification_frequency)
    
    if "interface" in settings_data:
        user_settings.dark_mode = settings_data["interface"].get("darkMode", user_settings.dark_mode)
        user_settings.compact_view = settings_data["interface"].get("compactView", user_settings.compact_view)
        user_settings.show_statistics = settings_data["interface"].get("showStatistics", user_settings.show_statistics)
        user_settings.highlight_detections = settings_data["interface"].get("highlightDetections", user_settings.highlight_detections)
    
    db.commit()
    db.refresh(user_settings)
    
    # Formatar resposta
    response = {
        "notifications": {
            "email": user_settings.email_notifications,
            "browser": user_settings.browser_notifications,
            "mobile": user_settings.mobile_notifications,
            "frequency": user_settings.notification_frequency
        },
        "detection": {
            "confidenceThreshold": 0.6,  # Valores padrão
            "minDetectionInterval": 30,
            "motionSensitivity": 5,
            "enableWeaponDetection": True,
            "enableFaceDetection": True,
            "enableBehaviorAnalysis": True
        },
        "interface": {
            "darkMode": user_settings.dark_mode,
            "compactView": user_settings.compact_view,
            "showStatistics": user_settings.show_statistics,
            "highlightDetections": user_settings.highlight_detections
        }
    }
    
    # Atualizar valores de detecção se fornecidos
    if "detection" in settings_data:
        response["detection"].update(settings_data["detection"])
    
    return response 