"""
Script para criar o usuário administrador inicial.
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from dotenv import load_dotenv
from datetime import datetime

# Carrega variáveis de ambiente
load_dotenv()

# Configuração de criptografia
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_admin_user():
    # Conecta ao MongoDB
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongodb_url)
    db = client.detecao
    users_collection = db.users

    # Verifica se o admin já existe
    admin = await users_collection.find_one({"username": "admin"})
    if admin:
        print("Usuário admin já existe.")
        return

    # Cria o usuário admin
    admin_user = {
        "username": "admin",
        "email": "admin@example.com",
        "hashed_password": pwd_context.hash("admin123"),
        "full_name": "Administrador",
        "disabled": False,
        "role": "admin",
        "created_at": datetime.now()
    }

    await users_collection.insert_one(admin_user)
    print("Usuário admin criado com sucesso!")

if __name__ == "__main__":
    asyncio.run(create_admin_user()) 