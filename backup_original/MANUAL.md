# Manual do Sistema de Detecção de Crimes

## Visão Geral

O Sistema de Detecção de Crimes é uma plataforma de vigilância inteligente que utiliza técnicas avançadas de visão computacional e inteligência artificial para identificar comportamentos suspeitos, detectar armas e gerar alertas de segurança em tempo real. Este sistema foi projetado para funcionar com câmeras IP (como as da Intelbras) ou webcams locais para fins de teste.

## Componentes do Sistema

### Backend (Python)

O backend é responsável por:
- Conectar-se às câmeras e capturar o streaming de vídeo
- Processar as imagens para detectar objetos, armas e comportamentos
- Armazenar eventos de segurança no banco de dados
- Disponibilizar uma API REST para o frontend

### Frontend (React)

O frontend oferece:
- Interface de usuário amigável para visualização do sistema
- Dashboard com estatísticas e indicadores
- Gerenciamento de câmeras (adicionar, editar, iniciar, parar)
- Visualização dos eventos de segurança com filtros

## Requisitos do Sistema

### Hardware
- Processador: Intel Core i5 ou superior (8ª geração ou mais recente)
- RAM: 8GB ou mais (16GB recomendado)
- Armazenamento: 10GB de espaço livre para o software
- GPU: Recomendado para melhor desempenho na detecção (NVIDIA com suporte CUDA)
- Webcam ou câmera IP Intelbras compatível

### Software
- Sistema Operacional: Windows 10/11, Linux Ubuntu 20.04+ ou MacOS
- Python 3.8 ou superior
- Node.js 14.x ou superior e npm
- MongoDB
- CMake (para compilação de dependências)
- Compilador C++ (Visual Studio Build Tools no Windows)

## Instalação e Configuração

### 1. Preparação do Ambiente

#### Instalação do CMake (Windows)
CMake é necessário para compilar algumas dependências Python:

1. Baixe o instalador do site oficial: https://cmake.org/download/
2. Escolha o instalador Windows x64
3. Execute o instalador e selecione a opção de adicionar CMake ao PATH
4. Reinicie o terminal após a instalação

Alternativamente, use o Chocolatey:
```
choco install cmake
```

#### Instalação do Visual Studio Build Tools (Windows)
1. Baixe o instalador: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Selecione "Ferramentas de compilação para C++"
3. Conclua a instalação

#### Instalação do MongoDB
1. Baixe o MongoDB Community Edition: https://www.mongodb.com/try/download/community
2. Instale seguindo as instruções para seu sistema operacional
3. Certifique-se que o serviço do MongoDB está em execução

### 2. Instalação do Backend

1. Clone o repositório do projeto ou extraia os arquivos para um diretório local

2. Abra um terminal e navegue até o diretório do projeto:
```bash
cd caminho/para/sistema-deteccao-crimes
```

3. Instale as dependências Python:
```bash
pip install -r requirements.txt
```

Se encontrar erros com OpenCV ou outras dependências, tente instalar individualmente:
```bash
pip install ultralytics
pip install fastapi uvicorn
pip install motor pymongo
pip install python-multipart python-jose passlib
pip install opencv-python
pip install python-dotenv
```

4. Crie uma cópia do arquivo de ambiente:
```bash
cp .env.example .env
```

5. Edite o arquivo `.env` conforme necessário para seu ambiente

### 3. Instalação do Frontend

1. Navegue até o diretório frontend:
```bash
cd frontend
```

2. Instale as dependências:
```bash
npm install
```

## Configuração das Câmeras

### Usando Webcam Local

1. Abra o arquivo `config.json` e verifique se a configuração da webcam está ativada:
```json
{
  "cameras": [
    {
      "id": "webcam",
      "url": 0,
      "location": "Webcam Local",
      "enabled": true
    }
  ]
}
```

2. O valor `0` na URL se refere à webcam padrão. Se você tiver múltiplas webcams, use `1`, `2`, etc.

### Usando Câmera IP Intelbras

1. Modifique o arquivo `config.json` para incluir sua câmera IP:
```json
{
  "cameras": [
    {
      "id": "camera1",
      "url": "rtsp://admin:senha@192.168.0.100:554/cam/realmonitor?channel=1&subtype=0",
      "location": "Entrada Principal",
      "enabled": true
    }
  ]
}
```

2. Substitua `admin:senha@192.168.0.100` pelas credenciais e IP da sua câmera

## Executando o Sistema

### Modo Desenvolvimento (Sem Backend)

Para testar apenas a interface sem precisar do backend:

