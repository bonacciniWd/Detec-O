from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """Modelo base para usuários."""
    email: EmailStr = Field(..., description="Email do usuário")
    name: str = Field(..., description="Nome completo do usuário")

class UserCreate(UserBase):
    """Modelo para criação de usuários."""
    password: str = Field(..., min_length=6, description="Senha do usuário (mínimo 6 caracteres)")

class UserLogin(BaseModel):
    """Modelo para login de usuários."""
    email: EmailStr
    password: str

class UserInDB(UserBase):
    """Modelo para usuários armazenados no banco."""
    id: str
    hashed_password: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

class UserResponse(UserBase):
    """Modelo de resposta para usuários."""
    id: str
    is_active: bool
    created_at: datetime

class UserUpdate(BaseModel):
    """Modelo para atualização de usuários."""
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    password: Optional[str] = None

class TokenResponse(BaseModel):
    """Modelo para resposta de token."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Tempo de expiração em segundos")
    refresh_token: Optional[str] = None 