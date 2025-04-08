"""
Módulo para conexão e operações com o banco de dados PostgreSQL usando SQLAlchemy.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, select, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from datetime import datetime
from contextlib import asynccontextmanager

# Configurar logger
logger = logging.getLogger(__name__)

# Variáveis globais para controle da conexão
engine = None
SessionLocal = None
Base = declarative_base()

async def init_db(config: Dict[str, Any]) -> bool:
    """
    Inicializa a conexão com o banco de dados.

    Args:
        config: Configurações da aplicação

    Returns:
        bool: True se a conexão foi estabelecida, False caso contrário
    """
    global engine, SessionLocal

    try:
        # Obter configurações
        db_url = config.get('database_url', os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/deteco'))
        db_name = db_url.split('/')[-1]

        # Registrar início da conexão (sem expor senha)
        safe_url = db_url.replace(db_url.split('@')[-2].split(':')[-1], '****')
        logger.info(f"Conectando ao PostgreSQL: {safe_url}")

        # Criar engine SQLAlchemy
        engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,  # Reciclar conexões após 30 minutos
            connect_args={"check_same_thread": False} if db_url.startswith("sqlite") else {}
        )
        
        # Criar fábrica de sessão
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Verificar conexão
        with SessionLocal() as session:
            # Executa uma query simples para verificar conexão
            session.execute("SELECT 1")
        
        logger.info(f"Conexão estabelecida com o banco de dados: {db_name}")
        
        # Criar tabelas se não existirem
        await _ensure_tables()
        
        return True
    except Exception as e:
        logger.error(f"Erro ao conectar ao PostgreSQL: {str(e)}")
        return False

async def close_db() -> None:
    """
    Fecha a conexão com o banco de dados.
    """
    global engine

    if engine:
        logger.info("Fechando conexão com o PostgreSQL")
        engine.dispose()
        engine = None

async def _ensure_tables() -> None:
    """
    Cria tabelas necessárias no banco de dados se não existirem.
    """
    global engine

    if not engine:
        logger.warning("Banco de dados não inicializado ao tentar criar tabelas")
        return

    try:
        # Importar modelos para criar tabelas
        from app.models.models import AIModel, CameraAISettings, DetectionEvent, User
        from app.models.camera import Camera
        
        # Criar todas as tabelas definidas
        Base.metadata.create_all(bind=engine)
        
        logger.info("Tabelas criadas/verificadas com sucesso")
    except Exception as e:
        logger.error(f"Erro ao criar tabelas: {str(e)}")

@asynccontextmanager
async def get_db_session():
    """
    Contexto assíncrono para gerenciar sessões de banco de dados.
    
    Yields:
        Session: Uma sessão de banco de dados SQLAlchemy
    """
    global SessionLocal
    
    if not SessionLocal:
        raise RuntimeError("Banco de dados não inicializado")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def save_detection_event(event_data: Dict[str, Any]) -> Optional[int]:
    """
    Salva um evento de detecção no banco de dados.

    Args:
        event_data: Dados do evento

    Returns:
        int: ID do registro inserido ou None em caso de falha
    """
    # Implementar a inserção usando SQLAlchemy
    from app.models.models import DetectionEvent
    
    try:
        async with get_db_session() as db:
            # Garantir que timestamp existe
            if 'timestamp' not in event_data:
                event_data['timestamp'] = datetime.now()
                
            new_event = DetectionEvent(**event_data)
            db.add(new_event)
            db.commit()
            db.refresh(new_event)
            logger.info(f"Evento salvo com ID: {new_event.id}")
            return new_event.id
    except Exception as e:
        logger.error(f"Erro ao salvar evento de detecção: {str(e)}")
        return None

async def get_detection_events(camera_ids: Optional[List[int]] = None, 
                               start_date: Optional[datetime] = None, 
                               end_date: Optional[datetime] = None, 
                               limit: int = 100) -> List[Dict[str, Any]]:
    """
    Recupera eventos de detecção do banco de dados.
    
    Args:
        camera_ids: Lista de IDs de câmeras para filtrar (opcional)
        start_date: Data de início para filtrar eventos
        end_date: Data de fim para filtrar eventos
        limit: Número máximo de eventos a retornar
    
    Returns:
        list: Lista de eventos de detecção
    """
    from app.models.models import DetectionEvent
    
    try:
        async with get_db_session() as db:
            # Construir consulta
            query = select(DetectionEvent).order_by(DetectionEvent.timestamp.desc()).limit(limit)
            
            # Adicionar filtros
            filters = []
            
            if camera_ids:
                filters.append(DetectionEvent.camera_id.in_(camera_ids))
                
            if start_date:
                filters.append(DetectionEvent.timestamp >= start_date)
                
            if end_date:
                filters.append(DetectionEvent.timestamp <= end_date)
                
            if filters:
                query = query.where(and_(*filters))
                
            # Executar consulta
            result = await db.execute(query)
            events = result.scalars().all()
            
            # Converter para dicionários para compatibilidade com código anterior
            return [
                {
                    "id": event.id,
                    "camera_id": event.camera_id,
                    "ai_model_id": event.ai_model_id,
                    "event_type": event.event_type,
                    "confidence": event.confidence,
                    "detected_class": event.detected_class,
                    "bounding_box": event.bounding_box,
                    "image_path": event.image_path,
                    "video_path": event.video_path,
                    "timestamp": event.timestamp
                }
                for event in events
            ]
    except Exception as e:
        logger.error(f"Erro ao buscar eventos: {str(e)}")
        return []

async def save_person_record(person_data: Dict[str, Any]) -> Optional[int]:
    """
    Salva ou atualiza registro de pessoa no banco de dados.
    
    Args:
        person_data: Dados da pessoa
    
    Returns:
        int: ID do registro inserido/atualizado ou None em caso de falha
    """
    # Este método precisará ser implementado quando o modelo Person for definido
    # Por enquanto, vai apenas registrar que foi chamado
    logger.warning("Método save_person_record chamado, mas ainda não implementado para PostgreSQL")
    return None

async def get_person_records(identification: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Recupera registros de pessoas do banco de dados.
    
    Args:
        identification: Identificação para filtrar (opcional)
    
    Returns:
        list: Lista de registros de pessoas
    """
    # Este método precisará ser implementado quando o modelo Person for definido
    # Por enquanto, vai apenas registrar que foi chamado
    logger.warning("Método get_person_records chamado, mas ainda não implementado para PostgreSQL")
    return [] 