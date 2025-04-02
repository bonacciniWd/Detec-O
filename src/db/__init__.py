"""
Módulo de acesso a banco de dados.

Este módulo gerencia a conexão e operações com o banco de dados MongoDB.
"""

# Módulo de acesso ao banco de dados
from .database import (
    init_db, 
    save_detection_event, 
    get_detection_events, 
    get_person_records,
    save_person_record,
    close_db
)

__all__ = [
    'init_db', 
    'save_detection_event', 
    'get_detection_events', 
    'get_person_records',
    'save_person_record',
    'close_db'
] 