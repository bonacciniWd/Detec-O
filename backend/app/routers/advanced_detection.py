from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Path, Query
from typing import List, Optional, Dict, Any
from ..db.database import get_database
from ..auth.dependencies import get_current_user
from ..models.user import User
from ..services.advanced_detection_service import AdvancedDetectionService
from ..services.detection_service import DetectionService
import os
import aiofiles
import uuid
from datetime import datetime
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/advanced-detection",
    tags=["advanced detection"]
)

# Diretório para salvar uploads temporários
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/analyze-image", response_model=Dict[str, Any])
async def analyze_image(
    file: UploadFile = File(...),
    check_similarity: bool = Form(True),
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Analisa uma imagem com modelos avançados para detecção de objetos perigosos,
    comportamentos agressivos ou situações suspeitas.
    """
    try:
        # Criar serviço de detecção avançada
        advanced_detection = AdvancedDetectionService()
        
        # Salvar arquivo temporariamente
        file_extension = os.path.splitext(file.filename)[1]
        temp_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, temp_filename)
        
        # Salvar o arquivo
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        
        # Analisar a imagem
        results = await advanced_detection.analyze_image(file_path)
        
        # Verificar similaridade com objetos perigosos se solicitado
        if check_similarity and results.get("detections"):
            enhanced_detections = []
            for detection in results["detections"]:
                if "class" in detection and "bbox" in detection:
                    similar_class, confidence = await advanced_detection.check_object_similarity(
                        detection["class"],
                        file_path,
                        detection["bbox"]
                    )
                    detection["similar_to"] = similar_class
                    detection["similarity_confidence"] = confidence
                enhanced_detections.append(detection)
            results["detections"] = enhanced_detections
        
        # Adicionar informações do processo
        results["metadata"]["timestamp"] = datetime.utcnow().isoformat()
        results["metadata"]["file_name"] = file.filename
        results["metadata"]["user_id"] = str(current_user["_id"])
        
        # Opcional: registrar o resultado no banco de dados para histórico
        # ou acompanhamento posterior
        
        return results
    
    except Exception as e:
        logger.error(f"Erro ao analisar imagem: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao analisar imagem: {str(e)}"
        )
    finally:
        # Limpar arquivo temporário após uso
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)

@router.post("/analyze-video", response_model=Dict[str, Any])
async def analyze_video(
    file: UploadFile = File(...),
    start_time: float = Form(0),
    duration: float = Form(10),
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Analisa um segmento de vídeo com modelos avançados para detecção de 
    objetos perigosos, comportamentos agressivos ou situações suspeitas.
    """
    try:
        # Criar serviço de detecção avançada
        advanced_detection = AdvancedDetectionService()
        
        # Salvar arquivo temporariamente
        file_extension = os.path.splitext(file.filename)[1]
        temp_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, temp_filename)
        
        # Salvar o arquivo
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        
        # Analisar o vídeo
        results = await advanced_detection.analyze_video_segment(
            file_path,
            start_time,
            duration
        )
        
        # Adicionar informações do processo
        results["video_metadata"]["timestamp"] = datetime.utcnow().isoformat()
        results["video_metadata"]["file_name"] = file.filename
        results["video_metadata"]["user_id"] = str(current_user["_id"])
        
        # Opcional: registrar o resultado no banco de dados para histórico
        
        return results
        
    except Exception as e:
        logger.error(f"Erro ao analisar vídeo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao analisar vídeo: {str(e)}"
        )
    finally:
        # Limpar arquivo temporário após uso
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)

@router.post("/verify-detection", response_model=Dict[str, Any])
async def verify_detection(
    event_id: str = Form(...),
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Realiza uma verificação adicional em uma detecção existente.
    
    Útil quando o sistema genérico detecta algo, mas você quer aplicar um 
    modelo mais especializado para verificar se realmente é um objeto perigoso.
    """
    try:
        # Obter o evento do banco de dados
        from bson import ObjectId
        
        event = await db.events.find_one({
            "_id": ObjectId(event_id),
            "user_id": current_user["_id"]
        })
        
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento não encontrado"
            )
        
        # Verificar se o evento tem uma imagem
        if "image_path" not in event:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Evento não possui imagem para verificação"
            )
        
        # Obter o caminho da imagem
        image_path = event["image_path"]
        
        # Criar serviço de detecção avançada
        advanced_detection = AdvancedDetectionService()
        
        # Analisar a imagem
        results = await advanced_detection.analyze_image(image_path)
        
        # Para cada boundingbox no evento, verificar similaridade
        if "bounding_boxes" in event and results.get("detections"):
            enhanced_detections = []
            
            for bbox in event["bounding_boxes"]:
                if "label" in bbox and "coordinates" in bbox:
                    coords = bbox["coordinates"]
                    # Converter para formato esperado pelo método [x, y, width, height]
                    bbox_format = [
                        coords.get("x", 0),
                        coords.get("y", 0),
                        coords.get("width", 100),
                        coords.get("height", 100)
                    ]
                    
                    similar_class, confidence = await advanced_detection.check_object_similarity(
                        bbox["label"],
                        image_path,
                        bbox_format
                    )
                    
                    enhanced_detections.append({
                        "original_label": bbox["label"],
                        "similar_to": similar_class,
                        "similarity_confidence": confidence,
                        "coordinates": bbox["coordinates"]
                    })
            
            results["enhanced_detections"] = enhanced_detections
        
        # Adicionar informações do processo
        results["metadata"]["verification_timestamp"] = datetime.utcnow().isoformat()
        results["metadata"]["event_id"] = event_id
        results["metadata"]["user_id"] = str(current_user["_id"])
        
        # Opcional: atualizar o evento com os resultados da verificação
        
        return results
        
    except Exception as e:
        logger.error(f"Erro ao verificar detecção: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao verificar detecção: {str(e)}"
        )

@router.get("/model-status", response_model=Dict[str, Any])
async def get_model_status(
    current_user: User = Depends(get_current_user)
):
    """
    Obtém o status dos modelos de detecção avançada disponíveis.
    """
    try:
        # Criar serviço de detecção avançada
        advanced_detection = AdvancedDetectionService()
        
        # Obter status dos modelos
        status = await advanced_detection.get_model_status()
        
        return status
        
    except Exception as e:
        logger.error(f"Erro ao obter status dos modelos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter status dos modelos: {str(e)}"
        ) 