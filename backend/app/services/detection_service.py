import asyncio
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import logging
from typing import Dict, Any, List, Optional, Union
import os
import uuid
from pathlib import Path

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
    
    def __init__(self):
        self.db = None
        self.collection = None
        # Cache para armazenar o timestamp da última detecção por câmera/tipo
        self._last_detections: Dict[str, Dict[str, datetime]] = {}
        
    async def initialize(self):
        """Inicializar serviço com conexão ao banco de dados."""
        self.db = await get_database()
        self.collection = self.db.detection_settings
        
    async def create_settings(self, user_id: str, camera_id: Optional[str], settings: DetectionSettingsCreate) -> DetectionSettingsResponse:
        """Cria novas configurações de detecção para um usuário e câmera."""
        # Verificar se já existem configurações para esta câmera
        existing = await self.collection.find_one({
            "user_id": user_id,
            "camera_id": camera_id
        })
        
        if existing:
            # Atualizar configurações existentes
            return await self.update_settings(user_id, camera_id, settings)
        
        # Criar novo documento
        now = datetime.now()
        settings_dict = {
            **settings.dict(),
            "user_id": user_id,
            "camera_id": camera_id,
            "created_at": now,
            "updated_at": now
        }
        
        result = await self.collection.insert_one(settings_dict)
        
        # Recuperar o documento inserido
        inserted = await self.collection.find_one({"_id": result.inserted_id})
        
        if inserted:
            # Converter ObjectId para string
            inserted["id"] = str(inserted["_id"])
            del inserted["_id"]
            return DetectionSettingsResponse(**inserted)
        
        return None
        
    async def get_settings(self, user_id: str, camera_id: Optional[str]) -> Optional[DetectionSettingsResponse]:
        """Obtém configurações de detecção para um usuário e câmera."""
        # Buscar configurações específicas para esta câmera
        settings = await self.collection.find_one({
            "user_id": user_id,
            "camera_id": camera_id
        })
        
        # Se não encontrou, usar configurações globais do usuário
        if not settings and camera_id:
            settings = await self.collection.find_one({
                "user_id": user_id,
                "camera_id": None
            })
            
        if settings:
            # Converter ObjectId para string
            settings["id"] = str(settings["_id"])
            del settings["_id"]
            return DetectionSettingsResponse(**settings)
            
        # Se não encontrou configurações, criar uma nova com valores padrão
        return await self.create_settings(
            user_id, 
            camera_id, 
            DetectionSettingsCreate()
        )
        
    async def update_settings(self, user_id: str, camera_id: Optional[str], settings_update: DetectionSettingsUpdate) -> Optional[DetectionSettingsResponse]:
        """Atualiza configurações de detecção existentes."""
        # Verificar se existem configurações para atualizar
        existing = await self.collection.find_one({
            "user_id": user_id,
            "camera_id": camera_id
        })
        
        if not existing:
            # Criar novas configurações se não existirem
            return await self.create_settings(
                user_id, 
                camera_id, 
                DetectionSettingsCreate(**settings_update.dict(exclude_unset=True))
            )
        
        # Preparar atualização
        update_data = settings_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.now()
        
        # Atualizar documento
        await self.collection.update_one(
            {"_id": existing["_id"]},
            {"$set": update_data}
        )
        
        # Recuperar documento atualizado
        updated = await self.collection.find_one({"_id": existing["_id"]})
        
        if updated:
            # Converter ObjectId para string
            updated["id"] = str(updated["_id"])
            del updated["_id"]
            return DetectionSettingsResponse(**updated)
            
        return None
    
    async def get_camera_preview(self, user_id: str, camera_id: str) -> Optional[str]:
        """
        Obtém o caminho para uma imagem de preview da câmera.
        
        Em ambiente de produção, isso buscaria um frame atual da câmera.
        Para desenvolvimento, usamos uma imagem estática de exemplo.
        """
        # Em um ambiente real, buscar imagem atual da câmera
        # Para desenvolvimento, usar uma imagem de exemplo
        # Verificar diretório de assets estáticos
        static_dir = Path(__file__).parent.parent / "static" / "camera_previews"
        
        # Criar diretório se não existir
        os.makedirs(static_dir, exist_ok=True)
        
        # Caminho para uma imagem de exemplo baseada no ID da câmera
        # Em produção, seria gerado dinamicamente a partir do stream da câmera
        example_file = f"camera_{camera_id[-4:] if len(camera_id) >= 4 else camera_id}.jpg"
        example_path = static_dir / example_file
        
        # Se não tiver um exemplo específico, usar imagem padrão
        if not example_path.exists():
            default_examples = ["example1.jpg", "example2.jpg", "example3.jpg"]
            # Usar hash do camera_id para selecionar um exemplo aleatório mas consistente
            example_index = hash(camera_id) % len(default_examples)
            example_file = default_examples[example_index]
            example_path = static_dir / example_file
            
            # Se ainda não existir, criar uma imagem preta simples (placeholder)
            if not example_path.exists():
                # Em um ambiente real, usaríamos uma biblioteca como Pillow
                # para criar uma imagem preta, mas por simplicidade vamos apenas
                # retornar uma URL para uma imagem placeholder
                return f"/static/camera_previews/placeholder.jpg"
        
        # Retornar caminho relativo da imagem para uso no frontend
        return f"/static/camera_previews/{example_file}"
    
    async def apply_detection_zones(self, frame, camera_id: str, user_id: str):
        """
        Aplica as zonas de detecção configuradas a um frame.
        Apenas objetos dentro das zonas ativas serão detectados.
        
        Em ambiente de produção, isso seria usado pelo algoritmo de detecção.
        """
        settings = await self.get_settings(user_id, camera_id)
        if not settings:
            # Se não há configurações, detectar em todo o frame
            return frame, False
            
        # Verificar se há zonas de detecção definidas
        if not settings.detection_zones or not settings.use_zones_only:
            # Se não há zonas ou não é para usar apenas as zonas, detectar em todo o frame
            return frame, False
            
        # Em uma implementação real, aqui aplicaríamos uma máscara ao frame
        # baseado nas zonas de detecção, para que apenas objetos dentro das
        # zonas fossem detectados
        
        # Por simplicidade, apenas retornamos o frame original e um flag
        # indicando que as zonas devem ser aplicadas
        return frame, True
    
    async def check_object_in_zones(self, detection_result, camera_id: str, user_id: str):
        """
        Verifica se um objeto detectado está dentro de alguma zona de detecção.
        
        Args:
            detection_result: Resultado da detecção com coordenadas (x, y, w, h)
            camera_id: ID da câmera
            user_id: ID do usuário
            
        Returns:
            Tupla (bool, str): (está em zona, nome da zona)
        """
        settings = await self.get_settings(user_id, camera_id)
        if not settings or not settings.detection_zones or not settings.use_zones_only:
            # Se não há configurações ou zonas, considerar como fora de zona
            return True, "Global"
            
        # Extrair coordenadas do objeto detectado (normalizado 0-1)
        # Formato exemplo: {x: 0.2, y: 0.3, width: 0.1, height: 0.2}
        x = detection_result.get("x", 0)
        y = detection_result.get("y", 0)
        w = detection_result.get("width", 0)
        h = detection_result.get("height", 0)
        
        # Pontos do centro do objeto
        center_x = x + w/2
        center_y = y + h/2
        
        # Verificar cada zona
        for zone in settings.detection_zones:
            if not zone.enabled:
                continue
                
            # Verificar se o objeto está dentro desta zona
            if self._point_in_polygon(center_x, center_y, zone.points):
                # Verificar se a classe do objeto é válida para esta zona
                obj_class = detection_result.get("class", "")
                if (not zone.detection_classes or 
                    obj_class in zone.detection_classes):
                    return True, zone.name
                    
        # Se chegou aqui, não está em nenhuma zona habilitada
        return False, None
    
    def _point_in_polygon(self, x: float, y: float, points: List[Dict[str, float]]) -> bool:
        """
        Verifica se um ponto está dentro de um polígono usando o algoritmo ray-casting.
        
        Args:
            x: Coordenada X do ponto
            y: Coordenada Y do ponto
            points: Lista de pontos do polígono [{x: float, y: float}, ...]
            
        Returns:
            bool: True se o ponto estiver dentro do polígono
        """
        if len(points) < 3:
            return False
            
        n = len(points)
        inside = False
        
        p1x, p1y = points[0]["x"], points[0]["y"]
        for i in range(1, n + 1):
            p2x, p2y = points[i % n]["x"], points[i % n]["y"]
            
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
            
        return inside
    
    async def should_process_detection(self, 
                                      user_id: str, 
                                      camera_id: str,
                                      event_type: str,
                                      confidence: float) -> bool:
        """
        Verifica se uma detecção deve ser processada com base nas configurações
        e no intervalo desde a última detecção do mesmo tipo.
        """
        settings = await self.get_settings(user_id, camera_id)
        
        # Verificar se o tipo de evento está habilitado
        if event_type not in settings.enabled_event_types:
            logger.info(f"Evento {event_type} ignorado: tipo não habilitado")
            return False
        
        # Verificar confiança mínima
        if confidence < settings.min_confidence:
            logger.info(f"Evento {event_type} ignorado: confiança ({confidence}) abaixo do mínimo")
            return False
        
        # Verificar intervalo entre detecções
        detection_interval = settings.detection_interval
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
            return "red" if settings.red_events_enabled else "blue"
        
        # Verificar metadados para potenciais ameaças
        if metadata.get("is_weapon") or metadata.get("potential_aggression"):
            return "red" if settings.red_events_enabled else "blue"
            
        # Verificar metadados para situações específicas
        if metadata.get("is_suspicious") or metadata.get("is_potential_threat"):
            return "yellow" if settings.yellow_events_enabled else "blue"
        
        if "time_in_location" in metadata and metadata["time_in_location"] > 60:  # mais de 1 minuto
            if confidence >= settings.red_confidence_threshold:
                return "red" if settings.red_events_enabled else "blue"
            elif confidence >= settings.yellow_confidence_threshold:
                return "yellow" if settings.yellow_events_enabled else "blue"
        
        # Objetos comumente confundidos com armas ou objetos perigosos
        if event_type in OBJECT_SIMILARITY_MAP:
            return "yellow" if settings.yellow_events_enabled else "blue"
        
        # Determinar com base na confiança
        if confidence >= settings.red_confidence_threshold:
            return "red" if settings.red_events_enabled else "blue"
        elif confidence >= settings.yellow_confidence_threshold:
            return "yellow" if settings.yellow_events_enabled else "blue"
        
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
        
        settings = await self.get_settings(user_id, camera_id)
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
        if settings.notification_enabled:
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

# Criar instância global do serviço
detection_service = DetectionService() 