"""
Utilidades e ferramentas para o sistema de detecção de crimes.

Este módulo contém funções auxiliares e utilitárias usadas ao longo do sistema.
"""

# Módulo de utilidades e configurações
from .config import (
    load_config, 
    get_cameras
)

__all__ = [
    'load_config', 
    'get_cameras'
] 