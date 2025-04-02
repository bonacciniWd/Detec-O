"""
Modulo de deteccao de pessoas, objetos e comportamentos suspeitos.

Este modulo gerencia a deteccao com YOLO, analise de postura e reconhecimento facial.
"""

# Remover importacoes de camera.py que nao existem mais ou foram renomeadas
# from .camera import init_camera_system, start_camera, stop_camera, get_camera_status

# Manter outras importacoes relevantes, se houver (ex: pose_analyzer)
from .pose_analyzer import analyze_hand_movements

# Atualizar __all__ para exportar apenas o que for necessario deste modulo
__all__ = ['analyze_hand_movements']

# Remover bloco duplicado 