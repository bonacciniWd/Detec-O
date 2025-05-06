# Detec-O: Sistema de Detecção por Câmeras

Sistema completo para monitoramento de câmeras e detecção de eventos utilizando inteligência artificial.

## Sobre o Projeto

O Detec-O é um sistema de monitoramento de câmeras com detecção de objetos e eventos em tempo real. O sistema permite:

- Conectar a diferentes câmeras IP via RTSP
- Detectar objetos de interesse (veículos, animais, etc.)
- **Cadastrar pessoas e reconhecê-las nos vídeos (Reconhecimento Facial)**
- Configurar zonas de detecção específicas em cada câmera (Funcionalidade futura)
- Visualizar eventos detectados com informações e snapshots (incluindo a pessoa reconhecida, se aplicável)
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

## Gerenciamento de Pessoas e Reconhecimento Facial (NOVO)

Esta funcionalidade permite cadastrar indivíduos no sistema para que possam ser reconhecidos automaticamente durante o processamento dos vídeos das câmeras.

### Cadastro
- A interface frontend na rota `/pessoas` permite listar, adicionar, editar e remover pessoas.
- Ao adicionar ou editar uma pessoa, é possível definir:
    - Nome
    - Descrição (opcional)
    - Categoria (Padrão, Aluno, Funcionário, Visitante, VIP, Acesso Restrito)
    - Classe/Turma (campo adicional exibido apenas se a categoria for "Aluno")
- O cadastro inicial de uma pessoa requer uma imagem facial.
- É possível adicionar múltiplas imagens faciais para a mesma pessoa (através do botão "Adicionar Face" no card da pessoa).
- O sistema oferece duas formas de fornecer a imagem facial:
    - **Upload de Arquivo:** Selecionar uma foto do dispositivo.
    - **Captura por Webcam:** Um modal dedicado é aberto, exibindo a pré-visualização da câmera com uma moldura oval guia para ajudar no enquadramento do rosto.
- Um modal instrutivo com animação Lottie e dicas de captura é exibido na primeira vez que o usuário acessa a página `/pessoas`.

### Backend e Processamento
- Novas rotas foram adicionadas em `/api/persons/` para gerenciar o CRUD de pessoas e em `/api/persons/{id}/faces` para adicionar faces.
- Novos modelos SQLAlchemy (`Person`, `FaceEmbedding`) e tabelas correspondentes (`persons`, `face_embeddings`) foram criados no banco de dados PostgreSQL.
- Ao cadastrar uma pessoa ou adicionar uma face:
    - A imagem (recebida em base64) é processada no backend.
    - A biblioteca `face_recognition` é utilizada para detectar o rosto e extrair seu *embedding* (representação vetorial).
    - O embedding é armazenado na tabela `face_embeddings` associado à pessoa.
    - Uma imagem de *thumbnail* do rosto detectado é gerada e salva em `api/snapshots/thumbnails/persons/`.
- O modelo `DetectionEvent` foi atualizado com a coluna `detected_person_id` para vincular um evento de detecção a uma pessoa reconhecida.
- (Lógica futura: Durante o processamento do vídeo, os rostos detectados terão seus embeddings comparados com os do banco de dados para realizar o reconhecimento e preencher `detected_person_id` nos eventos.)

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
*   **Gerenciamento de Pessoas:**
    *   **Interface `/pessoas` funcional para CRUD de pessoas e adição de faces.**
    *   **Cadastro via upload de arquivo ou captura por webcam (com modal dedicado e guia oval).**
    *   **Backend armazena dados da pessoa, embeddings faciais (via `face_recognition`) e thumbnails.**
    *   **Exclusão de pessoa remove também o arquivo thumbnail associado.**
    *   (Reconhecimento em tempo real e vinculação a eventos ainda precisam ser implementados no loop de processamento da câmera).

## Próximos Passos Atuais


    *   Implementar atualização completa das Configurações Gerais (`handleSubmit` em `CameraSettings.jsx`).
    *   Documentar port forwarding/DDNS.
    *   Segurança (HTTPS, etc.).
    *   Implementar Live View opcional.

## Dependências Externas

*   **FFmpeg:** Necessário para a funcionalidade de geração de vídeo a partir de snapshots de eventos. O backend espera que o comando `ffmpeg` esteja instalado e acessível no PATH do sistema onde a API está rodando.

## Problemas Conhecidos e Melhorias Futuras

