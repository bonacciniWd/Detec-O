"""
Detec-O: Sistema de detecção e monitoramento por câmeras

Este pacote implementa o backend do sistema Detec-O, oferecendo funcionalidades para:
- Gerenciamento de usuários e autenticação
- Conexão com câmeras e dispositivos de gravação
- Detecção de objetos e eventos
- Armazenamento e consulta de eventos
- Configurações de detecção
"""

# Imports importantes para inicialização
from .services.connectors import onvif_connector
from .services.connectors import hikvision_connector

# Versão do sistema
__version__ = "0.1.0" 