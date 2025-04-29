"""
Pacote de rotas da API
"""
from fastapi import APIRouter

from api.routes import auth, cameras, events

# Criar router principal
api_router = APIRouter(prefix="/api")

# Incluir sub-routers
api_router.include_router(auth.router)
api_router.include_router(cameras.router)
api_router.include_router(events.router) 