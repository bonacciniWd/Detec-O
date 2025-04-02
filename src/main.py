"""
Módulo principal do Sistema de Detecção de Crimes.

Este módulo inicializa a aplicação FastAPI e gerencia os eventos de inicialização
e encerramento do sistema.
"""

import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .api.routes import router as api_router
from .api.auth import router as auth_router

def create_app():
    app = FastAPI(
        title="Sistema de Detecção de Crimes", 
        description="API para sistema de vigilância e detecção de atividades suspeitas",
        version="1.0.0"
    )

    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        # Permitir a origem do frontend Vite e a origem antiga (se necessário)
        allow_origins=["http://localhost:5173", "http://localhost:5000"],
        allow_credentials=True,
        allow_methods=["*"], # Permitir todos os métodos
        allow_headers=["*"], # Permitir todos os cabeçalhos
    )

    # Incluir rotas da API
    app.include_router(api_router)
    app.include_router(auth_router)

    @app.get("/")
    async def root():
        """Endpoint raiz para verificar status da API"""
        return {
            "status": "online", 
            "message": "Sistema de Detecção de Crimes em execução",
            "docs_url": "/docs",
            "version": "1.0.0"
        }

    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 