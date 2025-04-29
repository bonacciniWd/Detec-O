"""
Funções de segurança e autenticação
"""
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from .db import get_db
from .models import User

# Carregar variáveis de ambiente
load_dotenv()

# Chave secreta para tokens JWT
SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
# Algoritmo para assinatura do token
ALGORITHM = "HS256"
# Tempo de expiração do token (minutos)
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 horas por padrão

# Context para hash de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuração do OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se a senha em texto plano corresponde ao hash armazenado
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Gera um hash seguro para a senha
    """
    return pwd_context.hash(password)

def get_user(db: Session, username: str) -> Optional[User]:
    """
    Busca um usuário pelo username no banco de dados
    """
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Busca um usuário pelo email no banco de dados
    """
    return db.query(User).filter(User.email == email).first()

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Autentica um usuário com username e senha
    """
    user = None
    
    # Tentar autenticar por email (se parecer um email)
    if '@' in username:
        user = get_user_by_email(db, username)
    
    # Se não encontrou por email, tentar pelo username
    if not user:
        user = get_user(db, username)
    
    # Se não encontrou o usuário ou a senha está incorreta
    if not user or not verify_password(password, user.hashed_password):
        return None
    
    # Atualizar último login
    user.last_login = datetime.utcnow()
    db.commit()
    
    return user

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um token JWT de acesso
    """
    to_encode = data.copy()
    
    # Definir tempo de expiração
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Adicionar expiração ao payload
    to_encode.update({"exp": expire})
    
    # Criar token JWT
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Valida o token JWT e retorna o usuário atual
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decodificar o token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Extrair username do token
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Buscar usuário no banco de dados
    user = get_user(db, username)
    if user is None:
        raise credentials_exception
    
    # Verificar se o usuário está ativo
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo"
        )
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Verifica se o usuário está ativo
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo"
        )
    return current_user 