*   **Visualização de Vídeo de Eventos (Erro 401):**
    *   **Problema:** Atualmente, ao tentar visualizar o vídeo de um evento (no modal da página de eventos), ocorre um erro 401 Unauthorized. Isso acontece porque a tag `<video>` não envia o token de autenticação necessário para acessar o endpoint `/api/events/{event_id}/video`.
    *   **Solução Proposta:** Modificar o componente frontend para buscar o vídeo usando `fetch` ou `axios` (incluindo o cabeçalho `Authorization`), receber a resposta como `blob`, gerar uma `URL.createObjectURL()` e usar essa URL temporária como `src` da tag `<video>`.
*   **Refatoração da Exibição de Detalhes do Evento:**
    *   **Problema:** A lógica detalhada de exibição de um evento (incluindo o vídeo) está atualmente implementada dentro de um modal na página `EventsPage.jsx`, tornando o componente extenso. A página dedicada `EventDetail.jsx` não está sendo utilizada para este fim.
    *   **Melhoria Proposta:** Refatorar a aplicação para que o botão "Ver Detalhes" na `EventsPage.jsx` navegue para a rota `/events/:id`, utilizando a página `EventDetail.jsx` para exibir todas as informações do evento, incluindo o vídeo (com a correção do erro 401 aplicada nesta página).

## Licença

[MIT](LICENSE) 

### Notas Importantes

#### Endpoint de Snapshot da Câmera (`GET /api/cameras/{camera_id}/snapshot`)

*   Obter snapshots ao vivo de streams RTSP pode ser lento e propenso a falhas (câmera offline, URL incorreta, etc.), o que pode bloquear o servidor.
*   Para garantir a responsividade da API, este endpoint **retorna uma imagem placeholder** (`api/assets/logo.png`) por padrão.
*   Para solicitar uma tentativa de obter um snapshot *real* e atualizado, adicione o parâmetro de consulta `?force=true` à URL (`GET /api/cameras/{camera_id}/snapshot?force=true`).
*   **Atenção:** Mesmo com `force=true`, a API tentará conectar à câmera algumas vezes com timeouts curtos. A requisição pode levar alguns segundos e ainda pode retornar o placeholder ou um código de erro (503, 504) se a câmera não responder às tentativas. Use `force=true` com moderação, preferencialmente em resposta a ações explícitas do usuário.
*   Certifique-se de que a imagem placeholder exista em `api/assets/logo.png`.

## Guia de Atualização do Frontend na VPS

### Procedimento padrão de atualização

1. **Acesse a VPS via SSH:**
   ```
   ssh denisbonaccini@srv778922
   ```

2. **Navegue até o repositório e atualize o código:**
   ```
   cd ~/Detec-O
   git stash         # Caso haja alterações locais
   git pull origin main
   ```

3. **Compile o frontend:**
   ```
   cd frontend
   npm install       # Atualiza dependências
   npm run build     # Gera arquivos para produção
   ```

4. **Copie os arquivos para o diretório servido pelo NGINX:**
   ```
   sudo cp -r dist/* /var/www/detec-o/
   sudo chown -R www-data:www-data /var/www/detec-o
   ```

5. **Reinicie o NGINX:**
   ```
   sudo service nginx restart
   ```

### Solução de problemas comuns

#### Erro 500 Internal Server Error

Se ocorrer um erro 500 após a atualização:

1. **Verifique a sintaxe da configuração NGINX:**
   ```
   sudo nginx -t
   ```

2. **Verifique os logs de erro:**
   ```
   sudo tail -n 100 /var/log/nginx/error.log
   ```

3. **Restaure para uma versão básica funcionando:**
   ```
   sudo bash -c 'echo "<html><body>Teste básico</body></html>" > /var/www/detec-o/index.html'
   sudo service nginx restart
   ```

4. **Corrija a configuração NGINX se necessário:**
   ```
   sudo nano /etc/nginx/sites-available/default
   ```

   Configuração básica funcional:
   ```
   server {
       listen 80;
       server_name detec-o.com.br;
       return 301 https://$host$request_uri;
   }

   server {
       listen 443 ssl;
       server_name detec-o.com.br;

       ssl_certificate /etc/letsencrypt/live/detec-o.com.br/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/detec-o.com.br/privkey.pem;

       root /var/www/detec-o;
       index index.html;

       location / {
           try_files $uri $uri/ /index.html;
           add_header Cache-Control "no-store, no-cache, must-revalidate";
       }

       location /api/ {
           proxy_pass http://127.0.0.1:8080/api/v1/;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

#### Problemas com dependências do Node.js

Se ocorrerem erros relacionados a dependências durante o build:

1. **Limpe a instalação e reinstale:**
   ```
   rm -rf node_modules
   rm package-lock.json
   npm install
   ```

2. **Certifique-se de usar a versão correta do Node.js:**
   ```
   node -v  # Verifique a versão
   # Use nvm se precisar alternar versões
   ```


