import apiClient from './api';

/**
 * Serviço para gerenciar eventos de detecção
 */
const eventService = {
  /**
   * Obter a URL base da API
   * @returns {string} URL base da API
   */
  getApiBaseUrl: () => {
    return apiClient.defaults.baseURL;
  },

  /**
   * Buscar eventos com filtros opcionais
   * @param {Object} params - Parâmetros de filtro (dias, câmera, tipo, etc)
   * @returns {Promise<Array>} Lista de eventos
   */
  getEvents: async (params = {}) => {
    try {
      const response = await apiClient.get('/api/v1/events', { params });
      return response.data;
    } catch (error) {
      console.error('Erro ao buscar eventos:', error);
      throw error;
    }
  },

  /**
   * Buscar detalhes de um evento específico
   * @param {string} eventId - ID do evento
   * @returns {Promise<Object>} Detalhes do evento
   */
  getEventDetails: async (eventId) => {
    try {
      const response = await apiClient.get(`/api/v1/events/${eventId}`);
      return response.data;
    } catch (error) {
      console.error(`Erro ao buscar detalhes do evento ${eventId}:`, error);
      throw error;
    }
  },

  /**
   * Enviar feedback sobre um evento (verdadeiro positivo, falso positivo, etc)
   * @param {string} eventId - ID do evento
   * @param {string} feedback - Tipo de feedback ('true_positive', 'false_positive', 'uncertain')
   * @returns {Promise<Object>} Resposta da API
   */
  submitFeedback: async (eventId, feedback) => {
    try {
      const response = await apiClient.post(`/api/v1/events/${eventId}/feedback`, {
        feedback_value: feedback
      });
      return response.data;
    } catch (error) {
      console.error(`Erro ao enviar feedback para evento ${eventId}:`, error);
      throw error;
    }
  },

  /**
   * Buscar estatísticas de eventos (contagens, distribuição, etc)
   * @param {Object} params - Parâmetros de filtro para as estatísticas
   * @returns {Promise<Object>} Estatísticas dos eventos
   */
  getEventStats: async (params = {}) => {
    try {
      const response = await apiClient.get('/api/v1/events/stats', { params });
      return response.data;
    } catch (error) {
      console.error('Erro ao buscar estatísticas de eventos:', error);
      throw error;
    }
  },

  /**
   * Marcar um evento como lido/visualizado
   * @param {string} eventId - ID do evento
   * @returns {Promise<Object>} Resposta da API
   */
  markAsViewed: async (eventId) => {
    try {
      const response = await apiClient.post(`/api/v1/events/${eventId}/view`);
      return response.data;
    } catch (error) {
      console.error(`Erro ao marcar evento ${eventId} como visualizado:`, error);
      throw error;
    }
  },
  
  /**
   * Baixar a imagem de um evento
   * @param {string} eventId - ID do evento
   * @returns {Promise<Blob>} Blob da imagem
   */
  downloadEventImage: async (eventId) => {
    try {
      const response = await apiClient.get(`/api/v1/events/${eventId}/image`, {
        responseType: 'blob'
      });
      return response.data;
    } catch (error) {
      console.error(`Erro ao baixar imagem do evento ${eventId}:`, error);
      throw error;
    }
  }
};

export default eventService; 