from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, users, cameras, events, detection_settings, advanced_detection
from .db.database import startup_db_client, shutdown_db_client
import os

# Criação da aplicação FastAPI
app = FastAPI(
    title="Detec-o API",
    description="API para sistema de detecção por câmera",
    version="1.0.0"
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Eventos de inicialização e encerramento
app.add_event_handler("startup", startup_db_client)
app.add_event_handler("shutdown", shutdown_db_client)

# Inclusão dos routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(cameras.router)
app.include_router(events.router)
app.include_router(detection_settings.router)
app.include_router(advanced_detection.router)

@app.get("/", tags=["Root"])
async def root():
    """Endpoint raiz para verificar se a API está online."""
    return {
        "status": "online",
        "message": "Detec-o API está funcionando!",
        "documentation": "/docs"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Endpoint para verificar a saúde da aplicação."""
    return {
        "status": "healthy",
        "version": app.version
    } 