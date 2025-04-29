"""
Módulo para conexão com o banco de dados PostgreSQL
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de conexão com o PostgreSQL
POSTGRES_USER = os.getenv("POSTGRES_USER", "denisbonaccini")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "7ce3284bA")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "deteco")

# Montar URL de conexão
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Criar engine do SQLAlchemy
engine = create_engine(DATABASE_URL)

# Criar sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos declarativos
Base = declarative_base()

# Função para obter uma sessão do banco de dados
def get_db():
    """
    Dependency para obter uma sessão do banco de dados
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 