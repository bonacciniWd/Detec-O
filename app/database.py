from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os
from contextlib import contextmanager

# Obter a URL do banco de dados da variável de ambiente ou usar PostgreSQL como padrão
# Formato PostgreSQL: postgresql://username:password@localhost:5432/deteco
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:7ce3284bA@localhost:5432/deteco")

# Criar engine com pool de conexões
engine = create_engine(
    DATABASE_URL, 
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,  # Reciclar conexões após 30 minutos
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

# Criar sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos ORM
Base = declarative_base()

# Função para obter uma sessão de banco de dados
@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Função para inicializar o banco de dados
def init_db():
    from app.models.models import Base
    Base.metadata.create_all(bind=engine) 