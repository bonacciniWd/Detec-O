# Documentação do Banco de Dados PostgreSQL para Detec-O

## Informações de Conexão
- **Tipo de Banco**: PostgreSQL
- **Nome do Banco**: deteco
- **Usuário**: denisbonaccini
- **Senha**: 7ce3284bA (conforme configurado no .env)
- **Host**: localhost (127.0.0.1)
- **Porta**: 5432 (padrão PostgreSQL)
- **String de Conexão**: `postgresql://denisbonaccini:7ce3284bA@localhost:5432/deteco`

## Tabelas Principais

### Tabela `users`
Armazena informações dos usuários do sistema.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INTEGER | Chave primária, auto incremento |
| username | VARCHAR | Nome de usuário, deve ser único |
| email | VARCHAR | Email do usuário, deve ser único |
| hashed_password | VARCHAR | Senha criptografada com bcrypt |
| full_name | VARCHAR | Nome completo (opcional) |
| is_active | BOOLEAN | Se o usuário está ativo |
| is_admin | BOOLEAN | Se o usuário tem privilégios de administrador |
| created_at | TIMESTAMP | Data de criação da conta |
| last_login | TIMESTAMP | Data do último login (opcional) |

### Tabela `cameras`
Armazena informações sobre as câmeras conectadas.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INTEGER | Chave primária, auto incremento |
| name | VARCHAR | Nome da câmera |
| ip_address | VARCHAR | Endereço IP ou URL da câmera |
| model | VARCHAR | Modelo da câmera (opcional) |
| manufacturer | VARCHAR | Fabricante da câmera (opcional) |
| port | INTEGER | Porta para conexão (padrão: 80) |
| username | VARCHAR | Usuário para autenticação na câmera (opcional) |
| password | VARCHAR | Senha para autenticação na câmera (opcional) |
| location | VARCHAR | Localização física da câmera (opcional) |
| owner | VARCHAR | Usuário proprietário da câmera |
| connector_type | VARCHAR | Tipo de conector (onvif, hikvision, etc.) |
| detection_enabled | BOOLEAN | Se a detecção está habilitada |
| detection_confidence | FLOAT | Limiar de confiança para detecção |
| detection_objects | JSON | Lista de objetos a serem detectados |
| detection_zones | JSON | Zonas de detecção na imagem |
| detection_schedule | JSON | Programação para detecção |
| ai_enabled | BOOLEAN | Se a IA está habilitada |
| ai_model_id | VARCHAR | ID do modelo de IA a ser usado |
| ai_confidence_threshold | FLOAT | Limiar de confiança para IA |
| ai_use_gpu | BOOLEAN | Se deve usar GPU para IA |
| ai_enable_tracking | BOOLEAN | Se rastreamento deve ser habilitado |
| notifications_enabled | BOOLEAN | Se notificações estão habilitadas |
| notification_settings | JSON | Configurações de notificação |
| created_at | TIMESTAMP | Data de criação do registro |
| updated_at | TIMESTAMP | Data da última atualização |

### Tabela `ai_models`
Armazena informações sobre modelos de IA disponíveis.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | VARCHAR | Chave primária (UUID) |
| name | VARCHAR | Nome do modelo |
| description | VARCHAR | Descrição do modelo (opcional) |
| file_path | VARCHAR | Caminho para o arquivo do modelo |
| classes | JSON | Lista de classes que o modelo pode detectar |
| size_mb | FLOAT | Tamanho do modelo em MB |
| speed_rating | VARCHAR | Classificação de velocidade do modelo |
| created_at | TIMESTAMP | Data de criação do registro |
| updated_at | TIMESTAMP | Data da última atualização |

### Tabela `camera_ai_settings`
Armazena configurações de IA específicas para cada câmera.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INTEGER | Chave primária, auto incremento |
| camera_id | INTEGER | Referência à tabela cameras (FK) |
| ai_model_id | VARCHAR | Referência à tabela ai_models (FK) |
| confidence_threshold | FLOAT | Limiar de confiança personalizado |
| enabled | BOOLEAN | Se a IA está habilitada para esta câmera |
| target_classes | JSON | Classes-alvo específicas para esta câmera |
| created_at | TIMESTAMP | Data de criação do registro |
| updated_at | TIMESTAMP | Data da última atualização |

### Tabela `detection_events`
Armazena eventos de detecção.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INTEGER | Chave primária, auto incremento |
| camera_id | INTEGER | Referência à tabela cameras (FK) |
| ai_model_id | VARCHAR | Referência à tabela ai_models (FK) |
| event_type | VARCHAR | Tipo de evento (movimento, objeto, pessoa, etc) |
| confidence | FLOAT | Confiança da detecção |
| detected_class | VARCHAR | Classe detectada |
| bounding_box | JSON | Coordenadas da caixa delimitadora [x, y, w, h] |
| image_path | VARCHAR | Caminho para imagem salva (opcional) |
| video_path | VARCHAR | Caminho para vídeo salvo (opcional) |
| timestamp | TIMESTAMP | Data e hora do evento |

## Usuários do Sistema

### Usuário Administrador Padrão
- **Username**: admin
- **Senha**: AdminPassword123!
- **Email**: admin@detec-o.com
- **Papel**: Administrador

## Scripts Importantes

### Script de Inicialização do Banco de Dados
- **Caminho**: `~/Detec-O/initialize_db.py`
- **Função**: Cria as tabelas e insere dados iniciais
- **Uso**: `python -m initialize_db`

### Arquivo de Configuração de Ambiente
- **Caminho**: `~/Detec-O/.env`
- **Conteúdo Relevante**:
  ```
  DATABASE_URL=postgresql://denisbonaccini:7ce3284bA@localhost:5432/deteco
  ADMIN_EMAIL=admin@detec-o.com
  ADMIN_USERNAME=admin
  ADMIN_PASSWORD=AdminPassword123!
  ```

