import axios from 'axios';

// Criar instância do axios com configuração básica
const api = axios.create({
  baseURL: '',  // Será gerenciado pelo proxy do Vite
  timeout: 15000, // Aumentar o timeout para debug
  headers: {
    'Content-Type': 'application/json'
  }
});

// Interceptador para requisições
api.interceptors.request.use(
  config => {
    // Log da requisição para debug
    // console.log(`Enviando requisição: ${config.method.toUpperCase()} ${config.url}`);
    console.log(`[Interceptor Request] Método: ${config.method.toUpperCase()}, URL Original: ${config.url}`); // Log URL original
    
    // Não modificar headers para requisições de autenticação, definimos diretamente na chamada
    const token = localStorage.getItem('token');
    if (token && !config.url.includes('/auth/')) {
      config.headers['Authorization'] = `Bearer ${token}`;
      console.log(`[Interceptor Request] Token adicionado para URL: ${config.url}`); // Confirma adição
    } else if (!token && !config.url.includes('/auth/')) {
      console.warn(`[Interceptor Request] Token NÃO encontrado para URL: ${config.url}`); // Aviso se token faltar
    } else {
       console.log(`[Interceptor Request] URL de auth ou token já presente. Header não modificado para: ${config.url}`);
    }
    return config;
  },
  error => {
    // console.error('Erro na requisição:', error);
    console.error('[Interceptor Request] Erro:', error);
    return Promise.reject(error);
  }
);

// Interceptor para tratar erros de autenticação (não redireciona mais em caso de erro 401)
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Registra o erro para debug
    console.error("API Error interceptado:", error.response?.status);
    
    // Se for erro 401 (Unauthorized), apenas registra no console
    if (error.response && error.response.status === 401) {
      console.log("Erro 401 detectado - sessão expirada ou token inválido");
      // Não remove o token nem redireciona para permitir refresh rápido
    }
    
    return Promise.reject(error);
  }
);

// Serviço de autenticação simplificado e robusto
export const authService = {
  // Método de login usando form-urlencoded
  login: async (email, password) => {
    try {
      console.log(`Tentando login para: ${email}`);
      
      // Tentar login com a rota /login usando JSON (Rota mais específica para JSON)
      const response = await api.post('/api/auth/login', {
        username: email,
        password: password
      });
      
      console.log('Resposta de login:', response.data);
      
      // Armazenar token
      if (response.data && response.data.access_token) {
        localStorage.setItem('token', response.data.access_token);
        localStorage.setItem('accessToken', response.data.access_token);
      }
      
      return response.data;
    } catch (error) {
      console.error('Erro no login:', error);
      
      // Detalhar erro para debug
      if (error.response) {
        console.error('Detalhes do erro de login:', {
          status: error.response.status,
          data: error.response.data || 'Sem dados',
          headers: error.response.headers
        });
      } else if (error.request) {
        console.error('Erro na requisição - sem resposta:', error.request);
      } else {
        console.error('Erro ao configurar requisição:', error.message);
      }
      
      // Apenas propagar o erro sem redirecionamento
      throw error;
    }
  },
  
  // Login alternativo com JSON
  loginWithJson: async (email, password) => {
    try {
      console.log(`Tentando login com JSON para: ${email}`);
      
      const response = await api.post('/api/auth/login', {
        username: email,
        password: password
      });
      
      // Armazenar token
      if (response.data && response.data.access_token) {
        localStorage.setItem('token', response.data.access_token);
        localStorage.setItem('accessToken', response.data.access_token);
      }
      
      return response.data;
    } catch (error) {
      console.error('Erro no login com JSON:', error);
      throw error;
    }
  },
  
  // Método de login usando form-urlencoded (caso o JSON falhe)
  loginWithForm: async (email, password) => {
    try {
      console.log(`Tentando login com form-urlencoded para: ${email}`);
      
      // Criar form-urlencoded data
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);
      
      // Usar URL direta do backend para evitar problemas
      const backendUrl = 'http://localhost:8000';
      const response = await axios.post(`${backendUrl}/api/auth/token`, formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      
      console.log('Resposta de login form:', response.data);
      
      // Armazenar token
      if (response.data && response.data.access_token) {
        localStorage.setItem('token', response.data.access_token);
        localStorage.setItem('accessToken', response.data.access_token);
      }
      
      return response.data;
    } catch (error) {
      console.error('Erro no login com form:', error);
      throw error;
    }
  },
  
  // Obter dados do usuário atual
  getUser: async () => {
    try {
      const token = localStorage.getItem('token') || localStorage.getItem('accessToken');
      if (!token) {
        throw new Error('Nenhum token encontrado');
      }
      
      console.log('Obtendo dados do usuário com token:', token.substring(0, 15) + '...');
      
      const response = await api.get('/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      console.log('Dados do usuário obtidos:', response.data);
      return response.data;
    } catch (error) {
      console.error('Erro ao obter dados do usuário:', error);
      throw error;
    }
  },
  
  // Logout
  logout: () => {
    console.log('Realizando logout, removendo tokens');
    localStorage.removeItem('token');
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
  },
  
  // Registro de novo usuário
  register: async (userData) => {
    try {
      console.log('Registrando novo usuário:', userData.email);
      const response = await api.post('/api/auth/register', userData);
      console.log('Usuário registrado com sucesso:', response.data);
      return response.data;
    } catch (error) {
      console.error('Erro ao registrar usuário:', error);
      throw error;
    }
  }
};

// Adicionar serviço de mock para endpoints não implementados
// Adicionar esta função após o serviço de autenticação

/* Mocks removidos - usando apenas a API real */

// Interceptador de requisição para endpoints que ainda não existem
const originalRequest = api.request;
api.request = function (config) {
  // Enviar todas as requisições para a API real
  return originalRequest.apply(this, arguments);
};

export default api; 