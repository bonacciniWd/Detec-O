# Detec-O: Atualizações Recentes e Planejamento Futuro

Este documento consolida informações sobre as atualizações recentes implementadas no sistema Detec-O, bem como o planejamento para futuras funcionalidades. Também inclui instruções para deploy no VPS.

## 1. Atualizações Recentes

### 1.1 Correções de Interface (UI Fixes)

Foram implementadas correções importantes na interface do usuário para melhorar a experiência:

- **Correção da tela branca durante navegação**: Implementado componente `ScrollToTop` que garante renderização adequada ao alternar entre páginas
- **Eliminação de scroll horizontal**: Adicionado CSS para controlar overflow e garantir que o conteúdo se ajuste à largura da tela
- **Melhorias para dispositivos móveis**: Espaçamento adequado no final das páginas para garantir que o conteúdo não seja coberto em dispositivos móveis
- **Reestruturação de componentes chave**: 
  - Criação de um novo componente `Navbar` mais responsivo
  - Revisão do `MainLayout` para melhor organização de conteúdo
  - Ajustes no `ZoneEditor` para garantir exibição adequada em todas as telas

### 1.2 Reconhecimento Facial

Foi implementada a estrutura inicial para reconhecimento facial:

- **Modelo de pessoa**: Criação da entidade `Person` para armazenar pessoas reconhecíveis
- **Armazenamento de faces**: Suporte para múltiplas imagens faciais por pessoa
- **Endpoints de API**: Rotas para gerenciar pessoas, adicionar faces e realizar reconhecimento

### 1.3 Integração com Câmeras Reais

- **Processador de vídeo**: Implementação do `VideoProcessor` para conectar-se a câmeras ONVIF/Hikvision
- **Detecção de objetos**: Integração com modelos YOLO para processamento de frames
- **Zonas de detecção**: Capacidade de definir áreas específicas para monitoramento

## 2. Planejamento para Próximas Funcionalidades

### 2.1 Rastreamento de Faces Desconhecidas

Esta funcionalidade permitirá ao sistema:

- Detectar, registrar e rastrear automaticamente pessoas desconhecidas
- Correlacionar diferentes aparições da mesma pessoa
- Permitir investigação retroativa após incidentes
- Possibilitar identificação posterior sem perder o histórico

**Estimativa de implementação**: 6-9 dias de desenvolvimento

#### Tabelas de Banco de Dados Necessárias

```sql
-- Tabela para pessoas desconhecidas
CREATE TABLE unknown_persons (
    id TEXT PRIMARY KEY,
    first_seen_at TIMESTAMP NOT NULL,
    last_seen_at TIMESTAMP NOT NULL,
    face_encoding TEXT NOT NULL,
    face_count INTEGER DEFAULT 1,
    identified_as TEXT DEFAULT NULL,
    user_id TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

-- Tabela para aparições de pessoas desconhecidas
CREATE TABLE unknown_person_appearances (
    id TEXT PRIMARY KEY,
    unknown_person_id TEXT NOT NULL,
    camera_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    confidence REAL NOT NULL,
    snapshot_path TEXT NOT NULL,
    bounding_box TEXT NOT NULL,
    FOREIGN KEY(unknown_person_id) REFERENCES unknown_persons(id)
);
```

#### Endpoints de API a Implementar

```
GET /api/v1/unknown-persons
GET /api/v1/unknown-persons/{id}
GET /api/v1/unknown-persons/{id}/appearances
PUT /api/v1/unknown-persons/{id}/identify
```

### 2.2 Visualização de Gravações Passadas

Implementação de funcionalidade para:

- Armazenar gravações de vídeo por períodos configuráveis
- Visualizar gravações de datas/horários específicos
- Pesquisar e filtrar gravações com base em eventos detectados
- Exportar clipes específicos

### 2.3 Integração com Roboflow

- Acesso a modelos pré-treinados para diferentes casos de uso
- Possibilidade de treinar modelos customizados para necessidades específicas
- API simplificada para inferência

## 3. Instruções para Deploy no VPS

### 3.1 Configuração de PostgreSQL

#### Instalação no VPS Hostinger

