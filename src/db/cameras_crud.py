import os
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from ..models.pyobjectid import PyObjectId # Precisaremos criar este helper

# Conexão com MongoDB (Reutilizando a configuração de auth.py por enquanto, idealmente centralizar)
MONGODB_URL = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGODB_URL)
db = client[os.environ.get("DB_NAME", "crime_detection_system")]
cameras_collection = db.cameras

# Modelo Pydantic para Câmera no Banco de Dados
class CameraDB(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(...)
    url: str = Field(...)
    location: Optional[str] = None
    owner: str = Field(...)  # Armazena o username do proprietário
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "name": "Câmera Garagem",
                "url": "rtsp://admin:pass@192.168.1.100/stream1",
                "location": "Garagem Fundos",
                "owner": "user1",
            }
        }

# Modelo para criação de câmera (usado na API)
class CameraCreate(BaseModel):
    name: str = Field(...)
    url: str = Field(...)
    location: Optional[str] = None

# Funções CRUD Assíncronas

async def add_camera(camera_data: CameraCreate, owner: str) -> CameraDB:
    """Adiciona uma nova câmera ao banco de dados."""
    camera_doc = camera_data.dict()
    camera_doc["owner"] = owner
    camera_doc["created_at"] = datetime.now()
    
    result = await cameras_collection.insert_one(camera_doc)
    created_camera = await cameras_collection.find_one({"_id": result.inserted_id})
    return CameraDB(**created_camera)

async def get_cameras_by_user(owner: str) -> List[CameraDB]:
    """Busca todas as câmeras pertencentes a um usuário."""
    cameras = []
    cursor = cameras_collection.find({"owner": owner})
    async for camera_doc in cursor:
        cameras.append(CameraDB(**camera_doc))
    return cameras

async def get_camera_by_id(camera_id: str, owner: Optional[str] = None) -> Optional[CameraDB]:
    """Busca uma câmera específica pelo seu ID, opcionalmente verificando o proprietário."""
    try:
        obj_id = ObjectId(camera_id)
    except Exception:
        return None # ID inválido
        
    query = {"_id": obj_id}
    if owner:
        query["owner"] = owner
        
    camera_doc = await cameras_collection.find_one(query)
    if camera_doc:
        return CameraDB(**camera_doc)
    return None

async def delete_camera(camera_id: str, owner: str) -> bool:
    """Deleta uma câmera pelo ID, garantindo que pertence ao usuário."""
    try:
        obj_id = ObjectId(camera_id)
    except Exception:
        return False # ID inválido
        
    result = await cameras_collection.delete_one({"_id": obj_id, "owner": owner})
    return result.deleted_count > 0

# Você também pode adicionar funções de update se necessário
# async def update_camera(camera_id: str, owner: str, update_data: dict) -> Optional[CameraDB]:
#     ... 