1. Certifique-se de que o modo de desenvolvimento está ativado alterando para `DEV_MODE = true` nos seguintes arquivos:
   - `frontend/src/utils/AuthContext.js`
   - `frontend/src/pages/Dashboard.js`
   - `frontend/src/pages/Cameras.js`
   - `frontend/src/pages/Events.js`

2. Inicie o frontend:
```bash
cd frontend
npm start
```

3. Acesse a interface no navegador: http://localhost:3000

4. Use as credenciais de teste:
   - Usuário: admin
   - Senha: admin123

### Modo Completo (Com Backend)

1. Inicie o MongoDB se ainda não estiver em execução

2. Inicie o backend em um terminal:
```bash
python src/main.py
```

Se você configurou uma webcam, uma janela deve abrir mostrando o feed da câmera com as detecções.

3. Em outro terminal, inicie o frontend:
```bash
cd frontend
npm start
```

4. Acesse a interface no navegador: http://localhost:3000

5. Faça login com as credenciais configuradas
   - Padrão: admin / admin123

## Funcionalidades Principais

### 1. Dashboard

O dashboard apresenta uma visão geral do sistema:
- Total de eventos detectados
- Distribuição de tipos de eventos
- Status das câmeras
- Alertas recentes

### 2. Gerenciamento de Câmeras

Na seção Câmeras você pode:
- Visualizar câmeras conectadas
- Iniciar/Parar o monitoramento
- Adicionar novas câmeras
- Editar configurações de câmeras existentes

### 3. Eventos de Segurança

A seção Eventos permite:
- Visualizar todos os eventos detectados
- Filtrar por tipo de evento, data ou câmera
- Ver detalhes de cada detecção
- Exportar relatórios (em desenvolvimento)

### 4. Tipos de Detecções

O sistema é capaz de detectar:
- **Armas**: Facas, pistolas, revólveres
- **Movimentos Suspeitos**: Gestos rápidos em direção a bolsos
- **Permanência Prolongada**: Pessoas ficando muito tempo em um mesmo local
- **Comportamento Errático**: Movimentações estranhas ou padrões suspeitos

## Solução de Problemas

### Problemas com a Instalação

#### CMake não encontrado
- Verifique se o CMake foi instalado corretamente e está no PATH
- Reinicie o terminal após a instalação
- Use `cmake --version` para verificar se está disponível

#### Erros de compilação com OpenCV
- Certifique-se de ter o compilador C++ instalado
- No Windows, instale o Visual Studio Build Tools
- No Linux, instale o pacote build-essential: `sudo apt install build-essential`

#### MongoDB não conecta
- Verifique se o serviço MongoDB está em execução
- Teste a conexão: `mongosh` ou `mongo`
- Verifique as configurações de conexão no arquivo `.env`

### Problemas com a Webcam

#### Webcam não abre
- Verifique se outra aplicação está usando a webcam
- Teste a webcam em outro programa como o aplicativo Câmera do Windows
- Verifique se o índice da webcam está correto (0, 1, etc.)

#### Janela da webcam fecha imediatamente
- Verifique erros no console
- Pode indicar problemas no carregamento do modelo YOLO
- Certifique-se que os arquivos do modelo estão presentes na pasta `models/`

### Problemas com o Frontend

#### Não consegue fazer login
- Em modo de desenvolvimento (`DEV_MODE = true`), use as credenciais admin/admin123
- Em modo completo, verifique se o backend está rodando na porta 8000
- Verifique os logs do console do navegador para erros específicos

## Monitoramento e Manutenção

### Logs do Sistema
Os logs são essenciais para diagnóstico de problemas:
- Logs do backend são exibidos no terminal durante a execução
- Problemas do frontend podem ser vistos no console do navegador (F12)

### Backup do Banco de Dados
Recomenda-se fazer backups periódicos do MongoDB:
```bash
mongodump --db crime_detection_system --out /caminho/para/backup
```

### Atualizações
Para atualizar o sistema:
1. Faça backup do banco de dados e dos arquivos de configuração
2. Puxe as atualizações do repositório ou substitua os arquivos
3. Reinicie o backend e o frontend

## Considerações de Segurança

- Use apenas em redes seguras e privadas
- Altere as senhas padrão em ambiente de produção
- Habilite HTTPS se expor a API para a internet
- Considere a privacidade e aspectos legais da vigilância por vídeo

## Suporte e Contato

Para dúvidas, sugestões ou relato de problemas:
- Abra uma issue no repositório do GitHub
- Entre em contato com a equipe de desenvolvimento

---

Este manual está em constante atualização. Última revisão: MAR/2025