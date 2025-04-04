import os
import sys
import logging
from pathlib import Path

# Adicionar diretório pai ao path
current_path = Path(__file__).parent.absolute()
sys.path.append(str(current_path.parent))

# Importar os módulos necessários
from app.database import Base, engine
from app.models.user import User
from app.models.camera import Camera, AIModel
from app.models.event import Event
from app.models.person import Person, FaceEncoding  # Importar modelos de pessoa

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def create_tables():
    """Cria todas as tabelas definidas nos modelos SQLAlchemy."""
    logger.info("Iniciando criação de tabelas...")
    
    # Criar tabelas
    Base.metadata.create_all(bind=engine)
    
    # Listar tabelas criadas
    tables = Base.metadata.tables.keys()
    logger.info(f"Tabelas criadas: {', '.join(tables)}")
    
    # Criar tabelas SQL diretamente se necessário
    with engine.connect() as conn:
        # Verificar se a tabela de pessoas existe
        result = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='persons'")
        if not result.fetchone():
            logger.info("Criando tabela 'persons'...")
            conn.execute("""
            CREATE TABLE IF NOT EXISTS persons (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT DEFAULT 'default',
                user_id TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                face_count INTEGER DEFAULT 0,
                face_encodings TEXT DEFAULT '[]'
            )
            """)
    
    logger.info("Criação de tabelas concluída com sucesso!")

if __name__ == "__main__":
    create_tables() 