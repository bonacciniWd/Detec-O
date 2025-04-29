"""
Inicialização do pacote de banco de dados.

Este módulo expõe a conexão com o banco de dados e funções úteis.
"""

# Importar principais funções e classes do módulo de banco de dados
from .database import (
    get_db,
    get_db_session,
    save_detection_event,
    get_detection_events,
    save_person_record,
    get_person_records
)

# Garantir que cameras_crud esteja disponível para importação
from . import cameras_crud

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
    'get_db',
    'get_db_session',
    'save_detection_event',
    'get_detection_events',
    'save_person_record',
    'get_person_records',
    'add_camera',
    'get_cameras_by_user',
    'get_camera_by_id',
    'update_camera',
    'delete_camera'
] 