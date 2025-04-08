from fastapi import APIRouter, HTTPException, Depends, Body, Path, Query, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Dict, List, Any, Optional
import logging
import io
import cv2
import numpy as np
import json
import base64
import asyncio
from datetime import datetime
import sys
import os

# Adicionar caminho para importar módulos da pasta src
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Importar o detector de objetos perigosos
from src.detection.dangerous_objects_detector import create_detector, DangerousObjectDetector

# Configurar logging
logger = logging.getLogger(__name__)

# Inicializar o router
router = APIRouter(
    prefix="/api/v1/detection",
    tags=["detection"],
    responses={404: {"description": "Not found"}}
)

# Detector global - será inicializado uma única vez
detector = None

# Configurações de detecção para cada câmera
camera_detection_settings = {}

# Histórico de detecções (últimas 100 por câmera)
detection_history = {}

# Contadores de estatísticas
detection_stats = {
    "total_detections": 0,
    "dangerous_objects": 0,
    "suspicious_behaviors": 0,
    "cameras_processed": set()
}

@router.get("/status")
async def get_detection_status():
    """Obter status do sistema de detecção"""
    global detector
    
    # Inicializar detector se necessário
    if detector is None:
        try:
            detector = create_detector()
            detector_status = "running"
        except Exception as e:
            logger.error(f"Erro ao inicializar detector: {str(e)}")
            detector_status = f"error: {str(e)}"
    else:
        detector_status = "running"
    
    return {
        "status": detector_status,
        "num_cameras_configured": len(camera_detection_settings),
        "statistics": {
            "total_detections": detection_stats["total_detections"],
            "dangerous_objects": detection_stats["dangerous_objects"],
            "suspicious_behaviors": detection_stats["suspicious_behaviors"],
            "cameras_processed": len(detection_stats["cameras_processed"])
        },
        "model_info": {
            "path": detector.model_path if detector else None,
            "device": detector.device if detector else None
        }
    }

@router.post("/configure/{camera_id}")
async def configure_detection(
    camera_id: str = Path(..., description="ID da câmera"),
    settings: Dict[str, Any] = Body(..., description="Configurações de detecção")
):
    """Configurar detecção para uma câmera específica"""
    # Validar configurações mínimas
    required_fields = ["enabled", "confidence_threshold"]
    for field in required_fields:
        if field not in settings:
            raise HTTPException(
                status_code=400,
                detail=f"Campo obrigatório ausente: {field}"
            )
    
    # Validar valores
    if settings.get("confidence_threshold", 0) < 0.1 or settings.get("confidence_threshold", 0) > 1.0:
        raise HTTPException(
            status_code=400,
            detail="Limiar de confiança deve estar entre 0.1 e 1.0"
        )
    
    # Adicionar timestamp
    settings["updated_at"] = datetime.now().isoformat()
    
    # Salvar configurações
    camera_detection_settings[camera_id] = settings
    
    # Inicializar histórico de detecções para esta câmera se não existir
    if camera_id not in detection_history:
        detection_history[camera_id] = []
    
    return {
        "camera_id": camera_id,
        "settings": settings,
        "status": "configured"
    }

@router.get("/settings/{camera_id}")
async def get_detection_settings(
    camera_id: str = Path(..., description="ID da câmera")
):
    """Obter configurações de detecção para uma câmera específica"""
    if camera_id not in camera_detection_settings:
        # Retornar configurações padrão
        return {
            "camera_id": camera_id,
            "settings": {
                "enabled": False,
                "confidence_threshold": 0.5,
                "iou_threshold": 0.45,
                "detect_objects": True,
                "detect_behaviors": True,
                "detection_interval": 5,  # Processar a cada 5 frames
                "alert_on_detection": True,
                "object_classes": ["knife", "gun", "scissors"],
                "behavior_classes": ["aggressive_posture", "running", "fighting"],
                "updated_at": datetime.now().isoformat()
            },
            "status": "default"
        }
    
    return {
        "camera_id": camera_id,
        "settings": camera_detection_settings[camera_id],
        "status": "configured"
    }

