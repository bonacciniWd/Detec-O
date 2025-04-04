echo '
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
' > temp_routes.py