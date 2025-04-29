# Detec-O: Sistema de Detecção por Câmeras

Sistema completo para monitoramento de câmeras e detecção de eventos utilizando inteligência artificial.

## Sobre o Projeto

O Detec-O é um sistema de monitoramento de câmeras com detecção de objetos e eventos em tempo real. O sistema permite:

- Conectar a diferentes câmeras IP via RTSP
- Detectar pessoas, veículos e outros objetos de interesse (Funcionalidade futura)
- Configurar zonas de detecção específicas em cada câmera (Funcionalidade futura)
- Visualizar eventos detectados com informações e snapshots
- Fornecer feedback sobre eventos detectados (Funcionalidade futura)

## Tecnologias Utilizadas

### Backend
- Python 3.x
- FastAPI
- SQLAlchemy (ORM)
- PostgreSQL (Banco de dados principal)
- Alembic (Migrações de banco de dados - se aplicável)
- Uvicorn (Servidor ASGI)
- Passlib (Hashing de senhas)
- python-jose (Tokens JWT)
- python-dotenv (Gerenciamento de variáveis de ambiente)
- OpenCV-Python (Para validação RTSP e processamento futuro)

### Frontend
- React (JavaScript)
- Vite (Build tool)
- Axios (Requisições HTTP)
- TailwindCSS (Estilização)
- React Router (Roteamento)
- Context API (Gerenciamento de estado global)

## Estrutura do Projeto

```
detec-o/
├── api/                  # Código da API Backend (FastAPI)
│   ├── db/               # Configuração do banco de dados (SQLAlchemy)
│   ├── models/           # Modelos de dados (SQLAlchemy)
│   ├── routes/           # Endpoints da API (routers FastAPI)
│   ├── schemas/          # Schemas Pydantic (validação de dados)
│   └── security.py       # Funções de segurança e autenticação
├── frontend/             # Código da Interface Frontend (React)
│   ├── public/           # Recursos estáticos
│   ├── src/              # Código fonte React
│   │   ├── components/   # Componentes reutilizáveis
│   │   ├── contexts/     # Contextos React (ex: AuthContext)
│   │   ├── pages/        # Componentes de página (Login, Dashboard, etc.)
│   │   ├── services/     # Serviços de API (axios, authService, etc.)
│   │   └── App.jsx       # Componente principal da aplicação
│   │   └── main.jsx      # Ponto de entrada do React
│   ├── index.html        # HTML principal
│   └── vite.config.js    # Configuração do Vite (inclui proxy para API)
├── .env                  # Arquivo de variáveis de ambiente (NÃO versionado)
├── .gitignore            # Arquivos e pastas ignorados pelo Git
├── create_user.py        # Script para criar usuários manualmente
├── main.py               # Ponto de entrada principal da API FastAPI
├── requirements.txt      # Dependências Python do Backend
└── README.md             # Este arquivo
```

## Instalação e Configuração

### Pré-requisitos
- Python 3.8+ e Pip
- Node.js 16+ e npm (ou yarn)
- PostgreSQL instalado e rodando
- Git

### Configuração do Backend

1.  **Clone o repositório:**
    ```bash
    git clone <url-do-seu-repositorio>
    cd detec-o
    ```

2.  **Crie e ative um ambiente virtual:**
```bash
python -m venv venv
    # No Windows:
    venv\Scripts\activate
    # No Linux/macOS:
    source venv/bin/activate
    ```

3.  **Instale as dependências Python:**
    ```bash
pip install -r requirements.txt
    ```

4.  **Configure o Banco de Dados PostgreSQL:**
    *   Crie um banco de dados PostgreSQL para o Detec-O (ex: `deteco_db`).
    *   Crie um usuário e senha para acessar este banco de dados.

