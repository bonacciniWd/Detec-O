"""
Módulo de gerenciamento de câmeras e detecção de objetos.

Este módulo gerencia a conexão com câmeras e implementa a detecção de objetos,
pessoas e comportamentos suspeitos usando YOLO e análise de movimento.
"""

import cv2
import numpy as np
import time
import asyncio
import logging
from datetime import datetime
from ultralytics import YOLO
import face_recognition
# from ..db.database import save_detection_event, get_person_records  # Temporariamente comentado
from .pose_analyzer import analyze_hand_movements
from ..utils.config import get_cameras
import os
from threading import Thread
import torch
import base64
from dotenv import load_dotenv
from typing import Dict, List, Optional
import threading # Certificar que está importado

# Configurar logging
logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente
load_dotenv()

# Configurações do sistema
is_local_webcam = os.getenv('USE_LOCAL_WEBCAM', 'true').lower() == 'true'

# Adicionar um Lock para acesso concorrente aos frames
frame_lock = threading.Lock()

# Variáveis globais
# 'cameras' agora rastreia apenas o estado de execução das câmeras iniciadas
running_cameras_status: Dict[str, dict] = {} 

# Variáveis globais
model = None
face_database = {}
visit_times = {}

class HandMovementAnalyzer:
    def __init__(self):
        self.prev_frame = None
        self.prev_time = None
        self.movement_history = []
        self.history_size = 30  # Tamanho do histórico de movimentos
        self.frame_count = 0
        self.detection_interval = 5  # Executar detecção a cada 5 frames para economizar recursos

    def analyze_frame(self, frame, detected_objects):
        # Implementação do método analyze_frame
        return False

# Inicializar o analisador de movimentos de mão
hand_analyzer = HandMovementAnalyzer()

class SimpleDetector:
    def __init__(self):
        self.model = None
        self.classes = []

    def detect(self, frame):
        # Implementação simplificada da detecção
        return []

    def draw_detections(self, frame, detections):
        # Implementação simplificada do desenho das detecções
        return frame

# Inicializar o detector simplificado AQUI:
yolo_detector = SimpleDetector()

# Modificar start_camera para receber URL e location
async def start_camera_process(camera_id: str, url: str, location: Optional[str]):
    """Inicia o processamento de uma câmera específica."""
    global running_cameras_status

    if camera_id in running_cameras_status and running_cameras_status[camera_id].get("running", False):
        logger.warning(f"Tentativa de iniciar câmera {camera_id} que já está rodando.")
        return False # Já rodando
    
    try:
        logger.info(f"Iniciando captura de vídeo para câmera {camera_id} ({url}) - Local: {location}")
        cap = cv2.VideoCapture(url) 
        if not cap.isOpened():
            raise ValueError(f"Não foi possível abrir stream de vídeo: {url}")
        
        # Atualizar/Adicionar estado da câmera em execução
        running_cameras_status[camera_id] = {
            "running": True,
            "url": url,
            "location": location,
            "thread": None, # Armazenará a thread
            "start_time": time.time(), # Registrar hora de início
            "last_frame": None, # Inicializar campo para último frame JPEG
            "error": None # Campo para armazenar erros da thread
        }
        
        # Iniciar thread de processamento
        import threading # Mover import para cá se não estiver global
        thread = threading.Thread(
            target=process_camera_feed,
            args=(camera_id, cap, location or camera_id) # Passar location ou ID como nome da janela
        )
        thread.daemon = True
        running_cameras_status[camera_id]["thread"] = thread
        thread.start()
        logger.info(f"Thread de processamento iniciada para câmera {camera_id}.")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao iniciar câmera {camera_id}: {str(e)}")
        # Limpar estado se falhar ao iniciar
        if camera_id in running_cameras_status:
             running_cameras_status[camera_id]["running"] = False
        return False

# Modificar stop_camera
async def stop_camera_process(camera_id: str):
    """Para o processamento de uma câmera específica."""
    global running_cameras_status

    if camera_id in running_cameras_status and running_cameras_status[camera_id].get("running", False):
        logger.info(f"Parando processamento da câmera {camera_id}.")
        running_cameras_status[camera_id]["running"] = False
        # Aqui precisaríamos de uma forma de sinalizar a thread para parar e talvez dar join(),
        # mas a lógica atual da thread verifica running_cameras_status[camera_id]["running"].
        # A thread deve limpar seu próprio estado em 'finally'.
        # A remoção da chave do dict pode ser feita aqui ou na thread.
        # Considerar remover a entrada após a thread confirmar que parou, se necessário.
        # del running_cameras_status[camera_id] # Cuidado com race conditions
        return True
    else:
        logger.warning(f"Tentativa de parar câmera {camera_id} que não está rodando.")
        return False

# Renomear get_camera_status para refletir o que ela retorna
# Ou criar uma nova função para obter apenas o status de execução
def get_running_camera_statuses() -> Dict[str, dict]:
    """Retorna o status atual das câmeras que estão sendo processadas."""
    # Retorna uma cópia para evitar modificações externas indesejadas
    return running_cameras_status.copy()

