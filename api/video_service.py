# api/video_service.py
import cv2
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import io  # Para trabalhar com bytes em memória
import threading # Para rodar em background
import time      # Para adicionar delays
from typing import Optional, Dict, List
import os # Para construir caminhos de arquivo
from ultralytics import YOLO # Importar YOLO
from datetime import datetime # Para timestamp do evento
import uuid # Para nomes de arquivo únicos

# Importar modelos do mesmo diretório (api)
# Assumindo que models.py está em api/
try:
    from . import models, schemas
except ImportError:
    # Fallback se rodar diretamente (menos provável)
    import models
    import schemas

# Definir caminho base para snapshots
SNAPSHOTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snapshots")
# Criar diretório se não existir
os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

def get_camera_snapshot_bytes(db: Session, camera_id: str) -> bytes:
    """
    Conecta a uma câmera via RTSP, captura um frame e retorna como bytes JPEG.

    Args:
        db: Sessão do banco de dados SQLAlchemy.
        camera_id: ID da câmera a ser conectada.

    Returns:
        Bytes da imagem JPEG do snapshot.

    Raises:
        HTTPException 404: Se a câmera não for encontrada.
        HTTPException 400: Se a câmera não tiver URL RTSP.
        HTTPException 503: Se não for possível conectar ao stream RTSP ou ler um frame.
    """
    print(f"[Video Service] Tentando obter snapshot para camera_id: {camera_id}")

    # 1. Buscar a câmera no banco de dados
    db_camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()

    if not db_camera:
        print(f"[Video Service] Câmera não encontrada: {camera_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Câmera não encontrada")

    if not db_camera.rtsp_url:
        print(f"[Video Service] Câmera {camera_id} não possui URL RTSP definida.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL RTSP não configurada para esta câmera."
        )

    rtsp_url = db_camera.rtsp_url
    print(f"[Video Service] Conectando a: {rtsp_url} usando backend FFMPEG")

    # 2. Tentar conectar e capturar frame
    cap = None
    try:
        # Forçar o uso do backend FFMPEG
        cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

        if not cap.isOpened():
            print(f"[Video Service] Falha ao abrir VideoCapture com FFMPEG para: {rtsp_url}")
            # Levantar exceção específica (será pega pelo FastAPI)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Não foi possível conectar ao stream RTSP da câmera (falha ao abrir com FFMPEG)."
            )

        # Ler um frame
        ret, frame = cap.read()

        if not ret or frame is None:
            print(f"[Video Service] Falha ao ler frame de: {rtsp_url}")
            # Levantar exceção específica (será pega pelo FastAPI)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Conectado ao stream RTSP, mas falha ao ler o frame."
            )

        print(f"[Video Service] Frame capturado com sucesso para: {rtsp_url}")

        # 3. Codificar o frame como JPEG
        is_success, buffer = cv2.imencode(".jpg", frame)

        if not is_success:
            print(f"[Video Service] Falha ao codificar frame como JPEG.")
            # Levantar exceção específica (será pega pelo FastAPI)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao codificar o frame capturado como JPEG."
            )

        # Converter buffer numpy para bytes
        image_bytes = io.BytesIO(buffer).getvalue()
        return image_bytes

    except HTTPException as http_exc:
        # Repassar HTTPExceptions já tratadas diretamente
        raise http_exc 
    except Exception as e:
        # Capturar apenas exceções *inesperadas* e retornar 500
        print(f"[Video Service] Exceção inesperada durante captura/codificação: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro inesperado ao processar snapshot: {e}"
        )
    finally:
        if cap is not None and cap.isOpened():
            cap.release()
            print(f"[Video Service] Recurso VideoCapture liberado para: {rtsp_url}")

# --- Classe para Processamento de Câmera --- 

