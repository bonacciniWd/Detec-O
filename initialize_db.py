"""
Script para inicializar o banco de dados PostgreSQL com as estruturas necessárias
"""
import os
import sys
import json
import datetime
import asyncio
import traceback
from sqlalchemy import create_engine, text, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from dotenv import load_dotenv

# Adicionar diretório parent ao path para importar módulos do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar modelos e base após adicionar o path
from app.database import Base
from app.models.camera import Camera
from app.models.models import AIModel, User

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do banco de dados
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/deteco")

# Teste da conexão com o PostgreSQL (síncrono)
def test_db_connection():
    print(f"Testando conexão com o banco de dados: {DATABASE_URL.split('@')[1].split('?')[0]}")
    try:
        # Tentar uma conexão síncrona primeiro
        engine = create_engine(DATABASE_URL)
        connection = engine.connect()
        result = connection.execute(text("SELECT 1")).fetchone()
        connection.close()
        engine.dispose()
        
        print("✅ Conexão síncrona com PostgreSQL bem-sucedida!")
        return True
    except Exception as e:
        print(f"❌ Erro ao conectar (síncrono): {str(e)}")
        print("\nStacktrace:")
        traceback.print_exc()
        return False

async def initialize_database():
    """Inicializa o banco de dados com as tabelas e dados iniciais"""
    try:
        # Testar conexão primeiro
        if not test_db_connection():
            print("Erro na conexão síncrona. Verificando se o serviço PostgreSQL está rodando...")
            return
            
        # Criar engine assíncrona
        if DATABASE_URL.startswith('postgresql://'):
            async_url = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')
        else:
            async_url = DATABASE_URL
            
        print(f"Usando URL assíncrona: {async_url.split('@')[1].split('?')[0]}")
            
        engine = create_async_engine(async_url)
        
        # Criar sessão assíncrona
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        print(f"Conectado ao banco de dados PostgreSQL: {DATABASE_URL.split('@')[1].split('?')[0]}")
        
        # Criar todas as tabelas definidas nas classes Base
        print("Criando tabelas...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("Tabelas criadas com sucesso")
        
        # Verificar e inserir dados iniciais
        await _insert_initial_data(async_session)
        
        # Fechar conexões
        await engine.dispose()
        
        print("Inicialização do banco de dados concluída com sucesso!")
        
    except Exception as e:
        print(f"Erro ao inicializar o banco de dados: {str(e)}")
        print("\nStacktrace:")
        traceback.print_exc()
        sys.exit(1)

async def _insert_initial_data(async_session):
    """Insere dados iniciais no banco de dados, se necessário"""
    async with async_session() as session:
        # Verificar se existem modelos de IA
        result = await session.execute(select(func.count()).select_from(AIModel))
        ai_models_count = result.scalar()
        
        if not ai_models_count:
            # Inserir modelo YOLOv8n padrão
            print("Adicionando modelo YOLOv8n padrão...")
            default_model = AIModel(
                name="YOLOv8n",
                description="Modelo padrão YOLOv8 nano para detecção de objetos",
                file_path="models/yolov8n.pt",
                classes=["person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat"],
                size_mb=6.2,
                speed_rating="fast"
            )
            session.add(default_model)
            
        # Verificar se existe um usuário administrador
        result = await session.execute(select(User).where(User.is_admin == True).limit(1))
        admin_user = result.scalars().first()
        
        if not admin_user:
            # Criar usuário admin
            print("Criando usuário administrador padrão...")
            # Obter parâmetros do ambiente ou usar valores padrão
            admin_email = os.getenv("ADMIN_EMAIL", "admin@detec-o.com")
            admin_username = os.getenv("ADMIN_USERNAME", "admin")
            # Nunca usar senhas codificadas em produção! Senhas devem vir de variáveis de ambiente ou ser definidas no primeiro uso
            # Este é apenas um exemplo para desenvolvimento
            from app.utils.security import get_password_hash
            admin_password = get_password_hash(os.getenv("ADMIN_PASSWORD", "AdminPassword123!"))
            
            admin = User(
                email=admin_email,
                username=admin_username,
                hashed_password=admin_password,
                is_active=True,
                is_admin=True
            )
            session.add(admin)
        
        # Commit das alterações
        await session.commit()
        print("Dados iniciais inseridos com sucesso")

if __name__ == "__main__":
    # Executar a função assíncrona de inicialização
    asyncio.run(initialize_database()) 