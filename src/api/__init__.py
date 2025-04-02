"""
Módulo de API para o sistema de detecção de crimes.

Este módulo implementa os endpoints da API REST para consulta de eventos,
gerenciamento de câmeras e autenticação.
"""

# Módulo API para o sistema de detecção de crimes 
from .routes import router as api_router
from .auth import router as auth_router, get_current_user

__all__ = ['api_router', 'auth_router', 'get_current_user']