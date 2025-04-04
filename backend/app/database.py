from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os
from contextlib import contextmanager

# Obter a URL do banco de dados da variável de ambiente ou usar SQLite como padrão
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./deteco.db")

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

# Função para criar usuário admin padrão se não existir
def create_default_admin():
    from app.models.models import User
    from sqlalchemy.orm import Session
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    with get_db() as db:
        # Verificar se já existe algum usuário admin
        admin_user = db.query(User).filter(User.email == "admin@exemplo.com").first()
        
        if not admin_user:
            # Criar usuário admin padrão
            hashed_password = pwd_context.hash("senha123")
            admin = User(
                email="admin@exemplo.com",
                name="Admin",
                hashed_password=hashed_password,
                is_active=True
            )
            db.add(admin)
            db.commit()
            print("Usuário admin padrão criado com sucesso.")
        else:
            print("Usuário admin já existe.") 