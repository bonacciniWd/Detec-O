from sqlalchemy.orm import Session
from sqlalchemy import desc
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from ..models.person import PersonCreate, PersonUpdate, PersonResponse, PersonList

# Tabela para armazenar pessoas
def create_person(db: Session, person_data: PersonCreate, user_id: str) -> Dict[str, Any]:
    """
    Cria uma nova pessoa no banco de dados.
    
    Args:
        db: Sessão do banco de dados
        person_data: Dados da pessoa
        user_id: ID do usuário que está criando a pessoa
        
    Returns:
        Dicionário com os dados da pessoa criada
    """
    now = datetime.now()
    person_id = str(uuid.uuid4())
    
    # Criar documento para a pessoa
    person = {
        "id": person_id,
        "name": person_data.name,
        "description": person_data.description,
        "category": person_data.category,
        "user_id": user_id,
        "created_at": now,
        "updated_at": now,
        "face_count": 0,
        "face_encodings": []
    }
    
    # Adicionar ao banco
    db.execute(
        """
        INSERT INTO persons (id, name, description, category, user_id, created_at, updated_at, face_count, face_encodings)
        VALUES (:id, :name, :description, :category, :user_id, :created_at, :updated_at, :face_count, :face_encodings)
        """,
        {
            "id": person["id"],
            "name": person["name"],
            "description": person["description"],
            "category": person["category"],
            "user_id": person["user_id"],
            "created_at": person["created_at"],
            "updated_at": person["updated_at"],
            "face_count": person["face_count"],
            "face_encodings": "[]"  # JSON string
        }
    )
    db.commit()
    
    return person

def get_person(db: Session, person_id: str) -> Optional[Dict[str, Any]]:
    """
    Busca uma pessoa pelo ID.
    
    Args:
        db: Sessão do banco de dados
        person_id: ID da pessoa
        
    Returns:
        Dicionário com os dados da pessoa ou None se não encontrada
    """
    result = db.execute(
        """
        SELECT id, name, description, category, user_id, created_at, updated_at, face_count, face_encodings
        FROM persons
        WHERE id = :person_id
        """,
        {"person_id": person_id}
    ).fetchone()
    
    if not result:
        return None
    
    # Converter para dicionário
    person = {
        "id": result[0],
        "name": result[1],
        "description": result[2],
        "category": result[3],
        "user_id": result[4],
        "created_at": result[5],
        "updated_at": result[6],
        "face_count": result[7],
        "face_encodings": result[8]  # JSON string ou lista de dicionários
    }
    
    # Garantir que face_encodings seja uma lista de dicionários
    if isinstance(person["face_encodings"], str):
        import json
        try:
            person["face_encodings"] = json.loads(person["face_encodings"])
        except:
            person["face_encodings"] = []
    
    return person

def update_person(db: Session, person_id: str, person_data: PersonUpdate) -> Optional[Dict[str, Any]]:
    """
    Atualiza os dados de uma pessoa.
    
    Args:
        db: Sessão do banco de dados
        person_id: ID da pessoa
        person_data: Dados a atualizar
        
    Returns:
        Dicionário com os dados atualizados ou None se não encontrada
    """
    # Verificar se a pessoa existe
    person = get_person(db, person_id)
    if not person:
        return None
    
    # Preparar dados de atualização
    update_values = {}
    if person_data.name is not None:
        update_values["name"] = person_data.name
    if person_data.description is not None:
        update_values["description"] = person_data.description
    if person_data.category is not None:
        update_values["category"] = person_data.category
    
    if not update_values:
        return person  # Nada para atualizar
    
    # Adicionar timestamp de atualização
    update_values["updated_at"] = datetime.now()
    
    # Construir consulta SQL dinamicamente
    query = "UPDATE persons SET "
    query += ", ".join([f"{key} = :{key}" for key in update_values.keys()])
    query += " WHERE id = :person_id"
    
    # Adicionar person_id aos parâmetros
    update_values["person_id"] = person_id
    
    # Executar atualização
    db.execute(query, update_values)
    db.commit()
    
    # Retornar dados atualizados
    return get_person(db, person_id)

def delete_person(db: Session, person_id: str) -> bool:
    """
    Remove uma pessoa do banco de dados.
    
    Args:
        db: Sessão do banco de dados
        person_id: ID da pessoa
        
    Returns:
        True se removida com sucesso, False caso contrário
    """
    # Verificar se a pessoa existe
    person = get_person(db, person_id)
    if not person:
        return False
    
    # Remover a pessoa
    db.execute(
        """
        DELETE FROM persons
        WHERE id = :person_id
        """,
        {"person_id": person_id}
    )
    db.commit()
    
    return True

