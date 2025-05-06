# api/video_service.py
import cv2
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import io  # Para trabalhar com bytes em memória
import threading # Para rodar em background
import time      # Para adicionar delays
import queue     # Para comunicação entre threads
from typing import Optional, Dict, List
import os # Para construir caminhos de arquivo
from ultralytics import YOLO # Importar YOLO
from datetime import datetime # Para timestamp do evento
import uuid # Para nomes de arquivo únicos
import collections # <<< Importar collections

# Importar modelos do mesmo diretório (api)
# Assumindo que models.py está em api/
try:
    from . import models, schemas
except ImportError:
    # Fallback se rodar diretamente (menos provável)
    import models
    import schemas

# Definir caminho base para snapshots e placeholder
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Não precisamos mais da raiz
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) # Diretório atual (api/)
SNAPSHOTS_DIR = os.path.join(CURRENT_DIR, "snapshots")
PLACEHOLDER_PATH = os.path.join(CURRENT_DIR, "assets", "logo.png") # Caminho relativo a api/

# Criar diretório de snapshots se não existir
os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

# Carregar placeholder em memória uma vez para reuso (opcional, mas pode ser eficiente)
placeholder_image_bytes: Optional[bytes] = None
try:
    if os.path.exists(PLACEHOLDER_PATH):
        placeholder_img = cv2.imread(PLACEHOLDER_PATH)
        if placeholder_img is not None:
            is_success, buffer = cv2.imencode(".jpg", placeholder_img)
            if is_success:
                placeholder_image_bytes = io.BytesIO(buffer).getvalue()
                print(f"[Video Service] Placeholder image carregado de {PLACEHOLDER_PATH}")
            else:
                print(f"[Video Service] ERRO: Falha ao codificar placeholder de {PLACEHOLDER_PATH}")
        else:
             print(f"[Video Service] ERRO: Falha ao ler placeholder de {PLACEHOLDER_PATH} com OpenCV")
    else:
        print(f"[Video Service] AVISO: Placeholder image não encontrado em {PLACEHOLDER_PATH}")
except Exception as e:
    print(f"[Video Service] ERRO ao carregar/codificar placeholder: {e}")

def _capture_frame_worker(rtsp_url: str, result_queue: queue.Queue):
    """Worker executado em uma thread para capturar um frame com timeout implícito."""
    cap = None
    try:
        # print(f"[Snapshot Worker] Tentando conectar a: {rtsp_url}") # Log menos verboso
        cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            # print(f"[Snapshot Worker] Falha ao abrir VideoCapture para: {rtsp_url}")
            result_queue.put(Exception("Falha ao abrir VideoCapture")) # Usar Exceção genérica
            return
        
        # print(f"[Snapshot Worker] Conectado, tentando ler frame de: {rtsp_url}")
        ret, frame = cap.read()
        if not ret or frame is None:
            # print(f"[Snapshot Worker] Falha ao ler frame de: {rtsp_url}")
            result_queue.put(Exception("Falha ao ler frame"))
            return
        
        # print(f"[Snapshot Worker] Frame lido com sucesso de: {rtsp_url}")
        result_queue.put(frame)
    except Exception as e:
        # print(f"[Snapshot Worker] Exceção inesperada: {e}")
        result_queue.put(e)
    finally:
        if cap is not None and cap.isOpened():
            cap.release()
            # print(f"[Snapshot Worker] Recurso VideoCapture liberado para: {rtsp_url}")

