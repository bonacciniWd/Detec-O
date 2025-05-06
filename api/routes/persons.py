"""
Rotas da API para Gerenciamento de Pessoas
"""
import base64
import io
import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
import face_recognition
import numpy as np
from PIL import Image
from datetime import datetime

# Importações reais
from .. import schemas, models # Importar de __init__.py nos níveis superiores
from ..db import get_db

# --- Constantes --- 
THUMBNAIL_DIR = os.path.join("api", "snapshots", "thumbnails", "persons")
THUMBNAIL_SIZE = (150, 150) # Tamanho do thumbnail em pixels

# Garantir que o diretório de thumbnails exista
os.makedirs(THUMBNAIL_DIR, exist_ok=True)

router = APIRouter(
    prefix="/persons",
    tags=["Persons"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.PersonResponse, status_code=status.HTTP_201_CREATED)
def create_person(person: schemas.PersonCreate, db: Session = Depends(get_db)):
    """
    Cria uma nova pessoa no sistema.
    Recebe dados da pessoa e a imagem facial inicial (base64).
    Retorna a pessoa criada.
    """
    print(f"Recebido para criar pessoa: {person.name}")

    # 1. Decodificar imagem base64
    try:
        # Remover cabeçalho data:image/...;base64, se presente
        if "," in person.face_image:
            header, encoded_data = person.face_image.split(",", 1)
        else:
            encoded_data = person.face_image
        
        image_bytes = base64.b64decode(encoded_data)
        image_stream = io.BytesIO(image_bytes)
        pil_image = Image.open(image_stream)
        # Converter para RGB se necessário (face_recognition espera RGB)
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        image_np = np.array(pil_image)
    except Exception as e:
        print(f"Erro ao decodificar/carregar imagem base64: {e}")
        raise HTTPException(status_code=400, detail=f"Imagem base64 inválida ou não suportada: {e}")

    # 2. Processar imagem: detectar rosto e gerar embedding
    face_locations = face_recognition.face_locations(image_np)

    if not face_locations:
        raise HTTPException(status_code=400, detail="Nenhum rosto detectado na imagem.")
    if len(face_locations) > 1:
        print(f"Aviso: Múltiplos rostos detectados ({len(face_locations)}). Usando o primeiro.")
        # Poderia usar o maior rosto: face_locations = sorted(face_locations, key=lambda loc: (loc[2]-loc[0])*(loc[1]-loc[3]), reverse=True)
    
    # Usar a localização do primeiro rosto detectado
    top, right, bottom, left = face_locations[0]
    face_encoding = face_recognition.face_encodings(image_np, [face_locations[0]])[0]

    # 3. Salvar dados básicos da pessoa no banco
    db_person = models.Person(
        name=person.name,
        description=person.description,
        category=person.category
        # thumbnail_path será definido após salvar o arquivo
    )
    db.add(db_person)
    try:
        db.commit()
        db.refresh(db_person) # Para obter o ID gerado
    except Exception as e:
        db.rollback()
        print(f"Erro ao salvar pessoa no DB: {e}")
        # Poderia verificar se é erro de nome duplicado, etc.
        raise HTTPException(status_code=500, detail="Erro ao salvar dados da pessoa.")

    # 4. Salvar embedding associado à pessoa
    db_embedding = models.FaceEmbedding(
        person_id=db_person.id,
        embedding=face_encoding.tobytes() # Converter numpy array para bytes
        # label e source_image_path podem ser adicionados se necessário
    )
    db.add(db_embedding)

    # 5. Gerar e salvar thumbnail
    thumbnail_path_rel = None
    thumbnail_url = None
    try:
        face_image_pil = pil_image.crop((left, top, right, bottom))
        face_image_pil.thumbnail(THUMBNAIL_SIZE) # Redimensiona in-place preservando aspecto
        
        thumbnail_filename = f"{db_person.id}.jpg"
        thumbnail_path_abs = os.path.join(THUMBNAIL_DIR, thumbnail_filename)
        face_image_pil.save(thumbnail_path_abs, "JPEG")
        
        # Salvar caminho relativo no banco
        thumbnail_path_rel = os.path.join("thumbnails", "persons", thumbnail_filename).replace("\\", "/")
        db_person.thumbnail_path = thumbnail_path_rel
        
        # Construir URL relativa para resposta (baseada na montagem estática)
        thumbnail_url = f"/snapshots/{thumbnail_path_rel}" 

    except Exception as e:
        db.rollback() # Desfaz adição do embedding e pessoa se thumbnail falhar?
                      # Ou apenas loga o erro e continua sem thumbnail?
        print(f"Erro ao gerar/salvar thumbnail: {e}")
        # Decide se deve falhar a requisição inteira ou continuar sem thumbnail
        # raise HTTPException(status_code=500, detail="Erro ao processar thumbnail da imagem.")
        # Por enquanto, vamos continuar sem thumbnail se falhar
        db_person.thumbnail_path = None # Garante que está nulo no DB se falhou
        thumbnail_url = None
        # Precisamos fazer commit de novo se continuarmos
        db.commit()
        db.refresh(db_person) # Atualiza o objeto db_person com thumbnail_path=None
        # Commitar o embedding também se não foi desfeito
        try: 
            db.commit()
            db.refresh(db_embedding)
        except Exception as commit_err:
             print(f"Erro ao commitar embedding após falha do thumbnail: {commit_err}")
             # Aqui a situação fica inconsistente, talvez melhor falhar antes
             raise HTTPException(status_code=500, detail="Erro interno ao salvar dados faciais.")

    else:
        # Commit final se thumbnail foi sucesso
        try:
            db.commit()
            db.refresh(db_person)
            db.refresh(db_embedding)
        except Exception as e:
            db.rollback()
            print(f"Erro no commit final após sucesso do thumbnail: {e}")
            raise HTTPException(status_code=500, detail="Erro ao finalizar salvamento dos dados.")

    # 6. Calcular face_count (será 1 após a criação inicial)
    # Poderia contar de db_person.face_embeddings mas pode ser ineficiente se houver muitos.
    # Fazer uma query de contagem é melhor se necessário, mas aqui sabemos que é 1.
    face_count = 1

    # 7. Retornar dados da pessoa criada
    return schemas.PersonResponse(
        id=db_person.id,
        name=db_person.name,
        description=db_person.description,
        category=db_person.category,
        thumbnail_url=thumbnail_url, # URL relativa para o frontend
        face_count=face_count,
        created_at=db_person.created_at,
        updated_at=db_person.updated_at
    )

@router.get("/", response_model=List[schemas.PersonResponse])
def read_persons(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Lista todas as pessoas cadastradas, com paginação.
    """
    persons = db.query(models.Person).order_by(models.Person.name).offset(skip).limit(limit).all()
    response_persons = []
    for p in persons:
        face_count = len(p.face_embeddings)
        thumbnail_url = f"/snapshots/{p.thumbnail_path}" if p.thumbnail_path else None
        response_persons.append(schemas.PersonResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            category=p.category,
            class_group=p.class_group,
            thumbnail_url=thumbnail_url,
            face_count=face_count,
            created_at=p.created_at,
            updated_at=p.updated_at
        ))
    return response_persons

@router.get("/{person_id}", response_model=schemas.PersonResponse)
def read_person(person_id: str, db: Session = Depends(get_db)): # ID é string (UUID)
    """
    Obtém detalhes de uma pessoa específica pelo ID.
    """
    db_person = db.query(models.Person).filter(models.Person.id == person_id).first()
    if db_person is None:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    
    face_count = len(db_person.face_embeddings)
    thumbnail_url = f"/snapshots/{db_person.thumbnail_path}" if db_person.thumbnail_path else None

    return schemas.PersonResponse(
        id=db_person.id,
        name=db_person.name,
        description=db_person.description,
        category=db_person.category,
        class_group=db_person.class_group,
        thumbnail_url=thumbnail_url,
        face_count=face_count,
        created_at=db_person.created_at,
        updated_at=db_person.updated_at
    )

@router.put("/{person_id}", response_model=schemas.PersonResponse)
def update_person(person_id: str, person: schemas.PersonUpdate, db: Session = Depends(get_db)): # ID é string
    """
    Atualiza os dados de uma pessoa existente (nome, descrição, categoria).
    Não atualiza imagens faciais por aqui.
    """
    db_person = db.query(models.Person).filter(models.Person.id == person_id).first()
    if db_person is None:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada para atualizar")

    # Usar .dict(exclude_unset=True) para Pydantic V1
    update_data = person.dict(exclude_unset=True) # Pega só os campos enviados
    for key, value in update_data.items():
        setattr(db_person, key, value)
    
    db_person.updated_at = datetime.utcnow()
    try:
        db.commit()
        db.refresh(db_person)
    except Exception as e:
        db.rollback()
        print(f"Erro ao atualizar pessoa no DB: {e}")
        raise HTTPException(status_code=500, detail="Erro ao salvar atualização da pessoa.")

    face_count = len(db_person.face_embeddings)
    thumbnail_url = f"/snapshots/{db_person.thumbnail_path}" if db_person.thumbnail_path else None

    return schemas.PersonResponse(
        id=db_person.id,
        name=db_person.name,
        description=db_person.description,
        category=db_person.category,
        class_group=db_person.class_group,
        thumbnail_url=thumbnail_url,
        face_count=face_count,
        created_at=db_person.created_at,
        updated_at=db_person.updated_at
    )

@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_person(person_id: str, db: Session = Depends(get_db)): # ID é string
    """
    Remove uma pessoa e todos os seus dados associados (incluindo faces/embeddings e thumbnail).
    Retorna status 204 se sucesso.
    """
    db_person = db.query(models.Person).filter(models.Person.id == person_id).first()
    if db_person is None:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada para deletar")

    # Guardar o caminho do thumbnail antes de deletar do DB
    thumbnail_path_to_delete = db_person.thumbnail_path

    try:
        # A deleção em cascata deve cuidar dos face_embeddings
        db.delete(db_person)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Erro ao deletar pessoa do DB: {e}")
        raise HTTPException(status_code=500, detail="Erro ao remover dados da pessoa do banco.")

    # Tentar remover o arquivo thumbnail do sistema de arquivos
    if thumbnail_path_to_delete:
        # Construir caminho absoluto baseado na raiz do projeto (ou onde main.py está)
        # Assumindo que THUMBNAIL_DIR é relativo a api/ e main.py está na raiz
        # O caminho salvo é relativo a /snapshots, então precisamos montá-lo a partir da raiz física.
        # snapshot_base_dir = os.path.join(os.path.dirname(__file__), "..", "snapshots") # Se persons.py está em api/routes
        # Ajuste: THUMBNAIL_DIR já é api/snapshots/thumbnails/persons
        # Precisamos do caminho do arquivo dentro dessa pasta
        filename = os.path.basename(thumbnail_path_to_delete)
        absolute_thumbnail_path = os.path.join(THUMBNAIL_DIR, filename)
        
        try:
            print(f"Tentando remover arquivo thumbnail: {absolute_thumbnail_path}")
            os.remove(absolute_thumbnail_path)
            print(f"Arquivo thumbnail removido com sucesso.")
        except FileNotFoundError:
            print(f"Arquivo thumbnail não encontrado para remover (talvez já removido ou nunca existiu): {absolute_thumbnail_path}")
        except Exception as e:
            # Logar o erro, mas talvez não falhar a requisição inteira por causa disso?
            print(f"Erro ao tentar remover o arquivo thumbnail {absolute_thumbnail_path}: {e}")
            # Dependendo da política, poderia levantar um erro 500 aqui ou apenas logar.

    return None # Retorna status 204

# TODO: Adicionar rota POST /{person_id}/faces para adicionar novas imagens faciais
# (Precisa de lógica de processamento de imagem/IA)

# Adicionar import datetime se não estiver presente
from datetime import datetime

# Rota para buscar eventos associados a uma pessoa
@router.get("/{person_id}/events", response_model=List[schemas.DetectionEventResponse])
def read_person_events(
    person_id: str,
    skip: int = 0,
    limit: int = 50, # Limite menor padrão para esta lista?
    db: Session = Depends(get_db)
    # Adicionar autenticação se necessário: current_user: models.User = Depends(security.get_current_user)
    # A verificação de permissão aqui pode ser complexa (o usuário pode ver essa pessoa? pode ver os eventos?)
    # Por enquanto, vamos simplificar e não verificar permissão nesta rota específica.
):
    """
    Lista os eventos de detecção associados a uma pessoa específica.
    """
    # Verificar se a pessoa existe (opcional, mas bom)
    person_exists = db.query(models.Person).filter(models.Person.id == person_id).first()
    if not person_exists:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")

    # Buscar eventos
    events = (
        db.query(models.DetectionEvent)
        .options(joinedload(models.DetectionEvent.camera)) # Carregar nome da câmera
        .filter(models.DetectionEvent.detected_person_id == person_id)
        .order_by(models.DetectionEvent.timestamp.desc()) # Mais recentes primeiro
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Converter para o schema de resposta (incluindo nome da pessoa)
    response_events = []
    for event in events:
        # Reutilizar a lógica de construção da resposta da rota get_event?
        # Por enquanto, vamos construir manualmente
        response = schemas.DetectionEventResponse.from_orm(event).dict()
        # O nome da pessoa já está implícito (é a pessoa que estamos buscando), 
        # mas podemos adicionar para consistência ou remover do schema de resposta aqui?
        response['detected_person_name'] = person_exists.name 
        response['camera_name'] = event.camera.name if event.camera else None # Adicionar nome da câmera
        response_events.append(response)
        
    return response_events

"""
Exemplo de como incluir no api/routes/__init__.py:

from api.routes import auth, cameras, events, users, persons # Adicionar persons

api_router = APIRouter(prefix="/api")

api_router.include_router(auth.router)
api_router.include_router(cameras.router)
api_router.include_router(events.router)
api_router.include_router(users.router)
api_router.include_router(persons.router) # Adicionar esta linha
""" 