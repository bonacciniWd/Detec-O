import os
import cv2
import uuid
import base64
import numpy as np
import logging
import face_recognition
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

from ..models.person import PersonCreate, FaceEncodingCreate, FaceMatchResult

# Diretório para armazenar imagens de faces
FACES_DIR = Path("app/static/faces")
if not FACES_DIR.exists():
    FACES_DIR.mkdir(parents=True, exist_ok=True)

# Cache para encodings faciais carregados
face_encodings_cache = {}
last_cache_update = datetime.now()

def save_face_image(face_image_base64: str, person_id: str) -> Tuple[str, str]:
    """
    Salva a imagem da face e retorna o caminho do arquivo.
    
    Args:
        face_image_base64: Imagem em base64 sem o prefixo (data:image/jpeg;base64,)
        person_id: ID da pessoa
        
    Returns:
        Tuple contendo (face_id, caminho_relativo)
    """
    try:
        # Decodificar imagem base64
        if "base64," in face_image_base64:
            face_image_base64 = face_image_base64.split("base64,")[1]
            
        image_data = base64.b64decode(face_image_base64)
        
        # Criar ID único para esta face
        face_id = str(uuid.uuid4())
        
        # Criar diretório para a pessoa se não existir
        person_dir = FACES_DIR / person_id
        if not person_dir.exists():
            person_dir.mkdir(parents=True, exist_ok=True)
        
        # Salvar imagem
        image_path = person_dir / f"{face_id}.jpg"
        with open(image_path, "wb") as f:
            f.write(image_data)
        
        # Criar e salvar thumbnail
        image_array = np.frombuffer(image_data, dtype=np.uint8)
        img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        # Redimensionar para thumbnail
        thumbnail = cv2.resize(img, (120, 120))
        thumbnail_path = person_dir / f"{face_id}_thumb.jpg"
        cv2.imwrite(str(thumbnail_path), thumbnail)
        
        # Retornar caminhos relativos para armazenamento no banco
        rel_path = f"faces/{person_id}/{face_id}.jpg"
        return face_id, rel_path
        
    except Exception as e:
        logging.error(f"Erro ao salvar imagem da face: {str(e)}")
        raise

def extract_face_encoding(image_path: str) -> Optional[List[float]]:
    """
    Extrai a codificação da face da imagem fornecida.
    
    Args:
        image_path: Caminho para a imagem da face
        
    Returns:
        Lista de floats representando a codificação facial ou None se nenhuma face for detectada
    """
    try:
        # Carregar imagem
        image = face_recognition.load_image_file(image_path)
        
        # Detectar codificações faciais
        face_encodings = face_recognition.face_encodings(image)
        
        if not face_encodings:
            logging.warning(f"Nenhuma face detectada na imagem: {image_path}")
            return None
            
        # Retornar a primeira codificação encontrada
        # Convertemos para lista Python para serialização
        return face_encodings[0].tolist()
        
    except Exception as e:
        logging.error(f"Erro ao extrair codificação facial: {str(e)}")
        return None

def create_person_with_face(db: Session, person_data: PersonCreate, user_id: str) -> Dict[str, Any]:
    """
    Cria uma nova pessoa com uma face inicial.
    
    Args:
        db: Sessão do banco de dados
        person_data: Dados da nova pessoa
        user_id: ID do usuário que está criando a pessoa
        
    Returns:
        Dicionário com os dados da pessoa criada
    """
    from ..crud.person import create_person, add_face_to_person
    
    # Primeiro criar registro da pessoa
    person = create_person(db, person_data, user_id)
    
    # Salvar imagem da face
    face_id, face_path = save_face_image(person_data.face_image, person["id"])
    
    # Extrair codificação facial
    face_encoding = extract_face_encoding(os.path.join("app/static", face_path))
    
    if not face_encoding:
        # Se não foi possível extrair codificação facial, ainda mantemos a pessoa
        # mas registramos o problema
        logging.warning(f"Não foi possível extrair codificação facial para pessoa {person['id']}")
        return person
    
    # Criar registro de face e associar à pessoa
    face_data = {
        "id": face_id,
        "person_id": person["id"],
        "path": face_path,
        "encoding": face_encoding,
        "label": "principal",
        "thumbnail_path": face_path.replace(".jpg", "_thumb.jpg")
    }
    
    # Adicionar face à pessoa
    add_face_to_person(db, face_data)
    
    # Retornar dados da pessoa
    return person

