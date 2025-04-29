# Detec-O Frontend

Frontend para o sistema Detec-O de detecção de ameaças.

## Configuração Simplificada

Esta versão do frontend se conecta a um backend simplificado que fornece dados de demonstração.

### Requisitos

- Node.js 16+
- NPM ou Yarn

### Instalação

```bash
# Instalar dependências
npm install
```

### Execução

1. Inicie o backend simplificado:

```bash
# Na pasta backend
cd backend
start_simple_server.bat  # No Windows
# OU
python app/simpleauth.py  # Em sistemas Unix
```

2. Inicie o frontend:

```bash
# Na pasta frontend
npm run dev
```

3. Acesse o frontend em http://localhost:5173

### Credenciais de Acesso

- **Email**: admin@detec-o.com
- **Senha**: admin123

## Funcionalidades

- Dashboard com estatísticas
- Visualização de câmeras
- Lista de eventos
- Gerenciamento de alertas

## Tecnologias Utilizadas

- React.js
- Axios para requisições HTTP
- Vite como bundler
- TailwindCSS para estilização
