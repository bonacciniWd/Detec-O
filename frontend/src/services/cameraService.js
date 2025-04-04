import api from './api';

// Dados simulados para desenvolvimento/fallback
const mockCameras = [
  {
    id: 'cam1',
    name: 'Entrada Principal',
    url: 'rtsp://admin:admin@192.168.0.100:554/cam/realmonitor?channel=1&subtype=0',
    location: 'Entrada Principal',
    status: 'online',
    resolution: '1920x1080',
    type: 'IP',
    last_event: new Date().toISOString()
  },
  {
    id: 'cam2',
    name: 'Estacionamento',
    url: 'rtsp://admin:admin@192.168.0.101:554/cam/realmonitor?channel=1&subtype=0',
    location: 'Estacionamento',
    status: 'online',
    resolution: '1280x720',
    type: 'IP',
    last_event: new Date(Date.now() - 1800000).toISOString() // 30 minutos atrás
  },
  {
    id: 'cam3',
    name: 'Corredor',
    url: 'rtsp://admin:admin@192.168.0.102:554/cam/realmonitor?channel=1&subtype=0',
    location: 'Corredor Principal',
    status: 'offline',
    resolution: '1280x720',
    type: 'IP',
    last_event: new Date(Date.now() - 86400000).toISOString() // 1 dia atrás
  }
];

// Função para obter todas as câmeras
export const getCameras = async () => {
  try {
    const response = await api.get('/v1/cameras');
    return response.data;
  } catch (error) {
    console.error('Erro ao buscar câmeras:', error);
    
    // Dados simulados para desenvolvimento/fallback
    return mockCameras;
  }
};

// Função para obter uma câmera específica
export const getCamera = async (cameraId) => {
  try {
    const response = await api.get(`/v1/cameras/${cameraId}`);
    return response.data;
  } catch (error) {
    console.error(`Erro ao buscar câmera ${cameraId}:`, error);
    
    // Dados simulados para desenvolvimento/fallback
    const mockCamera = mockCameras.find(c => c.id === cameraId);
    return mockCamera || null;
  }
};

// Função para adicionar uma nova câmera
export const addCamera = async (cameraData) => {
  try {
    const response = await api.post('/v1/cameras', cameraData);
    return response.data;
  } catch (error) {
    console.error('Erro ao adicionar câmera:', error);
    
    // Simulação de adição para desenvolvimento/fallback
    const newCamera = {
      ...cameraData,
      id: `cam${mockCameras.length + 1}`,
      status: 'online',
      last_event: new Date().toISOString()
    };
    
    // Em um ambiente real, o backend seria responsável por salvar isso
    return newCamera;
  }
};

// Função para atualizar uma câmera existente
export const updateCamera = async (cameraId, cameraData) => {
  try {
    const response = await api.put(`/v1/cameras/${cameraId}`, cameraData);
    return response.data;
  } catch (error) {
    console.error(`Erro ao atualizar câmera ${cameraId}:`, error);
    
    // Simulação de atualização para desenvolvimento/fallback
    return {
      ...cameraData,
      id: cameraId,
      updated_at: new Date().toISOString()
    };
  }
};

// Função para excluir uma câmera
export const deleteCamera = async (cameraId) => {
  try {
    const response = await api.delete(`/v1/cameras/${cameraId}`);
    return response.data;
  } catch (error) {
    console.error(`Erro ao excluir câmera ${cameraId}:`, error);
    
    // Simulação de exclusão para desenvolvimento/fallback
    return { success: true, message: 'Câmera excluída com sucesso (simulado)' };
  }
};

// Função para obter o status de todas as câmeras
export const getCamerasStatus = async () => {
  try {
    const response = await api.get('/v1/cameras/status');
    return response.data;
  } catch (error) {
    console.error('Erro ao buscar status das câmeras:', error);
    
    // Dados simulados para desenvolvimento/fallback
    const online = mockCameras.filter(c => c.status === 'online').length;
    const offline = mockCameras.filter(c => c.status === 'offline').length;
    
    return {
      total: mockCameras.length,
      online: online,
      offline: offline,
      error: 0
    };
  }
};

const cameraService = {
  /**
   * Busca a lista de câmeras do usuário logado.
   * @returns {Promise<Array>} Uma promessa que resolve para a lista de câmeras.
   */
  getCameras: async () => {
    try {
      const response = await api.get('/v1/cameras');
      
      // Verificar o formato da resposta do servidor
      if (Array.isArray(response.data)) {
        return response.data;
      } else if (response.data && response.data.items && Array.isArray(response.data.items)) {
        return response.data.items;
      } else {
        console.warn('Formato de resposta inesperado:', response.data);
        return []; // Retorna array vazio se formato for desconhecido
      }
    } catch (error) {
      console.error("Erro ao buscar câmeras:", error.response?.data || error.message);
      throw error; // Re-lança o erro para ser tratado no componente
    }
  },

  /**
   * Adiciona uma nova câmera para o usuário logado.
   * @param {object} cameraData - Dados da câmera { name: string, url: string, location?: string }
   * @returns {Promise<object>} Uma promessa que resolve para o objeto da câmera criada.
   */
  addCamera: async (cameraData) => {
    try {
      const response = await api.post('/v1/cameras', cameraData);
      return response.data;
    } catch (error) {
      console.error("Erro ao adicionar câmera:", error.response?.data || error.message);
      throw error;
    }
  },

  /**
   * Deleta uma câmera específica do usuário logado.
   * @param {string} cameraId - O ID da câmera a ser deletada.
   * @returns {Promise<void>} Uma promessa que resolve quando a câmera é deletada.
   */
  deleteCamera: async (cameraId) => {
    try {
      // A API retorna 204 No Content em sucesso, então não esperamos dados
      await api.delete(`/v1/cameras/${cameraId}`);
    } catch (error) {
      console.error("Erro ao deletar câmera:", error.response?.data || error.message);
      throw error;
    }
  },

  // Adicionar funções para iniciar/parar detecção se necessário no futuro
  startCameraDetection: async (cameraId) => {
    try {
        const response = await api.post(`/v1/cameras/${cameraId}/start`);
        return response.data; // Retorna a mensagem de sucesso
    } catch (error) {
        console.error(`Erro ao iniciar detecção para câmera ${cameraId}:`, error.response?.data || error.message);
        throw error;
    }
  },
  
  stopCameraDetection: async (cameraId) => {
    try {
        const response = await api.post(`/v1/cameras/${cameraId}/stop`);
        return response.data; // Retorna a mensagem de sucesso
    } catch (error) {
        console.error(`Erro ao parar detecção para câmera ${cameraId}:`, error.response?.data || error.message);
        throw error;
    }
  },
};

export default cameraService; 