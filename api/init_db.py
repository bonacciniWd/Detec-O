"""
Script para inicializar o banco de dados
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text

# Adicionar diretório pai ao sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar após adicionar ao sys.path
from api.db import engine, Base, SessionLocal
from api.models import User, Camera, DetectionEvent

def init_db():
    """
    Inicializa o banco de dados criando todas as tabelas
    """
    try:
        print("Verificando tabelas existentes...")
        
        # Apagar tabelas existentes se for necessário
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS detection_events CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS cameras CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
            conn.commit()
        
        print("Criando tabelas no banco de dados...")
        # Criar todas as tabelas definidas nos modelos
        Base.metadata.create_all(bind=engine)
        print("Tabelas criadas com sucesso!")
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Carregar variáveis de ambiente
    load_dotenv()
    
    print("Inicializando banco de dados...")
    init_db()
    print("Banco de dados inicializado com sucesso!")
    
    print("Você pode criar um usuário administrador executando:")
    print("python -m api.create_admin") 