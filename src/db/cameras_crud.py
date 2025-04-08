import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from sqlalchemy import update, delete

# Importar os modelos SQLAlchemy
from app.models.camera import Camera
from .database import get_db_session, logger

# Função para criar câmera
async def add_camera(camera_data: Dict[str, Any], owner: str) -> Optional[Camera]:
    """
    Adiciona uma nova câmera ao banco de dados.
    
    Args:
        camera_data: Dados da câmera
        owner: Identificação do proprietário
        
    Returns:
        Camera: Objeto câmera criado ou None em caso de falha
    """
    try:
        async with get_db_session() as db:
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
    except Exception as e:
        logger.error(f"Erro ao adicionar câmera: {str(e)}")
        return None

async def get_cameras_by_user(owner: str) -> List[Camera]:
    """
    Busca todas as câmeras pertencentes a um usuário.
    
    Args:
        owner: Identificação do proprietário
        
    Returns:
        List[Camera]: Lista de câmeras do usuário
    """
    try:
        async with get_db_session() as db:
            # Executar consulta
            stmt = select(Camera).where(Camera.owner == owner)
            result = await db.execute(stmt)
            cameras = result.scalars().all()
            
            return list(cameras)
    except Exception as e:
        logger.error(f"Erro ao buscar câmeras do usuário {owner}: {str(e)}")
        return []

async def get_camera_by_id(camera_id: int, owner: Optional[str] = None) -> Optional[Camera]:
    """
    Busca uma câmera específica pelo seu ID, opcionalmente verificando o proprietário.
    
    Args:
        camera_id: ID da câmera
        owner: Identificação do proprietário (opcional)
        
    Returns:
        Camera: Objeto câmera encontrado ou None
    """
    try:
        async with get_db_session() as db:
            # Construir consulta base
            stmt = select(Camera).where(Camera.id == camera_id)
            
            # Adicionar filtro de proprietário se fornecido
            if owner:
                stmt = stmt.where(Camera.owner == owner)
                
            # Executar consulta
            result = await db.execute(stmt)
            camera = result.scalars().first()
            
            return camera
    except Exception as e:
        logger.error(f"Erro ao buscar câmera com ID {camera_id}: {str(e)}")
        return None

async def update_camera(camera_id: int, camera_data: Dict[str, Any], owner: Optional[str] = None) -> bool:
    """
    Atualiza os dados de uma câmera existente.
    
    Args:
        camera_id: ID da câmera a ser atualizada
        camera_data: Novos dados da câmera
        owner: Identificação do proprietário (para verificação)
        
    Returns:
        bool: True se a atualização foi bem-sucedida
    """
    try:
        async with get_db_session() as db:
            # Buscar a câmera existente
            stmt = select(Camera).where(Camera.id == camera_id)
            if owner:
                stmt = stmt.where(Camera.owner == owner)
                
            result = await db.execute(stmt)
            camera = result.scalars().first()
            
            if not camera:
                logger.warning(f"Câmera com ID {camera_id} não encontrada para atualização")
                return False
            
            # Atualizar campos
            for key, value in camera_data.items():
                if hasattr(camera, key):
                    setattr(camera, key, value)
                    
            # Salvar alterações
            db.commit()
            db.refresh(camera)
            
            logger.info(f"Câmera com ID {camera_id} atualizada com sucesso")
            return True
    except Exception as e:
        logger.error(f"Erro ao atualizar câmera com ID {camera_id}: {str(e)}")
        return False

async def delete_camera(camera_id: int, owner: Optional[str] = None) -> bool:
    """
    Remove uma câmera do banco de dados.
    
    Args:
        camera_id: ID da câmera a ser removida
        owner: Identificação do proprietário (para verificação)
        
    Returns:
        bool: True se a remoção foi bem-sucedida
    """
    try:
        async with get_db_session() as db:
            # Buscar a câmera existente
            stmt = select(Camera).where(Camera.id == camera_id)
            if owner:
                stmt = stmt.where(Camera.owner == owner)
                
            result = await db.execute(stmt)
            camera = result.scalars().first()
            
            if not camera:
                logger.warning(f"Câmera com ID {camera_id} não encontrada para remoção")
                return False
            
            # Remover câmera
            db.delete(camera)
            db.commit()
            
            logger.info(f"Câmera com ID {camera_id} removida com sucesso")
            return True
    except Exception as e:
        logger.error(f"Erro ao remover câmera com ID {camera_id}: {str(e)}")
        return False 