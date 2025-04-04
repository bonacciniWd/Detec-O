# Documentação do Projeto Detec-O

## Resumo das Últimas Alterações

### Alterações em 06/04/2024
1. **Melhorias no Sistema de Autenticação**:
   - Unificação dos sistemas de autenticação com o principal em `context/AuthContext.jsx`
   - Autenticação mais robusta com suporte a múltiplos formatos de API e endpoints
   - Implementação de compatibilidade com diversos formatos de token (`token`, `accessToken`)
   - Correção de problemas de navegação após login/logout

2. **Dashboard de Câmeras**:
   - Implementação completa do `CameraDashboard.jsx` com visualização em grid e lista
   - Adição de filtros por nome e status de câmeras
   - Suporte para visualização de streams de câmeras utilizando HLS.js
   - Indicadores visuais de status das câmeras

3. **Melhorias de Acessibilidade**:
   - Implementação do componente `AccessibilityMenu.jsx` com múltiplas opções:
     - Controle de tamanho de fonte (pequeno, normal, grande, extra-grande)
     - Ajustes de contraste (normal, alto, invertido)
     - Opções de redução de animações
     - Destaque de foco do teclado
     - Modo monocromático
   - Persistência das configurações de acessibilidade via localStorage

4. **Configurações do Frontend**:
   - Criação e otimização do `vite.config.js` para build mais eficiente
   - Configuração adequada para geração de assets compatíveis com o ambiente de produção
   - Animações em Lottie para feedback visual melhorado

5. **Dashboard Aprimorado**:
   - Implantação de dashboard analítico com múltiplas visualizações
   - Interface organizada em abas: Visão Geral, Eventos e Zonas de Detecção
   - Gráficos implementados: linha do tempo, distribuição por severidade, eventos por zona, tipos de eventos por hora
   - Indicadores de performance como taxa de precisão global
   - Sistema de filtragem por períodos de tempo (24h, 7d, 30d)
   - Instalação e configuração da biblioteca Recharts para visualizações de dados

6. **Implementação de Zonas de Detecção**:
   - Adição do componente DetectionSettings nas configurações de câmera
   - Interface para desenho de polígonos definindo zonas de interesse
   - Funcionalidade para adicionar, editar e remover zonas
   - Documentação de uso para zonas de detecção

### Alterações em 04/04/2024
1. **Criação do API Simulado**:
   - Criação do arquivo `api_fixed.py` que implementa endpoints simulados para autenticação, eventos, câmeras e configurações
   - Implementação de token de autenticação compatível com o frontend (`authToken` e `access_token`)
   - Adição de suporte a rotas com e sem trailing slash

2. **Configuração do Nginx**:
   - Configuração do Nginx como proxy reverso para direcionar requisições entre frontend e backend
   - Configuração de SSL com certificados Let's Encrypt
   - Otimização para servir arquivos estáticos do frontend
   - Correção de MIME types para JavaScript (application/javascript)

3. **Limpeza e Organização**:
   - Remoção de arquivos desnecessários para pasta `old_files` na VPS
   - Organização de arquivos locais obsoletos em `obsolete_files/`
   - Backup do arquivo principal `api_fixed.py` antes de qualquer alteração

### Alterações Anteriores
1. **Deploy Inicial**:
   - Configuração do ambiente na VPS
   - Deploy do frontend (React) e backend (FastAPI)
   - Configuração inicial do serviço systemd

## Informações de Acesso

### VPS
- Servidor: detec-o.com.br (hostname: srv778922)
- Usuários:
  - `root@detec-o.com.br` (usuário com privilégios administrativos)
  - `denisbonaccini@detec-o.com.br` (usuário normal, proprietário dos arquivos do projeto)

### Estrutura de Diretórios
- Frontend: `/home/denisbonaccini/Detec-O/frontend/`
- Backend: `/home/denisbonaccini/Detec-O/backend/`
- Modelos: Diretório `models/` na raiz do projeto (não em `backend/app/models/` que contém os modelos de dados)

## Componentes do Sistema

### Sistema de Autenticação
- **Arquivo principal**: `frontend/src/context/AuthContext.jsx`
- **Funcionalidades**:
  - Login com suporte a múltiplos endpoints (`/auth/token` e `/api/v1/auth/login`)
  - Armazenamento de tokens em vários formatos para compatibilidade
  - Gestão de estado do usuário autenticado
  - Persistência de sessão via localStorage
  - Redirecionamento inteligente pós-login e logout

### Componentes React Principais
- **MainLayout.jsx**: Layout principal da aplicação com menu lateral e topo
- **AccessibilityMenu.jsx**: Menu flutuante com opções de acessibilidade
- **CameraDashboard.jsx**: Dashboard para visualização e gerenciamento de câmeras
- **EventsList.jsx**: Lista de eventos detectados com filtragem

