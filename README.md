# Detec-O: Sistema de Detecção por Câmeras

Sistema completo para monitoramento de câmeras e detecção de eventos utilizando inteligência artificial.

## Atualizações Recentes

- **Conectores para Câmeras e DVRs/NVRs:** Implementação de conectores para integração com diferentes dispositivos de vídeo, incluindo suporte para ONVIF e dispositivos Hikvision.
- **Descoberta Automática:** Sistema para descoberta automática de dispositivos na rede local.
- **Routers para Eventos e Câmeras:** Implementação de routers para gerenciamento de câmeras e eventos com suporte a banco de dados real.
- **Suporte para Feedback:** Adição de funcionalidade para que usuários forneçam feedback sobre eventos detectados.
- **APIs para Relatórios:** Implementação de APIs para relatórios e resumos de eventos.

Veja detalhes completos das implementações recentes no documento [Implementações Recentes](docs/implementacoes_recentes.md).

## Sobre o Projeto

O Detec-O é um sistema de monitoramento de câmeras com detecção de objetos e eventos em tempo real. O sistema permite:

- Conectar a diferentes câmeras IP e sistemas de DVR/NVR
- Detectar pessoas, veículos e outros objetos de interesse
- Configurar zonas de detecção específicas em cada câmera
- Receber notificações personalizadas sobre eventos
- Revisar eventos detectados com imagens/vídeos
- Fornecer feedback para melhorar a precisão do sistema

## Tecnologias Utilizadas

### Backend
- FastAPI (Python)
- SQLAlchemy (ORM)
- SQLite/PostgreSQL (Banco de dados)
- ONVIF e APIs proprietárias para conexão com câmeras
- YOLOv8 para detecção de objetos

### Frontend
- React
- TypeScript
- TailwindCSS
- MaterialUI
- React Query

## Estrutura do Projeto

```
detec-o/
├── backend/            # API e serviços em FastAPI
│   ├── app/            # Código principal
│   │   ├── auth/       # Autenticação
│   │   ├── models/     # Modelos de dados
│   │   ├── routers/    # Endpoints API
│   │   └── services/   # Serviços (detectores, conectores)
│   └── tests/          # Testes automatizados
├── frontend/           # Interface de usuário em React
│   ├── public/         # Recursos estáticos
│   ├── src/            # Código fonte
│   │   ├── components/ # Componentes React
│   │   ├── hooks/      # Hooks customizados
│   │   ├── pages/      # Páginas da aplicação
│   │   └── utils/      # Funções utilitárias
│   └── tests/          # Testes do frontend
└── docs/               # Documentação
```

## Instalação

### Pré-requisitos
- Python 3.8+
- Node.js 14+
- PostgreSQL (opcional para produção)

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Conectores de Dispositivos

O sistema suporta múltiplos tipos de dispositivos de vídeo:

### ONVIF
Dispositivos que suportam o protocolo ONVIF, como muitas câmeras IP, DVRs e NVRs.

### Hikvision
Dispositivos Hikvision (DVRs, NVRs e câmeras IP) utilizando a API ISAPI do fabricante.

### Outros Fabricantes
É possível adicionar suporte para outros fabricantes como Dahua, Axis, etc. através 
do framework modular de conectores.

## Descoberta de Dispositivos

O sistema pode automaticamente descobrir dispositivos de vídeo na rede utilizando:

1. **WS-Discovery para ONVIF**: Usando o protocolo padrão para descoberta de dispositivos ONVIF
2. **Escaneamento de Rede**: Verificando portas comumente usadas por dispositivos de vídeo
3. **Métodos específicos de fabricantes**: Como broadcast UDP para dispositivos Hikvision/Dahua

## Próximos Passos

1. **Processamento de Vídeo em Tempo Real**
   - Implementar sistema para visualização de streams em tempo real
   - Adicionar detecção em tempo real nos streams

2. **Armazenamento de Mídia**
   - Desenvolver sistema para armazenamento de imagens e vídeos de eventos
   - Implementar visualização na interface

3. **Melhorias de Interface**
   - Finalizar página de configurações
   - Implementar visualização de múltiplas câmeras
   - Corrigir filtros de eventos

## Status do Projeto (Atualizado)

### Funcionalidades Implementadas:

#### Sistema de Visualização de Câmeras
- **Snapshots Periódicos**: Implementamos um sistema eficiente que exibe snapshots atualizados periodicamente das câmeras conectadas
- **Visualização em Tempo Real**: Suporte para visualização de streams de vídeo em tempo real sob demanda, usando HLS.js
- **Dashboard de Câmeras**: Interface completa para gerenciamento e visualização de múltiplas câmeras com:
  - Modos de visualização em grade ou lista
  - Intervalo de atualização configurável
  - Busca e filtragem por nome ou endereço IP
  - Indicadores de status das câmeras

#### Backend e Conectores
- **Endpoints para Dispositivos**: API completa para gerenciamento de câmeras e seus streams
- **Sistema de Cache**: Implementação de cache para snapshots, otimizando o uso de banda e desempenho
- **Conectores Modulares**: Estrutura extensível para diferentes tipos de câmeras (ONVIF, proprietárias)
- **Abstração de Streams**: Suporte para diferentes protocolos de streaming (RTSP, HTTP, HLS)

#### Interface de Usuário
- **Componentes Responsivos**: Design adaptável para diferentes tamanhos de tela
- **Indicadores Visuais**: Feedback visual para carregamento, erros e status
- **Controles Intuitivos**: Interfaces para pausa/reprodução, expansão e configuração

### Próximos Passos:

1. **Zonas de Detecção**:
   - Implementação da interface para definição de zonas de interesse
   - Sistema de análise para detectar movimento nas zonas definidas

2. **Sistema de Eventos**:
   - Armazenamento de eventos detectados com imagens/vídeos
   - Interface para visualização e filtragem de eventos históricos

3. **Integração Avançada**:
   - Suporte a proxy RTSP para visualização direta no navegador
   - Adição de mais conectores para diferentes fabricantes

## Licença

[MIT](LICENSE) 