5.  **Crie o arquivo `.env`:**
    *   Na raiz do projeto (`detec-o/`), crie um arquivo chamado `.env`.
    *   Copie o conteúdo de `.env.example` (se existir) ou adicione as seguintes variáveis:

    ```dotenv
    # .env
    DATABASE_URL=postgresql://USUARIO:SENHA@localhost:5432/deteco_db
    SECRET_KEY=SUA_CHAVE_SECRETA_AQUI
    ACCESS_TOKEN_EXPIRE_MINUTES=1440 # Tempo de expiração do token em minutos (ex: 1440 para 24h)

    # Opcional: Configurações de CORS (se necessário além do padrão)
    # CORS_ORIGINS=http://localhost:5173,http://seu-outro-frontend.com
    ```

    *   **Substitua:**
        *   `USUARIO`: Pelo nome de usuário do seu banco PostgreSQL.
        *   `SENHA`: Pela senha do seu usuário do banco PostgreSQL.
        *   `localhost:5432`: Pelo host e porta do seu servidor PostgreSQL, se diferente.
        *   `deteco_db`: Pelo nome do banco de dados que você criou.
    *   **Gere uma `SECRET_KEY` segura:** Use o comando abaixo no terminal e cole o resultado:
        ```bash
        openssl rand -hex 32
        ```
        *(Alternativamente, use um gerador online de chaves seguras)*

6.  **Execute as migrações do banco (se usar Alembic):**
    *   Se o projeto utiliza Alembic para gerenciar migrações de schema:
        ```bash
        alembic upgrade head
        ```
    *   Se não usar Alembic, as tabelas serão criadas automaticamente ao iniciar a API pela primeira vez (verifique `main.py` ou `db.py` por `Base.metadata.create_all(bind=engine)`).

### Configuração do Frontend

1.  **Navegue até a pasta do frontend:**
```bash
cd frontend
    ```

2.  **Instale as dependências Node.js:**
    ```bash
npm install
    # ou se usar yarn:
    # yarn install
    ```

3.  **Configuração do Proxy (Vite):**
    *   O arquivo `vite.config.js` já deve estar configurado com um proxy para redirecionar as chamadas `/api` para o backend FastAPI (geralmente rodando em `http://localhost:8000`). Verifique a seção `server.proxy` neste arquivo se precisar ajustar.

## Executando a Aplicação

1.  **Execute o Backend (API FastAPI):**
    *   Abra um terminal na **raiz do projeto** (`detec-o/`).
    *   Certifique-se de que seu ambiente virtual Python (`venv`) está ativado.
    *   Execute o servidor Uvicorn:
        ```bash
        uvicorn main:app --reload --host 0.0.0.0 --port 8000
        ```
    *   A API estará disponível em `http://localhost:8000`. A documentação interativa (Swagger UI) estará em `http://localhost:8000/docs`.

2.  **Execute o Frontend (React):**
    *   Abra **outro** terminal na pasta `frontend` (`detec-o/frontend/`).
    *   Execute o servidor de desenvolvimento Vite:
        ```bash
        npm run dev
        # ou se usar yarn:
        # yarn dev
        ```
    *   A aplicação React estará acessível em `http://localhost:5173` (ou a porta indicada pelo Vite).

3.  **Acesse a Aplicação:** Abra seu navegador e vá para `http://localhost:5173`.

## Conectando Câmeras Remotas (IMPORTANTE)

Como o backend do Detec-O é projetado para rodar em um servidor central (como uma VPS) e as câmeras/NVRs estarão localizadas nas redes dos clientes, é **essencial** entender como a conexão é estabelecida:

1.  **Necessidade de Acesso Externo:** O backend na sua VPS precisa conseguir iniciar uma conexão com o dispositivo de vídeo (NVR/DVR/Câmera IP) na rede do cliente através da internet.
2.  **Redirecionamento de Porta (Port Forwarding):** Para permitir isso, o cliente **precisa** configurar o roteador da sua rede local para:
    *   Redirecionar (encaminhar) uma **porta externa** (você pode escolher uma, ex: 554, 5554, etc.) para o **endereço IP local** do NVR/DVR/Câmera na rede do cliente.
    *   O redirecionamento deve apontar para a **porta RTSP interna** do dispositivo (geralmente a porta `554`).
3.  **Endereço Público / DDNS:** O cliente precisará fornecer no formulário de adição de câmera:
    *   O **Endereço IP Público** atual da rede dele, OU
    *   Um **Hostname DDNS** (DNS Dinâmico, ex: `meunvr.ddns.net`) que aponte para o IP público atual. Isso é recomendado, pois IPs públicos podem mudar.
    *   A **Porta Externa** que foi configurada no passo de redirecionamento.
    *   O **Caminho RTSP** específico do stream (ex: `/cam/realmonitor?channel=1&subtype=0`).
    *   As **Credenciais RTSP** (usuário/senha), se o stream for protegido.