### Sistema de Visualização de Câmeras
- **Componentes de Visualização**:
  - `CameraSnapshot`: Exibição de snapshots com atualização periódica
  - `CameraStream`: Visualização de streams de vídeo em tempo real (usando HLS.js)
  - `StreamModal`: Modal para visualização expandida de streams

- **Recursos Implementados**:
  - Visualização em grid ou lista
  - Controle de intervalo de atualização
  - Filtros por nome e status
  - Indicadores visuais de estado das câmeras
  - Stream de vídeo sob demanda

### Conectores para Dispositivos de Vídeo
- **Arquitetura de Conectores**:
  - Estrutura modular baseada em classes abstratas
  - Padrão Factory para criação e gerenciamento
  - Registro dinâmico via decoradores

- **Conectores Implementados**:
  - Conector ONVIF para dispositivos compatíveis
  - Conector Hikvision para dispositivos desta marca

- **Sistema de Descoberta**:
  - Descoberta automática de dispositivos na rede local
  - Métodos para ONVIF, Hikvision e escaneamento genérico

### Dashboard Analítico
- **Arquivo principal**: `frontend/src/pages/DashboardPage.jsx`
- **Frameworks utilizados**: Recharts para visualizações de dados
- **Principais visualizações**:
  - **Cartões de estatísticas**: Contadores e métricas-chave do sistema
  - **Eventos ao longo do tempo**: Gráfico temporal de eventos 
  - **Análise por zona**: Dados compilados por zonas de detecção
  - **Distribuição por severidade**: Visualização proporcional por nível de criticidade
  - **Eventos recentes**: Listagem dos últimos eventos detectados
- **Recursos implementados**:
  - Filtragem por período (24h, 7d, 30d)
  - Sistema de navegação por abas
  - Visualização detalhada por zona
  - Análise de distribuição por tipo de evento e hora

## Modelos Pré-treinados

### Modelos Atuais
- YOLOv8n (modelo leve para detecção de objetos): `models/yolov8n.pt`

### Uso de Modelos
- Os modelos pré-treinados são utilizados para detecção de objetos nas câmeras
- Diferentes câmeras podem utilizar diferentes modelos dependendo do ambiente (interno/externo) e objetivos de detecção
- Os modelos determinam quais classes de objetos podem ser detectadas (pessoas, veículos, animais, etc.)

### Planejamento Futuro para Modelos
- Implementar suporte para múltiplos modelos específicos por câmera
- Permitir configuração de modelo diferente para cada câmera (ex: câmeras externas vs internas)
- Adicionar modelos especializados para diferentes tipos de detecção
- Implementar treinamento incremental ou fine-tuning com dados específicos do cliente

## Configuração do Backend

### API
- Arquivo principal: `/home/denisbonaccini/Detec-O/backend/api_fixed.py`
- Ambiente virtual: `/home/denisbonaccini/Detec-O/backend/venv/`
- Porta: 8080

### Endpoints API
O backend atual fornece dados (simulados e reais) para as seguintes rotas:
- **Autenticação**: 
  - `/auth/token` e `/api/v1/auth/login`
  - `/auth/me` e `/api/v1/auth/me`
- **Dados do Sistema**:
  - `/api/v1/events` - Eventos detectados
  - `/api/v1/cameras` - Informações sobre câmeras
  - `/api/v1/users/{user_id}/settings` - Configurações de usuário
  - `/api/v1/statistics` - Estatísticas do sistema
  - `/api/v1/notifications` - Notificações do sistema
- **Dispositivos de Vídeo**:
  - `/api/v1/connectors/types` - Tipos de conectores disponíveis
  - `/api/v1/devices` - Lista de dispositivos configurados
  - `/api/v1/devices/discover` - Descoberta de dispositivos na rede
  - `/api/v1/devices/{device_id}/snapshot` - Snapshots de câmeras
  - `/api/v1/devices/{device_id}/streams` - Streams disponíveis

### Arquivos Não Utilizados na VPS (podem ser removidos)
- `/home/denisbonaccini/Detec-O/backend/simple_api.py`
- `/home/denisbonaccini/Detec-O/backend/simple_api.py.bak`
- `/home/denisbonaccini/Detec-O/backend/micro_api.py`
- `/home/denisbonaccini/Detec-O/backend/basic_api.py`
- `/home/denisbonaccini/Detec-O/backend/api.py`
- `/home/denisbonaccini/Detec-O/backend/app/main.py.save` (se existir)

### Arquivos Não Utilizados Localmente (podem ser removidos)
- `simple_api.py` (no diretório raiz)
- `temp_routes.py` (no diretório raiz)
- `nginx-config.txt` (no diretório raiz)
- `test_db.py` (usado apenas para testes)
- `start_frontend.ps1`, `start_backend.ps1`, `start_system.ps1` (scripts de inicialização que podem ser mantidos se forem úteis)

