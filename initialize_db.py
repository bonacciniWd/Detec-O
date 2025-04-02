"""
Script para inicializar o banco de dados MongoDB com as estruturas necessárias
"""
import os
import sys
import json
import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do banco de dados
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
db_name = os.getenv("DB_NAME", "crime_detection_system")

def initialize_database():
    """Inicializa o banco de dados com as coleções e dados iniciais"""
    try:
        # Conectar ao MongoDB
        client = MongoClient(mongo_uri)
        db = client[db_name]
        
        print(f"Conectado ao banco de dados: {db_name}")
        
        # Criar/verificar coleções
        collections = [
            "users",
            "events",
            "cameras",
            "logs",
            "settings"
        ]
        
        # Verificar se as coleções existem, se não, criar
        existing_collections = db.list_collection_names()
        for collection in collections:
            if collection not in existing_collections:
                db.create_collection(collection)
                print(f"Coleção criada: {collection}")
            else:
                print(f"Coleção já existe: {collection}")
        
        # Adicionar usuário admin se não existir
        if db.users.count_documents({"username": "admin"}) == 0:
            db.users.insert_one({
                "username": "admin",
                "password": "admin123",  # Em produção, deveria ser hash
                "email": "admin@example.com",
                "role": "admin",
                "created_at": datetime.datetime.now(),
                "last_login": None
            })
            print("Usuário admin criado com sucesso")
        else:
            print("Usuário admin já existe")
        
        # Adicionar câmera de exemplo se não existir
        if db.cameras.count_documents({}) == 0:
            db.cameras.insert_one({
                "id": "cam1",
                "url": 0,  # 0 representa a webcam padrão
                "location": "Webcam Principal",
                "enabled": True,
                "created_at": datetime.datetime.now()
            })
            print("Câmera de exemplo adicionada")
        else:
            print("Câmeras já existem")
        
        # Adicionar configurações padrão se não existirem
        if db.settings.count_documents({}) == 0:
            # Carregar configurações do arquivo config.json
            try:
                with open("config.json", "r") as config_file:
                    config = json.load(config_file)
                    db.settings.insert_one(config)
                    print("Configurações padrão adicionadas a partir do config.json")
            except FileNotFoundError:
                print("Arquivo config.json não encontrado, criando configurações padrão")
                db.settings.insert_one({
                    "app_name": "Sistema de Detecção de Crimes",
                    "detection": {
                        "confidence_threshold": 0.4,
                        "target_classes": ["person", "knife", "scissors", "gun"]
                    }
                })
        else:
            print("Configurações já existem")
        
        print("Banco de dados inicializado com sucesso!")
        
    except Exception as e:
        print(f"Erro ao inicializar o banco de dados: {e}")
        sys.exit(1)

if __name__ == "__main__":
    initialize_database() 