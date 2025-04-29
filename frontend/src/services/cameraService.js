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
    const response = await api.get('/api/cameras/');
    
    // Verificar o formato da resposta do servidor
    if (Array.isArray(response.data)) {
      return response.data;
    } else if (response.data && response.data.items && Array.isArray(response.data.items)) {
      return response.data.items;
    } else {
      // Verifica se a resposta é HTML
      const isHtmlResponse = typeof response.data === 'string' && 
        (response.data.toLowerCase().startsWith('<!doctype') || 
        response.data.toLowerCase().startsWith('<html'));
      
      if (isHtmlResponse) {
        console.warn('Formato de resposta inesperado: [HTML - não exibido no console]');
      } else {
        console.warn('Formato de resposta inesperado:', response.data);
      }
      
      return []; // Retorna array vazio se formato for desconhecido
    }
  } catch (error) {
    console.error("Erro ao buscar câmeras:", error.response?.data || error.message);
    throw error; // Re-lança o erro para ser tratado no componente
  }
};

// Função para obter uma câmera específica (Removida / no final)
const fetchCameraById = async (cameraId) => {
  try {
    // Remover a barra final para evitar o redirect 307 que perde o Auth Header
    const url = '/api/cameras/' + cameraId; 
    console.log("[Service] Chamando getCamera com URL:", url); 
    const response = await api.get(url);
    return response.data;
  } catch (error) {
    console.error(`Erro ao buscar câmera ${cameraId}:`, error.response?.data || error.message);
    throw error; // Re-lançar erro
  }
};

// Função para adicionar uma nova câmera
export const addCamera = async (cameraData) => {
  try {
    const response = await api.post('/api/cameras/', cameraData);
    return response.data;
  } catch (error) {
    console.error("Erro ao adicionar câmera:", error.response?.data || error.message);
    throw error;
  }
};

// Função para atualizar uma câmera existente (Ajustada)
export const updateCamera = async (cameraId, cameraData) => {
  try {
    // Usar PUT e a rota correta (sem / no final, como definido no backend)
    // Filtrar os dados enviados para corresponder ao CameraUpdate schema (ou o backend lida com isso)
    const updateData = { 
      name: cameraData.name, 
      location: cameraData.location,
      // Adicionar outros campos do formData que podem ser atualizados aqui
      // Ex: username, password (se for diferente de vazio), ip_address, port, connector_type?
      // Cuidado ao permitir atualização de ip_address/port/rtsp_url aqui sem revalidar conexão.
    };
    if (cameraData.password) { // Só enviar senha se o campo não estiver vazio
      updateData.password = cameraData.password;
    }
    // Mapear de volta para ip_address/port se o backend esperar isso em CameraUpdate?
    // Ou ajustar CameraUpdate no backend para aceitar public_host/etc?
    // Por ora, vamos enviar apenas name e location.
    
    const response = await api.put(`/api/cameras/${cameraId}`, updateData); 
    return response.data;
  } catch (error) {
    console.error(`Erro ao atualizar câmera ${cameraId}:`, error.response?.data || error.message);
    throw error;
  }
};

