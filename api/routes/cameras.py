"""
Rotas para gerenciamento de câmeras
"""
import cv2 # Importar OpenCV
from fastapi import APIRouter, Depends, HTTPException, status, Body, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from urllib.parse import quote # Para codificar username/password na URL
import io
from fastapi.responses import StreamingResponse # Usar StreamingResponse pode ser mais apropriado
from sqlalchemy import desc # Para ordenar eventos

from api import models, schemas, security
from api.db import get_db, SessionLocal # Importar SessionLocal como fábrica

# Importar o novo serviço (assumindo que está em api/video_service.py)
try:
    from .. import video_service
except ImportError as e:
    print(f"AVISO: Não foi possível importar video_service. Erro: {e}. Endpoint de snapshot pode não funcionar.")
    video_service = None

router = APIRouter(prefix="/cameras", tags=["cameras"])

@router.get("/", response_model=List[schemas.CameraResponse])
async def get_cameras(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Obtém a lista de câmeras do usuário atual, incluindo o path do último snapshot de evento.
    Converte objetos SQLAlchemy em dicts para evitar erros de serialização.
    """
    # Buscar câmeras do usuário atual
    cameras_db = db.query(models.Camera).filter(
        models.Camera.owner_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    # WORKAROUND: Converter e Adicionar Último Snapshot
    cameras_list = []
    for camera in cameras_db:
        # Converter camera base para dict
        camera_dict = {
            field: getattr(camera, field) 
            for field in schemas.CameraResponse.__fields__ 
            if hasattr(camera, field) and field != 'last_event_image_path' # Excluir o campo que vamos adicionar
        }
        
        # Buscar o último evento com imagem para esta câmera
        last_event_with_image = db.query(models.DetectionEvent).filter(
            models.DetectionEvent.camera_id == camera.id,
            models.DetectionEvent.image_path != None # Garantir que tem imagem
        ).order_by(
            desc(models.DetectionEvent.timestamp) # Ordenar por mais recente
        ).first()
        
        # Adicionar o path ao dicionário
        camera_dict['last_event_image_path'] = last_event_with_image.image_path if last_event_with_image else None
        
        cameras_list.append(camera_dict)
        
    return cameras_list

@router.post("/", response_model=schemas.CameraResponse, status_code=status.HTTP_201_CREATED)
async def create_camera(
    camera_data: schemas.CameraBase, # Schema agora usa ip_address, rtsp_port
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Cria uma nova câmera para o usuário atual, validando a conexão RTSP local.
    """
    
    # 1. Montar a URL RTSP completa com dados locais
    user_part = ""
    if camera_data.username:
        user_part = f"{quote(camera_data.username)}"
        if camera_data.password:
            user_part += f":{quote(camera_data.password)}"
        user_part += "@"
        
    path_part = camera_data.rtsp_path
    if not path_part.startswith("/"):
        path_part = f"/{path_part}"
        
    # Usar ip_address e rtsp_port do schema
    full_rtsp_url = f"rtsp://{user_part}{camera_data.ip_address}:{camera_data.rtsp_port}{path_part}" 
    print(f"Tentando validar URL RTSP: {full_rtsp_url}")

    # 2. Validar a conexão RTSP (Reativado)
    cap = cv2.VideoCapture(full_rtsp_url, cv2.CAP_FFMPEG)
    is_opened = cap.isOpened()
    cap.release()
    
    if not is_opened:
        print(f"Falha ao conectar à câmera: {full_rtsp_url}") 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Não foi possível conectar ao stream RTSP. "
                "Verifique o IP Local, Porta RTSP, Caminho RTSP, e credenciais."
            )
        )
    print(f"Conexão RTSP validada com sucesso para: {full_rtsp_url}")

    # 3. Criar nova câmera
    # Mapear campos do schema para o modelo (ip_address e rtsp_port para os campos do modelo)
    db_camera_data = camera_data.dict()
    db_camera_data['rtsp_url'] = full_rtsp_url # Salvar a URL completa montada
    db_camera_data['port'] = camera_data.rtsp_port # Mapear rtsp_port para port
    # ip_address já está correto no dict
    
    # Remover campos que não existem no modelo models.Camera
    db_camera_data.pop('rtsp_port', None) 
    db_camera_data.pop('rtsp_path', None) # rtsp_path não existe no modelo DB
        
    db_camera = models.Camera(
        **db_camera_data,
        owner_id=current_user.id
    )
    
    # 4. Adicionar ao banco de dados
    try:
        db.add(db_camera)
        db.commit()
        db.refresh(db_camera)
    except Exception as e:
        db.rollback()
        print(f"Erro ao salvar câmera no DB: {e}") # Log de erro do DB
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao salvar a câmera no banco de dados: {e}"
        )
        
    return db_camera

