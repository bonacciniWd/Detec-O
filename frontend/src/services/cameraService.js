import apiClient from './api';

const cameraService = {
  /**
   * Busca a lista de câmeras do usuário logado.
   * @returns {Promise<Array>} Uma promessa que resolve para a lista de câmeras.
   */
  getCameras: async () => {
    try {
      const response = await apiClient.get('/api/v1/cameras');
      // A API retorna um array diretamente (ajustado no backend)
      return response.data; 
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
      const response = await apiClient.post('/api/v1/cameras', cameraData);
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
      await apiClient.delete(`/api/v1/cameras/${cameraId}`);
    } catch (error) {
      console.error("Erro ao deletar câmera:", error.response?.data || error.message);
      throw error;
    }
  },

  // Adicionar funções para iniciar/parar detecção se necessário no futuro
  startCameraDetection: async (cameraId) => {
    try {
        const response = await apiClient.post(`/api/v1/cameras/${cameraId}/start`);
        return response.data; // Retorna a mensagem de sucesso
    } catch (error) {
        console.error(`Erro ao iniciar detecção para câmera ${cameraId}:`, error.response?.data || error.message);
        throw error;
    }
  },
  
  stopCameraDetection: async (cameraId) => {
    try {
        const response = await apiClient.post(`/api/v1/cameras/${cameraId}/stop`);
        return response.data; // Retorna a mensagem de sucesso
    } catch (error) {
        console.error(`Erro ao parar detecção para câmera ${cameraId}:`, error.response?.data || error.message);
        throw error;
    }
  },
};

export default cameraService; 