### Serviço Systemd
- Nome do serviço: `deteco-api`
- Arquivo de configuração: `/etc/systemd/system/deteco-api.service`
- Logs: `journalctl -u deteco-api`

## Configuração do Frontend

### Build e Deploy
- Ferramenta de build: Vite
- Configuração: `frontend/vite.config.js`
- Diretório de produção: `/home/denisbonaccini/Detec-O/frontend/dist/`

### Configuração de Câmeras
- Classes de objetos detectáveis:
  - Pessoas
  - Veículos
  - Animais
  - Pássaros
  - Gatos
  - Cães
  - Bicicletas
  - Motos
- Opções de configuração por câmera:
  - Limiares de confiança
  - Zonas de detecção
  - Seleção de modelo pré-treinado a ser utilizado
  - Notificações por tipo de detecção

### Problemas Pendentes
1. Na visualização mobile, ao ajustar os valores dos limiares de confiança nas câmeras, os valores não se atualizam corretamente.
2. A zona de detecção ainda precisa ser implementada (aparece mensagem de "em desenvolvimento").
3. Os filtros de eventos não atualizam os valores da barra.
4. A aba de configurações mostra apenas um spinner infinito.

## Configuração do Nginx

- Arquivo de configuração: `/etc/nginx/sites-available/default`
- O Nginx está configurado como proxy reverso:
  - Frontend: servido a partir de `/home/denisbonaccini/Detec-O/frontend/dist/`
  - Backend API: proxying para `http://127.0.0.1:8080`
  - Certificado SSL: `/etc/letsencrypt/live/detec-o.com.br/fullchain.pem`
- Configurações especiais:
  - MIME types corretos para JavaScript (application/javascript)
  - Caching adequado para arquivos estáticos
  - Redirecionamento HTTP para HTTPS

## Estado Atual e Funcionalidades

### Funcionando
- Login e autenticação com tokens
- Dashboard mostrando eventos e câmeras
- Visualização de câmeras (snapshots e streams)
- Lista de eventos com filtragem
- Menu de acessibilidade com múltiplas opções
- Responsividade para dispositivos móveis

### Em Desenvolvimento
- Zonas de detecção para câmeras
- Persistência de configurações específicas por câmera
- Interface para seleção de modelos por câmera

## Próximos Passos

### Melhorias Backend
1. Implementar armazenamento real de dados em vez de dados simulados
2. Adicionar lógica condicional para mostrar dados de exemplo apenas quando não há dados reais
3. Implementar validação e persistência das configurações de usuário
4. Desenvolver funcionalidades para suporte a mais câmeras, DVRs e NVRs
5. Implementar seleção e carregamento dinâmico de modelos por câmera
6. Adicionar suporte para treinamento contínuo de modelos com novos dados

### Melhorias Frontend
1. Corrigir o problema de atualização dos valores dos limiares na visualização mobile
2. Implementar a funcionalidade de zona de detecção
3. Corrigir os filtros de eventos
4. Completar a implementação da página de configurações
5. Adicionar interface para seleção de modelos por câmera
6. Desenvolver interface para adição e gerenciamento de novas câmeras e dispositivos (DVRs/NVRs)

### Infraestrutura
1. Implementar backup regular dos dados
2. Configurar monitoramento do serviço
3. Implementar rotação de logs
4. Otimizar uso de GPU para inferência com múltiplos modelos

## Comandos Úteis

### Gerenciando o Serviço Backend
```bash
# Reiniciar o serviço
sudo systemctl restart deteco-api

# Verificar status
sudo systemctl status deteco-api

# Ver logs
sudo journalctl -u deteco-api -n 50
```

### Gerenciando o Nginx
```bash
# Testar configuração
sudo nginx -t

# Reiniciar
sudo systemctl restart nginx

# Verificar status
sudo systemctl status nginx

# Ver logs
sudo tail -n 50 /var/log/nginx/error.log
```

### Compilar e Fazer Deploy do Frontend
```bash
# Navegar para o diretório frontend
cd frontend

# Instalar dependências (se necessário)
npm install

# Construir para produção
npm run build

# Enviar para o servidor
scp -r dist/* root@detec-o.com.br:/var/www/detec-o/
```

### Backup e Manutenção

#### Na VPS
```bash
# Backup do arquivo principal da API
ssh root@detec-o.com.br "cp ~/Detec-O/backend/api_fixed.py ~/Detec-O/backend/api_fixed.py.bak"

# Verificar status do serviço
ssh root@detec-o.com.br "systemctl status deteco-api"
``` 