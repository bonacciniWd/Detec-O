from fastapi import FastAPI, Depends, HTTPException, status, Body, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid
import random

app = FastAPI(
    title="Detec-o API",
    description="API para sistema de detecção por câmera",
    version="1.0.0"
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurações de segurança
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"  # Chave secreta para produção deve ser mantida em variáveis de ambiente
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 dias

# Configuração do contexto de senha e OAuth2
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Bancos de dados simulados
USER_DB = []
CAMERA_DB = []
EVENTS_DB = []
SETTINGS_DB = []

# Criar usuário admin
admin_id = str(uuid.uuid4())
USER_DB.append({
    "id": admin_id,
    "email": "admin@exemplo.com",
    "name": "Admin",
    "hashed_password": pwd_context.hash("senha123"),
    "is_active": True,
    "created_at": datetime.now(),
    "updated_at": datetime.now()
})

# Funções de autenticação
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_user(email: str) -> Optional[Dict[str, Any]]:
    for user in USER_DB:
        if user["email"] == email:
            return user
    return None

def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    user = get_user(email)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    if not user["is_active"]:
        return None
    return user

def create_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_access_token(data: Dict[str, Any]) -> str:
    return create_token(
        data,
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

def create_refresh_token(data: Dict[str, Any]) -> str:
    return create_token(
        data,
        timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    )

def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user(email)
    if user is None:
        raise credentials_exception
    
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo"
        )
    
    return user

# Rotas da API
@app.get("/", tags=["Root"])
async def root():
    """Endpoint raiz para verificar se a API está online."""
    return {
        "status": "online",
        "message": "Detec-o API está funcionando!",
        "documentation": "/docs"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Endpoint para verificar a saúde da aplicação."""
    return {
        "status": "healthy",
        "version": app.version
    }

# Rotas de autenticação
@app.post("/auth/register", tags=["auth"])
async def register(user_data: Dict = Body(...)):
    """Registra um novo usuário."""
    # Verificar se o email já está em uso
    if get_user(user_data["email"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já registrado"
        )
    
    # Hash da senha
    hashed_password = pwd_context.hash(user_data["password"])
    
    # Criar usuário
    user_id = str(uuid.uuid4())
    now = datetime.now()
    new_user = {
        "id": user_id,
        "email": user_data["email"],
        "name": user_data.get("name", user_data["email"].split("@")[0]),
        "hashed_password": hashed_password,
        "is_active": True,
        "created_at": now,
        "updated_at": now
    }
    
    USER_DB.append(new_user)
    
    return {
        "id": new_user["id"],
        "email": new_user["email"],
        "name": new_user["name"],
        "is_active": new_user["is_active"],
        "created_at": new_user["created_at"]
    }

@app.post("/auth/token", tags=["auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Endpoint de login para obter token JWT."""
    # Autenticar usuário
    user = authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Criar tokens
    token_data = {"sub": user["email"]}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 60 * 60 * 24,  # 24 horas em segundos
        "refresh_token": refresh_token
    }

@app.post("/auth/refresh", tags=["auth"])
async def refresh_token(refresh_token: str = Body(..., embed=True)):
    """Atualiza um token JWT expirado."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token de atualização inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    token_data = {"sub": email}
    access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 60 * 60 * 24,  # 24 horas em segundos
        "refresh_token": new_refresh_token
    }

@app.get("/auth/me", tags=["auth"])
async def read_users_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Retorna informações do usuário autenticado."""
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "name": current_user["name"],
        "is_active": current_user["is_active"],
        "created_at": current_user["created_at"]
    }

# Rotas para câmeras
@app.get("/api/v1/cameras", tags=["cameras"])
async def list_cameras(
    page: int = Query(1, ge=1, description="Página atual"),
    limit: int = Query(10, ge=1, le=100, description="Itens por página"),
    search: Optional[str] = Query(None, description="Termo de busca para nome ou localização"),
    current_user: dict = Depends(get_current_user)
):
    """Lista todas as câmeras do usuário atual."""
    # Filtrar câmeras do usuário atual
    user_cameras = [cam for cam in CAMERA_DB if cam["user_id"] == current_user["id"]]
    
    # Aplicar filtro de busca, se fornecido
    if search:
        search = search.lower()
        filtered_cameras = [
            cam for cam in user_cameras 
            if search in cam["name"].lower() or search in cam["location"].lower()
        ]
    else:
        filtered_cameras = user_cameras
    
    # Calcular paginação
    total = len(filtered_cameras)
    pages = (total + limit - 1) // limit if total > 0 else 1
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    
    # Obter itens da página atual
    paginated_cameras = filtered_cameras[start_idx:end_idx]
    
    # Adicionar contagem de eventos simulada para cada câmera
    for camera in paginated_cameras:
        if "events_count" not in camera:
            camera["events_count"] = 0
        if "last_event" not in camera:
            camera["last_event"] = None
    
    return {
        "items": paginated_cameras,
        "total": total,
        "page": page,
        "pages": pages
    }

