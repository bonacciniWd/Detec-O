# create_user.py
import sys
import os
from getpass import getpass # Para esconder a senha digitada
from sqlalchemy.orm import Session

# Adiciona o diretório raiz ao path para encontrar os módulos da API
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Importa as dependências necessárias da sua aplicação
    from api.db import SessionLocal
    from api.models import User
    from api.security import get_password_hash, pwd_context
except ImportError as e:
    print(f"Erro ao importar módulos. Certifique-se de que o script está na raiz do projeto 'Detec-O'.")
    print(f"Verifique se as pastas 'api', 'api/db', 'api/models', 'api/security' existem e contêm os arquivos necessários.")
    print(f"Detalhes do erro: {e}")
    sys.exit(1)

def create_new_user():
    """Função para criar um novo usuário interativamente."""
    print("--- Criar Novo Usuário Detec-O ---")

    db: Session = SessionLocal()
    try:
        # Obter dados do novo usuário
        while True:
            username = input("Nome de usuário desejado: ").strip()
            if not username:
                print("Nome de usuário não pode ser vazio.")
            else:
                # Verificar se o nome de usuário já existe
                existing = db.query(User).filter(User.username == username).first()
                if existing:
                    print(f"Erro: Nome de usuário '{username}' já está em uso. Tente outro.")
                else:
                    break # Nome de usuário válido e disponível

        while True:
            email = input("Endereço de email: ").strip()
            if not email or '@' not in email: # Verificação simples de email
                print("Por favor, insira um email válido.")
            else:
                 # Verificar se o email já existe
                existing = db.query(User).filter(User.email == email).first()
                if existing:
                    print(f"Erro: Email '{email}' já está em uso. Tente outro.")
                else:
                    break # Email válido e disponível

        # Obter e confirmar a senha
        while True:
            password = getpass("Senha: ")
            if not password:
                print("Senha não pode ser vazia.")
                continue
            password_confirm = getpass("Confirmar Senha: ")
            if password == password_confirm:
                break
            else:
                print("Erro: As senhas não coincidem. Tente novamente.")

        full_name = input("Nome Completo (opcional, pressione Enter para pular): ").strip() or None
        is_admin_input = input("Tornar este usuário um administrador? (s/N): ").strip().lower()
        is_admin = is_admin_input == 's'

        # Gerar o hash da senha usando bcrypt (configurado no security.py)
        hashed_password = get_password_hash(password)
        print(f"Senha hasheada com sucesso usando {pwd_context.default_scheme()}.")

        # Criar a instância do novo usuário
        new_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_active=True,  # Ativar o usuário por padrão
            is_admin=is_admin
        )

        # Adicionar ao banco de dados
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        print("\n-----------------------------------------")
        print(f"Usuário '{new_user.username}' criado com sucesso!")
        print(f"ID: {new_user.id}")
        print(f"Email: {new_user.email}")
        print(f"Administrador: {'Sim' if new_user.is_admin else 'Não'}")
        print("-----------------------------------------")

    except Exception as e:
        db.rollback() # Desfaz alterações em caso de erro
        print(f"\nErro ao criar usuário: {e}")
        print("Verifique a conexão com o banco de dados e as permissões.")
    finally:
        db.close() # Sempre fechar a sessão

if __name__ == "__main__":
    print("Iniciando script para criação de usuário...")
    create_new_user()
    print("Script finalizado.")
