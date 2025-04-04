"""
Módulo de conectores para DVRs, NVRs e câmeras IP.

Este módulo fornece interfaces e implementações para conectar o sistema Detec-o 
a diferentes tipos de dispositivos de gravação e câmeras em rede.
"""

from .base import BaseConnector, ConnectorError, DeviceInfo, StreamInfo
from .factory import ConnectorFactory, register_connector

__all__ = [
    'BaseConnector',
    'ConnectorError',
    'DeviceInfo',
    'StreamInfo',
    'ConnectorFactory',
    'register_connector',
] 