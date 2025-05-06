"""
Rotas para gerenciamento de usuários (exceto autenticação)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any

from api import models, schemas, security
from api.db import get_db

router = APIRouter(
    prefix="/users", 
    tags=["users"],
    responses={404: {"description": "Não encontrado"}} # Resposta padrão para 404
)

@router.get(
    "/{user_id}/settings", 
    response_model=schemas.UserSettingsResponse,
    summary="Obter Configurações do Usuário",
    description="Obtém as configurações gerais para um usuário específico."
)
async def get_user_settings(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
) -> Any:
    """
    Obtém as configurações gerais de um usuário.
    Um usuário só pode obter suas próprias configurações.
    Retorna as configurações padrão se nenhuma estiver salva.
    """
    # 1. Verificar permissão: Usuário só pode ver suas próprias configs
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Não autorizado a visualizar as configurações deste usuário"
        )

    # 2. Buscar o usuário no banco de dados
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Usuário não encontrado"
        )

    # 3. Verificar se existem configurações salvas
    if db_user.settings:
        print(f"Retornando configurações salvas para usuário {user_id}")
        saved_settings = db_user.settings
        saved_settings["user_id"] = user_id # Garantir que user_id está presente para o response model
        return saved_settings
    else:
        # Se não houver configurações salvas, retornar as padrão do schema
        print(f"Retornando configurações padrão para usuário {user_id}")
        default_settings = schemas.UserSettingsBase().dict() # Gera dict com defaults
        default_settings["user_id"] = user_id # Adiciona o user_id
        return default_settings

@router.put(
    "/{user_id}/settings", 
    response_model=schemas.UserSettingsResponse,
    summary="Atualizar Configurações do Usuário",
    description="Atualiza as configurações gerais para um usuário específico."
)
async def update_user_settings(
    user_id: str,
    settings_data: schemas.UserSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
) -> Any:
    """
    Atualiza (substitui) as configurações gerais de um usuário.
    Um usuário só pode atualizar suas próprias configurações.
    """
    # 1. Verificar permissão: Usuário só pode alterar suas próprias configs
    if current_user.id != user_id:
        # Poderíamos permitir que admins alterem (verificando current_user.is_admin),
        # mas vamos manter simples por enquanto.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Não autorizado a atualizar as configurações deste usuário"
        )

    # 2. Buscar o usuário no banco de dados
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Usuário não encontrado"
        )

    # 3. Atualizar o campo JSONB com os novos dados (substituição completa - PUT)
    # O Pydantic já validou a estrutura de settings_data
    print(f"Atualizando configurações para usuário {user_id} com dados: {settings_data.dict()}")
    db_user.settings = settings_data.dict() 

    # 4. Salvar no banco de dados
    try:
        db.commit()
        db.refresh(db_user) # Atualiza a instância db_user com os dados do DB
        print(f"Configurações do usuário {user_id} salvas com sucesso.")
    except Exception as e:
        db.rollback()
        print(f"Erro ao salvar configurações do usuário no DB: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao salvar as configurações do usuário: {e}"
        )

    # 5. Retornar os dados atualizados 
    # Construir a resposta conforme o schema UserSettingsResponse
    response_data = db_user.settings # As configurações salvas
    response_data["user_id"] = db_user.id # Adicionar o user_id
    
    return response_data 