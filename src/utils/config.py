"""
Módulo para gerenciamento de configurações da aplicação.

Permite carregar configurações de arquivos JSON e variáveis de ambiente.
"""

import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configurar logger
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

def get_project_root():
    """Retorna o diretório raiz do projeto."""
    current_file = Path(__file__)
    # Vai até src/utils, depois sobe dois níveis para chegar na raiz
    return current_file.parent.parent.parent

def load_config():
    """
    Carrega configurações do arquivo JSON e variáveis de ambiente.
    
    Returns:
        dict: Configurações carregadas
    """
    try:
        config_path = os.path.join(get_project_root(), 'config.json')
        logger.info(f"Carregando configurações de {config_path}")
        
        if not os.path.exists(config_path):
            logger.warning(f"Arquivo de configuração não encontrado: {config_path}")
            return {}
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # Sobrescrever com variáveis de ambiente quando disponíveis
        if os.environ.get('MONGO_URI'):
            config['mongo_uri'] = os.environ.get('MONGO_URI')
        
        if os.environ.get('DB_NAME'):
            config['db_name'] = os.environ.get('DB_NAME')
            
        if os.environ.get('PORT'):
            config['api']['port'] = int(os.environ.get('PORT'))
            
        if os.environ.get('JWT_SECRET'):
            config['api']['jwt_secret'] = os.environ.get('JWT_SECRET')
        
        return config
    except Exception as e:
        logger.error(f"Erro ao carregar configurações: {str(e)}")
        return {}

def get_cameras():
    """
    Retorna a lista de câmeras configuradas.
    
    Returns:
        list: Lista de configurações de câmeras
    """
    config = load_config()
    return config.get('cameras', []) 