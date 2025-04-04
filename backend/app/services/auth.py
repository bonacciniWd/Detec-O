from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import uuid

# Configurações de segurança
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"  # Chave secreta para produção deve ser mantida em variáveis de ambiente
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 dias

# Configuração do contexto de senha para hash e verificação
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuração do OAuth2 com Bearer Token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Função para gerar hash de senha
def get_password_hash(password: str) -> str:
    """
    Gera um hash seguro para a senha.
    """
    return pwd_context.hash(password)

# Banco de dados simulado para usuários
# Em uma aplicação real, isso seria um banco de dados como MongoDB, PostgreSQL, etc.
USER_DB = [
    {
        "id": str(uuid.uuid4()),
        "email": "admin@exemplo.com",
        "name": "Admin",
        "hashed_password": get_password_hash("senha123"),
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
]

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se a senha em texto plano corresponde ao hash armazenado.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_user(email: str) -> Optional[Dict[str, Any]]:
    """
    Busca um usuário pelo email.
    """
    for user in USER_DB:
        if user["email"] == email:
            return user
    return None

def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Autentica um usuário com email e senha.
    """
    user = get_user(email)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    if not user["is_active"]:
        return None
    return user

def create_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um token JWT com os dados fornecidos e tempo de expiração.
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_access_token(data: Dict[str, Any]) -> str:
    """
    Cria um token de acesso JWT.
    """
    return create_token(
        data,
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Cria um token de atualização JWT.
    """
    return create_token(
        data,
        timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    )

def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Obtém e valida o usuário atual a partir do token JWT.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decodificar o token JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Extrair o email do payload
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        
    except JWTError:
        raise credentials_exception
    
    # Buscar o usuário no banco
    user = get_user(email)
    if user is None:
        raise credentials_exception
    
    # Verificar se o usuário está ativo
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo"
        )
    
    return user

def create_user(email: str, password: str, name: str) -> Dict[str, Any]:
    """
    Cria um novo usuário.
    """
    # Verificar se o email já está em uso
    if get_user(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já registrado"
        )
    
    # Hash da senha
    hashed_password = get_password_hash(password)
    
    # Gerar ID único
    user_id = str(uuid.uuid4())
    
    # Criar usuário
    now = datetime.utcnow()
    new_user = {
        "id": user_id,
        "email": email,
        "name": name,
        "hashed_password": hashed_password,
        "is_active": True,
        "created_at": now,
        "updated_at": now
    }
    
    # Adicionar ao banco simulado
    USER_DB.append(new_user)
    
    return new_user 