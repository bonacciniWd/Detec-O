"""
Sistema de Detecção de Crimes

Este módulo contém a implementação de um sistema de monitoramento e detecção
de atividades suspeitas através de câmeras. O sistema utiliza visão computacional
e aprendizado de máquina para identificar pessoas, objetos e comportamentos.

Principais componentes:
- Detecção de objetos e pessoas usando YOLO
- Análise de comportamento e movimento
- API para integração com sistemas de segurança
- Interface web para visualização e gerenciamento
"""

__version__ = "1.0.0"
__author__ = "Sistema de Detecção de Crimes"

import logging

# Configuração básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Inicializando logger para o pacote
logger = logging.getLogger(__name__)

# Sistema de Detecção de Crimes
from .api import api_router, auth_router
from .detection import analyze_hand_movements
from .db import init_db, save_detection_event, get_detection_events, close_db
from .utils import load_config, get_cameras

__all__ = [
    'api_router',
    'auth_router',
    'analyze_hand_movements',
    'init_db',
    'save_detection_event', 
    'get_detection_events',
    'close_db',
    'load_config',
    'get_cameras'
] 