# API Reference - Detec-o

## Visão Geral

Esta documentação descreve as APIs disponíveis no sistema Detec-o para processamento e configuração de detecções de câmeras de segurança.

## Autenticação

Todas as APIs requerem autenticação via token JWT. O token deve ser enviado no cabeçalho HTTP da seguinte maneira:

```
Authorization: Bearer {token}
```

## Endpoints de Detecção

### Configurações de Detecção

#### Obter Configurações
```
GET /api/v1/cameras/{camera_id}/settings
```

Retorna as configurações de detecção para uma câmera específica.

**Resposta**
```json
{
  "id": "string",
  "user_id": "string",
  "camera_id": "string",
  "min_confidence": 0.6,
  "detection_interval": 30,
  "enabled_event_types": ["person", "vehicle", "animal"],
  "notification_enabled": true,
  "red_events_enabled": true,
  "yellow_events_enabled": true,
  "blue_events_enabled": true,
  "red_confidence_threshold": 0.7,
  "yellow_confidence_threshold": 0.6,
  "blue_confidence_threshold": 0.5,
  "ignore_areas": [],
  "detection_zones": [],
  "use_zones_only": false,
  "custom_rules": [],
  "created_at": "2023-04-01T12:00:00Z",
  "updated_at": "2023-04-01T12:00:00Z"
}
```

#### Atualizar Configurações
```
PUT /api/v1/cameras/{camera_id}/settings
```

Atualiza as configurações de detecção para uma câmera específica.

**Corpo da Requisição**
```json
{
  "min_confidence": 0.6,
  "detection_interval": 30,
  "enabled_event_types": ["person", "vehicle", "animal"],
  "notification_enabled": true,
  "red_events_enabled": true,
  "yellow_events_enabled": true,
  "blue_events_enabled": true,
  "red_confidence_threshold": 0.7,
  "yellow_confidence_threshold": 0.6,
  "blue_confidence_threshold": 0.5,
  "ignore_areas": [],
  "detection_zones": [],
  "use_zones_only": false,
  "custom_rules": []
}
```

### Zonas de Detecção

#### Listar Zonas de Detecção
```
GET /api/v1/cameras/{camera_id}/detection-zones
```

Retorna todas as zonas de detecção configuradas para uma câmera.

**Resposta**
```json
[
  {
    "id": "string",
    "name": "string",
    "points": [
      {
        "x": 0.1,
        "y": 0.2
      }
    ],
    "enabled": true,
    "detection_classes": ["person", "car"]
  }
]
```

#### Adicionar Zona de Detecção
```
POST /api/v1/cameras/{camera_id}/detection-zones
```

Adiciona uma nova zona de detecção para uma câmera.

**Corpo da Requisição**
```json
{
  "id": "string",
  "name": "string",
  "points": [
    {
      "x": 0.1,
      "y": 0.2
    }
  ],
  "enabled": true,
  "detection_classes": ["person", "car"]
}
```

#### Atualizar Zona de Detecção
```
PUT /api/v1/cameras/{camera_id}/detection-zones/{zone_id}
```

Atualiza uma zona de detecção existente.

**Corpo da Requisição**
```json
{
  "id": "string",
  "name": "string",
  "points": [
    {
      "x": 0.1,
      "y": 0.2
    }
  ],
  "enabled": true,
  "detection_classes": ["person", "car"]
}
```

#### Excluir Zona de Detecção
```
DELETE /api/v1/cameras/{camera_id}/detection-zones/{zone_id}
```

Remove uma zona de detecção.

**Resposta**
```json
{
  "message": "Zona de detecção removida com sucesso"
}
```

#### Exportar Zonas de Detecção
```
GET /api/v1/cameras/{camera_id}/detection-zones/export
```

Exporta as zonas de detecção configuradas para uma câmera.

**Resposta**
```json
{
  "camera_id": "string",
  "detection_zones": [],
  "ignore_areas": [],
  "exported_at": "2023-04-01T12:00:00Z"
}
```

#### Importar Zonas de Detecção
```
POST /api/v1/cameras/{camera_id}/detection-zones/import
```

Importa zonas de detecção para uma câmera.

**Corpo da Requisição**
```json
{
  "detection_zones": [],
  "ignore_areas": []
}
```

**Resposta**
```json
{
  "message": "Zonas de detecção importadas com sucesso",
  "detection_zones_count": 2,
  "ignore_areas_count": 1
}
```

#### Obter Preview da Câmera
```
GET /api/v1/cameras/{camera_id}/preview
```

Obtém uma imagem de preview da câmera para configuração de zonas.

**Resposta**
```json
{
  "preview_url": "/static/camera_previews/example.jpg"
}
```

## Modelos de Dados

### Point
```json
{
  "x": 0.1,  // Coordenada X (0-1 ou pixel)
  "y": 0.2   // Coordenada Y (0-1 ou pixel)
}
```

### DetectionZone
```json
{
  "id": "string",               // Identificador único da zona
  "name": "string",             // Nome da zona (ex: "Entrada Principal")
  "points": [                   // Lista de pontos que formam o polígono
    {
      "x": 0.1,
      "y": 0.2
    }
  ],
  "enabled": true,              // Se a zona está ativa
  "detection_classes": ["string"] // Classes específicas para detecção nesta zona (opcional)
}
```

### DetectionSettings
```json
{
  "min_confidence": 0.6,        // Confiança mínima para considerar uma detecção (0.0-1.0)
  "detection_interval": 30,     // Intervalo mínimo em segundos entre detecções (min: 5s)
  "enabled_event_types": [],    // Tipos de eventos habilitados
  "notification_enabled": true, // Habilitar notificações de eventos
  "red_events_enabled": true,   // Habilitar eventos críticos (vermelho)
  "yellow_events_enabled": true, // Habilitar eventos de atenção (amarelo)
  "blue_events_enabled": true,  // Habilitar eventos informativos (azul)
  "red_confidence_threshold": 0.7, // Limiar para eventos críticos
  "yellow_confidence_threshold": 0.6, // Limiar para eventos de atenção
  "blue_confidence_threshold": 0.5, // Limiar para eventos informativos
  "ignore_areas": [],           // Áreas a serem ignoradas (zonas desativadas)
  "detection_zones": [],        // Zonas onde a detecção deve ser aplicada
  "use_zones_only": false,      // Se verdadeiro, a detecção só ocorre nas zonas definidas
  "custom_rules": []            // Regras personalizadas para detecção
}
``` 