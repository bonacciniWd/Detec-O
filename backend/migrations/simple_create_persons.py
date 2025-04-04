import os
import sys
import logging
import sqlite3
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def create_persons_table():
    """Cria a tabela de pessoas diretamente usando SQLite."""
    try:
        # Obter o caminho do banco de dados
        db_path = Path(__file__).parent.parent / "app.db"
        logger.info(f"Usando banco de dados: {db_path}")
        
        # Conectar ao banco de dados
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Verificar se a tabela já existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='persons'")
        if cursor.fetchone():
            logger.info("Tabela 'persons' já existe.")
            return
        
        # Criar a tabela persons
        logger.info("Criando tabela 'persons'...")
        cursor.execute("""
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
        
        # Confirmar alterações
        conn.commit()
        logger.info("Tabela 'persons' criada com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro ao criar tabela: {str(e)}")
    finally:
        # Fechar conexão
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    create_persons_table() 