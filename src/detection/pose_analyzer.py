"""
Módulo para análise de postura e detecção de movimentos suspeitos.

Este módulo implementa a análise de movimentos para detectar comportamentos
potencialmente suspeitos, como movimentos rápidos ou nervosos.
"""

import cv2
import numpy as np
import logging
from datetime import datetime, timedelta

# Configuração do logger
logger = logging.getLogger(__name__)

# Lista de padrões de movimento suspeitos
suspicious_hand_patterns = {
    "rapid_movement": "Movimento rápido detectado",
    "concealing_object": "Possível ocultação de objeto",
    "aggressive_gestures": "Gestos potencialmente agressivos",
    "nervous_movements": "Movimentos nervosos repetitivos"
}

class HandMovementAnalyzer:
    def __init__(self):
        self.prev_frame = None
        self.prev_time = None
        self.movement_history = []
        self.history_size = 30  # Tamanho do histórico de movimentos
        self.movement_threshold = 10000  # Limiar para considerar movimento significativo
        self.std_threshold = 3.0  # Número de desvios padrão para considerar movimento suspeito
        self.repetitive_threshold = 0.05  # Limiar para considerar movimento repetitivo
        
    def analyze_frame(self, frame, detected_objects):
        """
        Analisa os movimentos em um frame para detectar padrões suspeitos
        
        Args:
            frame: Frame atual da câmera
            detected_objects: Lista de objetos detectados pelo YOLO
            
        Returns:
            bool: True se movimento suspeito detectado, False caso contrário
        """
        if frame is None or frame.size == 0:
            return False
            
        # Converter para escala de cinza
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Aplicar blur para reduzir ruído
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        # Inicializar frame anterior se necessário
        if self.prev_frame is None:
            self.prev_frame = gray
            self.prev_time = datetime.now()
            return False
            
        # Calcular diferença entre frames
        frame_delta = cv2.absdiff(self.prev_frame, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Analisar movimentos
        current_time = datetime.now()
        time_diff = (current_time - self.prev_time).total_seconds()
        
        # Calcular quantidade de movimento
        movement_amount = sum(cv2.contourArea(contour) for contour in contours)
        
        # Ignorar movimentos muito pequenos
        if movement_amount < self.movement_threshold:
            return False
            
        # Normalizar movimento pelo tempo
        if time_diff > 0:
            movement_rate = movement_amount / time_diff
        else:
            movement_rate = 0
            
        # Atualizar histórico
        self.movement_history.append(movement_rate)
        if len(self.movement_history) > self.history_size:
            self.movement_history.pop(0)
            
        # Detectar padrões suspeitos
        if self._detect_suspicious_pattern():
            return True
            
        # Atualizar frame anterior
        self.prev_frame = gray
        self.prev_time = current_time
        
        return False
        
    def _detect_suspicious_pattern(self):
        """
        Detecta padrões suspeitos baseado no histórico de movimentos
        
        Returns:
            bool: True se padrão suspeito detectado, False caso contrário
        """
        if len(self.movement_history) < 2:
            return False
            
        # Calcular média e desvio padrão
        mean_movement = np.mean(self.movement_history)
        std_movement = np.std(self.movement_history)
        
        # Detectar movimentos rápidos (acima de N desvios padrão)
        if mean_movement > self.std_threshold * std_movement:
            return True
            
        # Detectar movimentos repetitivos
        if len(self.movement_history) >= 5:
            recent_movements = self.movement_history[-5:]
            if np.std(recent_movements) < mean_movement * self.repetitive_threshold:  # Movimentos muito consistentes
                return True
                
        return False

def analyze_hand_movements(image):
    """
    Analisa os movimentos das mãos em uma imagem para detectar padrões suspeitos
    
    Args:
        image: Imagem contendo a pessoa a ser analisada
        
    Returns:
        dict: Resultado da análise com indicador de suspeito e detalhes
    """
    result = {
        "suspicious": False,
        "details": "",
        "confidence": 0.0
    }
    
    if image.size == 0:
        return result
        
    # Criar analisador se não existir
    if not hasattr(analyze_hand_movements, 'analyzer'):
        analyze_hand_movements.analyzer = HandMovementAnalyzer()
        
    # Analisar frame
    if analyze_hand_movements.analyzer.analyze_frame(image, []):
        result["suspicious"] = True
        result["details"] = suspicious_hand_patterns.get("rapid_movement", "Movimento suspeito detectado")
        result["confidence"] = 0.75
        
    return result 