def add_face_encoding(db: Session, face_data: FaceEncodingCreate) -> Dict[str, Any]:
    """
    Adiciona uma nova codificação facial para uma pessoa existente.
    
    Args:
        db: Sessão do banco de dados
        face_data: Dados da nova face
        
    Returns:
        Dicionário com os dados da face adicionada
    """
    from ..crud.person import add_face_to_person, get_person
    
    # Verificar se a pessoa existe
    person = get_person(db, face_data.person_id)
    if not person:
        raise ValueError(f"Pessoa com ID {face_data.person_id} não encontrada")
    
    # Salvar imagem da face
    face_id, face_path = save_face_image(face_data.face_image, face_data.person_id)
    
    # Extrair codificação facial
    face_encoding = extract_face_encoding(os.path.join("app/static", face_path))
    
    if not face_encoding:
        raise ValueError("Não foi possível extrair codificação facial da imagem fornecida")
    
    # Criar registro de face
    face_record = {
        "id": face_id,
        "person_id": face_data.person_id,
        "path": face_path,
        "encoding": face_encoding,
        "label": face_data.label or f"face_{uuid.uuid4().hex[:8]}",
        "thumbnail_path": face_path.replace(".jpg", "_thumb.jpg")
    }
    
    # Adicionar face à pessoa
    face = add_face_to_person(db, face_record)
    
    # Limpar cache para forçar recarregamento
    global last_cache_update
    last_cache_update = datetime.now()
    if face_data.person_id in face_encodings_cache:
        del face_encodings_cache[face_data.person_id]
    
    return face

def load_face_encodings(db: Session) -> Dict[str, Dict[str, Any]]:
    """
    Carrega as codificações faciais do banco de dados e mantém em cache.
    
    Args:
        db: Sessão do banco de dados
        
    Returns:
        Dicionário com as codificações faciais por pessoa
    """
    from ..crud.person import get_all_face_encodings
    
    global face_encodings_cache, last_cache_update
    
    # Verificar se cache está válido (menos de 5 minutos)
    cache_age = (datetime.now() - last_cache_update).total_seconds()
    if face_encodings_cache and cache_age < 300:  # 5 minutos
        return face_encodings_cache
    
    # Recarregar encodings
    logging.info("Recarregando cache de codificações faciais")
    face_encodings_cache = get_all_face_encodings(db)
    last_cache_update = datetime.now()
    
    return face_encodings_cache

