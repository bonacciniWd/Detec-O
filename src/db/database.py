"""
Módulo para conexão e operações com o banco de dados MongoDB.
"""

import os
import logging
import motor.motor_asyncio
from datetime import datetime
from bson import ObjectId
from typing import Optional, List

# Configurar logger
logger = logging.getLogger(__name__)

# Variáveis globais para controle da conexão
client = None
db = None

async def init_db(config):
    """
    Inicializa a conexão com o banco de dados.
    
    Args:
        config: Configurações da aplicação
    
    Returns:
        bool: True se a conexão foi estabelecida, False caso contrário
    """
    global client, db
    
    try:
        # Obter configurações
        mongo_uri = config.get('mongo_uri', os.environ.get('MONGO_URI', 'mongodb://localhost:27017'))
        db_name = config.get('db_name', os.environ.get('DB_NAME', 'crime_detection_system'))
        
        # Registrar início da conexão (sem expor senha)
        safe_uri = mongo_uri.split('@')[-1]
        logger.info(f"Conectando ao MongoDB: {safe_uri}")
        
        # Criar cliente MongoDB assíncrono
        client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
        db = client[db_name]
        
        # Verificar conexão
        await client.admin.command('ping')
        logger.info(f"Conexão estabelecida com o banco de dados: {db_name}")
        
        # Criar índices necessários
        await _ensure_indexes()
        
        return True
    except Exception as e:
        logger.error(f"Erro ao conectar ao MongoDB: {str(e)}")
        return False

async def close_db():
    """
    Fecha a conexão com o banco de dados.
    """
    global client
    
    if client:
        logger.info("Fechando conexão com o MongoDB")
        client.close()
        client = None

async def _ensure_indexes():
    """
    Cria índices necessários no banco de dados.
    """
    global db
    
    if not db:
        logger.warning("Banco de dados não inicializado ao tentar criar índices")
        return
    
    try:
        # Índice para eventos por câmera e timestamp
        await db.detection_events.create_index([
            ("camera_id", 1),
            ("timestamp", -1)
        ])
        
        # Índice para busca de pessoas por identificação
        await db.person_records.create_index([
            ("identification", 1)
        ], unique=True)
        
        logger.info("Índices criados/verificados com sucesso")
    except Exception as e:
        logger.error(f"Erro ao criar índices: {str(e)}")

async def save_detection_event(event_data):
    """
    Salva um evento de detecção no banco de dados.
    
    Args:
        event_data: Dados do evento
    
    Returns:
        str: ID do documento inserido ou None em caso de falha
    """
    global db
    
    if not db:
        logger.warning("Tentativa de salvar evento sem conexão com banco de dados")
        return None
    
    try:
        # Garantir que timestamp existe
        if 'timestamp' not in event_data:
            event_data['timestamp'] = datetime.now()
        
        # Inserir documento
        result = await db.detection_events.insert_one(event_data)
        logger.info(f"Evento salvo com ID: {result.inserted_id}")
        
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Erro ao salvar evento: {str(e)}")
        return None

async def get_detection_events(camera_ids: Optional[List[str]] = None, start_date=None, end_date=None, limit=100):
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
    global db
    
    if not db:
        logger.warning("Tentativa de buscar eventos sem conexão com banco de dados")
        return []
    
    try:
        # Construir filtro
        query = {}
        
        # Modificado para aceitar lista de IDs
        if camera_ids:
            # Garante que são strings válidas, embora não valide formato ObjectId aqui
            valid_camera_ids = [str(cid) for cid in camera_ids if isinstance(cid, str)]
            if valid_camera_ids:
                query['camera_id'] = {'$in': valid_camera_ids}
            else:
                 # Se a lista for vazia ou inválida, não retorna nada para essas câmeras
                 return []
            
        if start_date or end_date:
            query['timestamp'] = {}
            
            if start_date:
                query['timestamp']['$gte'] = start_date
                
            if end_date:
                query['timestamp']['$lte'] = end_date
        
        # Executar consulta
        cursor = db.detection_events.find(query).sort('timestamp', -1).limit(limit)
        
        # Converter para lista de dicionários
        events = []
        async for event in cursor:
            # Converter ObjectId para string
            event['_id'] = str(event['_id'])
            # Garantir que camera_id também seja string na resposta, se existir
            if 'camera_id' in event and isinstance(event['camera_id'], ObjectId):
                event['camera_id'] = str(event['camera_id'])
            events.append(event)
        
        return events
    except Exception as e:
        logger.error(f"Erro ao buscar eventos: {str(e)}")
        return []

async def save_person_record(person_data):
    """
    Salva ou atualiza registro de pessoa no banco de dados.
    
    Args:
        person_data: Dados da pessoa
    
    Returns:
        str: ID do documento inserido/atualizado ou None em caso de falha
    """
    global db
    
    if not db:
        logger.warning("Tentativa de salvar registro de pessoa sem conexão com banco de dados")
        return None
    
    try:
        # Garantir que tem identificação
        if 'identification' not in person_data:
            logger.error("Tentativa de salvar pessoa sem identificação")
            return None
        
        # Verificar se já existe registro
        existing = await db.person_records.find_one({'identification': person_data['identification']})
        
        if existing:
            # Atualizar registro existente
            person_data['updated_at'] = datetime.now()
            result = await db.person_records.update_one(
                {'_id': existing['_id']},
                {'$set': person_data}
            )
            
            logger.info(f"Registro de pessoa atualizado: {existing['_id']}")
            return str(existing['_id'])
        else:
            # Criar novo registro
            person_data['created_at'] = datetime.now()
            person_data['updated_at'] = datetime.now()
            
            result = await db.person_records.insert_one(person_data)
            logger.info(f"Novo registro de pessoa criado: {result.inserted_id}")
            
            return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Erro ao salvar registro de pessoa: {str(e)}")
        return None

async def get_person_records(identification=None):
    """
    Recupera registros de pessoas do banco de dados.
    
    Args:
        identification: Identificação para filtrar (opcional)
    
    Returns:
        list: Lista de registros de pessoas
    """
    global db
    
    if not db:
        logger.warning("Tentativa de buscar registros de pessoas sem conexão com banco de dados")
        return []
    
    try:
        # Construir filtro
        query = {}
        
        if identification:
            query['identification'] = identification
        
        # Executar consulta
        cursor = db.person_records.find(query)
        
        # Converter para lista de dicionários
        records = []
        async for record in cursor:
            # Converter ObjectId para string
            record['_id'] = str(record['_id'])
            records.append(record)
        
        return records
    except Exception as e:
        logger.error(f"Erro ao buscar registros de pessoas: {str(e)}")
        return [] 