class CameraProcessor:
    """Gerencia a conexão e o loop de processamento para uma única câmera."""
    
    def __init__(self, camera_id: str, db_session_factory):
        """
        Inicializa o processador.
        
        Args:
            camera_id: O ID da câmera a ser processada.
            db_session_factory: Uma função que cria uma nova sessão SQLAlchemy 
                                  (necessário para acesso ao DB na thread).
        """
        self.camera_id = camera_id
        self.db_session_factory = db_session_factory
        self.camera_info: models.Camera = None # Será carregado
        self.rtsp_url: str = None
        self.ai_settings: dict = {} # Configurações de IA
        self.detection_settings: dict = {} # Configurações de detecção
        
        self._capture: cv2.VideoCapture = None
        self._thread: threading.Thread = None
        self._stop_event: threading.Event = threading.Event()
        self._is_running: bool = False
        self._last_error: Optional[str] = None
        self._model = None # Atributo para guardar o modelo carregado

    def _load_config(self) -> bool:
        """Carrega a configuração da câmera do banco de dados."""
        # Criar uma nova sessão DB para esta thread/operação
        db = self.db_session_factory()
        try:
            print(f"[{self.camera_id}] Carregando configuração do DB...")
            self.camera_info = db.query(models.Camera).filter(models.Camera.id == self.camera_id).first()
            if not self.camera_info:
                self._last_error = "Câmera não encontrada no DB."
                print(f"[{self.camera_id}] Erro: {self._last_error}")
                return False
            if not self.camera_info.rtsp_url:
                 self._last_error = "URL RTSP não definida para a câmera."
                 print(f"[{self.camera_id}] Erro: {self._last_error}")
                 return False
                 
            self.rtsp_url = self.camera_info.rtsp_url
            # Carregar settings (usar defaults se não existirem no DB)
            default_ai = schemas.AISettingsBase().dict()
            self.ai_settings = {**default_ai, **(self.camera_info.ai_settings or {})}
            
            default_detection = schemas.DetectionSettingsBase().dict()
            self.detection_settings = {**default_detection, **(self.camera_info.detection_settings or {})}
            
            print(f"[{self.camera_id}] Configuração carregada. RTSP: {self.rtsp_url}")
            return True
        except Exception as e:
            self._last_error = f"Erro ao carregar config do DB: {e}"
            print(f"[{self.camera_id}] Erro: {self._last_error}")
            return False
        finally:
            db.close()

    def start(self) -> bool:
        """Inicia o loop de processamento em uma thread separada."""
        if self._is_running:
            print(f"[{self.camera_id}] Processador já está rodando.")
            return True
        
        if not self._load_config(): # Carrega config antes de iniciar
             print(f"[{self.camera_id}] Falha ao carregar configuração. Não iniciando.")
             return False
             
        if not self.ai_settings.get('enabled', False):
             print(f"[{self.camera_id}] Processamento de IA desabilitado nas configurações. Não iniciando.")
             self._last_error = "Processamento de IA desabilitado."
             return False

        # --- Carregar Modelo de IA --- 
        model_id = self.ai_settings.get("model_id")
        use_gpu = self.ai_settings.get("use_gpu", True) # Default para GPU se disponível
        
        if not model_id:
            self._last_error = "Nenhum ID de modelo definido nas configurações de IA."
            print(f"[{self.camera_id}] Erro: {self._last_error}")
            return False
            
        # Assumindo que a pasta 'ai_models' está no mesmo nível que 'video_service.py' (ou seja, dentro de 'api/')
        # Ajustar o path base se necessário
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, "ai_models", model_id)
        print(f"[{self.camera_id}] Tentando carregar modelo de: {model_path}")

        try:
            # TODO: Considerar como lidar com o dispositivo (GPU/CPU) de forma mais robusta
            # device = 'cuda' if use_gpu and torch.cuda.is_available() else 'cpu'
            self._model = YOLO(model_path) # Carrega o modelo
            # Pode forçar CPU com: self._model = YOLO(model_path).to('cpu')
            print(f"[{self.camera_id}] Modelo {model_id} carregado com sucesso.")
        except Exception as e:
            self._last_error = f"Falha ao carregar modelo de IA '{model_id}': {e}"
            print(f"[{self.camera_id}] Erro: {self._last_error}")
            self._model = None # Garantir que o modelo não seja usado
            return False
        # --- Fim Carregar Modelo --- 

        print(f"[{self.camera_id}] Iniciando thread de processamento...")
        self._stop_event.clear() 
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._is_running = True
        self._last_error = None
        return True

    def stop(self):
        """Sinaliza para a thread de processamento parar."""
        if not self._is_running:
            print(f"[{self.camera_id}] Processador não está rodando.")
            return
            
        print(f"[{self.camera_id}] Solicitando parada da thread...")
        self._stop_event.set() # Sinaliza para o loop _run parar
        # Opcional: esperar a thread terminar com self._thread.join(timeout=...) 
        # Cuidado com deadlocks se a thread travar na leitura do frame.
        # Por enquanto, apenas sinalizamos.
        self._is_running = False
        print(f"[{self.camera_id}] Sinal de parada enviado.")

    def _run(self):
        """O loop principal que conecta, lê frames e processa com IA."""
        print(f"[{self.camera_id}] Loop de processamento iniciado.")
        frame_count = 0 # Contador para log periódico
        
        while not self._stop_event.is_set():
            db = None # Definir db fora do try/finally do DB
            try:
                # --- Conexão --- 
                if self._capture is None or not self._capture.isOpened():
                    print(f"[{self.camera_id}] Tentando conectar a {self.rtsp_url}...")
                    self._capture = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
                    if not self._capture.isOpened():
                        self._last_error = "Falha ao conectar ao stream RTSP."
                        print(f"[{self.camera_id}] Erro: {self._last_error} Aguardando antes de tentar novamente...")
                        self._capture = None # Resetar para tentar reconectar
                        self._stop_event.wait(10) # Espera 10s antes de tentar reconectar
                        continue # Volta para o início do while
                    else:
                         print(f"[{self.camera_id}] Conectado com sucesso.")
                         self._last_error = None
                
                # --- Leitura do Frame --- 
                ret, frame = self._capture.read()
                
                if not ret or frame is None:
                    self._last_error = "Falha ao ler frame do stream."
                    print(f"[{self.camera_id}] Erro: {self._last_error} Tentando reconectar...")
                    if self._capture:
                        self._capture.release()
                    self._capture = None # Força reconexão no próximo loop
                    time.sleep(2) # Pequena pausa antes de reconectar
                    continue
                
                # --- Log Periódico de Leitura --- 
                frame_count += 1
                log_frame = (frame_count % 100 == 0) # Logar periodicamente
                if log_frame:
                    print(f"[{self.camera_id}] Frame {frame_count} lido. Shape: {frame.shape}")

                # --- Processamento com IA e Salvamento de Eventos --- 
                if self._model:
                    try:
                        confidence_threshold = self.ai_settings.get("confidence_threshold", 0.4)
                        allowed_classes = self.detection_settings.get("object_classes", [])
                        
                        results = self._model(frame, conf=confidence_threshold, verbose=False)
                        
                        if results and results[0].boxes is not None:
                            detections_to_save = []
                            snapshot_saved_for_frame = False # Flag para salvar snapshot apenas uma vez por frame com detecção
                            snapshot_path = None

                            for box in results[0].boxes:
                                conf = box.conf.item() 
                                cls_id = int(box.cls.item())
                                class_name = self._model.names[cls_id]
                                
                                if class_name in allowed_classes:
                                    print(f"[{self.camera_id}] Detecção Relevante: {class_name} (Conf: {conf:.2f})")
                                    
                                    # --- Salvar Snapshot (se ainda não salvo para este frame) --- 
                                    if not snapshot_saved_for_frame:
                                        try:
                                            snapshot_filename = f"snapshot_{self.camera_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}_{uuid.uuid4().hex[:8]}.jpg"
                                            snapshot_path = os.path.join(SNAPSHOTS_DIR, snapshot_filename)
                                            is_success, buffer = cv2.imencode(".jpg", frame)
                                            if is_success:
                                                with open(snapshot_path, 'wb') as f:
                                                    f.write(buffer)
                                                print(f"[{self.camera_id}] Snapshot salvo em: {snapshot_path}")
                                                snapshot_saved_for_frame = True # Marca como salvo
                                            else:
                                                print(f"[{self.camera_id}] Falha ao codificar snapshot JPEG.")
                                                snapshot_path = None # Resetar path se falhar
                                        except Exception as snap_exc:
                                            print(f"[{self.camera_id}] Erro ao salvar snapshot: {snap_exc}")
                                            snapshot_path = None # Resetar path se falhar
                                    # --- Fim Salvar Snapshot --- 
                                    
                                    coords = box.xyxy[0].tolist() 
                                    bbox_dict = {"x1": coords[0], "y1": coords[1], "x2": coords[2], "y2": coords[3]}
                                    
                                    # Preparar dados do evento
                                    event_data = {
                                        "camera_id": self.camera_id,
                                        "event_type": class_name,
                                        "confidence": conf,
                                        "detected_class": class_name,
                                        "bounding_box": bbox_dict,
                                        "timestamp": datetime.utcnow(),
                                        "image_path": snapshot_path 
                                    }
                                    detections_to_save.append(models.DetectionEvent(**event_data))
                                else:
                                     pass 

                            # Salvar eventos no banco 
                            if detections_to_save:
                                try:
                                    db = self.db_session_factory()
                                    db.add_all(detections_to_save)
                                    db.commit()
                                    print(f"[{self.camera_id}] {len(detections_to_save)} evento(s) de detecção salvos no DB.")
                                except Exception as db_exc:
                                    print(f"[{self.camera_id}] Erro ao salvar eventos no DB: {db_exc}")
                                    if db: db.rollback() # Desfaz em caso de erro
                                finally:
                                     if db: db.close() # Sempre fecha a sessão criada

                    except Exception as e:
                        print(f"[{self.camera_id}] Erro durante a inferência/processamento IA: {e}")
                        pass 

                # Pequeno delay para controlar uso de CPU
                time.sleep(0.01)

            except Exception as e:
                self._last_error = f"Erro inesperado no loop: {e}"
                print(f"[{self.camera_id}] {self._last_error}")
                # Liberar captura em caso de erro inesperado e esperar antes de tentar de novo
                if self._capture:
                    self._capture.release()
                self._capture = None
                self._stop_event.wait(15) # Espera mais tempo após erro inesperado

        # --- Loop Terminado --- 
        print(f"[{self.camera_id}] Loop de processamento terminado.")
        if self._capture is not None and self._capture.isOpened():
            self._capture.release()
            print(f"[{self.camera_id}] Recurso VideoCapture final liberado.")
        self._is_running = False

    def get_status(self) -> dict:
         """Retorna o status atual do processador."""
         return {
             "camera_id": self.camera_id,
             "is_running": self._is_running,
             "rtsp_url": self.rtsp_url,
             "last_error": self._last_error,
             # Adicionar mais infos úteis se necessário
         }

