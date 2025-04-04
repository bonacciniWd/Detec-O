from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

# Modelo para representar um ponto de um polígono
class Point(BaseModel):
    x: float = Field(..., description="Coordenada X do ponto (0-1 ou pixel)")
    y: float = Field(..., description="Coordenada Y do ponto (0-1 ou pixel)")

# Modelo para representar uma zona de detecção
class DetectionZone(BaseModel):
    id: str = Field(..., description="Identificador único da zona")
    name: str = Field(..., description="Nome da zona")
    points: List[Point] = Field(..., description="Pontos que formam o polígono da zona")
    enabled: bool = Field(True, description="Se a zona está ativa")
    detection_classes: Optional[List[str]] = Field(None, description="Classes específicas para detecção nesta zona")
    
class DetectionSettingsBase(BaseModel):
    """Modelo base para configurações de detecção."""
    min_confidence: float = Field(0.6, ge=0.0, le=1.0, description="Confiança mínima para considerar uma detecção (0.0-1.0)")
    detection_interval: int = Field(30, ge=5, description="Intervalo mínimo em segundos entre detecções (min: 5s)")
    enabled_event_types: List[str] = Field(["person", "vehicle", "animal"], description="Tipos de eventos habilitados")
    notification_enabled: bool = Field(True, description="Habilitar notificações de eventos")
    
    # Configurações específicas por tipo de evento
    red_events_enabled: bool = Field(True, description="Habilitar eventos críticos (vermelho)")
    yellow_events_enabled: bool = Field(True, description="Habilitar eventos de atenção (amarelo)")
    blue_events_enabled: bool = Field(True, description="Habilitar eventos informativos (azul)")
    
    # Limiares de confiança por tipo de severidade
    red_confidence_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Limiar de confiança para eventos críticos")
    yellow_confidence_threshold: float = Field(0.6, ge=0.0, le=1.0, description="Limiar de confiança para eventos de atenção")
    blue_confidence_threshold: float = Field(0.5, ge=0.0, le=1.0, description="Limiar de confiança para eventos informativos")
    
    # Configurações adicionais
    ignore_areas: List[DetectionZone] = Field([], description="Áreas a serem ignoradas na detecção (zonas onde a detecção é desativada)")
    detection_zones: List[DetectionZone] = Field([], description="Zonas onde a detecção deve ser aplicada")
    use_zones_only: bool = Field(False, description="Se verdadeiro, a detecção só ocorre nas zonas definidas")
    custom_rules: List[dict] = Field([], description="Regras personalizadas para detecção")
    
    @validator('yellow_confidence_threshold')
    def yellow_threshold_valid(cls, v, values):
        if 'red_confidence_threshold' in values and v > values['red_confidence_threshold']:
            raise ValueError('O limiar de confiança para eventos amarelos deve ser menor ou igual ao de eventos vermelhos')
        return v
    
    @validator('blue_confidence_threshold')
    def blue_threshold_valid(cls, v, values):
        if 'yellow_confidence_threshold' in values and v > values['yellow_confidence_threshold']:
            raise ValueError('O limiar de confiança para eventos azuis deve ser menor ou igual ao de eventos amarelos')
        return v

class DetectionSettingsCreate(DetectionSettingsBase):
    """Modelo para criação de configurações de detecção."""
    pass

class DetectionSettingsUpdate(BaseModel):
    """Modelo para atualização parcial de configurações de detecção."""
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    detection_interval: Optional[int] = Field(None, ge=5)
    enabled_event_types: Optional[List[str]] = None
    notification_enabled: Optional[bool] = None
    red_events_enabled: Optional[bool] = None
    yellow_events_enabled: Optional[bool] = None
    blue_events_enabled: Optional[bool] = None
    red_confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    yellow_confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    blue_confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    ignore_areas: Optional[List[DetectionZone]] = None
    detection_zones: Optional[List[DetectionZone]] = None
    use_zones_only: Optional[bool] = None
    custom_rules: Optional[List[dict]] = None

class DetectionSettingsInDB(DetectionSettingsBase):
    """Modelo para configurações de detecção armazenadas no banco."""
    user_id: str
    camera_id: Optional[str] = None  # None para configuração global
    created_at: datetime
    updated_at: Optional[datetime] = None

class DetectionSettingsResponse(DetectionSettingsInDB):
    """Modelo de resposta para configurações de detecção."""
    id: str 