4.  **Segurança:** Expor portas diretamente para a internet aumenta os riscos de segurança. É **fundamental** que os dispositivos tenham **senhas fortes**. Considere camadas adicionais de segurança como VPNs em implantações de produção.

### Validação RTSP (Temporariamente Desativada)

Para facilitar o desenvolvimento e testes iniciais **sem a necessidade imediata de acesso físico às câmeras remotas**, a validação automática da conexão RTSP que ocorre ao adicionar uma nova câmera foi **temporariamente desativada**.

**Estado Atual do Código:**
*   No arquivo `api/routes/cameras.py`, dentro da função `create_camera`, o bloco de código que utiliza `cv2.VideoCapture(full_rtsp_url)` e verifica `cap.isOpened()` está **comentado**.
*   Isso permite adicionar câmeras à interface usando os dados públicos/DDNS teóricos, mesmo que a conexão real ainda não funcione. A API apenas salva os dados no banco sem tentar conectar.

**ATENÇÃO:** Antes de colocar o sistema em produção ou quando precisar garantir que apenas câmeras realmente acessíveis sejam adicionadas, você **DEVE REATIVAR** a validação RTSP descomentando o bloco correspondente na função `create_camera` em `api/routes/cameras.py`.

## Convenções da API (Barras Finais - Trailing Slashes)

O FastAPI, por padrão, trata URLs com e sem barra final (`/`) de forma específica. Se uma rota é definida no backend como `@router.get("/items")` (sem barra), mas o frontend chama `/api/items/` (com barra), o FastAPI pode emitir um redirecionamento 307 para a URL sem a barra.

**Problema:** Durante este redirecionamento, o cabeçalho `Authorization` contendo o token JWT pode ser perdido, resultando em erros `401 Unauthorized` na requisição redirecionada.

**Convenção Adotada:** Para evitar este problema, as chamadas de API no frontend (nos arquivos de serviço como `cameraService.js`, `eventService.js`, etc.) devem corresponder **exatamente** ao caminho definido no decorator da rota FastAPI correspondente no backend:

*   Se a rota no backend é `@router.post("/")` dentro de um router com prefixo `/cameras`, a chamada no frontend deve ser para `/api/cameras/` (com barra).
*   Se a rota no backend é `@router.get("/{camera_id}")` dentro do mesmo router (sem barra no decorator), a chamada no frontend deve ser para `/api/cameras/{id}` (sem barra).

Verifique sempre a definição da rota no backend ao implementar novas chamadas no frontend.

## Estado Atual das Funcionalidades (Data da Última Atualização)

*   **Adição/Listagem de Câmeras:** Funcional, com validação RTSP local.
*   **Configurações (Geral, Detecção, IA):** Busca e salvamento implementados e persistentes no banco de dados (colunas JSONB).
*   **Processamento Backend (Inicial):**
    *   Consegue conectar a streams RTSP locais.
    *   Carrega modelo YOLOv8 especificado.
    *   Realiza inferência e detecta objetos.
    *   **Salva eventos de detecção relevantes (`detection_events`) no banco.**
    *   **Salva snapshots (`.jpg`) das detecções na pasta `api/snapshots/` e associa o caminho ao evento.**
*   **Controle de Processamento:** APIs para iniciar/parar o processamento por câmera estão funcionais.

## Próximos Passos Atuais

1.  **Visualização de Eventos:**
    *   Implementar API `GET /api/events/` no backend para buscar eventos salvos.
    *   Implementar API no backend para servir arquivos estáticos da pasta `api/snapshots/`.
    *   Atualizar `EventsPage.jsx` (frontend) para buscar e exibir a lista de eventos e seus snapshots.
2.  **Processamento de Vídeo e IA (Refinamento):**
    *   Otimizar loop de processamento (ex: `asyncio`?).
    *   Analisar bounding box para exibição/outras lógicas.
    *   Refinar tratamento de erros.
3.  **Outros:**
    *   Implementar atualização completa das Configurações Gerais (`handleSubmit` em `CameraSettings.jsx`).
    *   Documentar port forwarding/DDNS.
    *   Segurança (HTTPS, etc.).
    *   Implementar Live View opcional.

## Licença

[MIT](LICENSE) 