```bash
# Atualizar o sistema
sudo apt update && sudo apt upgrade -y

# Instalar PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Iniciar e habilitar o serviço
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Acessar o PostgreSQL como usuário postgres
sudo -u postgres psql

# No console PostgreSQL, criar usuário e banco de dados
CREATE USER detec_user WITH PASSWORD 'senha_segura';
CREATE DATABASE detec_db OWNER detec_user;
\q

# Configurar o PostgreSQL para aceitar conexões
sudo nano /etc/postgresql/*/main/postgresql.conf
# Editar a linha: listen_addresses = '*'

sudo nano /etc/postgresql/*/main/pg_hba.conf
# Adicionar ao final: host all all 0.0.0.0/0 md5

# Reiniciar o PostgreSQL
sudo systemctl restart postgresql
```

#### Configuração da Aplicação para Usar PostgreSQL

1. Atualizar o arquivo de configuração em `backend/app/config.py`:

```python
# Configuração do banco de dados
DATABASE_URL = "postgresql://detec_user:senha_segura@localhost/detec_db"
```

2. Instalar dependências do PostgreSQL:

```bash
cd backend
source venv/bin/activate
pip install psycopg2-binary
```

3. Executar script de migração para criar tabelas:

```bash
cd backend
python -m app.migrations.create_tables
```

### 3.2 Deploy das Atualizações Recentes

#### Backend

```bash
# Acessar o diretório do backend no VPS
cd /caminho/para/detec-o/backend

# Ativar ambiente virtual
source venv/bin/activate

# Fazer backup do código atual
cp -r app app_backup_$(date +%Y%m%d)

# Transferir os arquivos atualizados
# (Usar scp, rsync ou git pull, dependendo do método preferido)

# Instalar novas dependências, se houver
pip install -r requirements.txt

# Executar migrações
python -m app.migrations.create_tables

# Reiniciar o serviço
sudo systemctl restart detec-o-backend
```

#### Frontend

```bash
# Acessar o diretório do frontend
cd /caminho/para/detec-o/frontend

# Fazer backup dos arquivos atuais
mkdir -p backup_$(date +%Y%m%d)
cp -r src backup_$(date +%Y%m%d)/

# Transferir os arquivos atualizados
# (Usar scp, rsync ou git pull, dependendo do método preferido)

# Instalar dependências e construir o frontend
npm install
npm run build

# Copiar arquivos para o diretório do servidor web
cp -r build/* /var/www/html/
```

### 3.3 Verificação Pós-Deploy

1. Verificar logs do backend:
```bash
sudo journalctl -u detec-o-backend -f
```

2. Testar os endpoints da API:
```bash
curl http://seu-servidor/api/v1/health
```

3. Verificar a interface de usuário em diferentes navegadores
4. Monitorar o consumo de recursos do sistema:
```bash
htop
```

## 4. Estrutura do Backend Atualizada

```
backend/
├── app/
│   ├── api/
│   │   ├── crud/
│   │   │   ├── person.py      # Operações para pessoas e faces
│   │   │   └── ...
│   │   ├── dependencies/
│   │   ├── models/
│   │   │   ├── models.py      # Modelos SQLAlchemy
│   │   │   ├── person.py      # Schemas Pydantic para pessoas
│   │   │   └── ...
│   │   ├── routers/
│   │   │   ├── persons.py     # Rotas para reconhecimento facial
│   │   │   └── ...
│   │   ├── services/
│   │   │   ├── face_service.py    # Serviço de reconhecimento facial
│   │   │   ├── video_processor.py # Processamento de vídeo
│   │   │   └── ...
│   │   ├── config.py
│   │   └── main.py
│   ├── models/                # Diretório para modelos de IA
│   └── venv/                  # Ambiente virtual Python
```

## 5. Próximos Passos

1. Implementar e testar a funcionalidade de rastreamento de faces desconhecidas
2. Desenvolver a interface para visualização do histórico de visitantes
3. Configurar o sistema de armazenamento para gravações de vídeo
4. Integrar com Roboflow para melhorar a precisão das detecções
5. Realizar testes de carga para verificar desempenho com múltiplas câmeras

## 6. Possíveis Problemas e Soluções

### Desempenho em Servidores com Recursos Limitados

- **Problema**: Alto consumo de CPU/RAM com muitas câmeras
- **Solução**: Implementar processamento em lotes, ajustar intervalo de análise, utilizar resolução mais baixa para processamento

### Armazenamento de Imagens e Vídeos

- **Problema**: Crescimento rápido do uso de disco
- **Solução**: Implementar políticas de retenção, compressão de imagens, armazenamento seletivo baseado em eventos

### Reconhecimento Facial em Condições Adversas

- **Problema**: Baixa precisão em ambientes com pouca luz
- **Solução**: Pré-processamento de imagem, modelos específicos para baixa luminosidade 