"""
Módulo para detecção de objetos perigosos e comportamentos suspeitos usando YOLOv8.
"""

import cv2
import numpy as np
import torch
import logging
from ultralytics import YOLO
from typing import List, Dict, Any, Tuple, Optional
import os
import time
from pathlib import Path

# Configuração de logging
logger = logging.getLogger(__name__)

# Classes de objetos perigosos em COCO/YOLOv8
DANGEROUS_OBJECTS = {
    "knife": {"id": 43, "severity": "high"},
    "gun": {"id": 0, "severity": "critical"}, # Na verdade é "person" no COCO, será substituído pelo modelo customizado
    "scissors": {"id": 76, "severity": "medium"}
}

# Classes de comportamentos suspeitos
SUSPICIOUS_BEHAVIORS = [
    "aggressive_posture",
    "running",
    "fighting",
    "falling_person"
]

class DangerousObjectDetector:
    """
    Classe para detectar objetos perigosos e comportamentos suspeitos em imagens/vídeos.
    Utiliza YOLOv8 para detecção de objetos e rede neural adicional para análise comportamental.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa o detector com configurações específicas.
        
        Args:
            config: Dicionário com as configurações para o detector
                - model_path: Caminho para o modelo YOLOv8 principal
                - behavior_model_path: (Opcional) Caminho para modelo de análise comportamental
                - confidence_threshold: Limiar de confiança para detecções (default: 0.5)
                - device: Dispositivo para inferência ('cuda', 'cpu', etc.)
        """
        self.config = config
        self.model_path = config.get("model_path", "models/yolov8n.pt")
        self.behavior_model_path = config.get("behavior_model_path", None)
        self.confidence_threshold = config.get("confidence_threshold", 0.5)
        self.iou_threshold = config.get("iou_threshold", 0.45)
        self.device = config.get("device", "cuda" if torch.cuda.is_available() else "cpu")
        
        # Carregar modelos
        self._load_models()
        
        # Mapeamento de IDs para nomes de classes (será preenchido ao carregar o modelo)
        self.class_names = {}
        
        # Métricas de desempenho
        self.last_inference_time = 0
        self.total_detections = 0
        self.true_positives = 0  # Para futuras validações
        
        logger.info(f"DangerousObjectDetector inicializado com modelo: {self.model_path}, usando dispositivo: {self.device}")

    def _load_models(self) -> None:
        """Carrega os modelos YOLO e de comportamento"""
        try:
            if not os.path.exists(self.model_path):
                # Tentar caminho relativo
                base_path = Path(__file__).parent.parent.parent
                self.model_path = os.path.join(base_path, self.model_path)
                if not os.path.exists(self.model_path):
                    raise FileNotFoundError(f"Modelo não encontrado em: {self.model_path}")
            
            logger.info(f"Carregando modelo YOLO de: {self.model_path}")
            self.model = YOLO(self.model_path)
            self.class_names = self.model.names
            
            # Verificar se temos algum nome de classe perigosa no modelo
            found_classes = [name for name in self.class_names.values() 
                           if name.lower() in DANGEROUS_OBJECTS.keys()]
            logger.info(f"Classes perigosas encontradas no modelo: {found_classes}")
            
            # Carregar modelo comportamental se especificado
            if self.behavior_model_path:
                logger.info(f"Carregando modelo comportamental de: {self.behavior_model_path}")
                # Implementação do carregamento do modelo comportamental aqui
                # self.behavior_model = ...
            else:
                self.behavior_model = None
                
        except Exception as e:
            logger.error(f"Erro ao carregar modelos: {str(e)}")
            raise

    def detect_objects(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detecta objetos no frame.
        
        Args:
            frame: Imagem em formato numpy array (BGR)
            
        Returns:
            Lista de detecções, cada uma com:
            - bbox: [x1, y1, x2, y2]
            - class_id: ID da classe
            - class_name: Nome da classe
            - confidence: Valor de confiança
            - is_dangerous: Se é um objeto perigoso
            - severity: Nível de severidade (critical, high, medium, low)
        """
        if frame is None or frame.size == 0:
            return []
            
        start_time = time.time()
        detections = []
        
        try:
            # Realizar inferência com YOLO
            results = self.model(frame, verbose=False, conf=self.confidence_threshold, iou=self.iou_threshold)
            
            # Processar resultados
            for det in results[0].boxes.data:
                x1, y1, x2, y2, conf, cls_id = det.cpu().numpy()
                
                # Converter para int para desenho
                x1, y1, x2, y2, cls_id = map(int, [x1, y1, x2, y2, cls_id])
                
                # Obter nome da classe
                class_name = self.class_names.get(cls_id, f"unknown_{cls_id}")
                
                # Verificar se é um objeto perigoso
                is_dangerous = class_name.lower() in DANGEROUS_OBJECTS.keys()
                
                # Determinar severidade
                severity = "low"
                if is_dangerous:
                    severity = DANGEROUS_OBJECTS[class_name.lower()]["severity"]
                
                # Adicionar à lista de detecções
                detections.append({
                    "bbox": [x1, y1, x2, y2],
                    "class_id": cls_id,
                    "class_name": class_name,
                    "confidence": float(conf),
                    "is_dangerous": is_dangerous,
                    "severity": severity
                })
            
            # Atualizar métricas
            self.last_inference_time = time.time() - start_time
            self.total_detections += len(detections)
            
            return detections
            
        except Exception as e:
            logger.error(f"Erro durante detecção: {str(e)}")
            return []

    def detect_behaviors(self, frame: np.ndarray, persons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detecta comportamentos suspeitos em pessoas detectadas.
        
        Args:
            frame: Imagem em formato numpy array (BGR)
            persons: Lista de detecções de pessoas
            
        Returns:
            Lista de comportamentos detectados
        """
        if self.behavior_model is None:
            return []
            
        # Implementação básica para detecção comportamental
        behaviors = []
        
        # Exemplo de implementação básica (sem modelo real)
        for person in persons:
            x1, y1, x2, y2 = person["bbox"]
            
            # Extrair ROI da pessoa
            person_roi = frame[y1:y2, x1:x2].copy()
            
            if person_roi.size == 0:
                continue
                
            # Aqui seria chamado o modelo comportamental real
            # Por enquanto, simulamos uma detecção básica
            
            # Simulação de análise de postura agressiva baseada em relação de aspecto
            h, w = y2 - y1, x2 - x1
            aspect_ratio = h / w if w > 0 else 0
            
            # Se a pessoa está "mais larga que alta", pode indicar postura agressiva
            if 0.5 < aspect_ratio < 1.5:
                behaviors.append({
                    "person_id": id(person),  # Usar ID do objeto como identificador
                    "bbox": person["bbox"],
                    "behavior_type": "aggressive_posture",
                    "confidence": 0.7,
                    "severity": "medium"
                })
        
        return behaviors

    def process_frame(self, frame: np.ndarray) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Processa um frame completo, detectando objetos perigosos e comportamentos.
        
        Args:
            frame: Imagem em formato numpy array (BGR)
            
        Returns:
            Tuple contendo:
            - Lista de detecções de objetos
            - Lista de comportamentos detectados
        """
        # Detectar todos os objetos
        detections = self.detect_objects(frame)
        
        # Filtrar pessoas para análise comportamental
        persons = [det for det in detections if det["class_name"].lower() == "person"]
        
        # Detectar comportamentos em pessoas
        behaviors = self.detect_behaviors(frame, persons)
        
        return detections, behaviors

    def draw_detections(self, frame: np.ndarray, detections: List[Dict[str, Any]], 
                       behaviors: List[Dict[str, Any]] = None) -> np.ndarray:
        """
        Desenha as detecções e comportamentos no frame.
        
        Args:
            frame: Imagem em formato numpy array (BGR)
            detections: Lista de detecções de objetos
            behaviors: Lista de comportamentos detectados
            
        Returns:
            Frame com detecções desenhadas
        """
        result_frame = frame.copy()
        
        # Desenhar detecções de objetos
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            class_name = det["class_name"]
            confidence = det["confidence"]
            is_dangerous = det["is_dangerous"]
            
            # Selecionar cor baseada na severidade
            color = (0, 255, 0)  # Verde para objetos normais
            if is_dangerous:
                severity = det["severity"]
                if severity == "critical":
                    color = (0, 0, 255)  # Vermelho
                elif severity == "high":
                    color = (0, 69, 255)  # Laranja
                elif severity == "medium":
                    color = (0, 215, 255)  # Amarelo
            
            # Desenhar caixa delimitadora
            cv2.rectangle(result_frame, (x1, y1), (x2, y2), color, 2)
            
            # Preparar texto
            text = f"{class_name} {confidence:.2f}"
            
            # Desenhar fundo para o texto
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            cv2.rectangle(
                result_frame, 
                (x1, y1 - text_size[1] - 5), 
                (x1 + text_size[0], y1), 
                color, 
                -1
            )
            
            # Desenhar texto
            cv2.putText(
                result_frame, 
                text, 
                (x1, y1 - 5), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.5, 
                (0, 0, 0), 
                2
            )
        
        # Desenhar comportamentos suspeitos
        if behaviors:
            for behavior in behaviors:
                x1, y1, x2, y2 = behavior["bbox"]
                behavior_type = behavior["behavior_type"]
                confidence = behavior["confidence"]
                
                # Cor vermelha para comportamentos suspeitos
                color = (0, 0, 255)
                
                # Desenhar caixa delimitadora tracejada
                for i in range(x1, x2, 5):
                    cv2.line(result_frame, (i, y1), (i + 3, y1), color, 2)
                    cv2.line(result_frame, (i, y2), (i + 3, y2), color, 2)
                for i in range(y1, y2, 5):
                    cv2.line(result_frame, (x1, i), (x1, i + 3), color, 2)
                    cv2.line(result_frame, (x2, i), (x2, i + 3), color, 2)
                
                # Texto do comportamento
                text = f"{behavior_type} {confidence:.2f}"
                
                # Desenhar fundo para o texto
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                cv2.rectangle(
                    result_frame, 
                    (x1, y1 - text_size[1] - 25), 
                    (x1 + text_size[0], y1 - 20), 
                    color, 
                    -1
                )
                
                # Desenhar texto
                cv2.putText(
                    result_frame, 
                    text, 
                    (x1, y1 - 25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.5, 
                    (255, 255, 255), 
                    2
                )
        
        # Adicionar informações de desempenho
        cv2.putText(
            result_frame,
            f"Inference: {self.last_inference_time*1000:.1f}ms",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )
        
        return result_frame
        
    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas de desempenho do detector"""
        return {
            "last_inference_time": self.last_inference_time,
            "total_detections": self.total_detections,
            "true_positives": self.true_positives
        }

# Função auxiliar para criar instância do detector
def create_detector(config: Dict[str, Any] = None) -> DangerousObjectDetector:
    """
    Cria e retorna uma instância do detector de objetos perigosos.
    
    Args:
        config: Configurações do detector. Se None, usa valores padrão.
        
    Returns:
        Instância do DangerousObjectDetector
    """
    if config is None:
        config = {
            "model_path": "models/yolov8n.pt",
            "confidence_threshold": 0.5,
            "iou_threshold": 0.45,
            "device": "cuda" if torch.cuda.is_available() else "cpu"
        }
    
    return DangerousObjectDetector(config) 