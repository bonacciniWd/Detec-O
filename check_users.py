"""
Script para verificar os usuários no banco de dados
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text

# Adicionar diretório pai ao sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar após adicionar ao sys.path
from api.db import engine, Base, SessionLocal

def check_users():
    """
    Verifica os usuários no banco de dados
    """
    try:
        # Criar sessão
        session = SessionLocal()
        
        try:
            # Executar consulta direta
            result = session.execute(text("SELECT * FROM users"))
            users = result.fetchall()
            
            if users:
                column_names = result.keys()
                print("=== Usuários encontrados ===")
                print(f"Colunas: {', '.join(column_names)}")
                
                for user in users:
                    print("-" * 50)
                    # Converter para dicionário para melhor visualização
                    user_dict = {}
                    for i, col_name in enumerate(column_names):
                        user_dict[col_name] = user[i]
                    
                    for key, value in user_dict.items():
                        print(f"{key}: {value}")
                
                print("-" * 50)
                print(f"Total de usuários: {len(users)}")
            else:
                print("Nenhum usuário encontrado.")
        finally:
            session.close()
        
    except Exception as e:
        print(f"Erro ao verificar usuários: {e}")

if __name__ == "__main__":
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Verificar usuários
    check_users() 