@app.post("/api/v1/cameras", tags=["cameras"], status_code=status.HTTP_201_CREATED)
async def create_camera(
    camera: Dict = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """Cria uma nova câmera para o usuário atual."""
    now = datetime.now()
    camera_id = str(uuid.uuid4())
    
    # Criar nova câmera
    new_camera = {
        "id": camera_id,
        "user_id": current_user["id"],
        "name": camera["name"],
        "location": camera["location"],
        "url": camera["url"],
        "is_active": camera.get("is_active", True),
        "detection_enabled": camera.get("detection_enabled", True),
        "created_at": now,
        "updated_at": now,
        "events_count": 0,
        "last_event": None,
        "thumbnail": None
    }
    
    # Adicionar ao banco simulado
    CAMERA_DB.append(new_camera)
    
    return new_camera

@app.get("/api/v1/cameras/{camera_id}", tags=["cameras"])
async def get_camera(
    camera_id: str = Path(..., description="ID da câmera"),
    current_user: dict = Depends(get_current_user)
):
    """Obtém detalhes de uma câmera específica."""
    # Encontrar a câmera pelo ID
    camera = next((cam for cam in CAMERA_DB if cam["id"] == camera_id), None)
    
    # Verificar se a câmera existe
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Câmera não encontrada"
        )
    
    # Verificar se a câmera pertence ao usuário atual
    if camera["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado a esta câmera"
        )
    
    return camera

@app.put("/api/v1/cameras/{camera_id}", tags=["cameras"])
async def update_camera(
    camera_update: Dict = Body(...),
    camera_id: str = Path(..., description="ID da câmera"),
    current_user: dict = Depends(get_current_user)
):
    """Atualiza uma câmera existente."""
    # Encontrar a câmera pelo ID
    camera_idx = None
    for idx, cam in enumerate(CAMERA_DB):
        if cam["id"] == camera_id:
            camera_idx = idx
            break
    
    # Verificar se a câmera existe
    if camera_idx is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Câmera não encontrada"
        )
    
    # Verificar se a câmera pertence ao usuário atual
    if CAMERA_DB[camera_idx]["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado a esta câmera"
        )
    
    # Atualizar campos da câmera
    camera_data = CAMERA_DB[camera_idx]
    for key, value in camera_update.items():
        # Não permitir atualizar id e user_id
        if key not in ["id", "user_id", "created_at"]:
            camera_data[key] = value
    
    # Atualizar timestamp
    camera_data["updated_at"] = datetime.now()
    
    # Atualizar no banco simulado
    CAMERA_DB[camera_idx] = camera_data
    
    return camera_data

@app.delete("/api/v1/cameras/{camera_id}", tags=["cameras"], status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(
    camera_id: str = Path(..., description="ID da câmera"),
    current_user: dict = Depends(get_current_user)
):
    """Remove uma câmera e todos os seus eventos associados."""
    # Encontrar a câmera pelo ID
    camera_idx = None
    for idx, cam in enumerate(CAMERA_DB):
        if cam["id"] == camera_id:
            camera_idx = idx
            break
    
    # Verificar se a câmera existe
    if camera_idx is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Câmera não encontrada"
        )
    
    # Verificar se a câmera pertence ao usuário atual
    if CAMERA_DB[camera_idx]["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado a esta câmera"
        )
    
    # Remover do banco simulado
    CAMERA_DB.pop(camera_idx)
    
    # Também remover eventos associados
    global EVENTS_DB
    EVENTS_DB = [event for event in EVENTS_DB if event["camera_id"] != camera_id]
    
    return

