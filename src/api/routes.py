"""
Módulo de rotas da API.

Define os endpoints da API REST para acesso a eventos, câmeras e outras funcionalidades.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from ..db import cameras_crud, database
from ..models.pyobjectid import PyObjectId
from .auth import get_current_active_user, UserInDB
# Importar funções de controle de câmera
from ..detection.camera import (
    start_camera_process,
    stop_camera_process,
    get_running_camera_statuses,
    get_latest_frame
)
from fastapi.responses import StreamingResponse
import asyncio

# Configuração do router
router = APIRouter(
    prefix="/api/v1",
    tags=["api"],
    dependencies=[Depends(get_current_active_user)],
    responses={401: {"description": "Não autorizado"}, 403: {"description": "Não permitido"}},
)

# Removidos modelos antigos CameraInfo, CameraStart
# Usaremos CameraDB e CameraCreate do cameras_crud
from ..db.cameras_crud import CameraDB, CameraCreate

# Novo modelo de resposta com status
class CameraStatusInfo(CameraDB):
    running: bool = False
    start_time: Optional[datetime] = None # Adicionar se quisermos mostrar uptime

# Modelo para Eventos (ajustar se necessário)
class EventInfo(BaseModel):
    id: str
    event_type: str
    camera_id: str
    timestamp: datetime
    details: Optional[str] = None

# --- Endpoints de Câmeras (CRUD por usuário) ---

@router.post("/cameras", response_model=CameraDB, status_code=status.HTTP_201_CREATED)
async def create_user_camera(
    camera: CameraCreate, 
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Registra uma nova câmera para o usuário logado."""
    created_camera = await cameras_crud.add_camera(camera_data=camera, owner=current_user.username)
    # Aqui podemos decidir se iniciamos a detecção automaticamente ou não
    # Ex: asyncio.create_task(start_detection_process(created_camera.id, created_camera.url))
    return created_camera