@router.get("/{camera_id}", response_model=schemas.CameraResponse)
async def get_camera(
    camera_id: str, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Obtém detalhes de uma câmera específica.
    Converte o objeto SQLAlchemy em dict para evitar erros de serialização.
    """
    # Buscar câmera no banco de dados
    camera = db.query(models.Camera).filter(
        models.Camera.id == camera_id,
        models.Camera.owner_id == current_user.id
    ).first()
    
    # Verificar se a câmera existe
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Câmera não encontrada ou não pertence ao usuário"
        )
    
    # WORKAROUND: Conversão Manual para Dict
    # Mesmo com `from_attributes = True` no schema CameraResponse, 
    # a serialização direta do objeto SQLAlchemy pode falhar.
    camera_dict = {
        field: getattr(camera, field) 
        for field in schemas.CameraResponse.__fields__ 
        if hasattr(camera, field)
    }

    # return camera # <<< Linha original comentada
    return camera_dict # <<< Retornar o dicionário

@router.put("/{camera_id}", response_model=schemas.CameraResponse)
async def update_camera(
    camera_id: str, 
    camera_update: schemas.CameraUpdate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Atualiza dados de uma câmera específica
    """
    # Buscar câmera no banco de dados
    db_camera = db.query(models.Camera).filter(
        models.Camera.id == camera_id,
        models.Camera.owner_id == current_user.id
    ).first()
    
    # Verificar se a câmera existe
    if not db_camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Câmera não encontrada"
        )
    
    # Atualizar campos que foram enviados (não nulos)
    camera_data = camera_update.dict(exclude_unset=True)
    for key, value in camera_data.items():
        setattr(db_camera, key, value)
    
    # Salvar alterações
    db.commit()
    db.refresh(db_camera)
    
    return db_camera

