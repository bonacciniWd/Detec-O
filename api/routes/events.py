"""
Rotas para gerenciamento de eventos de detecção
"""
import os # Para caminhos de arquivo
import subprocess # Para chamar ffmpeg
import tempfile # Para arquivo temporário de lista
import shutil # Para verificar se ffmpeg existe
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from fastapi.responses import StreamingResponse # Para retornar vídeo
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime, timedelta, date
import io
import asyncio
from sqlalchemy import or_, func, extract # Importar or_, func e extract

from api import models, schemas, security
from api.db import get_db
from pydantic import validator # Importar validator se não estiver já importado em schemas.py

router = APIRouter(prefix="/events", tags=["events"])

@router.get("/", response_model=List[schemas.DetectionEventResponse])
async def get_events(
    camera_id: Optional[str] = None,
    event_type: Optional[str] = None,
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Confiança mínima da detecção"),
    feedback_status: Optional[str] = Query(None, description="Filtrar por status de feedback (true_positive, false_positive, uncertain, none)"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Obtém a lista de eventos de detecção com filtros opcionais.
    Converte objetos SQLAlchemy em dicts para evitar erros de serialização.
    """
    # Iniciar query base
    query = db.query(models.DetectionEvent).join(
        models.Camera, models.DetectionEvent.camera_id == models.Camera.id
    ).filter(
        models.Camera.owner_id == current_user.id
    )
    
    # Aplicar filtros se fornecidos
    if camera_id:
        query = query.filter(models.DetectionEvent.camera_id == camera_id)
    
    if event_type:
        query = query.filter(models.DetectionEvent.event_type == event_type)
    
    if start_date:
        query = query.filter(models.DetectionEvent.timestamp >= start_date)
    
    if end_date:
        query = query.filter(models.DetectionEvent.timestamp <= end_date)
    
    # Aplicar novos filtros
    if min_confidence is not None:
        query = query.filter(models.DetectionEvent.confidence >= min_confidence)
        
    if feedback_status is not None:
        if feedback_status == 'none':
            # Filtrar por eventos onde feedback_status é NULL
            query = query.filter(models.DetectionEvent.feedback_status.is_(None))
        elif feedback_status in ['true_positive', 'false_positive', 'uncertain']:
            query = query.filter(models.DetectionEvent.feedback_status == feedback_status)
        # Ignorar valores inválidos de feedback_status ou adicionar um erro HTTPException
        # else:
        #     raise HTTPException(status_code=400, detail="Valor inválido para feedback_status")
            
    # Ordenar por data/hora, mais recentes primeiro
    query = query.order_by(models.DetectionEvent.timestamp.desc())
    
    # Paginar resultados
    events_db = query.offset(skip).limit(limit).all()
    
    # WORKAROUND: Converter para lista de dicionários
    events_list = []
    for event in events_db:
        event_dict = {
            field: getattr(event, field) 
            for field in schemas.DetectionEventResponse.__fields__ 
            if hasattr(event, field)
        }
        events_list.append(event_dict)
        
    return events_list

@router.get("/{event_id}", response_model=schemas.DetectionEventResponse)
async def get_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Obtém detalhes de um evento específico
    """
    # Buscar evento com verificação de permissão E carregar relacionamentos
    event = (
        db.query(models.DetectionEvent)
        .join(models.Camera, models.DetectionEvent.camera_id == models.Camera.id)
        .options(
            joinedload(models.DetectionEvent.camera), # Pode ser redundante com o join, mas seguro
            joinedload(models.DetectionEvent.detected_person) # Carregar pessoa
        )
        .filter(
            models.DetectionEvent.id == event_id,
            models.Camera.owner_id == current_user.id # Manter filtro de permissão
        )
        .first()
    )

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado ou acesso não permitido" # Mensagem mais clara
        )

    # Construir resposta a partir do objeto event encontrado
    # Usar .from_orm() diretamente pode funcionar se Config estiver ok
    response = schemas.DetectionEventResponse.from_orm(event).dict() # Converter para dict para modificar
    response['detected_person_name'] = event.detected_person.name if event.detected_person else None

    # Adicionar nome da câmera se necessário (exemplo)
    # response['camera_name'] = event.camera.name if event.camera else None

    return response # Retornar o dicionário modificado

@router.post("/", response_model=schemas.DetectionEventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event: schemas.DetectionEventCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Cria um novo evento de detecção (para testes ou uso interno)
    """
    # Verificar se a câmera existe e pertence ao usuário
    camera = db.query(models.Camera).filter(
        models.Camera.id == event.camera_id,
        models.Camera.owner_id == current_user.id
    ).first()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Câmera não encontrada ou não pertence ao usuário"
        )
    
    # Criar novo evento
    db_event = models.DetectionEvent(**event.dict())
    
    # Adicionar ao banco de dados
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    return db_event

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Remove um evento específico
    """
    # Buscar evento com verificação de permissão
    event = db.query(models.DetectionEvent).join(
        models.Camera, models.DetectionEvent.camera_id == models.Camera.id
    ).filter(
        models.DetectionEvent.id == event_id,
        models.Camera.owner_id == current_user.id
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado"
        )
    
    # Remover evento
    db.delete(event)
    db.commit()
    
    return None

@router.get("/stats", response_model=dict)
async def get_event_stats(
    days: int = 7,
    camera_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Obtém estatísticas dos eventos (contagem por tipo, severidade, etc.)
    """
    # Definir período
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Iniciar query base
    query = db.query(models.DetectionEvent).join(
        models.Camera, models.DetectionEvent.camera_id == models.Camera.id
    ).filter(
        models.Camera.owner_id == current_user.id,
        models.DetectionEvent.timestamp >= start_date,
        models.DetectionEvent.timestamp <= end_date
    )
    
    # Filtrar por câmera se especificado
    if camera_id:
        query = query.filter(models.DetectionEvent.camera_id == camera_id)
    
    # Buscar todos os eventos no período
    events = query.all()
    
    # Calcular estatísticas
    total_count = len(events)
    
    # Contagem por tipo de evento
    event_types = {}
    for event in events:
        event_type = event.event_type
        event_types[event_type] = event_types.get(event_type, 0) + 1
    
    # Outras estatísticas (implementar conforme necessário)
    
    return {
        "total_count": total_count,
        "period_days": days,
        "start_date": start_date,
        "end_date": end_date,
        "by_type": event_types
    }

# --- Nova Rota para Vídeo do Evento ---
@router.get(
    "/{event_id}/video",
    tags=["events"],
    summary="Obter Vídeo de um Evento",
    description=(
        "Busca os snapshots de um evento, gera um vídeo MP4 usando FFmpeg "
        "e retorna o vídeo. Requer que o FFmpeg esteja instalado e acessível no PATH."
    ),
    responses={
        200: {"content": {"video/mp4": {}}, "description": "Vídeo do evento em formato MP4"},
        404: {"description": "Evento ou snapshots não encontrados, ou evento não pertence ao usuário"},
        500: {"description": "Erro interno ao gerar o vídeo (ex: FFmpeg não encontrado ou erro do FFmpeg)"}
    }
)
async def get_event_video(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Gera e retorna um vídeo MP4 a partir dos snapshots de um evento."""

    # Verificar se ffmpeg está disponível
    if shutil.which("ffmpeg") is None:
        print("ERRO: Comando 'ffmpeg' não encontrado no PATH.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Dependência externa 'ffmpeg' não encontrada no servidor."
        )

    # 1. Buscar o evento e verificar permissão
    event = db.query(models.DetectionEvent).join(
        models.Camera, models.DetectionEvent.camera_id == models.Camera.id
    ).filter(
        models.DetectionEvent.id == event_id,
        models.Camera.owner_id == current_user.id
    ).first()

    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento não encontrado ou não pertence ao usuário")

    # 2. Buscar os snapshots associados, ordenados por timestamp
    snapshots = db.query(models.EventSnapshot).filter(
        models.EventSnapshot.event_id == event_id
    ).order_by(models.EventSnapshot.timestamp.asc()).all()

    if not snapshots:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhum snapshot encontrado para este evento.")

    # Diretório onde os snapshots são salvos (precisa ser consistente com video_service.py)
    # Assumindo que video_service está em api/ e snapshots em api/snapshots/
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Raiz do projeto? Ou api/? Ajustar se necessário.
    snapshots_dir = os.path.join(base_dir, "api", "snapshots") 
    # Se video_service.py está em api/ e usa CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)), então:
    current_dir = os.path.dirname(os.path.abspath(__file__)) # api/routes/
    api_dir = os.path.dirname(current_dir) # api/
    snapshots_dir = os.path.join(api_dir, "snapshots")
    print(f"[Event Video] Usando diretório de snapshots: {snapshots_dir}")

    # 3. Criar arquivo temporário com a lista de snapshots para o ffmpeg
    snapshot_files_exist = True
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_list_file:
            list_file_path = tmp_list_file.name
            print(f"[Event Video] Criado arquivo de lista temporário: {list_file_path}")
            for snapshot in snapshots:
                full_path = os.path.join(snapshots_dir, snapshot.snapshot_path)
                if not os.path.exists(full_path):
                    print(f"AVISO: Snapshot não encontrado no disco: {full_path}")
                    snapshot_files_exist = False
                    # O que fazer? Pular? Parar? Por enquanto, vamos continuar mas marcar.
                    continue # Pular este frame se não existir
                # Escapar caracteres especiais e usar barras corretas para ffmpeg
                safe_path = full_path.replace("\\", "/").replace("'", "'\\''") 
                tmp_list_file.write(f"file '{safe_path}'\n")
                tmp_list_file.write(f"duration 0.1\n") # Ajustar duração por frame (ex: 0.1s = 10fps)

        if not snapshot_files_exist:
            print(f"AVISO: Um ou mais arquivos de snapshot não foram encontrados para o evento {event_id}. O vídeo pode estar incompleto ou falhar.")
            # Poderia levantar 404 aqui se nenhum arquivo existir?

        # 4. Montar e executar o comando ffmpeg
        # Usar pipe:1 para direcionar a saída para stdout
        # -y: sobrescrever saída (não aplicável a pipe, mas seguro)
        # -f concat: usar o demuxer de concatenação
        # -safe 0: permitir caminhos absolutos ou relativos no arquivo de lista
        # -i list_file_path: arquivo de entrada com a lista
        # -c:v libx264: codec de vídeo
        # -pix_fmt yuv420p: formato de pixel compatível com a maioria dos players
        # -movflags +faststart: otimiza para streaming web
        # -vf "fps=10": Definir framerate de saída (ajustar conforme 'duration' na lista)
        # -f mp4: formato de saída
        # pipe:1: saída para stdout
        ffmpeg_cmd = [
            'ffmpeg',
            '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', list_file_path,
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-vf', 'fps=10', # Ajustar fps para corresponder à 'duration' (1/duration)
            '-movflags', '+faststart',
            '-f', 'mp4',
            'pipe:1'
        ]

        print(f"[Event Video] Executando FFmpeg: {' '.join(ffmpeg_cmd)}")
        process = await asyncio.create_subprocess_exec(
            *ffmpeg_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_message = stderr.decode() if stderr else "Erro desconhecido do FFmpeg"
            print(f"ERRO: FFmpeg falhou para o evento {event_id}. Código: {process.returncode}\nErro: {error_message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Falha ao gerar vídeo: {error_message[:200]}..."
            )

        print(f"[Event Video] Vídeo gerado com sucesso para evento {event_id} ({len(stdout)} bytes).")
        # 5. Retornar o vídeo como StreamingResponse
        return StreamingResponse(io.BytesIO(stdout), media_type="video/mp4")

    except FileNotFoundError:
        print(f"ERRO: Arquivo de lista temporário não pôde ser criado ou lido.")
        raise HTTPException(status_code=500, detail="Erro interno ao processar a lista de snapshots.")
    except Exception as e:
        print(f"ERRO inesperado ao gerar vídeo para evento {event_id}: {e}")
        # Limpar o arquivo temporário em caso de erro geral
        if 'list_file_path' in locals() and os.path.exists(list_file_path):
            os.remove(list_file_path)
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao gerar vídeo: {str(e)}")
    finally:
        # 6. Garantir a limpeza do arquivo temporário
        if 'list_file_path' in locals() and os.path.exists(list_file_path):
            print(f"[Event Video] Removendo arquivo de lista temporário: {list_file_path}")
            os.remove(list_file_path) 

@router.post("/{event_id}/feedback", response_model=schemas.DetectionEventResponse, status_code=status.HTTP_200_OK)
async def submit_event_feedback(
    event_id: str,
    feedback: schemas.EventFeedbackCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user) # Usar usuário ativo
):
    """Submete um feedback para um evento de detecção específico."""
    
    # 1. Buscar o evento e verificar permissão
    event = db.query(models.DetectionEvent).join(
        models.Camera, models.DetectionEvent.camera_id == models.Camera.id
    ).filter(
        models.DetectionEvent.id == event_id,
        models.Camera.owner_id == current_user.id
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado ou não pertence ao usuário"
        )
        
    # 2. Atualizar os campos de feedback no objeto do evento
    event.feedback_status = feedback.feedback_status
    event.feedback_notes = feedback.feedback_notes
    event.feedback_user_id = current_user.id
    event.feedback_timestamp = datetime.utcnow()
    
    # 3. Salvar as mudanças no banco de dados
    try:
        db.add(event) # Adicionar à sessão para rastrear mudanças
        db.commit()
        db.refresh(event) # Recarregar o objeto com os dados atualizados
    except Exception as e:
        db.rollback() # Reverter em caso de erro
        print(f"Erro ao salvar feedback para evento {event_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao salvar o feedback."
        )
        
    return event 

# --- Rota para Série Temporal de Eventos ---
@router.get("/stats/timeseries", response_model=List[schemas.EventTimeSeriesPoint])
async def get_event_timeseries(
    start_date: date = Query(..., description="Data inicial (YYYY-MM-DD)"),
    end_date: date = Query(..., description="Data final (YYYY-MM-DD)"),
    camera_id: Optional[str] = Query(None, description="ID opcional da câmera para filtrar"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Obtém a contagem de eventos por dia dentro de um intervalo de datas."""
    
    try:
        # Query base para contar eventos por dia
        query = db.query(
            func.date(models.DetectionEvent.timestamp).label('event_date'), 
            func.count(models.DetectionEvent.id).label('event_count')
        ).join(
            models.Camera, models.DetectionEvent.camera_id == models.Camera.id
        ).filter(
            models.Camera.owner_id == current_user.id,
            func.date(models.DetectionEvent.timestamp) >= start_date,
            func.date(models.DetectionEvent.timestamp) <= end_date
        )

        # Aplicar filtro de câmera se fornecido
        if camera_id:
            query = query.filter(models.DetectionEvent.camera_id == camera_id)

        # Agrupar por data e ordenar
        query = query.group_by('event_date').order_by('event_date')

        results = query.all()
        
        # Formatar resultado para o schema
        timeseries_data = [
            schemas.EventTimeSeriesPoint(date=row.event_date, count=row.event_count) 
            for row in results
        ]
        
        return timeseries_data
        
    except Exception as e:
        print(f"Erro ao buscar série temporal de eventos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar a série temporal de eventos."
        ) 

# --- Rota para Distribuição por Hora ---
@router.get("/stats/hourly", response_model=List[schemas.EventHourlyCount])
async def get_event_hourly_distribution(
    start_date: Optional[date] = Query(None, description="Data inicial opcional"),
    end_date: Optional[date] = Query(None, description="Data final opcional"),
    camera_id: Optional[str] = Query(None, description="ID opcional da câmera para filtrar"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Obtém a contagem de eventos agrupada por hora do dia."""
    try:
        query = db.query(
            extract('hour', models.DetectionEvent.timestamp).label('event_hour'),
            func.count(models.DetectionEvent.id).label('event_count')
        ).join(
            models.Camera, models.DetectionEvent.camera_id == models.Camera.id
        ).filter(
            models.Camera.owner_id == current_user.id
        )

        # Aplicar filtros de data se fornecidos
        if start_date:
            query = query.filter(func.date(models.DetectionEvent.timestamp) >= start_date)
        if end_date:
            query = query.filter(func.date(models.DetectionEvent.timestamp) <= end_date)
            
        # Aplicar filtro de câmera se fornecido
        if camera_id:
            query = query.filter(models.DetectionEvent.camera_id == camera_id)

        # Agrupar pela hora
        query = query.group_by('event_hour').order_by('event_hour')

        results = query.all()

        # Formatar para o schema de resposta
        hourly_counts = [
            schemas.EventHourlyCount(hour=row.event_hour, count=row.event_count)
            for row in results
        ]
        
        # Garantir que todas as 24 horas estejam presentes (com contagem 0 se necessário)
        # Isso pode ser feito aqui ou no frontend
        complete_hourly_data = {hour: 0 for hour in range(24)}
        for item in hourly_counts:
            complete_hourly_data[item.hour] = item.count
            
        final_data = [
            schemas.EventHourlyCount(hour=h, count=c) 
            for h, c in sorted(complete_hourly_data.items())
        ]

        return final_data

    except Exception as e:
        print(f"Erro ao buscar distribuição horária de eventos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar distribuição horária."
        ) 