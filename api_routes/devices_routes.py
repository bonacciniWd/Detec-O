"""
Rotas para descoberta e gerenciamento de dispositivos de câmera.
Estas rotas permitem que o frontend descubra câmeras na rede e gerencie conexões.
"""

# Banco de dados simulado para modelos de IA
AI_MODELS_DB = {
    "1": {
        "id": "1",
        "name": "YOLOv8n",
        "description": "Modelo leve para detecção de objetos baseado em YOLOv8",
        "file_path": "models/yolov8n.pt",
        "classes": ["person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat"],
        "size_mb": 6.2,
        "speed_rating": "Rápido",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    },
    "2": {
        "id": "2",
        "name": "YOLOv8s",
        "description": "Modelo para detecção de objetos com equilíbrio entre velocidade e precisão",
        "file_path": "models/yolov8s.pt",
        "classes": ["person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat"],
        "size_mb": 12.6,
        "speed_rating": "Médio",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    },
    "3": {
        "id": "3",
        "name": "YOLOv8m",
        "description": "Modelo avançado para detecção de objetos com alta precisão",
        "file_path": "models/yolov8m.pt",
        "classes": ["person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat"],
        "size_mb": 25.4,
        "speed_rating": "Lento",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }
}

# Configurações de IA para câmeras
AI_SETTINGS_DB = {}

@router.get("/v1/ai/models")
async def get_ai_models():
    """
    Retorna a lista de todos os modelos de IA disponíveis.
    """
    logger.info("Recebida solicitação para listar modelos de IA")
    
    # Retornar modelos simulados
    return list(AI_MODELS_DB.values())

@router.get("/v1/cameras/{camera_id}/ai-settings")
async def get_camera_ai_settings(camera_id: str):
    """
    Obtém as configurações de IA para uma câmera específica.
    """
    logger.info(f"Recebida solicitação para obter configurações de IA da câmera {camera_id}")
    
    if camera_id not in DEVICES_DB:
        raise HTTPException(status_code=404, detail="Câmera não encontrada")
    
    # Se não existirem configurações, criar padrão
    if camera_id not in AI_SETTINGS_DB:
        AI_SETTINGS_DB[camera_id] = {
            "enabled": True,
            "model_id": "1",  # YOLOv8n como padrão
            "confidence_threshold": 0.4,
            "use_gpu": True,
            "enable_tracking": True
        }
    
    return AI_SETTINGS_DB[camera_id]

@router.put("/v1/cameras/{camera_id}/ai-settings")
async def update_camera_ai_settings(camera_id: str, settings: dict):
    """
    Atualiza as configurações de IA para uma câmera específica.
    """
    logger.info(f"Recebida solicitação para atualizar configurações de IA da câmera {camera_id}")
    
    if camera_id not in DEVICES_DB:
        raise HTTPException(status_code=404, detail="Câmera não encontrada")
    
    # Verificar se o modelo existe
    if "model_id" in settings and settings["model_id"] not in AI_MODELS_DB:
        raise HTTPException(status_code=404, detail="Modelo de IA não encontrado")
    
    # Atualizar ou criar configurações
    if camera_id not in AI_SETTINGS_DB:
        AI_SETTINGS_DB[camera_id] = {
            "enabled": True,
            "model_id": "1",
            "confidence_threshold": 0.4,
            "use_gpu": True,
            "enable_tracking": True
        }
    
    # Atualizar valores
    for key, value in settings.items():
        AI_SETTINGS_DB[camera_id][key] = value
    
    return AI_SETTINGS_DB[camera_id] 