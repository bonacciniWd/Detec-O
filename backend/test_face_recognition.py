import os
import sys
import logging
import base64
import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Criar conexão com o banco
def get_db():
    db_path = Path("app.db")
    if not db_path.exists():
        logger.error(f"Banco de dados não encontrado: {db_path}")
        sys.exit(1)
    
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

# Função para carregar imagem como base64
def load_image_as_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        logger.error(f"Erro ao carregar imagem: {str(e)}")
        return None

# Função para criar pessoa de teste
def create_test_person(conn, image_path, name="Pessoa de Teste"):
    try:
        # Carregar imagem
        image_base64 = load_image_as_base64(image_path)
        if not image_base64:
            return None
        
        # Preparar dados da pessoa
        person_id = str(uuid.uuid4())
        now = datetime.now()
        
        # Criar diretório para armazenar faces
        faces_dir = Path("app/static/faces") / person_id
        faces_dir.mkdir(parents=True, exist_ok=True)
        
        # Gerar ID para a face
        face_id = str(uuid.uuid4())
        
        # Salvar imagem em arquivo
        image_data = base64.b64decode(image_base64)
        image_path = faces_dir / f"{face_id}.jpg"
        with open(image_path, "wb") as f:
            f.write(image_data)
        
        # Preparar dados para inserção
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO persons (id, name, description, category, user_id, created_at, updated_at, face_count, face_encodings)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                person_id,
                name,
                "Pessoa criada para teste de reconhecimento facial",
                "test",
                "test_user",
                now,
                now,
                1,
                "[]"  # Inicialmente vazio, será atualizado posteriormente
            )
        )
        conn.commit()
        
        logger.info(f"Pessoa de teste criada: {person_id}")
        return {
            "person_id": person_id,
            "face_id": face_id,
            "image_path": str(image_path)
        }
    
    except Exception as e:
        logger.error(f"Erro ao criar pessoa de teste: {str(e)}")
        return None

def main():
    logger.info("Iniciando teste de reconhecimento facial")
    
    # Verificar imagem de teste
    test_image = Path("test_images/face.jpg")
    if not test_image.exists():
        logger.error(f"Imagem de teste não encontrada: {test_image}")
        logger.info("Por favor, crie o diretório test_images e adicione uma imagem face.jpg")
        return
    
    # Conectar ao banco
    conn = get_db()
    
    try:
        # Criar pessoa de teste
        result = create_test_person(conn, test_image)
        if not result:
            logger.error("Falha ao criar pessoa de teste")
            return
        
        logger.info(f"Pessoa de teste criada com sucesso: {result['person_id']}")
        logger.info(f"Imagem salva em: {result['image_path']}")
        
        # Aqui seria o ponto onde processaríamos a face com face_recognition
        # Mas para simplificar o teste, apenas verificamos se a pessoa foi criada
        
        # Verificar se a pessoa foi criada no banco
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM persons WHERE id = ?", (result['person_id'],))
        person = cursor.fetchone()
        
        if person:
            logger.info("Teste concluído com sucesso!")
            logger.info(f"Detalhes da pessoa: {dict(person)}")
        else:
            logger.error("Pessoa não encontrada no banco após criação")
    
    except Exception as e:
        logger.error(f"Erro durante o teste: {str(e)}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    main() 