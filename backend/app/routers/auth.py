from fastapi import APIRouter, Depends, HTTPException, status, Form, Body
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from typing import Dict, Any

from app.models.user import UserCreate, UserResponse, TokenResponse
from ..services.auth import (
    create_user, authenticate_user, create_access_token, 
    create_refresh_token, get_current_user, SECRET_KEY, ALGORITHM
)
from jose import JWTError, jwt

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={401: {"description": "Unauthorized"}},
)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    Registra um novo usuário.
    
    - Retorna dados do usuário criado (sem a senha)
    - Gera um erro 400 se o email já estiver em uso
    """
    # Criar usuário com o serviço de autenticação
    user = create_user(
        email=user_data.email,
        password=user_data.password,
        name=user_data.name
    )
    
    # Retornar resposta formatada (sem a senha)
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "is_active": user["is_active"],
        "created_at": user["created_at"]
    }

@router.post("/token", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Endpoint de login OAuth2 para obter token JWT.
    
    - Aceita username e password (username deve ser um email)
    - Retorna access_token e refresh_token
    """
    # Autenticar usuário (username no OAuth2 é o email no nosso sistema)
    user = authenticate_user(form_data.username, form_data.password)
    
    # Verificar se a autenticação falhou
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Dados para o token (sub deve ser único, usamos o email)
    token_data = {"sub": user["email"]}
    
    # Criar tokens
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    # Retornar resposta
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 60 * 60 * 24,  # 24 horas em segundos
        "refresh_token": refresh_token
    }

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str = Body(..., embed=True)):
    """
    Atualiza um token JWT expirado usando um refresh token.
    
    - Aceita um refresh_token válido
    - Retorna um novo access_token e refresh_token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token de atualização inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decodificar o refresh token
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Extrair o email do payload
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        
    except JWTError:
        raise credentials_exception
    
    # Criar novos tokens
    token_data = {"sub": email}
    access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)
    
    # Retornar resposta
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 60 * 60 * 24,  # 24 horas em segundos
        "refresh_token": new_refresh_token
    }

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Retorna informações do usuário autenticado.
    """
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "name": current_user["name"],
        "is_active": current_user["is_active"],
        "created_at": current_user["created_at"]
    } 