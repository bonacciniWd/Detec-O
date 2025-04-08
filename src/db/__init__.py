"""
Módulo de acesso a banco de dados.

Este módulo gerencia a conexão e operações com o banco de dados PostgreSQL usando SQLAlchemy.
"""

# Módulo de acesso ao banco de dados
from .database import (
    init_db,
    close_db,
    get_db_session,
    save_detection_event,
    get_detection_events,
    save_person_record,
    get_person_records,
    Base
)

# Operações CRUD para câmeras
from .cameras_crud import (
    add_camera,
    get_cameras_by_user,
    get_camera_by_id,
    update_camera,
    delete_camera
)

# Lista de todas as funções exportadas pelo módulo
__all__ = [
    'init_db', 
    'close_db',
    'get_db_session',
    'save_detection_event',
    'get_detection_events',
    'save_person_record',
    'get_person_records',
    'add_camera',
    'get_cameras_by_user',
    'get_camera_by_id',
    'update_camera',
    'delete_camera',
    'Base'
] 