def recognize_face(db: Session, face_image_base64: str, confidence_threshold: float = 0.6) -> Optional[FaceMatchResult]:
    """
    Reconhece uma face em uma imagem e retorna a pessoa correspondente.
    
    Args:
        db: Sessão do banco de dados
        face_image_base64: Imagem em base64
        confidence_threshold: Limite de confiança para correspondência (0.0-1.0)
        
    Returns:
        Objeto FaceMatchResult se uma correspondência for encontrada, ou None
    """
    try:
        # Decodificar imagem
        if "base64," in face_image_base64:
            face_image_base64 = face_image_base64.split("base64,")[1]
            
        image_data = base64.b64decode(face_image_base64)
        image_array = np.frombuffer(image_data, dtype=np.uint8)
        img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        # Converter BGR para RGB (face_recognition usa RGB)
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Detectar faces
        face_locations = face_recognition.face_locations(rgb_img)
        
        if not face_locations:
            logging.info("Nenhuma face detectada na imagem")
            return None
        
        # Obter codificação da face detectada
        unknown_encoding = face_recognition.face_encodings(rgb_img, face_locations)[0]
        
        # Carregar codificações conhecidas
        known_encodings = load_face_encodings(db)
        
        # Se não há faces cadastradas, retornar None
        if not known_encodings:
            logging.info("Não há faces cadastradas no sistema")
            return None
        
        # Encontrar a melhor correspondência
        best_match = None
        best_distance = 1.0  # Iniciar com o pior caso (1.0 = sem correspondência)
        
        for person_id, person_data in known_encodings.items():
            for face in person_data["faces"]:
                # Converter encoding de lista para array numpy
                encoding = np.array(face["encoding"])
                
                # Calcular distância (menor é melhor)
                distance = face_recognition.face_distance([encoding], unknown_encoding)[0]
                
                # face_recognition considera distâncias menores que 0.6 como correspondência
                # convertemos para confiança (1.0 - distância)
                confidence = 1.0 - distance
                
                if confidence > confidence_threshold and confidence > (1.0 - best_distance):
                    best_distance = distance
                    best_match = {
                        "person_id": person_id,
                        "person_name": person_data["name"],
                        "match_confidence": confidence,
                        "thumbnail_url": face.get("thumbnail_url"),
                        "category": person_data.get("category", "default")
                    }
        
        if best_match:
            return FaceMatchResult(**best_match)
        
        return None
        
    except Exception as e:
        logging.error(f"Erro ao reconhecer face: {str(e)}")
        return None

def recognize_faces_in_frame(db: Session, frame: np.ndarray, confidence_threshold: float = 0.6) -> List[Dict[str, Any]]:
    """
    Reconhece todas as faces em um frame de vídeo.
    
    Args:
        db: Sessão do banco de dados
        frame: Frame de vídeo como array numpy
        confidence_threshold: Limite de confiança para correspondência (0.0-1.0)
        
    Returns:
        Lista de dicionários com informações sobre cada face reconhecida
    """
    try:
        # Converter BGR para RGB (face_recognition usa RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Detectar faces (localização)
        face_locations = face_recognition.face_locations(rgb_frame)
        
        if not face_locations:
            return []
        
        # Obter codificações das faces detectadas
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        # Carregar codificações conhecidas
        known_encodings = load_face_encodings(db)
        
        # Se não há faces cadastradas, retornar informações de localização apenas
        if not known_encodings:
            return [
                {
                    "bbox": [left, top, right, bottom],
                    "recognized": False
                }
                for (top, right, bottom, left) in face_locations
            ]
        
        results = []
        
        # Para cada face detectada
        for i, (face_encoding, (top, right, bottom, left)) in enumerate(zip(face_encodings, face_locations)):
            # Inicializar com face não reconhecida
            face_info = {
                "bbox": [left, top, right, bottom],
                "recognized": False
            }
            
            # Encontrar a melhor correspondência
            best_match = None
            best_distance = 1.0
            
            for person_id, person_data in known_encodings.items():
                for face in person_data["faces"]:
                    # Converter encoding de lista para array numpy
                    encoding = np.array(face["encoding"])
                    
                    # Calcular distância (menor é melhor)
                    distance = face_recognition.face_distance([encoding], face_encoding)[0]
                    
                    # Converter para confiança
                    confidence = 1.0 - distance
                    
                    if confidence > confidence_threshold and confidence > (1.0 - best_distance):
                        best_distance = distance
                        best_match = {
                            "person_id": person_id,
                            "person_name": person_data["name"],
                            "match_confidence": confidence,
                            "category": person_data.get("category", "default")
                        }
            
            if best_match:
                face_info.update(best_match)
                face_info["recognized"] = True
            
            results.append(face_info)
        
        return results
        
    except Exception as e:
        logging.error(f"Erro ao reconhecer faces no frame: {str(e)}")
        return [] 