def process_camera_feed(camera_id, cap, window_title):
    # Criar uma janela nomeada para exibição se for webcam local
    if is_local_webcam:
        window_name = f"Camera: {window_title} (ID: {camera_id})"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 800, 600)
    
    # Inicializar contadores e estado
    frame_count = 0
    detection_interval = 5  # Executar detecção a cada 5 frames para economizar recursos
    
    try:
        # Usar running_cameras_status em vez de 'cameras' global
        while running_cameras_status.get(camera_id, {}).get("running", False):
            # Ler frame da câmera
            ret, frame = cap.read()
            
            if not ret:
                logger.warning(f"Erro ao ler frame da câmera {camera_id}")
                # Tentar reconectar algumas vezes antes de desistir
                reconnect_attempts = 0
                while reconnect_attempts < 5 and running_cameras_status.get(camera_id, {}).get("running", False):
                    time.sleep(2)
                    cap.release()
                    cap = cv2.VideoCapture(running_cameras_status[camera_id]["url"])
                    ret, frame = cap.read()
                    if ret:
                        break
                    reconnect_attempts += 1
                
                if not ret:
                    logger.error(f"Falha permanente na câmera {camera_id} após tentativas de reconexão")
                    with frame_lock:
                        if camera_id in running_cameras_status:
                            running_cameras_status[camera_id]["error"] = "Falha permanente na leitura da câmera."
                            running_cameras_status[camera_id]["running"] = False # Parar se falhar
                    break
            
            # Incrementar contador de frames
            frame_count += 1
            
            # Executar detecção em intervalos para economizar CPU
            if frame_count % detection_interval == 0:
                # Detectar objetos com detector simplificado
                detected_objects = yolo_detector.detect(frame)
                
                # Frame para mostrar com detecções
                detection_frame = frame.copy()
                
                # Processar detecções
                for obj in detected_objects:
                    # Extrair informações
                    class_name = obj.get('class_name', '')
                    confidence = obj.get('confidence', 0)
                    x1, y1, x2, y2 = obj.get('bbox', (0, 0, 0, 0))
                    
                    # Desenhar caixa de detecção
                    color = (0, 255, 0)  # Verde para objetos normais
                    
                    # Desenhar caixa delimitadora e texto
                    cv2.rectangle(detection_frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(
                        detection_frame, 
                        f"{class_name} {confidence:.2f}", 
                        (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.5, 
                        color, 
                        2
                    )
                
                # Analisar movimentos de mão suspeitos
                if hand_analyzer.analyze_frame(frame, detected_objects):
                    # Registrar evento de movimento suspeito
                    event_data = {
                        "event_type": "suspicious_hand_movement",
                        "camera_id": camera_id,
                        "timestamp": datetime.now(),
                        "details": "Movimento suspeito de mão detectado",
                        "location": window_title
                    }
                    
                    asyncio.run_coroutine_threadsafe(
                        save_detection_event(event_data),
                        asyncio.get_event_loop()
                    )
            
            # Exibir frame com detecções se for webcam local
            if is_local_webcam and frame_count % detection_interval == 0:
                cv2.imshow(window_name, detection_frame)
                
            # Verificar se a janela foi fechada
            key = cv2.waitKey(1) & 0xFF
            if key == 27: # ESC
                 break
            if cv2.getWindowProperty(window_title, cv2.WND_PROP_VISIBLE) < 1:
                logger.info(f"Janela {window_title} fechada pelo usuário.")
                break
                
            # Codificar o frame (com ou sem detecções) como JPEG
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80] # Qualidade JPEG (0-100)
            result, encoded_jpeg = cv2.imencode('.jpg', detection_frame, encode_param)
            
            if result:
                # Armazenar o frame JPEG codificado de forma thread-safe
                with frame_lock:
                    if camera_id in running_cameras_status:
                         running_cameras_status[camera_id]["last_frame"] = encoded_jpeg.tobytes()
            
            # Pequena pausa para não sobrecarregar CPU se o loop for muito rápido
            # Ajustar conforme necessário, pode depender do frame rate da câmera
            time.sleep(0.01) 

    except Exception as e:
        logger.error(f"Erro no loop de processamento da câmera {camera_id}: {str(e)}")
        with frame_lock:
            if camera_id in running_cameras_status:
                 running_cameras_status[camera_id]["error"] = str(e)
                 running_cameras_status[camera_id]["running"] = False # Parar se der erro
    
    finally:
        # Liberar recursos
        cap.release()
        
        # Fechar janela se for webcam local
        if is_local_webcam:
            cv2.destroyWindow(window_name)
        
        # Atualizar o status final no dicionário global
        # A remoção pode ser feita aqui ou em stop_camera_process
        with frame_lock:
            if camera_id in running_cameras_status:
                running_cameras_status[camera_id]["running"] = False
                running_cameras_status[camera_id]["thread"] = None # Limpar referência da thread
                # Não limpar last_frame aqui, pode ser útil ver o último frame antes de parar
            
        logger.info(f"Processamento da câmera {camera_id} (Thread) finalizado.")

def load_face_database_from_db():
    """Carrega o banco de dados de faces do MongoDB."""
    try:
        # Buscar registros de pessoas no banco
        person_records = get_person_records()
        
        # Converter registros para o formato esperado pelo face_recognition
        known_faces = []
        for record in person_records:
            if 'face_encoding' in record and record['face_encoding']:
                # Converter a string base64 de volta para bytes
                face_bytes = base64.b64decode(record['face_encoding'])
                # Converter bytes para numpy array
                face_encoding = np.frombuffer(face_bytes, dtype=np.float64)
                known_faces.append({
                    'name': record['name'],
                    'face_encoding': face_encoding,
                    'id': str(record['_id'])
                })
        
        return known_faces
    except Exception as e:
        print(f"Erro ao carregar banco de faces: {e}")
        return [] 

# Nova função para obter o último frame de uma câmera específica
def get_latest_frame(camera_id: str) -> Optional[bytes]:
    """Obtém o último frame JPEG armazenado para uma câmera, de forma thread-safe."""
    with frame_lock: # Adquire o lock antes de acessar
        status = running_cameras_status.get(camera_id)
        if status and status.get("running"):
            return status.get("last_frame")
        return None 