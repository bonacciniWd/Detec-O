"""
Rotas para autenticação
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body, Form, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Any, Dict, Optional

from api import models, schemas, security
from api.db import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login-debug", response_model=schemas.Token)
async def login_debug(db: Session = Depends(get_db)) -> Any:
    """
    Endpoint de debug para login - sempre usa o usuário admin
    """
    # Autenticar usuário admin usando a senha correta
    user = security.authenticate_user(db, "admin", "AdminPassword123!")
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário admin não encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Criar token de acesso
    access_token = security.create_access_token(
        data={"sub": user.username}
    )
    
    # Retornar token
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": security.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Converter para segundos
    }

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    request: Request,
    form_data: Optional[OAuth2PasswordRequestForm] = Depends(None),
    db: Session = Depends(get_db)
) -> Any:
    """
    Endpoint para obter token de acesso
    Aceita tanto form-data quanto JSON
    """
    # Verificar tipo de conteúdo
    content_type = request.headers.get("Content-Type", "")
    
    username = None
    password = None
    
    # Se for JSON
    if "application/json" in content_type:
        try:
            body = await request.json()
            username = body.get("username") or body.get("email")
            password = body.get("password")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Erro ao processar JSON: {str(e)}"
            )
    # Se for form-data
    elif form_data:
        username = form_data.username
        password = form_data.password
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato inválido. Use JSON ou form-data"
        )
    
    # Autenticar usuário
    user = security.authenticate_user(db, username, password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nome de usuário/email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Criar token de acesso
    access_token = security.create_access_token(
        data={"sub": user.username}
    )
    
    # Retornar token
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": security.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Converter para segundos
    }

@router.post("/login", response_model=schemas.Token)
async def login(
    login_data: schemas.UserLogin,
    db: Session = Depends(get_db)
) -> Any:
    """
    Endpoint alternativo para login via JSON

    - **username**: Nome de usuário ou email
    - **password**: Senha
    """
    # Autenticar usuário
    user = security.authenticate_user(db, login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nome de usuário/email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Criar token de acesso
    access_token = security.create_access_token(
        data={"sub": user.username}
    )
    
    # Retornar token
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": security.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Converter para segundos
    }

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """
    Registrar um novo usuário

    - **username**: Nome de usuário único
    - **email**: Email único
    - **password**: Senha (mínimo 6 caracteres)
    - **full_name**: Nome completo (opcional)
    """
    # Verificar se o username já existe
    if db.query(models.User).filter(models.User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome de usuário já existe"
        )
    
    # Verificar se o email já existe
    if db.query(models.User).filter(models.User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já está em uso"
        )
    
    # Criar usuário
    hashed_password = security.get_password_hash(user_data.password)
    
    db_user = models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name
    )
    
    # Salvar usuário no banco de dados
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.get("/me", response_model=schemas.UserResponse)
async def read_users_me(
    current_user: models.User = Depends(security.get_current_active_user)
):
    """
    Obter informações do usuário autenticado.
    Retorna um dicionário em vez do objeto SQLAlchemy diretamente para evitar problemas de serialização.
    """
    # WORKAROUND: Conversão Manual para Dict
    # Mesmo com `from_attributes = True` no schema UserResponse, algumas versões/
    # combinações de FastAPI/Pydantic/SQLAlchemy podem falhar ao serializar 
    # o objeto SQLAlchemy diretamente, especialmente em respostas de lista ou 
    # com relacionamentos complexos. Retornar um dict explicitamente resolve isso.
    user_dict = {
        field: getattr(current_user, field) 
        for field in schemas.UserResponse.__fields__ 
        if hasattr(current_user, field)
    }
    # return current_user # << Linha original comentada
    return user_dict 
    # WORKAROUND: Conversão Manual para Dict
    # Mesmo com `from_attributes = True` no schema UserResponse, algumas versões/
    # combinações de FastAPI/Pydantic/SQLAlchemy podem falhar ao serializar 
    # o objeto SQLAlchemy diretamente, especialmente em respostas de lista ou 
    # com relacionamentos complexos. Retornar um dict explicitamente resolve isso.
    user_dict = {
        field: getattr(current_user, field) 
        for field in schemas.UserResponse.__fields__ 
        if hasattr(current_user, field)
    }
    # return current_user # << Linha original comentada
    return user_dict 