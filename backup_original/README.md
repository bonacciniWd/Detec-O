# Sistema de Detecção de Crimes

Sistema de vigilância inteligente que utiliza visão computacional para identificar atividades suspeitas e detectar armas a partir de câmeras de segurança.

## Funcionalidades

- Detecção de armas (facas, pistolas, etc)
- Identificação de movimentos suspeitos
- Monitoramento de permanência prolongada
- Interface web para visualização e gerenciamento
- Suporte para múltiplas câmeras
- Notificações em tempo real
- Armazenamento de eventos para análise posterior

## Requisitos do Sistema

- Python 3.8 ou superior
- MongoDB
- Node.js 14 ou superior (para o frontend)
- OpenCV e suas dependências
- GPU recomendada para melhor performance

## Estrutura do Projeto

```
.
├── frontend/               # Aplicação React para interface do usuário
├── src/                    # Código-fonte do backend
│   ├── api/                # Endpoints da API REST
│   ├── db/                 # Código de acesso ao banco de dados
│   ├── detection/          # Algoritmos de detecção e análise
│   ├── utils/              # Utilitários e helpers
│   └── main.py             # Ponto de entrada da aplicação
├── models/                 # Modelos pré-treinados (YOLO)
├── config.json             # Configurações do sistema
├── .env                    # Variáveis de ambiente
└── requirements.txt        # Dependências Python
```

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/sistema-deteccao-crimes.git
cd sistema-deteccao-crimes
```

2. Instale as dependências do backend:
```bash
pip install -r requirements.txt
```

3. Instale as dependências do frontend:
```bash
cd frontend
npm install
```

4. Configure as variáveis de ambiente copiando o arquivo de exemplo:
```bash
cp .env.example .env
```

5. Edite o arquivo `.env` com suas configurações

## Configuração

### Usando Webcam para Testes

Para testar o sistema usando sua webcam em vez de uma câmera IP:

1. No arquivo `config.json`, certifique-se de que a webcam está configurada:
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

2. O valor `0` na URL indica a webcam padrão do computador. Se você tiver múltiplas webcams, pode usar `1`, `2`, etc.

3. Você pode alternar entre o modo de desenvolvimento (frontend sem backend) e o modo completo alterando o valor de `DEV_MODE` nos seguintes arquivos:
   - `frontend/src/utils/AuthContext.js`
   - `frontend/src/pages/Dashboard.js` 
   - `frontend/src/pages/Cameras.js`
   - `frontend/src/pages/Events.js`

### Conectando a uma Câmera Intelbras

Para conectar a uma câmera IP da Intelbras:

1. Edite o arquivo `config.json` com as informações da sua câmera:
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

2. Substitua `admin:senha@192.168.0.100` pelas credenciais e IP corretos da sua câmera

## Executando o Sistema

1. Inicie o backend:
```bash
python src/main.py
```

2. Em outro terminal, inicie o frontend:
```bash
cd frontend
npm start
```

3. Acesse a interface web em: http://localhost:3000

4. Faça login usando as credenciais de teste:
   - Usuário: admin
   - Senha: admin123

## Configuração de Desenvolvimento

Para testar somente a interface sem o backend:

1. Abra os arquivos mencionados acima e altere `DEV_MODE = true`.
2. Inicie apenas o frontend com `npm start`.
3. A interface usará dados simulados para demonstrar as funcionalidades.

## Contribuição

Contribuições são bem-vindas! Por favor, siga estas etapas:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Faça commit das suas alterações (`git commit -m 'Adiciona nova funcionalidade'`)
4. Faça push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para mais detalhes. 