import asyncio
import cv2
import time
import logging
import numpy as np
import os
import json
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional, Tuple
import threading
import queue

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logging.warning("YOLO não encontrado. Algumas funcionalidades de detecção estarão indisponíveis.")

from ..models.camera import Camera, AIModel
from ..database import SessionLocal
from ..models.event import Event
from .connectors.factory import ConnectorFactory
from .point_in_polygon import point_in_polygon
from .face_service import recognize_faces_in_frame

# Pasta para armazenar snapshots
SNAPSHOT_DIR = Path("app/static/snapshots")
if not SNAPSHOT_DIR.exists():
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

# Diretório para modelos
MODELS_DIR = Path("models")
if not MODELS_DIR.exists():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Cache para modelos carregados
model_cache: Dict[str, Any] = {}

# Dicionário de processadores por câmera
processors: Dict[int, 'VideoProcessor'] = {}

# Fila de eventos para processamento assíncrono
event_queue = queue.Queue()


class VideoProcessor:
    """
    Classe para processamento de vídeo com IA.
    """
    def __init__(self, camera_id: int):
        """
        Inicializa um processador de vídeo para uma câmera específica.
        
        Args:
            camera_id: ID da câmera
        """
        self.camera_id = camera_id
        self.camera: Optional[Camera] = None
        self.model = None
        self.model_path = None
        self.running = False
        self.frame_queue = queue.Queue(maxsize=5)
        self.last_frame = None
        self.last_detections = []
        self.fps = 0
        self.processing_thread = None
        self.capture_thread = None
        self.connector = None
        self.stream_url = None
        self.cap = None
        self.last_event_time = {}  # Dict[str, datetime]
        
        # Configurações de reconhecimento facial
        self.face_recognition_enabled = False
        self.face_recognition_confidence = 0.6
        self.face_recognition_interval = 10  # Segundos entre reconhecimentos
        self.last_face_recognition_time = datetime.now()
        self.recognized_faces = []  # Lista de faces reconhecidas no último frame
        
        # Carregar configurações da câmera
        self._load_camera()
    
    def _load_camera(self):
        """
        Carrega as informações da câmera do banco de dados.
        """
        with SessionLocal() as db:
            self.camera = db.query(Camera).filter(Camera.id == self.camera_id).first()
            
            if not self.camera:
                raise ValueError(f"Câmera com ID {self.camera_id} não encontrada")
            
            # Carregar modelo de IA
            if self.camera.ai_enabled and self.camera.ai_model_id:
                ai_model = db.query(AIModel).filter(AIModel.id == self.camera.ai_model_id).first()
                if ai_model:
                    self.model_path = ai_model.file_path
            
            # Configurar reconhecimento facial
            if hasattr(self.camera, 'face_recognition_enabled'):
                self.face_recognition_enabled = self.camera.face_recognition_enabled
                
            if hasattr(self.camera, 'face_recognition_confidence'):
                self.face_recognition_confidence = self.camera.face_recognition_confidence
                
            if hasattr(self.camera, 'face_recognition_interval'):
                self.face_recognition_interval = self.camera.face_recognition_interval
    
    def _load_model(self):
        """
        Carrega o modelo de IA se necessário.
        """
        if not YOLO_AVAILABLE:
            logging.error("YOLO não está disponível. Não é possível carregar o modelo.")
            return False
        
        if not self.model_path:
            logging.warning(f"Modelo não especificado para câmera {self.camera_id}")
            return False
        
        # Verificar se o modelo já está em cache
        if self.model_path in model_cache:
            self.model = model_cache[self.model_path]
            logging.info(f"Modelo {self.model_path} carregado do cache")
            return True
        
        # Carregar novo modelo
        try:
            # Construir caminho completo se necessário
            if not os.path.isabs(self.model_path):
                full_path = MODELS_DIR / self.model_path
            else:
                full_path = Path(self.model_path)
            
            if not full_path.exists():
                logging.error(f"Arquivo de modelo não encontrado: {full_path}")
                return False
            
            # Carregar modelo YOLO com GPU se disponível
            self.model = YOLO(str(full_path))
            model_cache[self.model_path] = self.model
            logging.info(f"Modelo {self.model_path} carregado com sucesso")
            return True
        
        except Exception as e:
            logging.error(f"Erro ao carregar modelo: {str(e)}")
            return False
    
    async def connect(self):
        """
        Conecta à câmera e inicia o streaming.
        """
        try:
            # Criar conector
            self.connector = ConnectorFactory.create_connector(
                type=self.camera.connector_type,
                ip_address=self.camera.ip_address,
                port=self.camera.port,
                username=self.camera.username,
                password=self.camera.password
            )
            
            # Conectar ao dispositivo
            await self.connector.connect()
            
            # Obter informações do dispositivo
            device_info = await self.connector.get_device_info()
            
            # Listar streams disponíveis
            streams = await self.connector.list_streams()
            
            if not streams:
                logging.error(f"Nenhum stream disponível para a câmera {self.camera_id}")
                return False
            
            # Usar o primeiro stream como padrão
            self.stream_url = streams[0].url
            
            # Atualizar status da câmera no banco de dados
            with SessionLocal() as db:
                camera = db.query(Camera).filter(Camera.id == self.camera_id).first()
                if camera:
                    camera.status = "online"
                    camera.last_connection = datetime.now()
                    db.commit()
            
            return True
        
        except Exception as e:
            logging.error(f"Erro ao conectar à câmera {self.camera_id}: {str(e)}")
            
            # Atualizar status da câmera no banco de dados
            with SessionLocal() as db:
                camera = db.query(Camera).filter(Camera.id == self.camera_id).first()
                if camera:
                    camera.status = "error"
                    db.commit()
            
            return False
    
    def _capture_frames(self):
        """
        Thread para capturar frames do stream de vídeo.
        """
        self.cap = cv2.VideoCapture(self.stream_url)
        
        if not self.cap.isOpened():
            logging.error(f"Não foi possível abrir o stream da câmera {self.camera_id}")
            return
        
        frame_count = 0
        start_time = time.time()
        
        while self.running:
            ret, frame = self.cap.read()
            
            if not ret:
                logging.warning(f"Erro ao ler frame da câmera {self.camera_id}")
                time.sleep(1)
                # Tentar reconectar
                self.cap.release()
                self.cap = cv2.VideoCapture(self.stream_url)
                continue
            
            # Calcular FPS
            frame_count += 1
            elapsed_time = time.time() - start_time
            if elapsed_time >= 1.0:
                self.fps = frame_count / elapsed_time
                frame_count = 0
                start_time = time.time()
            
            # Usar Queue para enviar o frame para o thread de processamento
            if not self.frame_queue.full():
                self.frame_queue.put(frame)
            
            # Manter o último frame para snapshots
            self.last_frame = frame
            
            # Controlar taxa de quadros
            time.sleep(0.03)  # ~30 FPS max
    
    def _process_frames(self):
        """
        Thread para processar frames capturados.
        """
        db = SessionLocal()
        
        try:
            while self.running:
                # Obter frame da fila
                try:
                    frame = self.frame_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Processar frame se o modelo estiver carregado e a detecção estiver habilitada
                if self.model and self.camera.detection_enabled:
                    self._process_frame_with_model(frame, db)
                
                # Processar reconhecimento facial se habilitado
                if self.face_recognition_enabled:
                    self._process_face_recognition(frame, db)
                
                # Marcar tarefa como concluída
                self.frame_queue.task_done()
        
        finally:
            db.close()
    
    def _process_frame_with_model(self, frame: np.ndarray, db: Session):
        """
        Processa um frame com o modelo YOLO.
        
        Args:
            frame: Frame a ser processado
            db: Sessão do banco de dados
        """
        # Executar inferência
        results = self.model(frame)
        
        # Extrair detecções
        detections = []
        
        for result in results:
            # Converter para formato padrão
            boxes = result.boxes
            
            for i, box in enumerate(boxes):
                # Obter informações da detecção
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = result.names[class_id]
                
                # Verificar confiança mínima
                if confidence < self.camera.confidence_threshold:
                    continue
                
                # Verificar classe nas classes habilitadas (se configurado)
                if hasattr(self.camera, 'enabled_classes') and self.camera.enabled_classes:
                    if class_name not in self.camera.enabled_classes:
                        continue
                
                # Verificar zonas de detecção
                detection_zones = self.camera.detection_zones if hasattr(self.camera, 'detection_zones') else []
                
                # Calcular ponto central do objeto
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                
                # Se houver zonas, verificar se o objeto está em alguma delas
                in_any_zone = False
                if detection_zones:
                    for zone in detection_zones:
                        if point_in_polygon(center_x, center_y, zone['points']):
                            in_any_zone = True
                            break
                    
                    # Pular se não estiver em nenhuma zona e zonas estiverem configuradas
                    if not in_any_zone:
                        continue
                
                # Adicionar à lista de detecções
                detections.append({
                    'class_id': class_id,
                    'class_name': class_name,
                    'confidence': confidence,
                    'bbox': [x1, y1, x2, y2],
                    'center': [center_x, center_y]
                })
        
        # Atualizar detecções
        self.last_detections = detections
        
        # Verificar se deve criar evento
        self._check_and_create_events(frame, detections, db)
    
    def _process_face_recognition(self, frame: np.ndarray, db: Session):
        """
        Processa reconhecimento facial em um frame.
        
        Args:
            frame: Frame a ser processado
            db: Sessão do banco de dados
        """
        # Verificar intervalo de tempo desde o último reconhecimento
        now = datetime.now()
        time_since_last = (now - self.last_face_recognition_time).total_seconds()
        
        if time_since_last < self.face_recognition_interval:
            return
        
        # Executar reconhecimento facial
        recognized_faces = recognize_faces_in_frame(
            db, frame, confidence_threshold=self.face_recognition_confidence
        )
        
        # Atualizar estado
        self.recognized_faces = recognized_faces
        self.last_face_recognition_time = now
        
        # Criar eventos para pessoas reconhecidas
        for face in recognized_faces:
            if face.get('recognized', False):
                # Criar um evento para pessoa reconhecida
                self._create_face_recognition_event(frame, face, db)
    
    def _create_face_recognition_event(self, frame: np.ndarray, face: Dict[str, Any], db: Session):
        """
        Cria um evento para uma face reconhecida.
        
        Args:
            frame: Frame onde a face foi detectada
            face: Informações da face reconhecida
            db: Sessão do banco de dados
        """
        # Verificar se já criamos um evento para esta pessoa recentemente
        person_id = face.get('person_id')
        if not person_id:
            return
            
        # Verificar limite de tempo entre eventos (intervalo mínimo de 60 segundos por pessoa)
        now = datetime.now()
        last_event_time = self.last_event_time.get(f"face_{person_id}")
        
        if last_event_time and (now - last_event_time).total_seconds() < 60:
            return
        
        # Extrair informações
        person_name = face.get('person_name', 'Desconhecido')
        confidence = face.get('match_confidence', 0.0)
        bbox = face.get('bbox', [0, 0, 0, 0])
        category = face.get('category', 'default')
        
        # Criar snapshot com anotações
        snapshot_path = self._create_snapshot_with_face(frame, face, f"face_{person_id}")
        
        if not snapshot_path:
            return
        
        # Criar evento
        event_data = {
            'camera_id': self.camera_id,
            'event_type': 'face_recognition',
            'confidence': confidence,
            'timestamp': now,
            'image_path': snapshot_path,
            'bounding_boxes': [
                {
                    'class_name': f"face_{person_name}",
                    'confidence': confidence,
                    'bbox': bbox
                }
            ],
            'metadata': {
                'person_id': person_id,
                'person_name': person_name,
                'category': category
            }
        }
        
        # Adicionar à fila de eventos
        event_queue.put((db, event_data))
        
        # Atualizar último tempo de evento para esta pessoa
        self.last_event_time[f"face_{person_id}"] = now
    
    def _check_and_create_events(self, frame: np.ndarray, detections: List[Dict[str, Any]], db: Session):
        """
        Verifica se deve criar eventos com base nas detecções.
        
        Args:
            frame: Frame onde as detecções foram feitas
            detections: Lista de detecções
            db: Sessão do banco de dados
        """
        # Agrupar detecções por classe
        detections_by_class = {}
        for detection in detections:
            class_name = detection['class_name']
            if class_name not in detections_by_class:
                detections_by_class[class_name] = []
            detections_by_class[class_name].append(detection)
        
        # Verificar cada classe
        for class_name, class_detections in detections_by_class.items():
            # Verificar limite de tempo entre eventos (intervalo mínimo de 10 segundos por classe)
            now = datetime.now()
            last_event_time = self.last_event_time.get(class_name)
            
            if last_event_time and (now - last_event_time).total_seconds() < 10:
                continue
            
            # Escolher detecção com maior confiança
            best_detection = max(class_detections, key=lambda d: d['confidence'])
            
            # Criar snapshot com anotações
            snapshot_path = self._create_snapshot_with_detection(frame, class_detections, class_name)
            
            if not snapshot_path:
                continue
            
            # Criar evento
            event_data = {
                'camera_id': self.camera_id,
                'event_type': class_name,
                'confidence': best_detection['confidence'],
                'timestamp': now,
                'image_path': snapshot_path,
                'bounding_boxes': [
                    {
                        'class_name': d['class_name'],
                        'confidence': d['confidence'],
                        'bbox': d['bbox']
                    }
                    for d in class_detections
                ],
                'metadata': {}
            }
            
            # Adicionar à fila de eventos
            event_queue.put((db, event_data))
            
            # Atualizar último tempo de evento para esta classe
            self.last_event_time[class_name] = now
    
    def _create_snapshot_with_detection(self, frame: np.ndarray, detections: List[Dict[str, Any]], class_name: str) -> Optional[str]:
        """
        Cria um snapshot com anotações das detecções.
        
        Args:
            frame: Frame onde as detecções foram feitas
            detections: Lista de detecções
            class_name: Nome da classe
            
        Returns:
            Caminho relativo para o snapshot ou None em caso de erro
        """
        try:
            # Criar cópia do frame
            annotated_frame = frame.copy()
            
            # Desenhar cada detecção
            for detection in detections:
                x1, y1, x2, y2 = [int(coord) for coord in detection['bbox']]
                confidence = detection['confidence']
                
                # Desenhar retângulo
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Desenhar texto
                text = f"{detection['class_name']} {confidence:.2f}"
                cv2.putText(annotated_frame, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Criar nome de arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"camera_{self.camera_id}_{class_name}_{timestamp}.jpg"
            snapshot_path = SNAPSHOT_DIR / filename
            
            # Salvar imagem
            cv2.imwrite(str(snapshot_path), annotated_frame)
            
            # Retornar caminho relativo
            return f"snapshots/{filename}"
        
        except Exception as e:
            logging.error(f"Erro ao criar snapshot: {str(e)}")
            return None
    
    def _create_snapshot_with_face(self, frame: np.ndarray, face: Dict[str, Any], face_id: str) -> Optional[str]:
        """
        Cria um snapshot com anotações de face.
        
        Args:
            frame: Frame onde a face foi detectada
            face: Informações da face
            face_id: ID da face (normalmente person_id)
            
        Returns:
            Caminho relativo para o snapshot ou None em caso de erro
        """
        try:
            # Criar cópia do frame
            annotated_frame = frame.copy()
            
            # Extrair informações
            bbox = face.get('bbox', [0, 0, 0, 0])
            person_name = face.get('person_name', 'Desconhecido')
            confidence = face.get('match_confidence', 0.0)
            
            # Desenhar retângulo
            x1, y1, x2, y2 = [int(coord) for coord in bbox]
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            
            # Desenhar texto
            text = f"{person_name} {confidence:.2f}"
            cv2.putText(annotated_frame, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            # Criar nome de arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"camera_{self.camera_id}_{face_id}_{timestamp}.jpg"
            snapshot_path = SNAPSHOT_DIR / filename
            
            # Salvar imagem
            cv2.imwrite(str(snapshot_path), annotated_frame)
            
            # Retornar caminho relativo
            return f"snapshots/{filename}"
        
        except Exception as e:
            logging.error(f"Erro ao criar snapshot de face: {str(e)}")
            return None
    
    def start(self):
        """
        Inicia o processamento de vídeo.
        """
        if self.running:
            return
        
        # Carregar modelo
        if self.camera.detection_enabled:
            if not self._load_model():
                logging.error(f"Erro ao carregar modelo para câmera {self.camera_id}")
        
        # Iniciar threads
        self.running = True
        self.capture_thread = threading.Thread(target=self._capture_frames)
        self.processing_thread = threading.Thread(target=self._process_frames)
        
        self.capture_thread.daemon = True
        self.processing_thread.daemon = True
        
        self.capture_thread.start()
        self.processing_thread.start()
        
        logging.info(f"Processador de vídeo iniciado para câmera {self.camera_id}")
    
    def stop(self):
        """
        Para o processamento de vídeo.
        """
        if not self.running:
            return
        
        self.running = False
        
        # Aguardar threads terminarem
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)
        
        if self.processing_thread:
            self.processing_thread.join(timeout=2.0)
        
        # Liberar recursos
        if self.cap:
            self.cap.release()
        
        logging.info(f"Processador de vídeo parado para câmera {self.camera_id}")
    
    def get_snapshot(self) -> Optional[np.ndarray]:
        """
        Obtém o último frame capturado.
        
        Returns:
            Array numpy com o frame ou None se não houver frame
        """
        return self.last_frame
    
    def get_processed_snapshot(self) -> Optional[np.ndarray]:
        """
        Obtém o último frame com anotações de detecção.
        
        Returns:
            Array numpy com o frame anotado ou None se não houver frame
        """
        if self.last_frame is None or not self.last_detections:
            return self.last_frame
        
        # Criar cópia do frame
        annotated_frame = self.last_frame.copy()
        
        # Desenhar detecções
        for detection in self.last_detections:
            x1, y1, x2, y2 = [int(coord) for coord in detection['bbox']]
            confidence = detection['confidence']
            
            # Desenhar retângulo
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Desenhar texto
            text = f"{detection['class_name']} {confidence:.2f}"
            cv2.putText(annotated_frame, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Desenhar faces reconhecidas
        for face in self.recognized_faces:
            if face.get('recognized', False):
                bbox = face.get('bbox', [0, 0, 0, 0])
                person_name = face.get('person_name', 'Desconhecido')
                confidence = face.get('match_confidence', 0.0)
                
                # Desenhar retângulo
                x1, y1, x2, y2 = [int(coord) for coord in bbox]
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                
                # Desenhar texto
                text = f"{person_name} {confidence:.2f}"
                cv2.putText(annotated_frame, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        return annotated_frame


# Thread para processar eventos em segundo plano
def process_events():
    while True:
        try:
            # Obter evento da fila
            db, event_data = event_queue.get(timeout=1.0)
            
            # Criar evento no banco de dados
            _create_event(db, event_data)
            
            # Marcar tarefa como concluída
            event_queue.task_done()
            
        except queue.Empty:
            time.sleep(0.1)
        
        except Exception as e:
            logging.error(f"Erro ao processar evento: {str(e)}")


def _create_event(db: Session, event_data: Dict[str, Any]):
    """
    Cria um evento no banco de dados.
    
    Args:
        db: Sessão do banco de dados
        event_data: Dados do evento
    """
    try:
        # Adicionar severidade com base no tipo de evento
        if 'person' in event_data['event_type'].lower() or 'face' in event_data['event_type'].lower():
            event_data['severity'] = 'red'  # Pessoas e faces são críticos
        elif 'vehicle' in event_data['event_type'].lower():
            event_data['severity'] = 'yellow'  # Veículos são média severidade
        else:
            event_data['severity'] = 'blue'  # Outros são informativos
        
        # Buscar nome da câmera
        camera = db.query(Camera).filter(Camera.id == event_data['camera_id']).first()
        camera_name = camera.name if camera else f"Camera {event_data['camera_id']}"
        
        # Serializar dados
        metadata = json.dumps(event_data['metadata'])
        bounding_boxes = json.dumps(event_data['bounding_boxes'])
        
        # Inserir no banco
        db.execute(
            """
            INSERT INTO events (
                camera_id, event_type, confidence, timestamp, image_path,
                bounding_boxes, metadata, severity, camera_name
            )
            VALUES (
                :camera_id, :event_type, :confidence, :timestamp, :image_path,
                :bounding_boxes, :metadata, :severity, :camera_name
            )
            """,
            {
                "camera_id": str(event_data['camera_id']),
                "event_type": event_data['event_type'],
                "confidence": event_data['confidence'],
                "timestamp": event_data['timestamp'],
                "image_path": event_data['image_path'],
                "bounding_boxes": bounding_boxes,
                "metadata": metadata,
                "severity": event_data['severity'],
                "camera_name": camera_name
            }
        )
        db.commit()
        
        logging.info(f"Evento criado: {event_data['event_type']} na câmera {event_data['camera_id']}")
        
    except Exception as e:
        logging.error(f"Erro ao criar evento: {str(e)}")
        db.rollback()


# Iniciar thread de processamento de eventos
event_thread = threading.Thread(target=process_events)
event_thread.daemon = True
event_thread.start()


def get_processor(camera_id: int) -> VideoProcessor:
    """
    Obtém ou cria um processador de vídeo para uma câmera.
    
    Args:
        camera_id: ID da câmera
        
    Returns:
        Instância de VideoProcessor
    """
    if camera_id not in processors:
        processors[camera_id] = VideoProcessor(camera_id)
    
    return processors[camera_id]


def start_all_processors():
    """
    Inicia processadores para todas as câmeras com detecção habilitada.
    """
    with SessionLocal() as db:
        cameras = db.query(Camera).filter(Camera.detection_enabled == True).all()
        
        for camera in cameras:
            processor = get_processor(camera.id)
            processor.start()
            
    logging.info(f"Iniciados {len(cameras)} processadores de vídeo")


def stop_all_processors():
    """
    Para todos os processadores de vídeo.
    """
    for camera_id, processor in processors.items():
        processor.stop()
    
    processors.clear()
    logging.info("Todos os processadores de vídeo foram parados") 