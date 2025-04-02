import asyncio
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import logging
from typing import Dict, Any, List, Optional

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lista de objetos potencialmente perigosos para monitoramento adicional
DANGEROUS_OBJECTS = [
    "knife", "scissors", "gun", "pistol", "rifle", "weapon", "toothbrush",  # toothbrush pode ser confundido com faca
    "remote", "cell phone", "bottle", "cup",  # podem ser confundidos com armas
]

# Mapeamento de objetos comumente confundidos com objetos perigosos
OBJECT_SIMILARITY_MAP = {
    "toothbrush": "knife",
    "remote": "gun",
    "cell phone": "gun",
    "bottle": "weapon",
    "cup": "weapon",
}

class DetectionService:
    """Serviço para gerenciar detecções de câmeras."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        # Cache para armazenar o timestamp da última detecção por câmera/tipo
        self._last_detections: Dict[str, Dict[str, datetime]] = {}
        
    async def get_detection_settings(self, user_id: str, camera_id: Optional[str] = None) -> dict:
        """
        Obtém as configurações de detecção para um usuário/câmera.
        Se não houver configuração específica para a câmera, retorna configuração global.
        """
        settings = None
        
        if camera_id:
            # Buscar configuração específica da câmera
            settings = await self.db.detection_settings.find_one({
                "user_id": str(user_id),
                "camera_id": camera_id
            })
        
        if not settings:
            # Buscar configuração global do usuário
            settings = await self.db.detection_settings.find_one({
                "user_id": str(user_id),
                "camera_id": None
            })
        
        # Se não houver configuração, retorna configuração padrão
        if not settings:
            return {
                "min_confidence": 0.6,
                "detection_interval": 30,
                "enabled_event_types": ["person", "vehicle", "animal"],
                "notification_enabled": True,
                "red_events_enabled": True,
                "yellow_events_enabled": True,
                "blue_events_enabled": True,
                "red_confidence_threshold": 0.7,
                "yellow_confidence_threshold": 0.6,
                "blue_confidence_threshold": 0.5
            }
        
        return settings
    
    async def should_process_detection(self, 
                                      user_id: str, 
                                      camera_id: str,
                                      event_type: str,
                                      confidence: float) -> bool:
        """
        Verifica se uma detecção deve ser processada com base nas configurações
        e no intervalo desde a última detecção do mesmo tipo.
        """
        settings = await self.get_detection_settings(user_id, camera_id)
        
        # Verificar se o tipo de evento está habilitado
        if event_type not in settings.get("enabled_event_types", []):
            logger.info(f"Evento {event_type} ignorado: tipo não habilitado")
            return False
        
        # Verificar confiança mínima
        if confidence < settings.get("min_confidence", 0.6):
            logger.info(f"Evento {event_type} ignorado: confiança ({confidence}) abaixo do mínimo")
            return False
        
        # Verificar intervalo entre detecções
        detection_interval = settings.get("detection_interval", 30)
        camera_key = f"{user_id}:{camera_id}"
        
        now = datetime.utcnow()
        
        if camera_key in self._last_detections and event_type in self._last_detections[camera_key]:
            last_detection = self._last_detections[camera_key][event_type]
            time_diff = (now - last_detection).total_seconds()
            
            if time_diff < detection_interval:
                logger.info(f"Evento {event_type} ignorado: intervalo muito curto ({time_diff}s < {detection_interval}s)")
                return False
        
        # Atualizar timestamp da última detecção
        if camera_key not in self._last_detections:
            self._last_detections[camera_key] = {}
        
        self._last_detections[camera_key][event_type] = now
        return True
    
    def evaluate_potential_threat(self, 
                                event_type: str,
                                metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Avalia se uma detecção pode representar uma ameaça potencial,
        como objetos confundidos com armas ou facas.
        
        Retorna metadados enriquecidos com informações sobre a potencial ameaça.
        """
        enriched_metadata = metadata.copy() if metadata else {}
        
        # Verifica se o objeto detectado está na lista de objetos potencialmente perigosos
        if event_type in DANGEROUS_OBJECTS:
            enriched_metadata["is_potential_threat"] = True
            
            # Se for um objeto comumente confundido, registra possíveis equivalências
            if event_type in OBJECT_SIMILARITY_MAP:
                enriched_metadata["possible_threat"] = OBJECT_SIMILARITY_MAP[event_type]
                enriched_metadata["needs_review"] = True
                
            # Se for diretamente um objeto perigoso
            if event_type in ["knife", "gun", "pistol", "rifle", "weapon"]:
                enriched_metadata["is_weapon"] = True
        
        # Verifica padrões de comportamento suspeito nos metadados
        if metadata and "motion_patterns" in metadata:
            motion = metadata["motion_patterns"]
            
            # Exemplo: movimento rápido ou errático pode indicar comportamento suspeito
            if "rapid" in motion or "erratic" in motion:
                enriched_metadata["is_suspicious"] = True
                
            # Exemplo: movimentos que podem indicar agressão
            if "hitting" in motion or "fighting" in motion:
                enriched_metadata["potential_aggression"] = True
        
        return enriched_metadata
    
    def determine_severity(self, 
                          event_type: str, 
                          confidence: float,
                          metadata: Dict[str, Any],
                          settings: Dict[str, Any]) -> str:
        """
        Determina a severidade do evento (red, yellow, blue) com base no tipo,
        confiança e metadados adicionais.
        
        Red: Comportamentos agressivos, armas, agressão física
        Blue: Pessoas detectadas com tempo no local
        Yellow: Situações suspeitas
        """
        # Verificar se o evento é crítico (vermelho)
        if event_type in ["weapon", "gun", "knife", "aggression", "fight", "violence"]:
            return "red" if settings.get("red_events_enabled", True) else "blue"
        
        # Verificar metadados para potenciais ameaças
        if metadata.get("is_weapon") or metadata.get("potential_aggression"):
            return "red" if settings.get("red_events_enabled", True) else "blue"
            
        # Verificar metadados para situações específicas
        if metadata.get("is_suspicious") or metadata.get("is_potential_threat"):
            return "yellow" if settings.get("yellow_events_enabled", True) else "blue"
        
        if "time_in_location" in metadata and metadata["time_in_location"] > 60:  # mais de 1 minuto
            if confidence >= settings.get("red_confidence_threshold", 0.7):
                return "red" if settings.get("red_events_enabled", True) else "blue"
            elif confidence >= settings.get("yellow_confidence_threshold", 0.6):
                return "yellow" if settings.get("yellow_events_enabled", True) else "blue"
        
        # Objetos comumente confundidos com armas ou objetos perigosos
        if event_type in OBJECT_SIMILARITY_MAP:
            return "yellow" if settings.get("yellow_events_enabled", True) else "blue"
        
        # Determinar com base na confiança
        if confidence >= settings.get("red_confidence_threshold", 0.7):
            return "red" if settings.get("red_events_enabled", True) else "blue"
        elif confidence >= settings.get("yellow_confidence_threshold", 0.6):
            return "yellow" if settings.get("yellow_events_enabled", True) else "blue"
        
        # Padrão é azul (informativo)
        return "blue"
    
    async def process_detection(self,
                               user_id: str,
                               camera_id: str,
                               event_type: str,
                               confidence: float,
                               image_path: str,
                               bounding_boxes: List[Dict[str, Any]],
                               metadata: Dict[str, Any] = None) -> Optional[str]:
        """
        Processa uma nova detecção e retorna o ID do evento criado.
        Retorna None se a detecção for ignorada.
        """
        if not await self.should_process_detection(user_id, camera_id, event_type, confidence):
            return None
        
        settings = await self.get_detection_settings(user_id, camera_id)
        metadata = metadata or {}
        
        # Enriquecer metadados com avaliação de potencial ameaça
        enriched_metadata = self.evaluate_potential_threat(event_type, metadata)
        
        # Determinar severidade
        severity = self.determine_severity(event_type, confidence, enriched_metadata, settings)
        
        # Criar evento
        event_data = {
            "user_id": ObjectId(user_id),
            "camera_id": ObjectId(camera_id),
            "event_type": event_type,
            "confidence": confidence,
            "timestamp": datetime.utcnow(),
            "image_path": image_path,
            "bounding_boxes": bounding_boxes,
            "metadata": enriched_metadata,
            "severity": severity
        }
        
        # Adicionar possíveis ameaças detectadas nos metadados
        if enriched_metadata.get("is_potential_threat") or enriched_metadata.get("is_weapon"):
            event_data["potential_threat"] = True
            
            # Se for um objeto confundido, registrar possíveis ameaças reais
            if "possible_threat" in enriched_metadata:
                event_data["possible_threat_type"] = enriched_metadata["possible_threat"]
        
        result = await self.db.events.insert_one(event_data)
        event_id = str(result.inserted_id)
        
        logger.info(f"Evento criado: {event_id} | Tipo: {event_type} | Severidade: {severity}")
        
        # Verificar se notificações estão habilitadas
        if settings.get("notification_enabled", True):
            # Aqui poderia ser implementado um serviço de notificações
            # como envio de e-mail, push, etc.
            # Para ameaças graves (red), poderia haver notificações prioritárias
            if severity == "red":
                logger.info(f"ALERTA: Evento crítico detectado! ID: {event_id}, Tipo: {event_type}")
        
        return event_id
    
    async def cleanup_old_events(self, days_to_keep: int = 30) -> int:
        """Remove eventos antigos do banco de dados."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        result = await self.db.events.delete_many({
            "timestamp": {"$lt": cutoff_date}
        })
        
        deleted_count = result.deleted_count
        logger.info(f"Limpeza de eventos: {deleted_count} eventos antigos removidos")
        
        return deleted_count
        
    async def get_detection_statistics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Obtém estatísticas de detecções para um usuário nos últimos dias.
        Útil para analisar a eficácia do sistema e ajustar configurações.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Consulta base para eventos do usuário no período
        base_query = {
            "user_id": ObjectId(user_id),
            "timestamp": {"$gte": cutoff_date}
        }
        
        # Total de eventos
        total_events = await self.db.events.count_documents(base_query)
        
        # Eventos por severidade
        red_events = await self.db.events.count_documents({**base_query, "severity": "red"})
        yellow_events = await self.db.events.count_documents({**base_query, "severity": "yellow"})
        blue_events = await self.db.events.count_documents({**base_query, "severity": "blue"})
        
        # Eventos com feedback
        true_positives = await self.db.events.count_documents({**base_query, "feedback": "true_positive"})
        false_positives = await self.db.events.count_documents({**base_query, "feedback": "false_positive"})
        uncertain = await self.db.events.count_documents({**base_query, "feedback": "uncertain"})
        
        # Taxa de precisão (calculada com base no feedback)
        events_with_feedback = true_positives + false_positives + uncertain
        precision_rate = true_positives / events_with_feedback if events_with_feedback > 0 else 0
        
        return {
            "total_events": total_events,
            "severity": {
                "red": red_events,
                "yellow": yellow_events,
                "blue": blue_events
            },
            "feedback": {
                "true_positive": true_positives,
                "false_positive": false_positives,
                "uncertain": uncertain,
                "total": events_with_feedback
            },
            "precision_rate": precision_rate,
            "period_days": days
        } 