ssh denisbonaccini@detec-o.com.br "cat > ~/Detec-O/backend/simple_api.py" << 'EOF'
from fastapi import FastAPI, Depends, HTTPException, status, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from typing import List, Dict, Any, Optional
import uvicorn
from datetime import datetime, timedelta
import jwt
from pydantic import BaseModel

# Configurações de segurança
SECRET_KEY = "meu_jwt_secret_seguro_para_deteco"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Usuários simulados para teste
users_db = {
    "admin@exemplo.com": {
        "id": "user1",
        "name": "Admin",
        "email": "admin@exemplo.com",
        "password": "7ce3284bA",  # Em produção, use hash
        "is_active": True
    },
}

# Modelos Pydantic
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: str
    name: str
    email: str

class UserRegister(BaseModel):
    name: str
    email: str
    password: str

# Função para criar tokens JWT
def create_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Rota raiz
@app.get("/")
async def root():
    return {"message": "Detec-o API"}

# NOVOS ENDPOINTS COMPATÍVEIS COM O FRONTEND
@app.post("/api/v1/auth/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_db.get(form_data.username)
    if not user or user["password"] != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_token(
        data={"sub": user["email"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_token(
        data={"sub": user["email"]},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }

# Manter compatibilidade com o frontend
@app.post("/auth/token", response_model=Token)
async def old_login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_db.get(form_data.username)
    if not user or user["password"] != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_token(
        data={"sub": user["email"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_token(
        data={"sub": user["email"]},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }

# Rota para obter informações do usuário
@app.get("/api/v1/auth/me")
async def get_user_me(authorization: str = Depends(lambda x: x.headers.get("Authorization"))):
    # Simulação - em produção, validate the token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido")
    
    try:
        # Para teste, retornamos o primeiro usuário
        user = list(users_db.values())[0]
        return {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"]
        }
    except:
        raise HTTPException(status_code=401, detail="Token inválido")

# Compatibilidade com frontend
@app.get("/auth/me")
async def old_get_user_me(authorization: str = Depends(lambda x: x.headers.get("Authorization"))):
    # Simulação - em produção, validate the token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido")
    
    try:
        # Para teste, retornamos o primeiro usuário
        user = list(users_db.values())[0]
        return {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"]
        }
    except:
        raise HTTPException(status_code=401, detail="Token inválido")

# Rota para registro de usuário
@app.post("/api/v1/auth/register")
async def register_user(user_data: UserRegister = Body(None), 
                        name: str = Form(None), 
                        email: str = Form(None), 
                        password: str = Form(None)):
    # Prioriza dados JSON se fornecidos
    if user_data:
        name = user_data.name
        email = user_data.email
        password = user_data.password
    
    # Verifica se temos todos os dados necessários
    if not all([name, email, password]):
        raise HTTPException(
            status_code=422,
            detail="Dados incompletos. Informe nome, email e senha."
        )
    
    if email in users_db:
        raise HTTPException(status_code=400, detail="Email já registrado")
    
    user_id = f"user{len(users_db) + 1}"
    users_db[email] = {
        "id": user_id,
        "name": name,
        "email": email,
        "password": password,  # Em produção, use hash
        "is_active": True
    }
    
    return {"message": "Usuário registrado com sucesso"}

# Manter compatibilidade
@app.post("/auth/register")
async def old_register_user(user_data: UserRegister = Body(None),
                        name: str = Form(None), 
                        email: str = Form(None), 
                        password: str = Form(None)):
    # Prioriza dados JSON se fornecidos
    if user_data:
        name = user_data.name
        email = user_data.email
        password = user_data.password
    
    # Verifica se temos todos os dados necessários
    if not all([name, email, password]):
        raise HTTPException(
            status_code=422,
            detail="Dados incompletos. Informe nome, email e senha."
        )
    
    if email in users_db:
        raise HTTPException(status_code=400, detail="Email já registrado")
    
    user_id = f"user{len(users_db) + 1}"
    users_db[email] = {
        "id": user_id,
        "name": name,
        "email": email,
        "password": password,  # Em produção, use hash
        "is_active": True
    }
    
    return {"message": "Usuário registrado com sucesso"}

# Rota para configurações do usuário
@app.get("/api/v1/users/{user_id}/settings")
async def get_user_settings(user_id: str):
    # Retorna configurações padrão
    return {
        "notifications": {
            "email": False,
            "browser": True,
            "mobile": False,
            "frequency": "immediate",
        },
        "detection": {
            "confidenceThreshold": 0.6,
            "minDetectionInterval": 30,
            "motionSensitivity": 5,
            "enableWeaponDetection": True,
            "enableFaceDetection": True,
            "enableBehaviorAnalysis": True,
        },
        "interface": {
            "darkMode": False,
            "compactView": False,
            "showStatistics": True,
            "highlightDetections": True,
        }
    }

@app.put("/api/v1/users/{user_id}/settings")
async def update_user_settings(user_id: str, settings: dict):
    # Apenas simula salvar as configurações
    return settings

# Rotas para eventos
@app.get("/api/v1/events")
async def get_events():
    # Retorna lista de eventos simulados
    events = [
        {
            "id": "1",
            "timestamp": "2023-12-01T10:00:00Z",
            "camera_id": "cam1",
            "camera_name": "Entrada Principal",
            "type": "person_detected",
            "description": "Pessoa detectada na entrada",
            "image_url": "/images/events/person1.jpg",
            "severity": "info",
            "location": "Entrada Principal",
            "status": "new"
        },
        {
            "id": "2",
            "timestamp": "2023-12-01T09:30:00Z",
            "camera_id": "cam2",
            "camera_name": "Estacionamento",
            "type": "suspicious_activity",
            "description": "Atividade suspeita detectada",
            "image_url": "/images/events/suspicious1.jpg",
            "severity": "warning",
            "location": "Estacionamento",
            "status": "reviewing"
        }
    ]
    return {"events": events, "total": len(events)}

# Rotas para câmeras
@app.get("/api/v1/cameras")
async def get_cameras():
    # Retorna lista de câmeras simuladas
    cameras = [
        {
            "id": "cam1",
            "name": "Entrada Principal",
            "url": "rtsp://admin:admin@192.168.0.100:554/cam/realmonitor?channel=1&subtype=0",
            "location": "Entrada Principal",
            "status": "online",
            "resolution": "1920x1080",
            "type": "IP"
        },
        {
            "id": "cam2",
            "name": "Estacionamento",
            "url": "rtsp://admin:admin@192.168.0.101:554/cam/realmonitor?channel=1&subtype=0",
            "location": "Estacionamento",
            "status": "online",
            "resolution": "1280x720",
            "type": "IP"
        }
    ]
    return cameras

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
EOF