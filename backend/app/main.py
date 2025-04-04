from fastapi import FastAPI, Depends, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import logging
from pathlib import Path
import os
import asyncio
import traceback

from .database import init_db, create_default_admin, engine, Base, get_db
from .auth.dependencies import get_current_user
from .services.detection_service import detection_service
from .routers import auth, cameras, events, detection_settings, users, devices, ai_models, persons
from . import __version__
from .services.discover import discover_devices

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Criar diretório de arquivos estáticos para testes
static_dir = Path(__file__).parent / "static"
camera_preview_dir = static_dir / "camera_previews"
os.makedirs(camera_preview_dir, exist_ok=True)

# Criar a aplicação FastAPI
app = FastAPI(
    title="Detec-o API",
    description="API para sistema de detecção de ameaças em tempo real",
    version=__version__,
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos os domínios em desenvolvimento
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Eventos de inicialização e encerramento
@app.on_event("startup")
async def startup_event():
    """Executado na inicialização da aplicação."""
    # Inicializar o banco de dados
    await init_db()
    
    # Criar usuário admin default se não existir
    await create_default_admin()
    
    # Inicializar o serviço de detecção
    await detection_service.initialize()
    
    logger.info("Aplicação inicializada com sucesso!")

@app.on_event("shutdown")
async def shutdown_event():
    """Executado no encerramento da aplicação."""
    logger.info("Aplicação finalizada com sucesso!")

# Montar pasta estática
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Tratamento de exceções
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"},
    )

# Incluir routers
app.include_router(auth.router)
app.include_router(cameras.router)
app.include_router(events.router)
app.include_router(detection_settings.router)
app.include_router(users.router)
app.include_router(devices.router)
app.include_router(ai_models.router)
app.include_router(persons.router)

# Endpoint raiz
@app.get("/", tags=["Root"])
async def root():
    return {"message": "Bem-vindo à API Detec-o!", "version": __version__}

# Endpoint de saúde
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}

# Rota para descoberta de dispositivos
@app.get("/api/v1/discover", tags=["discover"])
async def discover_all_devices(
    current_user: dict = Depends(get_current_user),
    ip_range: str = Query(None, description="Faixa de IPs a serem verificados, no formato 192.168.1.0/24")
):
    """
    Descobre dispositivos compatíveis na rede.
    """
    try:
        from .services.discovery import discover_devices
        
        # Descobrir dispositivos
        devices = await discover_devices(ip_range)
        return {"devices": devices, "count": len(devices)}
    
    except Exception as e:
        logger.error(f"Erro ao descobrir dispositivos: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro ao descobrir dispositivos: {str(e)}")

def main():
    """Função principal para executar a aplicação"""
    import uvicorn
    
    # Obter porta do ambiente ou usar padrão
    port = int(os.environ.get("PORT", 8000))
    
    # Executar servidor
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True  # Em produção, definir como False
    )

if __name__ == "__main__":
    main() 