// Função para excluir uma câmera
export const deleteCamera = async (cameraId) => {
  try {
    await api.delete(`/api/cameras/${cameraId}`);
  } catch (error) {
    console.error("Erro ao deletar câmera:", error.response?.data || error.message);
    throw error;
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

// --- Funções para Configurações de Detecção ---

const getCameraDetectionSettings = async (cameraId) => {
  try {
    const url = `/api/cameras/${cameraId}/detection_settings`;
    console.log("[Service] Chamando getCameraDetectionSettings com URL:", url);
    const response = await api.get(url);
    return response.data; // Espera DetectionSettingsResponse do backend
  } catch (error) {
    console.error(`Erro ao buscar configurações de detecção para ${cameraId}:`, error.response?.data || error.message);
    throw error; 
  }
};

const updateCameraDetectionSettings = async (cameraId, settings) => {
  try {
    const url = `/api/cameras/${cameraId}/detection_settings`;
    console.log("[Service] Chamando updateCameraDetectionSettings com URL:", url, " Dados:", settings);
    // Usar PUT conforme definido no backend placeholder
    const response = await api.put(url, settings);
    return response.data; // Espera DetectionSettingsResponse do backend
  } catch (error) {
    console.error(`Erro ao atualizar configurações de detecção para ${cameraId}:`, error.response?.data || error.message);
    throw error; 
  }
};

// --- Funções para Configurações de IA ---

const getCameraAISettings = async (cameraId) => {
  try {
    const url = `/api/cameras/${cameraId}/ai_settings`;
    console.log("[Service] Chamando getCameraAISettings com URL:", url);
    const response = await api.get(url);
    return response.data; // Espera AISettingsResponse do backend
  } catch (error) {
    console.error(`Erro ao buscar configurações de IA para ${cameraId}:`, error.response?.data || error.message);
    throw error; 
  }
};

const updateCameraAISettings = async (cameraId, settings) => {
  try {
    const url = `/api/cameras/${cameraId}/ai_settings`;
    console.log("[Service] Chamando updateCameraAISettings com URL:", url, " Dados:", settings);
    // Usar PUT conforme definido no backend placeholder
    const response = await api.put(url, settings);
    return response.data; // Espera AISettingsResponse do backend
  } catch (error) {
    console.error(`Erro ao atualizar configurações de IA para ${cameraId}:`, error.response?.data || error.message);
    throw error; 
  }
};

// --- Funções para Controle de Processamento ---

const startProcessing = async (cameraId) => {
  try {
    const url = `/api/cameras/${cameraId}/start_processing`;
    console.log("[Service] Chamando startProcessing com URL:", url);
    // Usar POST conforme definido no backend
    const response = await api.post(url);
    return response.data; // Espera ProcessorStatus do backend
  } catch (error) {
    console.error(`Erro ao iniciar processamento para ${cameraId}:`, error.response?.data || error.message);
    throw error; 
  }
};

const stopProcessing = async (cameraId) => {
  try {
    const url = `/api/cameras/${cameraId}/stop_processing`;
    console.log("[Service] Chamando stopProcessing com URL:", url);
    // Usar POST conforme definido no backend
    const response = await api.post(url);
    return response.data; // Espera ProcessorStatus do backend
  } catch (error) {
    console.error(`Erro ao parar processamento para ${cameraId}:`, error.response?.data || error.message);
    throw error; 
  }
};

const getProcessingStatus = async (cameraId) => {
  try {
    const url = `/api/cameras/${cameraId}/processing_status`;
    console.log("[Service] Chamando getProcessingStatus com URL:", url);
    const response = await api.get(url);
    return response.data; // Espera ProcessorStatus do backend
  } catch (error) {
    console.error(`Erro ao buscar status de processamento para ${cameraId}:`, error.response?.data || error.message);
    // Retornar um status padrão de erro/não rodando em caso de falha na API?
    return { camera_id: cameraId, is_running: false, last_error: "Erro ao buscar status" }; 
  }
};

// --- Função para obter Snapshot como Blob ---

const getCameraSnapshotBlob = async (cameraId) => {
  try {
    const url = `/api/cameras/${cameraId}/snapshot`;
    console.log("[Service] Chamando getCameraSnapshotBlob com URL:", url);
    const response = await api.get(url, { 
      responseType: 'blob' // <<< Essencial para receber dados binários
    });
    return response.data; // Retorna o Blob da imagem
  } catch (error) {
    console.error(`Erro ao buscar snapshot blob para ${cameraId}:`, error.response?.data || error.message);
    // Tentar ler o erro do blob se for um erro da API com corpo JSON
    if (error.response && error.response.data instanceof Blob && error.response.data.type === "application/json") {
      try {
        const errJson = await error.response.data.text();
        const errData = JSON.parse(errJson);
        console.error("Detalhe do erro da API (Blob):", errData);
        throw new Error(errData.detail || 'Erro ao buscar snapshot blob');
      } catch (parseError) {
        // Ignora erro de parse e lança o erro original
      }
    }
    throw error; // Re-lança o erro original ou um novo se conseguiu parsear
  }
};

const cameraService = {
  /**
   * Busca a lista de câmeras do usuário logado.
   * @returns {Promise<Array>} Uma promessa que resolve para a lista de câmeras.
   */
  getCameras: async () => {
    try {
      const response = await api.get('/api/cameras/');
      
      // Verificar o formato da resposta do servidor
      if (Array.isArray(response.data)) {
        return response.data;
      } else if (response.data && response.data.items && Array.isArray(response.data.items)) {
        return response.data.items;
      } else {
        // Verifica se a resposta é HTML
        const isHtmlResponse = typeof response.data === 'string' && 
          (response.data.toLowerCase().startsWith('<!doctype') || 
          response.data.toLowerCase().startsWith('<html'));
        
        if (isHtmlResponse) {
          console.warn('Formato de resposta inesperado: [HTML - não exibido no console]');
        } else {
          console.warn('Formato de resposta inesperado:', response.data);
        }
        
        return []; // Retorna array vazio se formato for desconhecido
      }
    } catch (error) {
      console.error("Erro ao buscar câmeras:", error.response?.data || error.message);
      throw error; // Re-lança o erro para ser tratado no componente
    }
  },

  /**
   * Busca detalhes de uma câmera específica.
   * @param {string} cameraId - O ID da câmera.
   * @returns {Promise<object>} Uma promessa que resolve para o objeto da câmera.
   */
  getCamera: fetchCameraById,

  /**
   * Adiciona uma nova câmera para o usuário logado.
   * @param {object} cameraData - Dados da câmera { name: string, url: string, location?: string }
   * @returns {Promise<object>} Uma promessa que resolve para o objeto da câmera criada.
   */
  addCamera: async (cameraData) => {
    try {
      const response = await api.post('/api/cameras/', cameraData);
      return response.data;
    } catch (error) {
      console.error("Erro ao adicionar câmera:", error.response?.data || error.message);
      throw error;
    }
  },

  /**
   * Atualiza dados de uma câmera existente.
   * @param {string} cameraId - ID da câmera.
   * @param {object} cameraData - Dados a serem atualizados.
   * @returns {Promise<object>} Uma promessa que resolve para o objeto da câmera atualizada.
   */
  updateCamera: updateCamera,

  /**
   * Deleta uma câmera específica do usuário logado.
   * @param {string} cameraId - O ID da câmera a ser deletada.
   * @returns {Promise<void>} Uma promessa que resolve quando a câmera é deletada.
   */
  deleteCamera: async (cameraId) => {
    try {
      await api.delete(`/api/cameras/${cameraId}`);
    } catch (error) {
      console.error("Erro ao deletar câmera:", error.response?.data || error.message);
      throw error;
    }
  },

  /**
   * Obtém streams de um dispositivo/câmera específico
   * @param {string} deviceId - ID do dispositivo
   * @returns {Promise<Array>} Lista de streams disponíveis para o dispositivo
   */
  getDeviceStreams: async (deviceId) => {
    try {
      const response = await api.get(`/api/cameras/${deviceId}/streams`);
      return response.data;
    } catch (error) {
      console.error(`Erro ao buscar streams para câmera ${deviceId}:`, error.response?.data || error.message);
      return []; // Retorna array vazio em caso de erro
    }
  },

  // Adicionar funções para iniciar/parar detecção se necessário no futuro
  startCameraDetection: async (cameraId) => {
    try {
        const response = await api.post(`/api/cameras/${cameraId}/start`);
        return response.data; // Retorna a mensagem de sucesso
    } catch (error) {
        console.error(`Erro ao iniciar detecção para câmera ${cameraId}:`, error.response?.data || error.message);
        throw error;
    }
  },
  
  stopCameraDetection: async (cameraId) => {
    try {
        const response = await api.post(`/api/cameras/${cameraId}/stop`);
        return response.data; // Retorna a mensagem de sucesso
    } catch (error) {
        console.error(`Erro ao parar detecção para câmera ${cameraId}:`, error.response?.data || error.message);
        throw error;
    }
  },

  // Adicionar novas funções
  getCameraDetectionSettings: getCameraDetectionSettings,
  updateCameraDetectionSettings: updateCameraDetectionSettings,

  // Adicionar novas funções de IA
  getCameraAISettings: getCameraAISettings,
  updateCameraAISettings: updateCameraAISettings,

  // Adicionar novas funções de controle
  startProcessing: startProcessing,
  stopProcessing: stopProcessing,
  getProcessingStatus: getProcessingStatus,

  // Adicionar nova função de snapshot
  getCameraSnapshotBlob: getCameraSnapshotBlob,
};

export default cameraService; 