
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

async def test_mongodb_connection():
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Obter configurações
    mongo_uri = os.getenv('MONGO_URI')
    db_name = os.getenv('DB_NAME')
    
    print(f"Tentando conectar ao MongoDB...")
    print(f"URI: {mongo_uri}")
    print(f"Database: {db_name}")
    
    try:
        # Criar cliente
        client = AsyncIOMotorClient(mongo_uri)
        
        # Testar conexão
        await client.admin.command('ping')
        
        # Listar databases
        databases = await client.list_database_names()
        print("\nDatabases disponíveis:")
        for db in databases:
            print(f"- {db}")
        
        # Verificar se o banco de dados existe
        if db_name in databases:
            print(f"\nBanco de dados '{db_name}' encontrado!")
            
            # Listar coleções
            db = client[db_name]
            collections = await db.list_collection_names()
            print("\nColeções disponíveis:")
            for collection in collections:
                print(f"- {collection}")
        else:
            print(f"\nBanco de dados '{db_name}' não encontrado!")
        
        print("\nConexão com MongoDB estabelecida com sucesso!")
        
    except Exception as e:
        print(f"\nErro ao conectar ao MongoDB: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_mongodb_connection()) 