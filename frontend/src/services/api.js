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

// Interceptor de resposta para tratamento global de erros
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response) {
      // Tratamento específico para erros de autenticação
      if (error.response.status === 401) {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        // Redirecionar para login se necessário
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

// Métodos específicos para API
const apiClient = {
  // Métodos HTTP genéricos
  get: async (url, config) => {
    return api.get(url, config);
  },
  
  post: async (url, data, config) => {
    return api.post(url, data, config);
  },
  
  put: async (url, data, config) => {
    return api.put(url, data, config);
  },
  
  delete: async (url, config) => {
    return api.delete(url, config);
  },
  
  // Atributo para acessar a configuração defaults
  defaults: api.defaults,
  
  // Método base para obter URL da API
  getBaseUrl: () => {
    return api.defaults.baseURL;
  },
  
  // Métodos para gerenciamento de câmeras e dispositivos
  
  // Obter lista de todos os dispositivos
  getDevices: async () => {
    try {
      const response = await api.get('/v1/devices');
      return response.data;
    } catch (error) {
      console.error('Erro ao obter lista de dispositivos:', error);
      throw error;
    }
  },
  
  // Obter detalhes de um dispositivo específico
  getDevice: async (deviceId) => {
    try {
      const response = await api.get(`/v1/devices/${deviceId}`);
      return response.data;
    } catch (error) {
      console.error(`Erro ao obter detalhes do dispositivo ${deviceId}:`, error);
      throw error;
    }
  },
  
  // Obter streams de um dispositivo
  getDeviceStreams: async (deviceId) => {
    try {
      const response = await api.get(`/v1/devices/${deviceId}/streams`);
      return response.data;
    } catch (error) {
      console.error(`Erro ao obter streams do dispositivo ${deviceId}:`, error);
      throw error;
    }
  },
  
  // Atualizar um dispositivo
  updateDevice: async (deviceId, data) => {
    try {
      const response = await api.put(`/v1/devices/${deviceId}`, data);
      return response.data;
    } catch (error) {
      console.error(`Erro ao atualizar dispositivo ${deviceId}:`, error);
      throw error;
    }
  },
  
  // Excluir um dispositivo
  deleteDevice: async (deviceId) => {
    try {
      const response = await api.delete(`/v1/devices/${deviceId}`);
      return response.data;
    } catch (error) {
      console.error(`Erro ao excluir dispositivo ${deviceId}:`, error);
      throw error;
    }
  },
  
  // Descobrir câmeras disponíveis na rede
  discoverCameras: async (options = {}) => {
    try {
      const response = await api.post('/devices/discover', options);
      return response.data;
    } catch (error) {
      console.error('Erro ao descobrir câmeras:', error);
      throw error;
    }
  },
  
  // Conectar a uma câmera específica
  connectCamera: async (cameraData) => {
    try {
      const response = await api.post('/devices/connect', cameraData);
      return response.data;
    } catch (error) {
      console.error('Erro ao conectar à câmera:', error);
      throw error;
    }
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