def get_camera_snapshot_bytes(db: Session, camera_id: str) -> bytes:
    """
    Tenta obter um snapshot da câmera com N tentativas e timeout curto.
    Retorna bytes do snapshot ou de um placeholder em caso de falha.
    """
    MAX_ATTEMPTS = 3
    ATTEMPT_TIMEOUT = 3.0 # Segundos para esperar CADA tentativa
    RETRY_DELAY = 0.5 # Segundos entre tentativas
    
    # 1. Buscar a câmera no banco de dados (como antes)
    db_camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
    if not db_camera:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Câmera não encontrada")
    if not db_camera.rtsp_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL RTSP não configurada")

    rtsp_url = db_camera.rtsp_url
    print(f"[Video Service] Obtendo snapshot para {camera_id} (até {MAX_ATTEMPTS} tentativas de {ATTEMPT_TIMEOUT}s). URL: {rtsp_url}")

    # 2. Loop de Tentativas
    last_error = None
    for attempt in range(MAX_ATTEMPTS):
        print(f"[Video Service] Tentativa {attempt + 1}/{MAX_ATTEMPTS} para {camera_id}...")
        result_queue = queue.Queue()
        capture_thread = threading.Thread(
            target=_capture_frame_worker,
            args=(rtsp_url, result_queue),
            daemon=True
        )
        capture_thread.start()
        capture_thread.join(timeout=ATTEMPT_TIMEOUT)

        if capture_thread.is_alive():
            last_error = f"Timeout ({ATTEMPT_TIMEOUT}s) na tentativa {attempt + 1}"
            print(f"[Video Service] {last_error} para {camera_id}")
            # Não lançar exceção ainda, tentar novamente
        else:
            # A thread terminou, verificar resultado na queue
            try:
                result = result_queue.get_nowait() # Pega resultado sem bloquear
                if isinstance(result, Exception):
                    last_error = f"Erro na thread na tentativa {attempt + 1}: {result}"
                    print(f"[Video Service] {last_error} para {camera_id}")
                    # Não lançar exceção ainda, tentar novamente
                elif result is not None:
                    # Sucesso! Temos o frame
                    frame = result
                    print(f"[Video Service] Frame obtido com sucesso na tentativa {attempt + 1} para {camera_id}")
                    # 3. Codificar o frame como JPEG
                    try:
                        is_success, buffer = cv2.imencode(".jpg", frame)
                        if not is_success:
                            print(f"[Video Service] Falha ao codificar frame como JPEG para {camera_id}.")
                            last_error = "Falha na codificação JPEG"
                            break # Sair do loop de tentativas, pois a captura funcionou mas a codificação não
                        else:
                            image_bytes = io.BytesIO(buffer).getvalue()
                            print(f"[Video Service] Snapshot codificado com sucesso para {camera_id}.")
                            return image_bytes # <<< RETORNA frame real
                    except Exception as encode_exc:
                        print(f"[Video Service] Exceção durante codificação JPEG para {camera_id}: {encode_exc}")
                        last_error = f"Erro na codificação: {encode_exc}"
                        break # Sair do loop de tentativas
                else:
                    # Caso result seja None (não deveria acontecer com a lógica atual, mas por segurança)
                    last_error = f"Resultado inesperado (None) na tentativa {attempt + 1}"
                    print(f"[Video Service] {last_error} para {camera_id}")

            except queue.Empty:
                # A thread terminou mas a queue está vazia (erro interno ou worker não colocou nada)
                last_error = f"Erro interno (queue vazia após thread terminar) na tentativa {attempt + 1}"
                print(f"[Video Service] {last_error} para {camera_id}")
                # Tentar novamente
        
        # Se não retornou sucesso, esperar antes da próxima tentativa (se houver)
        if attempt < MAX_ATTEMPTS - 1:
             print(f"[Video Service] Aguardando {RETRY_DELAY}s antes da próxima tentativa para {camera_id}.")
             time.sleep(RETRY_DELAY)

    # 4. Se o loop terminou sem sucesso, retornar placeholder
    print(f"[Video Service] Todas as {MAX_ATTEMPTS} tentativas falharam para {camera_id}. Último erro: {last_error}. Retornando placeholder.")
    if placeholder_image_bytes:
        return placeholder_image_bytes # <<< RETORNA placeholder
    else:
        # Se nem o placeholder carregou, retornar erro 503 final
        print(f"[Video Service] ERRO CRÍTICO: Placeholder não disponível. Retornando 503.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Falha ao obter snapshot da câmera e imagem placeholder não está disponível."
        )

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
        self._frame_buffer = collections.deque(maxlen=30) # <<< Buffer para ~1 segundo a 30fps
        self._is_detecting_event = False # Flag para controlar captura de sequencia
        self._event_frames_to_capture = 0
        self._current_event_id = None
        self._captured_event_frames = [] # Lista temporária de frames para o evento atual

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
        self._thread.start() # <<< REATIVADO
        self._is_running = True # <<< REATIVADO
        self._last_error = None # <<< REATIVADO
        return True # <<< REATIVADO
        
        # # Forçar falha no início para impedir a thread (REMOVIDO)
        # self._last_error = "Processamento em background temporariamente desabilitado para teste."
        # print(f"[{self.camera_id}] {self._last_error}")
        # self._is_running = False
        # return False

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
        frame_count = 0
        
        while not self._stop_event.is_set():
            db = None # Definir fora do try/finally do DB
            try:
                # --- Conexão --- 
                if self._capture is None or not self._capture.isOpened():
                    print(f"[{self.camera_id}] Tentando conectar a {self.rtsp_url}...")
                    self._capture = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
                    if not self._capture.isOpened():
                        self._last_error = "Falha ao conectar ao stream RTSP."
                        print(f"[{self.camera_id}] Erro: {self._last_error} Aguardando antes de tentar novamente...")
                        self._capture = None
                        self._stop_event.wait(10)
                        continue
                    else:
                         print(f"[{self.camera_id}] Conectado com sucesso.")
                         self._last_error = None
                
                # --- Leitura do Frame --- 
                current_timestamp = datetime.utcnow()
                ret, frame = self._capture.read()
                
                if not ret or frame is None:
                    self._last_error = "Falha ao ler frame do stream."
                    print(f"[{self.camera_id}] Erro: {self._last_error} Tentando reconectar...")
                    if self._capture:
                        self._capture.release()
                    self._capture = None 
                    time.sleep(2) 
                    continue
                
                # Adicionar frame e timestamp ao buffer
                self._frame_buffer.append((current_timestamp, frame.copy())) # Guardar cópia
                
                # --- Log Periódico --- 
                frame_count += 1
                if frame_count % 100 == 0:
                    print(f"[{self.camera_id}] Frame {frame_count} lido. Buffer: {len(self._frame_buffer)}")

                # --- Processamento com IA --- 
                detected_objects_this_frame = [] # Lista de detecções para este frame
                if self._model:
                    try:
                        confidence_threshold = self.ai_settings.get("confidence_threshold", 0.4)
                        allowed_classes = self.detection_settings.get("object_classes", [])
                        
                        results = self._model(frame, conf=confidence_threshold, verbose=False)
                        
                        if results and results[0].boxes is not None:
                            for box in results[0].boxes:
                                conf = box.conf.item() 
                                cls_id = int(box.cls.item())
                                class_name = self._model.names[cls_id]
                                
                                if class_name in allowed_classes:
                                    coords = box.xyxy[0].tolist() 
                                    bbox_dict = {"x1": coords[0], "y1": coords[1], "x2": coords[2], "y2": coords[3]}
                                    detected_objects_this_frame.append({
                                        "event_type": class_name,
                                        "confidence": conf,
                                        "detected_class": class_name,
                                        "bounding_box": bbox_dict,
                                        "timestamp": current_timestamp # Usar timestamp da leitura do frame
                                    })
                                    # print(f"[{self.camera_id}] Detecção Relevante: {class_name} (Conf: {conf:.2f})")
                                    
                    except Exception as e:
                        print(f"[{self.camera_id}] Erro durante a inferência IA: {e}")
                        # Continuar mesmo se a inferência falhar?

                # --- Lógica de Captura de Sequência de Evento --- 
                if detected_objects_this_frame and not self._is_detecting_event:
                    # Primeira detecção de um possível evento
                    self._is_detecting_event = True
                    self._event_frames_to_capture = 30 # Capturar ~1s antes (do buffer) e ~1s depois (total ~2s a 30fps)
                    self._current_event_id = str(uuid.uuid4()) # Gerar ID único para este evento
                    self._captured_event_frames = list(self._frame_buffer) # Copiar buffer atual
                    self._event_frames_to_capture -= len(self._captured_event_frames)
                    print(f"[{self.camera_id}] Evento {self._current_event_id} iniciado. Capturando {len(self._captured_event_frames)} frames do buffer, restam {self._event_frames_to_capture}.")
                    
                    # Salvar o registro principal do evento no DB (sem snapshots ainda)
                    # Pegar a primeira detecção como representativa
                    first_detection = detected_objects_this_frame[0]
                    main_event_data = {
                        "id": self._current_event_id,
                        "camera_id": self.camera_id,
                        # Usar os dados da primeira detecção para o evento principal
                        **{k: v for k, v in first_detection.items() if k != 'timestamp'}, 
                        "timestamp": first_detection['timestamp'] # Usar timestamp da detecção
                    }
                    try:
                        db = self.db_session_factory()
                        db_event = models.DetectionEvent(**main_event_data)
                        db.add(db_event)
                        db.commit()
                        print(f"[{self.camera_id}] Registro principal do Evento {self._current_event_id} salvo.")
                    except Exception as db_exc:
                        print(f"[{self.camera_id}] ERRO ao salvar registro principal do Evento {self._current_event_id}: {db_exc}")
                        if db: db.rollback()
                        # Abortar captura de frames se o evento principal falhar?
                        self._is_detecting_event = False 
                        self._current_event_id = None
                        self._captured_event_frames = []
                    finally:
                         if db: db.close()
                         
                elif self._is_detecting_event and self._event_frames_to_capture > 0:
                    # Continuar capturando frames para o evento atual
                    self._captured_event_frames.append((current_timestamp, frame.copy()))
                    self._event_frames_to_capture -= 1
                    # print(f"[{self.camera_id}] Capturado frame extra para evento {self._current_event_id}. Restam {self._event_frames_to_capture}.")
                    
                    if self._event_frames_to_capture <= 0:
                        # Terminou de capturar a sequência
                        print(f"[{self.camera_id}] Captura de {len(self._captured_event_frames)} frames para Evento {self._current_event_id} completa. Salvando snapshots...")

                        event_snapshots_to_save: List[models.EventSnapshot] = [] # Especificar tipo
                        save_success = True
                        for i, (ts, event_frame) in enumerate(self._captured_event_frames):
                             try:
                                snapshot_filename = f"event_{self._current_event_id}_frame_{i:03d}.jpg"
                                snapshot_path = os.path.join(SNAPSHOTS_DIR, snapshot_filename)
                                is_success, buffer = cv2.imencode(".jpg", event_frame)
                                if is_success:
                                    with open(snapshot_path, 'wb') as f:
                                        f.write(buffer)
                                    # Preparar registro do snapshot para o DB
                                    event_snapshots_to_save.append(models.EventSnapshot(
                                        event_id=self._current_event_id,
                                        snapshot_path=snapshot_filename, # Salvar apenas nome do arquivo
                                        timestamp=ts
                                    ))
                                    # print(f"[{self.camera_id}] Snapshot {snapshot_filename} salvo e registro preparado.") # Log opcional
                                else:
                                    print(f"[{self.camera_id}] Falha ao codificar frame {i} para evento {self._current_event_id}.")
                                    save_success = False # Marcar falha, mas continuar tentando outros frames?
                                    # break # Ou parar tudo?
                             except Exception as snap_exc:
                                print(f"[{self.camera_id}] Erro ao salvar/preparar snapshot frame {i} para evento {self._current_event_id}: {snap_exc}")
                                save_success = False
                                # break
                        
                        # Salvar registros dos snapshots no DB
                        if event_snapshots_to_save and save_success:
                            db = None # Resetar db
                            try:
                                db = self.db_session_factory()
                                db.add_all(event_snapshots_to_save) # <<< Salvar todas as instâncias preparadas
                                db.commit()
                                print(f"[{self.camera_id}] {len(event_snapshots_to_save)} registros de snapshot salvos para Evento {self._current_event_id}.")
                            except Exception as db_exc:
                                print(f"[{self.camera_id}] ERRO ao salvar registros de snapshot para Evento {self._current_event_id}: {db_exc}")
                                if db: db.rollback()
                            finally:
                                if db: db.close()
                        elif not save_success:
                            print(f"[{self.camera_id}] Falha ao salvar um ou mais snapshots para Evento {self._current_event_id}. Registros DB não salvos.")
                        
                        # Resetar estado de captura de evento
                        self._is_detecting_event = False 
                        self._current_event_id = None
                        self._captured_event_frames = []

                # Pequeno delay para controlar uso de CPU
                time.sleep(0.01)

            except Exception as e:
                self._last_error = f"Erro inesperado no loop: {e}"
                print(f"[{self.camera_id}] {self._last_error}")
                if self._capture:
                    self._capture.release()
                self._capture = None
                self._stop_event.wait(15)

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
