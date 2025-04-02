# Detec-o: Sistema de Detecção por Câmera

O Detec-o é um sistema moderno para gerenciamento de câmeras, detecção de objetos e pessoas, com notificações em tempo real e controle avançado de configurações.

## Principais Recursos

- **Interface Moderna**: UI intuitiva baseada em Tailwind CSS.
- **Detecção Inteligente**: Configurações para minimizar falsos positivos.
- **Sistema de Feedback**: Similar ao Veesion, permite marcar eventos como verdadeiros/falsos positivos.
- **Visualização Avançada**: Visualização de detecções com destaque para os objetos identificados.
- **Acessibilidade**: Menu de acessibilidade para aumentar fonte, contraste e outras opções.
- **API RESTful**: Backend em Python/FastAPI para processamento de vídeo.

## Estrutura do Projeto

```
Detec-o/
├── backend/         # API FastAPI para processamento e detecção
├── frontend/        # Interface React com Vite
├── docker/          # Arquivos Docker para implantação
└── README.md        # Este arquivo
```

## Tecnologias Utilizadas

### Frontend
- React 18
- Vite
- Tailwind CSS
- React Router 6
- Axios

### Backend
- FastAPI
- MongoDB
- OpenCV
- PyTorch (YOLOv5)

## Configuração do Ambiente

### Pré-requisitos
- Node.js 18+ e npm
- Python 3.9+
- MongoDB
- (Opcional) Docker e Docker Compose

### Instalação e Execução

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

O frontend estará disponível em `http://localhost:5173`.

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

O backend estará disponível em `http://localhost:8080`.

## Uso

1. Acesse a interface em `http://localhost:5173`
2. Faça login ou registre uma nova conta
3. Adicione câmeras (RTSP, HTTP, arquivos locais)
4. Configure os parâmetros de detecção
5. Inicie o monitoramento

## Configuração de Detecção

Você pode configurar diversos parâmetros para cada câmera:

- **Limiar de Confiança**: Aumentar para reduzir falsos positivos.
- **Sensibilidade de Movimento**: Ajustar para diferentes ambientes.
- **Classes de Objetos**: Selecionar quais tipos de objetos detectar.
- **Intervalo Entre Detecções**: Evitar múltiplas notificações para o mesmo evento.

## Acessibilidade

O sistema inclui um painel de acessibilidade com:

- Ajuste de tamanho de fonte
- Modos de alto contraste
- Opção de redução de movimento
- Destaque de foco para navegação por teclado
- Modo monocromático

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.

## Contato

Para suporte ou dúvidas, entre em contato através das issues do projeto. 