@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(
    camera_id: str, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Remove uma câmera específica
    """
    # Buscar câmera no banco de dados
    db_camera = db.query(models.Camera).filter(
        models.Camera.id == camera_id,
        models.Camera.owner_id == current_user.id
    ).first()
    
    # Verificar se a câmera existe
    if not db_camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Câmera não encontrada"
        )
    
    # Remover câmera
    db.delete(db_camera)
    db.commit()
    
    return None 

# --- NOVA ROTA PARA SNAPSHOT --- 
@router.get(
    "/{camera_id}/snapshot", 
    tags=["cameras"], 
    summary="Obter Snapshot da Câmera",
    description="Retorna um frame JPEG atual da câmera especificada.",
    responses={
        200: {"content": {"image/jpeg": {}}, "description": "Snapshot da câmera em formato JPEG"},
        400: {"description": "URL RTSP não configurada"},
        401: {"description": "Não autenticado"},
        403: {"description": "Não autorizado (câmera não pertence ao usuário)"},
        404: {"description": "Câmera não encontrada"},
        501: {"description": "Serviço de vídeo não disponível"},
        503: {"description": "Falha ao conectar à câmera ou ler frame"},
        500: {"description": "Erro interno ao processar snapshot"}
    }
)
async def get_camera_snapshot(
    camera_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Obtém um snapshot (frame JPEG atual) de uma câmera específica.
    """
    # 1. Buscar câmera no banco
    db_camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
    if not db_camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Câmera não encontrada"
        )
        
    # 2. Verificar permissão
    if db_camera.owner_id != current_user.id:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Acesso não autorizado a esta câmera"
        )
        
    # 3. Verificar serviço
    if video_service is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED, 
            detail="Serviço de vídeo não está disponível."
        )

    # 4. Chamar o serviço
    try:
        image_bytes = video_service.get_camera_snapshot_bytes(db=db, camera_id=camera_id)
        
        # 5. Retornar a resposta
        return Response(content=image_bytes, media_type="image/jpeg") 
        
    except HTTPException as http_exc: 
        raise http_exc # Repassa exceções formatadas
    except Exception as e:
        error_detail = f"Erro interno inesperado ao obter snapshot: {str(e)}"
        print(f"Erro inesperado no endpoint de snapshot para câmera {camera_id}: {error_detail}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        ) 

# --- ROTAS PARA CONFIGURAÇÕES DE DETECÇÃO --- 

@router.get(
    "/{camera_id}/detection_settings", 
    response_model=schemas.DetectionSettingsResponse, 
    tags=["cameras", "detection"],
    summary="Obter Configurações de Detecção",
    description="Retorna as configurações de detecção atuais para uma câmera específica."
)
async def get_detection_settings(
    camera_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Obtém as configurações de detecção para uma câmera."""
    # 1. Verificar permissão (câmera pertence ao usuário)
    db_camera = db.query(models.Camera).filter(
        models.Camera.id == camera_id, 
        models.Camera.owner_id == current_user.id
    ).first()
    if not db_camera:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Câmera não encontrada ou não pertence ao usuário")

    # TODO: Implementar retorno dos dados salvos ou default se nulo
    print(f"[Placeholder] GET /detection_settings para câmera {camera_id}")
    if db_camera.detection_settings: # Verifica se há dados salvos
        print("Retornando configurações salvas do DB")
        saved_settings = db_camera.detection_settings
        saved_settings["camera_id"] = camera_id # Adicionar ID para response model
        # Aqui pode ser necessário validar/mesclar com defaults se a estrutura mudar
        return saved_settings
    else:
        print("Retornando configurações padrão")
        default_settings = schemas.DetectionSettingsBase().dict()
        default_settings["camera_id"] = camera_id
        return default_settings

@router.put(
    "/{camera_id}/detection_settings", 
    response_model=schemas.DetectionSettingsResponse, 
    tags=["cameras", "detection"],
    summary="Atualizar Configurações de Detecção",
    description="Atualiza (substitui) as configurações de detecção para uma câmera específica."
)
async def update_detection_settings(
    camera_id: str,
    settings_data: schemas.DetectionSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Atualiza as configurações de detecção para uma câmera."""
    # 1. Verificar permissão
    db_camera = db.query(models.Camera).filter(
        models.Camera.id == camera_id, 
        models.Camera.owner_id == current_user.id
    ).first()
    if not db_camera:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Câmera não encontrada ou não pertence ao usuário")

    # 2. Atualizar a coluna JSONB com os novos dados
    print(f"Atualizando detection_settings para câmera {camera_id} com dados: {settings_data.dict()}")
    db_camera.detection_settings = settings_data.dict() # Substitui o JSON inteiro
    
    # 3. Salvar no banco de dados
    try:
        db.commit()
        db.refresh(db_camera) # Atualiza a instância db_camera com os dados do DB
    except Exception as e:
        db.rollback()
        print(f"Erro ao salvar detection_settings no DB: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao salvar as configurações de detecção: {e}"
        )

    # 4. Retornar os dados atualizados (incluindo camera_id para o response model)
    response_data = db_camera.detection_settings
    response_data["camera_id"] = camera_id
    return response_data 

# --- ROTAS PARA CONFIGURAÇÕES DE IA (Implementação Real) --- 

@router.get(
    "/{camera_id}/ai_settings", 
    response_model=schemas.AISettingsResponse, 
    tags=["cameras", "ai"],
    summary="Obter Configurações de IA",
    description="Retorna as configurações de IA atuais para uma câmera específica."
)
async def get_ai_settings(
    camera_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Obtém as configurações de IA para uma câmera."""
    # 1. Verificar permissão
    db_camera = db.query(models.Camera).filter(
        models.Camera.id == camera_id, 
        models.Camera.owner_id == current_user.id
    ).first()
    if not db_camera:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Câmera não encontrada ou não pertence ao usuário")

    # 2. Retornar configurações salvas ou defaults
    print(f"Buscando ai_settings para câmera {camera_id}")
    saved_settings = db_camera.ai_settings # Pega o JSONB do banco
    print(f"[GET AI Settings] Dados salvos no DB (antes do merge): {saved_settings}") # << Log 1 (Dados Brutos)
    print(f"[GET AI Settings] Tipo de confidence_threshold do DB: {type(saved_settings.get('confidence_threshold') if saved_settings else None)}") # << Log 2 (Tipo do DB)
    
    default_settings_dict = schemas.AISettingsBase().dict()
    if saved_settings: 
        print("Retornando configurações de IA salvas mescladas com defaults")
        merged_settings = {**default_settings_dict, **saved_settings}
    else:
        print("Retornando configurações de IA padrão")
        merged_settings = default_settings_dict
        
    merged_settings["camera_id"] = camera_id 
    print(f"[GET AI Settings] Dados mesclados retornados: {merged_settings}") # << Log 3 (Após Merge)
    return merged_settings

@router.put(
    "/{camera_id}/ai_settings", 
    response_model=schemas.AISettingsResponse, 
    tags=["cameras", "ai"],
    summary="Atualizar Configurações de IA",
    description="Atualiza (substitui) as configurações de IA para uma câmera específica."
)
async def update_ai_settings(
    camera_id: str,
    settings_data: schemas.AISettingsUpdate, # Schema para PUT pode ser o Base ou um Update
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Atualiza as configurações de IA para uma câmera."""
    # 1. Verificar permissão
    db_camera = db.query(models.Camera).filter(
        models.Camera.id == camera_id, 
        models.Camera.owner_id == current_user.id
    ).first()
    if not db_camera:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Câmera não encontrada ou não pertence ao usuário")

    # 2. Preparar dados para salvar 
    # Log dos dados recebidos após validação Pydantic
    print(f"[PUT AI Settings] Dados recebidos (settings_data): {settings_data.dict()}") # << Log 4 (Dados Recebidos)
    print(f"[PUT AI Settings] Tipo de confidence_threshold recebido: {type(settings_data.confidence_threshold)}") # << Log 5 (Tipo Recebido)

    update_data = settings_data.dict(exclude_unset=True) 
    print(f"Atualizando ai_settings para câmera {camera_id} com dados (exclude_unset=True): {update_data}")
    
    # Atribuir ao campo do modelo
    db_camera.ai_settings = update_data 
    # Log do que está prestes a ser salvo
    print(f"[PUT AI Settings] Valor atribuído a db_camera.ai_settings: {db_camera.ai_settings}") # << Log 6 (Antes de Salvar)
    print(f"[PUT AI Settings] Tipo de confidence_threshold antes de salvar: {type(db_camera.ai_settings.get('confidence_threshold'))}") # << Log 7 (Tipo Antes de Salvar)
    
    # 3. Salvar no banco de dados
    try:
        db.commit()
        db.refresh(db_camera) 
        print(f"[PUT AI Settings] Commit realizado com sucesso.") # << Log 8 (Após Salvar)
    except Exception as e:
        db.rollback()
        print(f"Erro ao salvar ai_settings no DB: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao salvar as configurações de IA: {e}"
        )

    # 4. Retornar os dados atualizados mesclados com defaults (para garantir resposta completa)
    # Mesma lógica do GET para garantir consistência na resposta
    default_settings_dict = schemas.AISettingsBase().dict()
    saved_settings = db_camera.ai_settings if db_camera.ai_settings else {}
    merged_settings = {**default_settings_dict, **saved_settings}
    merged_settings["camera_id"] = camera_id
    return merged_settings 

# --- ROTAS PARA CONTROLE DE PROCESSAMENTO --- 

@router.post(
    "/{camera_id}/start_processing", 
    response_model=schemas.ProcessorStatus, # Retorna o status após tentar iniciar
    tags=["processing"], 
    summary="Iniciar Processamento de Vídeo",
    description="Inicia o processo em background para conectar e analisar o stream RTSP da câmera."
)
async def start_processing(
    camera_id: str,
    # Não precisa de `db: Session = Depends(get_db)` aqui,
    # pois passaremos a fábrica para a função do serviço.
    current_user: models.User = Depends(security.get_current_user)
):
    """Inicia o processamento para uma câmera específica."""
    # 1. Verificar se o serviço está disponível
    if video_service is None:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Serviço de vídeo não está disponível.")
        
    # 2. Verificar permissão (usuário precisa ter acesso à câmera para iniciá-la)
    #    Reutilizar get_db para criar uma sessão temporária para esta verificação
    db = SessionLocal()
    try:
        db_camera = db.query(models.Camera).filter(
            models.Camera.id == camera_id, 
            models.Camera.owner_id == current_user.id
        ).first()
        if not db_camera:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Câmera não encontrada ou não pertence ao usuário")
    finally:
        db.close()

    # 3. Chamar a função do serviço para iniciar, passando a fábrica de sessão
    status_info = video_service.start_camera_processing(camera_id, SessionLocal)
    if not status_info.get("is_running") and status_info.get("last_error"):
        # Se falhou ao iniciar, retornar um erro HTTP apropriado
        # Usar 503 se for falha de conexão, 400 se config errada, etc.
        # Por simplicidade, usaremos 500 por enquanto se houver erro ao iniciar.
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Falha ao iniciar processamento: {status_info['last_error']}")
         
    return status_info

@router.post(
    "/{camera_id}/stop_processing", 
    response_model=schemas.ProcessorStatus, # Retorna o status após tentar parar
    tags=["processing"],
    summary="Parar Processamento de Vídeo",
    description="Para o processo em background que analisa o stream RTSP da câmera."
)
async def stop_processing(
    camera_id: str,
    current_user: models.User = Depends(security.get_current_user)
):
    """Para o processamento para uma câmera específica."""
    if video_service is None:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Serviço de vídeo não está disponível.")

    # Verificar permissão antes de parar (opcional, mas bom)
    db = SessionLocal()
    try:
        db_camera = db.query(models.Camera).filter(
            models.Camera.id == camera_id, 
            models.Camera.owner_id == current_user.id
        ).first()
        if not db_camera:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Câmera não encontrada ou não pertence ao usuário")
    finally:
        db.close()
        
    status_info = video_service.stop_camera_processing(camera_id)
    return status_info

@router.get(
    "/{camera_id}/processing_status", 
    response_model=schemas.ProcessorStatus,
    tags=["processing"],
    summary="Obter Status do Processamento",
    description="Verifica o status atual do processo de análise para uma câmera específica."
)
async def get_processing_status(
    camera_id: str,
    current_user: models.User = Depends(security.get_current_user)
):
    """Obtém o status de processamento para uma câmera específica."""
    if video_service is None:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Serviço de vídeo não está disponível.")

    # Verificar permissão (opcional, mas bom)
    db = SessionLocal()
    try:
        db_camera = db.query(models.Camera).filter(
            models.Camera.id == camera_id, 
            models.Camera.owner_id == current_user.id
        ).first()
        if not db_camera:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Câmera não encontrada ou não pertence ao usuário")
    finally:
        db.close()
        
    processor = video_service.active_processors.get(camera_id)
    if processor:
        return processor.get_status()
    else:
        # Se não está ativo, retornar um status indicando isso
        # Poderia buscar a URL do DB para retornar, mas simplificamos
        return schemas.ProcessorStatus(camera_id=camera_id, is_running=False, last_error="Processador não ativo")

# Opcional: Rota para ver o status de todos os processadores
# @router.get("/processing/status", response_model=List[schemas.ProcessorStatus], tags=["processing"])
# async def get_all_statuses(current_user: models.User = Depends(security.get_current_active_admin_user)): # Exemplo: Só admin vê todos
#     if video_service is None:
#         raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Serviço de vídeo não está disponível.")
#     # TODO: Filtrar status para mostrar apenas câmeras do usuário se não for admin?
#     return video_service.get_all_processors_status()

# ... (final do arquivo) ... 