# Rotas para eventos
def generate_sample_events(user_id, camera_id=None, num_events=5):
    """Gera eventos de amostra para demonstração."""
    events = []
    now = datetime.now()
    
    # Tipos de eventos possíveis
    event_types = ["pessoa", "arma", "aglomeração", "objeto_suspeito"]
    
    for i in range(num_events):
        # Determinar severidade baseado no tipo de evento
        event_type = random.choice(event_types)
        
        if event_type == "arma":
            severity = "red"
        elif event_type == "objeto_suspeito":
            severity = "yellow"
        else:
            severity = "blue"
        
        # Criar um evento simulado
        event = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "camera_id": camera_id or str(uuid.uuid4()),
            "camera_name": f"Câmera {random.randint(1, 5)}",
            "camera_location": f"Local {random.randint(1, 10)}",
            "event_type": event_type,
            "confidence": round(random.uniform(0.7, 0.98), 2),
            "timestamp": now - timedelta(minutes=random.randint(0, 60 * 24)),
            "image_path": f"/images/events/sample_{i+1}.jpg",
            "bounding_boxes": [
                {
                    "x": random.randint(10, 500),
                    "y": random.randint(10, 300),
                    "width": random.randint(50, 200),
                    "height": random.randint(50, 200),
                    "class": event_type,
                    "confidence": round(random.uniform(0.7, 0.98), 2)
                }
            ],
            "metadata": {
                "detector": "YOLOv8",
                "processing_time": round(random.uniform(0.05, 0.2), 3)
            },
            "severity": severity,
            "feedback": None
        }
        events.append(event)
    
    return events

@app.get("/api/v1/events", tags=["events"])
async def list_events(
    page: int = Query(1, ge=1, description="Página atual"),
    limit: int = Query(10, ge=1, le=100, description="Itens por página"),
    days: int = Query(7, ge=1, le=90, description="Últimos N dias"),
    camera_id: Optional[str] = Query(None, description="Filtrar por ID da câmera"),
    severity: Optional[str] = Query(None, description="Filtrar por severidade (red, yellow, blue)"),
    current_user: dict = Depends(get_current_user)
):
    """Lista eventos de detecção com opções de filtro e paginação."""
    # Gerar eventos de exemplo se o banco estiver vazio
    if not EVENTS_DB:
        sample_events = generate_sample_events(current_user["id"])
        EVENTS_DB.extend(sample_events)
    
    # Filtrar eventos do usuário atual
    user_events = [event for event in EVENTS_DB if event["user_id"] == current_user["id"]]
    
    # Filtrar por data (últimos N dias)
    cutoff_date = datetime.now() - timedelta(days=days)
    filtered_events = [event for event in user_events if event["timestamp"] >= cutoff_date]
    
    # Aplicar filtro de câmera, se fornecido
    if camera_id:
        filtered_events = [event for event in filtered_events if event["camera_id"] == camera_id]
    
    # Aplicar filtro de severidade, se fornecido
    if severity:
        filtered_events = [event for event in filtered_events if event["severity"] == severity]
    
    # Ordenar por data (mais recentes primeiro)
    sorted_events = sorted(filtered_events, key=lambda x: x["timestamp"], reverse=True)
    
    # Calcular paginação
    total = len(sorted_events)
    pages = (total + limit - 1) // limit if total > 0 else 1
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    
    # Obter itens da página atual
    paginated_events = sorted_events[start_idx:end_idx]
    
    return {
        "items": paginated_events,
        "total": total,
        "page": page,
        "pages": pages
    }

@app.get("/api/v1/events/{event_id}", tags=["events"])
async def get_event(
    event_id: str = Path(..., description="ID do evento"),
    current_user: dict = Depends(get_current_user)
):
    """Obtém detalhes de um evento específico."""
    # Encontrar o evento pelo ID
    event = next((event for event in EVENTS_DB if event["id"] == event_id), None)
    
    # Verificar se o evento existe
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado"
        )
    
    # Verificar se o evento pertence ao usuário atual
    if event["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado a este evento"
        )
    
    return event