@router.post("/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    confidence: float = Query(0.5, ge=0.1, le=1.0, description="Limiar de confiança"),
    camera_id: Optional[str] = Query(None, description="ID da câmera (opcional)")
):
    """
    Analisa uma imagem enviada para detecção de objetos perigosos e comportamentos suspeitos.
    Retorna as detecções encontradas.
    """
    global detector, detection_stats
    
    # Inicializar detector se necessário
    if detector is None:
        try:
            detector = create_detector()
        except Exception as e:
            logger.error(f"Erro ao inicializar detector: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao inicializar detector: {str(e)}"
            )
    
    try:
        # Ler a imagem
        image_data = await file.read()
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(
                status_code=400,
                detail="Não foi possível processar a imagem. Verifique se é um formato válido."
            )
        
        # Configurar detector com o limiar de confiança
        detector.confidence_threshold = confidence
        
        # Processar a imagem
        detections, behaviors = detector.process_frame(img)
        
        # Atualizar estatísticas
        detection_stats["total_detections"] += len(detections)
        detection_stats["dangerous_objects"] += sum(1 for d in detections if d["is_dangerous"])
        detection_stats["suspicious_behaviors"] += len(behaviors)
        if camera_id:
            detection_stats["cameras_processed"].add(camera_id)
        
        # Registrar no histórico se tiver camera_id
        if camera_id:
            # Criar entrada de detecção
            detection_entry = {
                "timestamp": datetime.now().isoformat(),
                "camera_id": camera_id,
                "detections": detections,
                "behaviors": behaviors,
                "confidence_threshold": confidence
            }
            
            # Adicionar ao histórico (mantendo apenas as últimas 100)
            detection_history[camera_id] = detection_history.get(camera_id, [])
            detection_history[camera_id].append(detection_entry)
            if len(detection_history[camera_id]) > 100:
                detection_history[camera_id].pop(0)
        
        # Desenhar resultados na imagem
        result_img = detector.draw_detections(img, detections, behaviors)
        
        # Converter imagem para base64
        _, buffer = cv2.imencode('.jpg', result_img)
        result_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Retornar resultados
        return {
            "image_result": f"data:image/jpeg;base64,{result_base64}",
            "detections": detections,
            "behaviors": behaviors,
            "timestamp": datetime.now().isoformat(),
            "statistics": {
                "inference_time": detector.last_inference_time,
                "num_detections": len(detections),
                "num_behaviors": len(behaviors)
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao analisar imagem: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao analisar imagem: {str(e)}"
        )

@router.get("/history/{camera_id}")
async def get_detection_history(
    camera_id: str = Path(..., description="ID da câmera"),
    limit: int = Query(10, ge=1, le=100, description="Número de eventos a retornar")
):
    """Obter histórico de detecções para uma câmera específica"""
    if camera_id not in detection_history or not detection_history[camera_id]:
        return {
            "camera_id": camera_id,
            "events": [],
            "count": 0
        }
    
    # Obter os últimos eventos até o limite
    events = detection_history[camera_id][-limit:]
    
    return {
        "camera_id": camera_id,
        "events": events,
        "count": len(events)
    }

@router.get("/stats")
async def get_detection_stats():
    """Obter estatísticas de detecção"""
    global detection_stats
    
    # Retornar estatísticas
    return {
        "total_detections": detection_stats["total_detections"],
        "dangerous_objects": detection_stats["dangerous_objects"],
        "suspicious_behaviors": detection_stats["suspicious_behaviors"],
        "cameras_processed": len(detection_stats["cameras_processed"]),
        "camera_ids": list(detection_stats["cameras_processed"]),
        "num_cameras_configured": len(camera_detection_settings)
    }

@router.post("/reset_stats")
async def reset_detection_stats():
    """Resetar estatísticas de detecção"""
    global detection_stats
    
    # Resetar estatísticas
    old_stats = detection_stats.copy()
    detection_stats = {
        "total_detections": 0,
        "dangerous_objects": 0,
        "suspicious_behaviors": 0,
        "cameras_processed": set()
    }
    
    return {
        "message": "Estatísticas resetadas com sucesso",
        "previous_stats": {
            "total_detections": old_stats["total_detections"],
            "dangerous_objects": old_stats["dangerous_objects"],
            "suspicious_behaviors": old_stats["suspicious_behaviors"],
            "cameras_processed": len(old_stats["cameras_processed"])
        }
    } 