# --- Gerenciamento Global dos Processadores (Exemplo Simples) --- 
# Este dicionário manterá as instâncias ativas
# A chave será o camera_id, o valor será a instância CameraProcessor
active_processors: Dict[str, CameraProcessor] = {}

# Função para iniciar o processamento de uma câmera
# Esta função seria chamada por uma rota da API, por exemplo
def start_camera_processing(camera_id: str, db_session_factory) -> dict:
    if camera_id in active_processors:
        print(f"Processamento para câmera {camera_id} já está ativo.")
        return active_processors[camera_id].get_status()
        
    print(f"Criando e iniciando processador para câmera {camera_id}...")
    processor = CameraProcessor(camera_id, db_session_factory)
    success = processor.start() 
    if success:
        active_processors[camera_id] = processor
        print(f"Processador para {camera_id} iniciado e adicionado aos ativos.")
        return processor.get_status()
    else:
        print(f"Falha ao iniciar processador para {camera_id}. Erro: {processor._last_error}")
        return {"camera_id": camera_id, "is_running": False, "last_error": processor._last_error or "Falha ao iniciar"}

# Função para parar o processamento de uma câmera
# Esta função seria chamada por uma rota da API
def stop_camera_processing(camera_id: str) -> dict:
    if camera_id not in active_processors:
        print(f"Nenhum processador ativo encontrado para câmera {camera_id}.")
        return {"camera_id": camera_id, "is_running": False, "last_error": "Processador não estava ativo."}
        
    print(f"Parando processador para câmera {camera_id}...")
    processor = active_processors[camera_id]
    processor.stop()
    # Remover do dicionário após sinalizar parada
    # A thread pode ainda demorar um pouco para terminar completamente
    del active_processors[camera_id]
    print(f"Processador para {camera_id} sinalizado para parar e removido dos ativos.")
    # Retornar o último status antes da parada pode ser útil
    return processor.get_status() 

# Função para obter o status de todos os processadores ativos
def get_all_processors_status() -> List[dict]:
    return [p.get_status() for p in active_processors.values()]