@app.post("/api/v1/events/{event_id}/feedback", tags=["events"])
async def provide_feedback(
    event_id: str,
    feedback_type: str = Query(..., description="Tipo de feedback (true_positive, false_positive, uncertain)"),
    comment: Optional[str] = Query(None, description="Comentário opcional sobre o feedback"),
    current_user: dict = Depends(get_current_user)
):
    """Fornece feedback sobre um evento de detecção."""
    # Validar o tipo de feedback
    valid_feedback_types = ["true_positive", "false_positive", "uncertain"]
    if feedback_type not in valid_feedback_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de feedback inválido. Deve ser um de: {', '.join(valid_feedback_types)}"
        )
    
    # Encontrar o evento pelo ID
    event_idx = None
    for idx, event in enumerate(EVENTS_DB):
        if event["id"] == event_id:
            event_idx = idx
            break
    
    # Verificar se o evento existe
    if event_idx is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado"
        )
    
    # Verificar se o evento pertence ao usuário atual
    if EVENTS_DB[event_idx]["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado a este evento"
        )
    
    # Atualizar feedback
    EVENTS_DB[event_idx]["feedback"] = feedback_type
    if comment:
        if "metadata" not in EVENTS_DB[event_idx]:
            EVENTS_DB[event_idx]["metadata"] = {}
        EVENTS_DB[event_idx]["metadata"]["feedback_comment"] = comment
    
    return EVENTS_DB[event_idx]

# Rotas para configurações de detecção
@app.get("/api/v1/detection-settings", tags=["detection_settings"])
async def get_detection_settings(
    current_user: dict = Depends(get_current_user)
):
    """Obtém as configurações de detecção do usuário atual."""
    # Buscar configurações do usuário atual
    user_settings = next((settings for settings in SETTINGS_DB 
                         if settings["user_id"] == current_user["id"]), None)
    
    # Se não existir, criar configurações padrão
    if not user_settings:
        settings_id = str(uuid.uuid4())
        now = datetime.now()
        
        user_settings = {
            "id": settings_id,
            "user_id": current_user["id"],
            "detection_interval": 10,  # Intervalo entre detecções em segundos
            "confidence_threshold": 0.5,  # Limiar de confiança para detecções
            "sensitivity": "medium",  # Sensibilidade do detector (low, medium, high)
            "notify_on_detection": True,  # Notificar quando uma detecção ocorrer
            "detect_people": True,  # Detectar pessoas
            "detect_weapons": True,  # Detectar armas
            "detect_vehicles": False,  # Detectar veículos
            "detect_animals": False,  # Detectar animais
            "detect_suspicious": True,  # Detectar comportamento suspeito
            "created_at": now,
            "updated_at": now
        }
        
        # Adicionar ao banco de dados simulado
        SETTINGS_DB.append(user_settings)
    
    return user_settings

@app.put("/api/v1/detection-settings", tags=["detection_settings"])
async def update_detection_settings(
    settings: Dict = Body(..., description="Configurações de detecção a serem atualizadas"),
    current_user: dict = Depends(get_current_user)
):
    """Atualiza as configurações de detecção do usuário atual."""
    # Verificar campos obrigatórios
    required_fields = [
        "detection_interval", "confidence_threshold", "sensitivity", 
        "notify_on_detection", "detect_people", "detect_weapons"
    ]
    
    for field in required_fields:
        if field not in settings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Campo obrigatório ausente: {field}"
            )
    
    # Validar valores
    if settings["detection_interval"] < 1 or settings["detection_interval"] > 3600:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Intervalo de detecção deve estar entre 1 e 3600 segundos"
        )
    
    if settings["confidence_threshold"] < 0.1 or settings["confidence_threshold"] > 1.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limiar de confiança deve estar entre 0.1 e 1.0"
        )
    
    if settings["sensitivity"] not in ["low", "medium", "high"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sensibilidade deve ser 'low', 'medium' ou 'high'"
        )
    
    # Buscar configurações existentes do usuário
    settings_idx = None
    for idx, s in enumerate(SETTINGS_DB):
        if s["user_id"] == current_user["id"]:
            settings_idx = idx
            break
    
    now = datetime.now()
    
    if settings_idx is not None:
        # Atualizar configurações existentes
        for key, value in settings.items():
            SETTINGS_DB[settings_idx][key] = value
        
        # Atualizar timestamp
        SETTINGS_DB[settings_idx]["updated_at"] = now
        
        return SETTINGS_DB[settings_idx]
    else:
        # Criar novas configurações
        settings_id = str(uuid.uuid4())
        
        new_settings = {
            "id": settings_id,
            "user_id": current_user["id"],
            "created_at": now,
            "updated_at": now,
            **settings
        }
        
        # Adicionar ao banco de dados simulado
        SETTINGS_DB.append(new_settings)
        
        return new_settings

# Iniciar servidor se executado diretamente
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 