## Arquivos de Modelo SQLAlchemy

### Modelo Camera
- **Caminho**: `~/Detec-O/app/models/camera.py`
- **Classe**: `Camera`
- **Tabela**: `cameras`

### Modelos Principais 
- **Caminho**: `~/Detec-O/app/models/models.py`
- **Classes**: `AIModel`, `CameraAISettings`, `DetectionEvent`, `User`
- **Tabelas**: `ai_models`, `camera_ai_settings`, `detection_events`, `users`

## Operações Comuns de Banco de Dados

### Consultar Usuários
```sql
SELECT * FROM users;
```

### Consultar Câmeras
```sql
SELECT * FROM cameras;
```

### Consultar Eventos
```sql
SELECT * FROM detection_events ORDER BY timestamp DESC LIMIT 100;
```

### Criar Novo Usuário (via SQL)
```sql
INSERT INTO users (username, email, hashed_password, full_name, is_active, is_admin, created_at)
VALUES ('novo_usuario', 'usuario@exemplo.com', 
        '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 
        'Nome Completo', true, false, NOW());
```
Nota: A senha hash acima corresponde a 'password'. Use o método `get_password_hash()` na aplicação para gerar hashes seguros.

### Backup do Banco de Dados
```bash
pg_dump -U denisbonaccini -d deteco > backup_deteco_$(date +%Y%m%d).sql
```

### Restaurar Backup
```bash
psql -U denisbonaccini -d deteco < backup_deteco_20230101.sql
```

## Configuração do Serviço

### Serviço systemd
- **Nome**: deteco-postgres.service
- **Caminho**: `/etc/systemd/system/deteco-postgres.service`
- **Conteúdo**:
  ```
  [Unit]
  Description=Detec-O API com PostgreSQL
  After=network.target

  [Service]
  User=denisbonaccini
  WorkingDirectory=/home/denisbonaccini/Detec-O
  ExecStart=/home/denisbonaccini/Detec-O/backend/venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8080
  Restart=always
  RestartSec=5

  [Install]
  WantedBy=multi-user.target
  ```

### Comandos de Gerenciamento do Serviço
```bash
# Iniciar o serviço
sudo systemctl start deteco-postgres.service

# Parar o serviço
sudo systemctl stop deteco-postgres.service

# Reiniciar o serviço
sudo systemctl restart deteco-postgres.service

# Verificar status
sudo systemctl status deteco-postgres.service

# Ver logs
sudo journalctl -u deteco-postgres.service -f
```

## Solução de Problemas Comuns

### Erro de Conexão com o Banco de Dados
1. Verifique se o PostgreSQL está rodando:
   ```bash
   sudo systemctl status postgresql
   ```
2. Verifique as credenciais no arquivo `.env`
3. Teste a conexão diretamente:
   ```bash
   psql -U denisbonaccini -d deteco -c "SELECT 1;"
   ```

### Erro de Autenticação
1. Verifique se o usuário existe:
   ```bash
   psql -U denisbonaccini -d deteco -c "SELECT username FROM users WHERE username='admin';"
   ```
2. Redefinir a senha do administrador:
   ```bash
   # No Python
   from app.api.auth import get_password_hash
   print(get_password_hash("NovaSenha123!"))
   
   # Depois no PostgreSQL
   psql -U denisbonaccini -d deteco -c "UPDATE users SET hashed_password='[novo_hash]' WHERE username='admin';"
   ```

### Reinicializar o Banco de Dados (em caso extremo)
```bash
# Remover e recriar o banco
sudo -u postgres psql -c "DROP DATABASE deteco;"
sudo -u postgres psql -c "CREATE DATABASE deteco OWNER denisbonaccini;"

# Reinicializar
cd ~/Detec-O
python -m initialize_db
```

## Dependências do Projeto
- **SQLAlchemy**: ORM para interação com o banco de dados
- **psycopg2-binary**: Driver PostgreSQL para Python
- **asyncpg**: Driver PostgreSQL assíncrono
- **FastAPI**: Framework web
- **python-jose**: Implementação JWT
- **passlib**: Hashing de senhas
- **python-dotenv**: Carregamento de variáveis de ambiente
- **email-validator**: Validação de emails
- **uvicorn**: Servidor ASGI

## Histórico de Migração

### Migração de MongoDB para PostgreSQL
- **Data**: 02/05/2024
- **Arquivos Modificados**:
  - `initialize_db.py`: Script de inicialização do banco de dados
  - `app/database.py`: Configuração de conexão com o banco de dados
  - `app/models/camera.py`: Modelo para câmeras
  - `app/models/models.py`: Modelos para usuários, eventos, etc.
  - `src/db/database.py`: Funções para interação com o banco de dados
  - `src/db/cameras_crud.py`: Operações CRUD para câmeras
  - `src/api/auth.py`: Autenticação e autorização
  - `src/main.py`: Configuração principal da aplicação

### Backup do MongoDB (antes da migração)
A configuração antiga do MongoDB foi preservada em:
- `config.json`: URI de conexão ao MongoDB
- Backup das collections do MongoDB (se disponível)

## Próximos Passos e Melhorias

### Melhorias Pendentes
- Implementar migração completa de todos os componentes para PostgreSQL
- Atualizar documentação com novos campos e tabelas conforme necessário
- Implementar sistema de migração de banco de dados (Alembic)
- Adição de índices para melhorar performance em tabelas grandes

Esta documentação deve ser mantida atualizada sempre que houver alterações no esquema ou nas configurações do banco de dados.