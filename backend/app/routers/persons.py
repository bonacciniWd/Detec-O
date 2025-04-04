from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import base64
from io import BytesIO

from ..models.person import (
    PersonCreate, PersonUpdate, PersonResponse, PersonList,
    FaceEncodingCreate, FaceEncoding, FaceMatchResult
)
from ..dependencies import get_db, get_current_user
from ..crud import person as person_crud
from ..services import face_service

router = APIRouter(prefix="/api/v1/persons", tags=["persons"])

@router.get("", response_model=PersonList)
async def list_persons(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Lista pessoas cadastradas com suas faces."""
    return person_crud.get_persons(db, current_user["id"], skip, limit)

@router.post("", response_model=PersonResponse)
async def create_person(
    person_data: PersonCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Cria uma nova pessoa com uma face inicial."""
    try:
        # Criar pessoa com face
        person = face_service.create_person_with_face(db, person_data, current_user["id"])
        
        # Retornar resposta formatada
        thumbnail_url = None
        if person.get("face_encodings") and len(person["face_encodings"]) > 0:
            first_face = person["face_encodings"][0]
            if "thumbnail_path" in first_face:
                thumbnail_url = f"/static/{first_face['thumbnail_path']}"
        
        return PersonResponse(
            id=person["id"],
            name=person["name"],
            description=person["description"],
            category=person["category"],
            created_at=person["created_at"],
            updated_at=person["updated_at"],
            face_count=person["face_count"],
            thumbnail_url=thumbnail_url
        )
    except Exception as e:
        logging.error(f"Erro ao criar pessoa: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Erro ao criar pessoa: {str(e)}")

@router.get("/{person_id}", response_model=PersonResponse)
async def get_person(
    person_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obtém detalhes de uma pessoa específica."""
    person = person_crud.get_person(db, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    
    if person["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Sem permissão para acessar esta pessoa")
    
    # Formatar resposta
    thumbnail_url = None
    if person["face_encodings"] and len(person["face_encodings"]) > 0:
        first_face = person["face_encodings"][0]
        if "thumbnail_path" in first_face:
            thumbnail_url = f"/static/{first_face['thumbnail_path']}"
    
    return PersonResponse(
        id=person["id"],
        name=person["name"],
        description=person["description"],
        category=person["category"],
        created_at=person["created_at"],
        updated_at=person["updated_at"],
        face_count=person["face_count"],
        thumbnail_url=thumbnail_url
    )

@router.put("/{person_id}", response_model=PersonResponse)
async def update_person(
    person_data: PersonUpdate,
    person_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Atualiza os dados de uma pessoa."""
    # Verificar se a pessoa existe e pertence ao usuário
    person = person_crud.get_person(db, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    
    if person["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Sem permissão para atualizar esta pessoa")
    
    # Atualizar pessoa
    updated_person = person_crud.update_person(db, person_id, person_data)
    
    # Formatar resposta
    thumbnail_url = None
    if updated_person["face_encodings"] and len(updated_person["face_encodings"]) > 0:
        first_face = updated_person["face_encodings"][0]
        if "thumbnail_path" in first_face:
            thumbnail_url = f"/static/{first_face['thumbnail_path']}"
    
    return PersonResponse(
        id=updated_person["id"],
        name=updated_person["name"],
        description=updated_person["description"],
        category=updated_person["category"],
        created_at=updated_person["created_at"],
        updated_at=updated_person["updated_at"],
        face_count=updated_person["face_count"],
        thumbnail_url=thumbnail_url
    )

@router.delete("/{person_id}", status_code=204)
async def delete_person(
    person_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Remove uma pessoa e todas as suas faces."""
    # Verificar se a pessoa existe e pertence ao usuário
    person = person_crud.get_person(db, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    
    if person["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Sem permissão para remover esta pessoa")
    
    # Remover pessoa
    success = person_crud.delete_person(db, person_id)
    if not success:
        raise HTTPException(status_code=500, detail="Erro ao remover pessoa")

@router.post("/{person_id}/faces", response_model=FaceEncoding)
async def add_face(
    face_data: FaceEncodingCreate,
    person_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Adiciona uma nova face a uma pessoa existente."""
    # Verificar se a pessoa existe e pertence ao usuário
    person = person_crud.get_person(db, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    
    if person["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Sem permissão para adicionar face a esta pessoa")
    
    # Validar se os IDs correspondem
    if face_data.person_id != person_id:
        raise HTTPException(status_code=400, detail="ID da pessoa na URL e no corpo da requisição não correspondem")
    
    try:
        # Adicionar face
        face = face_service.add_face_encoding(db, face_data)
        
        # Formatar resposta
        return FaceEncoding(
            id=face["id"],
            person_id=face["person_id"],
            created_at=face["created_at"],
            label=face["label"],
            thumbnail_url=f"/static/{face['thumbnail_path']}" if "thumbnail_path" in face else None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Erro ao adicionar face: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao adicionar face: {str(e)}")

@router.delete("/{person_id}/faces/{face_id}", status_code=204)
async def remove_face(
    person_id: str = Path(...),
    face_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Remove uma face de uma pessoa."""
    # Verificar se a pessoa existe e pertence ao usuário
    person = person_crud.get_person(db, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    
    if person["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Sem permissão para remover face desta pessoa")
    
    # Remover face
    success = person_crud.remove_face_from_person(db, person_id, face_id)
    if not success:
        raise HTTPException(status_code=404, detail="Face não encontrada")

@router.post("/recognize", response_model=Optional[FaceMatchResult])
async def recognize_face(
    face_image: str = Body(..., embed=True),
    confidence_threshold: float = Query(0.6, ge=0.1, le=1.0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Reconhece uma face em uma imagem base64.
    Retorna a pessoa correspondente ou null se não encontrada.
    """
    try:
        # Reconhecer face
        match_result = face_service.recognize_face(
            db, face_image, confidence_threshold
        )
        return match_result
    except Exception as e:
        logging.error(f"Erro ao reconhecer face: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar imagem: {str(e)}")

@router.post("/recognize-file", response_model=Optional[FaceMatchResult])
async def recognize_face_file(
    file: UploadFile = File(...),
    confidence_threshold: float = Query(0.6, ge=0.1, le=1.0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Reconhece uma face em um arquivo de imagem.
    Retorna a pessoa correspondente ou null se não encontrada.
    """
    try:
        # Ler arquivo
        contents = await file.read()
        
        # Converter para base64
        base64_image = base64.b64encode(contents).decode("utf-8")
        
        # Reconhecer face
        match_result = face_service.recognize_face(
            db, base64_image, confidence_threshold
        )
        return match_result
    except Exception as e:
        logging.error(f"Erro ao reconhecer face do arquivo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar imagem: {str(e)}") 