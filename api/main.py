"""
Aplicação FastAPI para Detec-O
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from api.routes import api_router
from api.db import engine, Base

# Carregar variáveis de ambiente
load_dotenv()

# Criar as tabelas no banco de dados
Base.metadata.create_all(bind=engine)

# Criar aplicação FastAPI
app = FastAPI(
    title="Detec-O API",
    description="API para o sistema de detecção de ameaças Detec-O",
    version="1.0.0"
)

# Configuração de CORS
origins = [
    "http://localhost:5173",  # Frontend Vite
    "http://localhost:3000",  # Frontend React alternativo
    "http://localhost:5000",  # Frontend de produção
    "https://detec-o.com.br",    # Domínio de produção
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir router principal da API
app.include_router(api_router)

# Rota raiz
@app.get("/")
async def root():
    """
    Endpoint raiz para verificar status da API
    """
    return {
        "app": "Detec-O API",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Verificação de saúde
@app.get("/health")
async def health_check():
    """
    Endpoint para verificar saúde da API
    """
    return {"status": "healthy"} 