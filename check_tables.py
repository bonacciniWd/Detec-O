"""
Script para verificar as tabelas no PostgreSQL
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

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

def check_tables():
    """
    Verifica as tabelas no PostgreSQL
    """
    try:
        # Criar engine
        engine = create_engine(DATABASE_URL)
        
        # Conectar ao banco de dados
        with engine.connect() as conn:
            # Listar todas as tabelas
            result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = result.fetchall()
            
            print("=== Tabelas no banco de dados ===")
            for table in tables:
                print(f"- {table[0]}")
            
            # Verificar estrutura da tabela users
            if ('users',) in tables:
                print("\n=== Estrutura da tabela users ===")
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' AND table_name = 'users'
                """))
                columns = result.fetchall()
                for col in columns:
                    print(f"{col[0]}: {col[1]} (Nullable: {col[2]})")
                
                # Tentar recuperar usuários de forma diferente
                try:
                    print("\n=== Usuários ===")
                    result = conn.execute(text("SELECT * FROM users"))
                    users = result.fetchall()
                    
                    if users:
                        # Imprimir nome das colunas
                        column_names = result.keys()
                        print(f"Colunas: {', '.join(column_names)}")
                        
                        for user in users:
                            print("-" * 30)
                            for i, value in enumerate(user):
                                if i < len(column_names):
                                    print(f"{column_names[i]}: {value}")
                    else:
                        print("Nenhum usuário encontrado")
                except Exception as user_err:
                    print(f"Erro ao buscar usuários: {user_err}")
            
            # Verificar número de registros em cada tabela
            print("\n=== Contagem de registros ===")
            for table in tables:
                try:
                    count = conn.execute(text(f"SELECT COUNT(*) FROM {table[0]}"))
                    count_value = count.scalar()
                    print(f"{table[0]}: {count_value} registros")
                except Exception as count_err:
                    print(f"Erro ao contar registros em {table[0]}: {count_err}")
    
    except Exception as e:
        print(f"Erro ao verificar tabelas: {e}")

if __name__ == "__main__":
    check_tables() 