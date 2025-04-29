"""
Script para criar usuário administrador
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Adicionar diretório pai ao sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar após adicionar ao sys.path
from api.db import SessionLocal
from api.models import User
from api.security import get_password_hash

def create_admin_user():
    """
    Cria um usuário administrador se não existir
    """
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Obter credenciais do arquivo .env
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_email = os.getenv("ADMIN_EMAIL", "admin@detec-o.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    
    # Criar sessão
    db = SessionLocal()
    
    try:
        # Verificar se o usuário admin já existe
        admin = db.query(User).filter(
            (User.username == admin_username) | (User.email == admin_email)
        ).first()
        
        if admin:
            print(f"Usuário administrador já existe: {admin.username} ({admin.email})")
            print(f"Senha configurada: {admin_password}")
            # Atualizar senha do admin para ter certeza
            admin.hashed_password = get_password_hash(admin_password)
            db.commit()
            print("Senha atualizada com sucesso!")
            return
        
        # Criar usuário admin
        print(f"Criando usuário administrador: {admin_username} ({admin_email})")
        
        # Hash da senha
        hashed_password = get_password_hash(admin_password)
        
        # Criar usuário
        admin = User(
            username=admin_username,
            email=admin_email,
            hashed_password=hashed_password,
            full_name="Administrador",
            is_active=True,
            is_admin=True
        )
        
        # Salvar no banco de dados
        db.add(admin)
        db.commit()
        
        print("Usuário administrador criado com sucesso!")
        print(f"Username: {admin_username}")
        print(f"Email: {admin_email}")
        print(f"Senha: {admin_password}")
    
    except Exception as e:
        db.rollback()
        print(f"Erro ao criar usuário administrador: {e}")
    
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user() 