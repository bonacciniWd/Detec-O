import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

# Importar os modelos SQLAlchemy
from app.models.camera import Camera
from app.database import get_db

# Configurar logger
logger = logging.getLogger(__name__)

# Função para criar câmera
def add_camera(camera_data: Dict[str, Any], owner: str, db: Session = None) -> Optional[Camera]:
    """
    Adiciona uma nova câmera ao banco de dados.
    
    Args:
        camera_data: Dados da câmera
        owner: Identificação do proprietário
        db: Sessão de banco de dados (opcional)
        
    Returns:
        Camera: Objeto câmera criado ou None em caso de falha
    """
    try:
        # Verificar se uma sessão foi fornecida
        session_provided = db is not None
        if not session_provided:
            db = next(get_db())
        
        try:
            # Preparar dados da câmera
            camera_dict = dict(camera_data)
            camera_dict["owner"] = owner
            
            # Criar novo objeto de câmera
            new_camera = Camera(**camera_dict)
            
            # Adicionar à sessão e salvar
            db.add(new_camera)
            db.commit()
            db.refresh(new_camera)
            
            logger.info(f"Câmera adicionada com ID: {new_camera.id}")
            return new_camera
        finally:
            # Fechar sessão se foi criada aqui
            if not session_provided:
                db.close()
    except Exception as e:
        logger.error(f"Erro ao adicionar câmera: {str(e)}")
        return None

def get_cameras_by_user(owner: str, db: Session = None) -> List[Camera]:
    """
    Busca todas as câmeras pertencentes a um usuário.
    
    Args:
        owner: Identificação do proprietário
        db: Sessão de banco de dados (opcional)
        
    Returns:
        List[Camera]: Lista de câmeras do usuário
    """
    try:
        # Verificar se uma sessão foi fornecida
        session_provided = db is not None
        if not session_provided:
            db = next(get_db())
        
        try:
            # Executar consulta
            cameras = db.query(Camera).filter(Camera.owner == owner).all()
            return list(cameras)
        finally:
            # Fechar sessão se foi criada aqui
            if not session_provided:
                db.close()
    except Exception as e:
        logger.error(f"Erro ao buscar câmeras do usuário {owner}: {str(e)}")
        return []

def get_camera_by_id(camera_id: int, owner: Optional[str] = None, db: Session = None) -> Optional[Camera]:
    """
    Busca uma câmera específica pelo seu ID, opcionalmente verificando o proprietário.
    
    Args:
        camera_id: ID da câmera
        owner: Identificação do proprietário (opcional)
        db: Sessão de banco de dados (opcional)
        
    Returns:
        Camera: Objeto câmera encontrado ou None
    """
    try:
        # Verificar se uma sessão foi fornecida
        session_provided = db is not None
        if not session_provided:
            db = next(get_db())
        
        try:
            # Construir consulta base
            query = db.query(Camera).filter(Camera.id == camera_id)
            
            # Adicionar filtro de proprietário se fornecido
            if owner:
                query = query.filter(Camera.owner == owner)
                
            # Executar consulta
            camera = query.first()
            return camera
        finally:
            # Fechar sessão se foi criada aqui
            if not session_provided:
                db.close()
    except Exception as e:
        logger.error(f"Erro ao buscar câmera com ID {camera_id}: {str(e)}")
        return None

def update_camera(camera_id: int, camera_data: Dict[str, Any], owner: Optional[str] = None, db: Session = None) -> bool:
    """
    Atualiza os dados de uma câmera existente.
    
    Args:
        camera_id: ID da câmera a ser atualizada
        camera_data: Novos dados da câmera
        owner: Identificação do proprietário (para verificação)
        db: Sessão de banco de dados (opcional)
        
    Returns:
        bool: True se a atualização foi bem-sucedida
    """
    try:
        # Verificar se uma sessão foi fornecida
        session_provided = db is not None
        if not session_provided:
            db = next(get_db())
        
        try:
            # Buscar a câmera existente
            query = db.query(Camera).filter(Camera.id == camera_id)
            if owner:
                query = query.filter(Camera.owner == owner)
                
            camera = query.first()
            
            if not camera:
                logger.warning(f"Câmera com ID {camera_id} não encontrada para atualização")
                return False
            
            # Atualizar campos
            for key, value in camera_data.items():
                if hasattr(camera, key):
                    setattr(camera, key, value)
            
            # Atualizar campo updated_at
            camera.updated_at = datetime.now()
                    
            # Salvar alterações
            db.commit()
            db.refresh(camera)
            
            logger.info(f"Câmera com ID {camera_id} atualizada com sucesso")
            return True
        finally:
            # Fechar sessão se foi criada aqui
            if not session_provided:
                db.close()
    except Exception as e:
        logger.error(f"Erro ao atualizar câmera com ID {camera_id}: {str(e)}")
        return False

def delete_camera(camera_id: int, owner: Optional[str] = None, db: Session = None) -> bool:
    """
    Remove uma câmera do banco de dados.
    
    Args:
        camera_id: ID da câmera a ser removida
        owner: Identificação do proprietário (para verificação)
        db: Sessão de banco de dados (opcional)
        
    Returns:
        bool: True se a remoção foi bem-sucedida
    """
    try:
        # Verificar se uma sessão foi fornecida
        session_provided = db is not None
        if not session_provided:
            db = next(get_db())
        
        try:
            # Buscar a câmera existente
            query = db.query(Camera).filter(Camera.id == camera_id)
            if owner:
                query = query.filter(Camera.owner == owner)
                
            camera = query.first()
            
            if not camera:
                logger.warning(f"Câmera com ID {camera_id} não encontrada para remoção")
                return False
            
            # Remover câmera
            db.delete(camera)
            db.commit()
            
            logger.info(f"Câmera com ID {camera_id} removida com sucesso")
            return True
        finally:
            # Fechar sessão se foi criada aqui
            if not session_provided:
                db.close()
    except Exception as e:
        logger.error(f"Erro ao remover câmera com ID {camera_id}: {str(e)}")
        return False

# Criar funções auxiliares para compatibilidade com chamadas assíncronas
async def async_add_camera(camera_data: Dict[str, Any], owner: str) -> Optional[Camera]:
    return add_camera(camera_data, owner)

async def async_get_cameras_by_user(owner: str) -> List[Camera]:
    return get_cameras_by_user(owner)

async def async_get_camera_by_id(camera_id: int, owner: Optional[str] = None) -> Optional[Camera]:
    return get_camera_by_id(camera_id, owner)

async def async_update_camera(camera_id: int, camera_data: Dict[str, Any], owner: Optional[str] = None) -> bool:
    return update_camera(camera_id, camera_data, owner)

async def async_delete_camera(camera_id: int, owner: Optional[str] = None) -> bool:
    return delete_camera(camera_id, owner)

# Adicionar apelidos para compatibilidade com o código existente
add_camera = async_add_camera
get_cameras_by_user = async_get_cameras_by_user
get_camera_by_id = async_get_camera_by_id
update_camera = async_update_camera
delete_camera = async_delete_camera 