@router.get("/cameras", response_model=List[CameraStatusInfo])
async def list_user_cameras_with_status(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Lista todas as câmeras pertencentes ao usuário logado, incluindo status de execução.
    """
    # 1. Obter câmeras do banco de dados
    db_cameras = await cameras_crud.get_cameras_by_user(owner=current_user.username)
    
    # 2. Obter status das câmeras em execução (pode ser síncrono)
    try:
        running_status_dict = get_running_camera_statuses() 
    except Exception as e:
        logger.error(f"Erro ao obter status das câmeras em execução: {e}")
        running_status_dict = {} # Continuar sem status se houver erro

    # 3. Combinar informações
    cameras_with_status = []
    for db_cam in db_cameras:
        cam_id_str = str(db_cam.id)
        status_info = running_status_dict.get(cam_id_str)
        
        is_running = status_info.get("running", False) if status_info else False
        start_timestamp = status_info.get("start_time") if status_info else None
        start_dt = datetime.fromtimestamp(start_timestamp) if start_timestamp else None

        camera_info = CameraStatusInfo(
            **db_cam.dict(), 
            running=is_running,
            start_time=start_dt
        )
        cameras_with_status.append(camera_info)
        
    return cameras_with_status

@router.get("/cameras/{camera_id}", response_model=CameraStatusInfo)
async def get_user_camera_with_status(
    camera_id: str, 
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Busca uma câmera específica do usuário pelo ID, incluindo status."""
    db_camera = await cameras_crud.get_camera_by_id(camera_id=camera_id, owner=current_user.username)
    if db_camera is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Câmera não encontrada ou não pertence ao usuário")

    try:
        running_status_dict = get_running_camera_statuses()
    except Exception as e:
        logger.error(f"Erro ao obter status da câmera em execução {camera_id}: {e}")
        running_status_dict = {}

    status_info = running_status_dict.get(camera_id)
    is_running = status_info.get("running", False) if status_info else False
    start_timestamp = status_info.get("start_time") if status_info else None
    start_dt = datetime.fromtimestamp(start_timestamp) if start_timestamp else None

    camera_info = CameraStatusInfo(
        **db_camera.dict(), 
        running=is_running,
        start_time=start_dt
    )
    return camera_info

@router.delete("/cameras/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_camera(
    camera_id: str, 
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Deleta uma câmera do usuário e tenta parar o processo se estiver rodando."""
    # Verificar se a câmera pertence ao usuário antes de tentar parar
    camera = await cameras_crud.get_camera_by_id(camera_id=camera_id, owner=current_user.username)
    if camera is None:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Câmera não encontrada ou não pertence ao usuário")
    
    # Tentar parar o processo de detecção (não bloqueante)
    try:
        stopped = await stop_camera_process(camera_id)
        if stopped:
            logger.info(f"Processo da câmera {camera_id} parado antes da deleção.")
        else:
             logger.info(f"Processo da câmera {camera_id} não estava rodando ou não foi encontrado para parar.")
    except Exception as e:
        logger.error(f"Erro ao tentar parar câmera {camera_id} antes de deletar: {e}")
        # Continuar com a deleção do DB mesmo se parar falhar

    # Deletar do banco de dados
    deleted = await cameras_crud.delete_camera(camera_id=camera_id, owner=current_user.username)
    if not deleted:
        # Isso não deveria acontecer se a verificação inicial passou, mas por segurança:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Falha ao deletar a câmera do banco de dados")
    
    return

# --- Endpoints para Controle de Detecção --- 

@router.post("/cameras/{camera_id}/start", status_code=status.HTTP_200_OK)
async def start_camera_detection(
    camera_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Inicia o processo de detecção para uma câmera específica."""
    # 1. Verificar permissão e buscar dados da câmera
    camera = await cameras_crud.get_camera_by_id(camera_id=camera_id, owner=current_user.username)
    if camera is None:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Câmera não encontrada ou não pertence ao usuário")
         
    # 2. Chamar a função para iniciar o processo
    try:
        success = await start_camera_process(camera_id=str(camera.id), url=camera.url, location=camera.location)
        if success:
            return {"message": f"Processo de detecção iniciado para a câmera {camera.name}"}
        else:
            # Pode já estar rodando ou ter falhado ao iniciar
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Câmera já está rodando ou falhou ao iniciar. Verifique os logs.")
    except Exception as e:
        logger.error(f"Erro inesperado ao iniciar detecção para câmera {camera_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro interno ao iniciar detecção: {e}")

@router.post("/cameras/{camera_id}/stop", status_code=status.HTTP_200_OK)
async def stop_camera_detection(
    camera_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Para o processo de detecção para uma câmera específica."""
    # 1. Verificar permissão (importante para garantir que usuário só pare suas câmeras)
    camera = await cameras_crud.get_camera_by_id(camera_id=camera_id, owner=current_user.username)
    if camera is None:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Câmera não encontrada ou não pertence ao usuário")

    # 2. Chamar a função para parar o processo
    try:
        success = await stop_camera_process(camera_id=str(camera.id))
        if success:
            return {"message": f"Processo de detecção parado para a câmera {camera.name}"}
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processo da câmera não estava rodando ou não foi encontrado.")
    except Exception as e:
        logger.error(f"Erro inesperado ao parar detecção para câmera {camera_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro interno ao parar detecção: {e}")

# --- Endpoints de Eventos (precisa adaptar a lógica de acesso/filtragem) ---

@router.get("/events", response_model=List[EventInfo])
async def list_events(
    camera_id: Optional[str] = None, 
    days: Optional[int] = 7,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Lista eventos de detecção.
    TODO: Adaptar get_detection_events para filtrar por usuário ou buscar câmeras do usuário primeiro.
    
    - camera_id: Filtrar por câmera específica (garantir que pertence ao usuário)
    - days: Número de dias para buscar (padrão: 7)
    """
    # Verificação se a camera_id (se fornecida) pertence ao usuário
    if camera_id:
        cam = await cameras_crud.get_camera_by_id(camera_id, owner=current_user.username)
        if not cam:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Câmera especificada não encontrada ou não pertence ao usuário")
            
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # --- Lógica de Filtragem por Usuário (Exemplo) ---
        # Opção 1: Modificar get_detection_events para aceitar user_id/owner
        # events = await database.get_detection_events(
        #     owner=current_user.username, # Novo parâmetro
        #     camera_id=camera_id,
        #     start_date=start_date,
        #     end_date=end_date
        # )
        
        # Opção 2: Buscar câmeras do usuário e depois filtrar eventos (menos eficiente se muitos eventos)
        user_cameras = await cameras_crud.get_cameras_by_user(owner=current_user.username)
        user_camera_ids = [str(cam.id) for cam in user_cameras]
        
        # Se um camera_id foi fornecido E pertence ao usuário, usar apenas ele
        filter_camera_ids = [camera_id] if camera_id else user_camera_ids
        
        if not filter_camera_ids:
             return [] # Usuário não tem câmeras, logo não tem eventos

        # Buscar eventos apenas para as câmeras permitidas
        events = await database.get_detection_events(
            camera_ids=filter_camera_ids, # Modificar get_detection_events para aceitar lista de IDs
            start_date=start_date,
            end_date=end_date
        )
        # --- Fim da Lógica de Filtragem (Exemplo) ---
        
        return events
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar eventos: {str(e)}"
        )

# --- Endpoint de Streaming MJPEG --- 

async def stream_generator(camera_id: str, current_user: UserInDB):
    """Gerador assíncrono para o stream MJPEG."""
    # 1. Verificar se a câmera pertence ao usuário
    camera = await cameras_crud.get_camera_by_id(camera_id=camera_id, owner=current_user.username)
    if camera is None:
        # Não podemos levantar HTTPException aqui diretamente, pois é um gerador.
        # A melhor abordagem pode ser retornar um frame de erro ou simplesmente parar.
        # Por simplicidade, vamos logar e parar.
        logger.error(f"Tentativa de stream não autorizado ou câmera não encontrada: user={current_user.username}, cam_id={camera_id}")
        yield b'' # Enviar um byte vazio e parar
        return

    logger.info(f"Iniciando stream MJPEG para câmera {camera_id} para usuário {current_user.username}")
    last_yielded_frame = None
    try:
        while True:
            # Obter o último frame JPEG da câmera de forma thread-safe
            frame_bytes = get_latest_frame(camera_id)
            
            # Verificar se a câmera ainda está registrada como rodando
            # (get_latest_frame já faz isso, mas uma verificação extra pode ser útil)
            running_statuses = get_running_camera_statuses()
            if camera_id not in running_statuses or not running_statuses[camera_id].get('running'):
                 logger.warning(f"Câmera {camera_id} não está mais rodando. Parando stream.")
                 # TODO: Enviar um frame indicando "Câmera Parada"?
                 break # Sai do loop para encerrar o stream

            if frame_bytes and frame_bytes != last_yielded_frame:
                # Enviar o frame no formato MJPEG
                yield (
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'
                )
                last_yielded_frame = frame_bytes
            elif frame_bytes is None:
                # Frame ainda não disponível ou a câmera parou entre chamadas
                # logger.debug(f"Frame não disponível para {camera_id}. Aguardando...")
                pass
                # Se não houver frame, podemos não enviar nada ou enviar um placeholder?
                # Não enviar nada é melhor para MJPEG, o cliente espera.

            # Pequeno delay para evitar busy-waiting extremo e permitir que outras tarefas rodem
            # Ajustar conforme necessário (trade-off entre latência e uso de CPU)
            await asyncio.sleep(0.03) # Aproximadamente 33 FPS max
            
    except asyncio.CancelledError:
        logger.info(f"Stream MJPEG cancelado para câmera {camera_id}")
    except Exception as e:
        logger.error(f"Erro durante o streaming MJPEG para câmera {camera_id}: {e}")
    finally:
        logger.info(f"Encerrando stream MJPEG para câmera {camera_id}")

@router.get("/cameras/{camera_id}/stream")
async def get_camera_stream(
    camera_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Retorna um stream MJPEG do vídeo da câmera especificada."""
    # A verificação de permissão é feita dentro do stream_generator
    return StreamingResponse(
        stream_generator(camera_id, current_user),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

# --- Endpoint de status do sistema (mantido) ---
@router.get("/status", include_in_schema=False)
async def system_status():
    """
    Retorna o status atual do sistema (não requer autenticação)
    """
    return {
        "status": "online",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    } 