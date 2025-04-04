import axios from 'axios';

// Criar instância do axios com configuração base
const api = axios.create({
  baseURL: '/api', // Base URL para todas as requisições
  timeout: 10000, // Timeout de 10 segundos
  headers: {
    'Content-Type': 'application/json'
  }
});

// Interceptor para adicionar token em todas as requisições
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para tratar respostas de erro (401, 403, etc)
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    // Implementação básica - pode ser expandida conforme necessário
    if (error.response) {
      // Se o erro for 401 (não autorizado), redirecionar para login
      if (error.response.status === 401) {
        console.log('Sessão expirada ou usuário não autenticado');
        // Limpar token e redirecionar (pode ser implementado de forma mais sofisticada)
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        window.location.href = '/login';
      }
      
      // Se for 403 (proibido), mostrar mensagem de acesso negado
      if (error.response.status === 403) {
        console.error('Acesso negado');
      }
    }
    
    return Promise.reject(error);
  }
);

// Métodos específicos para detecção
const apiClient = {
  // Método base para obter URL da API
  getBaseUrl: () => {
    return api.defaults.baseURL;
  },
  
  // Obter configurações de detecção para uma câmera
  getDetectionSettings: async (cameraId) => {
    try {
      const response = await api.get(`/v1/cameras/${cameraId}/settings`);
      return response.data;
    } catch (error) {
      console.error('Erro ao obter configurações de detecção:', error);
      throw error;
    }
  },
  
  // Salvar configurações de detecção para uma câmera
  saveDetectionSettings: async (cameraId, settings) => {
    try {
      const response = await api.put(`/v1/cameras/${cameraId}/settings`, settings);
      return response.data;
    } catch (error) {
      console.error('Erro ao salvar configurações de detecção:', error);
      throw error;
    }
  },
  
  // Obter preview de uma câmera
  getCameraPreview: (cameraId) => {
    return `${api.defaults.baseURL}/v1/cameras/${cameraId}/preview`;
  },
  
  // Exportar as zonas de detecção
  exportDetectionZones: async (cameraId) => {
    try {
      const response = await api.get(`/v1/cameras/${cameraId}/detection-zones/export`);
      return response.data;
    } catch (error) {
      console.error('Erro ao exportar zonas de detecção:', error);
      throw error;
    }
  },
  
  // Importar zonas de detecção
  importDetectionZones: async (cameraId, zonesData) => {
    try {
      const response = await api.post(`/v1/cameras/${cameraId}/detection-zones/import`, zonesData);
      return response.data;
    } catch (error) {
      console.error('Erro ao importar zonas de detecção:', error);
      throw error;
    }
  }
};

export default apiClient; 