def add_face_to_person(db: Session, face_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adiciona uma nova face à pessoa.
    
    Args:
        db: Sessão do banco de dados
        face_data: Dados da face
        
    Returns:
        Dicionário com os dados da face adicionada
    """
    person_id = face_data["person_id"]
    
    # Buscar a pessoa
    person = get_person(db, person_id)
    if not person:
        raise ValueError(f"Pessoa com ID {person_id} não encontrada")
    
    # Adicionar metadata à face
    face_entry = {
        "id": face_data["id"],
        "path": face_data["path"],
        "encoding": face_data["encoding"],
        "created_at": datetime.now().isoformat(),
        "label": face_data.get("label", ""),
        "thumbnail_path": face_data.get("thumbnail_path", "")
    }
    
    # Adicionar face à lista de faces da pessoa
    face_encodings = person["face_encodings"]
    face_encodings.append(face_entry)
    
    # Atualizar contagem de faces
    face_count = len(face_encodings)
    
    # Serializar para JSON
    import json
    face_encodings_json = json.dumps(face_encodings)
    
    # Atualizar no banco
    db.execute(
        """
        UPDATE persons
        SET face_encodings = :face_encodings, face_count = :face_count, updated_at = :updated_at
        WHERE id = :person_id
        """,
        {
            "face_encodings": face_encodings_json,
            "face_count": face_count,
            "updated_at": datetime.now(),
            "person_id": person_id
        }
    )
    db.commit()
    
    return face_entry

def remove_face_from_person(db: Session, person_id: str, face_id: str) -> bool:
    """
    Remove uma face de uma pessoa.
    
    Args:
        db: Sessão do banco de dados
        person_id: ID da pessoa
        face_id: ID da face
        
    Returns:
        True se removida com sucesso, False caso contrário
    """
    # Buscar a pessoa
    person = get_person(db, person_id)
    if not person:
        return False
    
    # Encontrar e remover a face
    face_encodings = person["face_encodings"]
    original_count = len(face_encodings)
    face_encodings = [face for face in face_encodings if face["id"] != face_id]
    
    if len(face_encodings) == original_count:
        return False  # Face não encontrada
    
    # Serializar para JSON
    import json
    face_encodings_json = json.dumps(face_encodings)
    
    # Atualizar no banco
    db.execute(
        """
        UPDATE persons
        SET face_encodings = :face_encodings, face_count = :face_count, updated_at = :updated_at
        WHERE id = :person_id
        """,
        {
            "face_encodings": face_encodings_json,
            "face_count": len(face_encodings),
            "updated_at": datetime.now(),
            "person_id": person_id
        }
    )
    db.commit()
    
    return True

def get_persons(db: Session, user_id: str, skip: int = 0, limit: int = 100) -> PersonList:
    """
    Busca todas as pessoas do usuário com paginação.
    
    Args:
        db: Sessão do banco de dados
        user_id: ID do usuário
        skip: Quantos registros pular
        limit: Máximo de registros a retornar
        
    Returns:
        Objeto PersonList com as pessoas encontradas
    """
    # Contar total de registros
    total = db.execute(
        """
        SELECT COUNT(*)
        FROM persons
        WHERE user_id = :user_id
        """,
        {"user_id": user_id}
    ).scalar()
    
    # Buscar pessoas
    results = db.execute(
        """
        SELECT id, name, description, category, created_at, updated_at, face_count
        FROM persons
        WHERE user_id = :user_id
        ORDER BY updated_at DESC
        LIMIT :limit OFFSET :skip
        """,
        {"user_id": user_id, "skip": skip, "limit": limit}
    ).fetchall()
    
    # Converter resultados para modelos
    items = []
    for row in results:
        # Buscar thumbnail da primeira face se existir
        thumbnail_url = None
        person_detail = get_person(db, row[0])
        if person_detail and person_detail["face_encodings"]:
            first_face = person_detail["face_encodings"][0]
            if "thumbnail_path" in first_face:
                thumbnail_url = f"/static/{first_face['thumbnail_path']}"
        
        items.append(PersonResponse(
            id=row[0],
            name=row[1],
            description=row[2],
            category=row[3],
            created_at=row[4],
            updated_at=row[5],
            face_count=row[6],
            thumbnail_url=thumbnail_url
        ))
    
    # Calcular páginas
    pages = (total + limit - 1) // limit if limit > 0 else 1
    page = (skip // limit) + 1 if limit > 0 else 1
    
    return PersonList(
        items=items,
        total=total,
        page=page,
        pages=pages
    )

def get_all_face_encodings(db: Session) -> Dict[str, Dict[str, Any]]:
    """
    Carrega todas as codificações faciais do banco de dados.
    
    Args:
        db: Sessão do banco de dados
        
    Returns:
        Dicionário com as codificações faciais por pessoa
    """
    results = db.execute(
        """
        SELECT id, name, category, face_encodings
        FROM persons
        WHERE face_count > 0
        """
    ).fetchall()
    
    encodings = {}
    
    for row in results:
        person_id = row[0]
        name = row[1]
        category = row[2]
        face_encodings_str = row[3]
        
        # Converter JSON para objeto Python
        import json
        try:
            face_encodings = json.loads(face_encodings_str) if face_encodings_str else []
        except:
            face_encodings = []
        
        # Adicionar à lista
        encodings[person_id] = {
            "name": name,
            "category": category,
            "faces": face_encodings
        }
    
    return encodings 