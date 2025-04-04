import api from './api';

/**
 * Serviço para gerenciar eventos do sistema
 */
const eventService = {
  /**
   * Obtém a lista de eventos com opções de filtragem e paginação
   * @param {Object} options - Opções de consulta
   * @param {number} options.limit - Quantidade de eventos a retornar
   * @param {number} options.offset - Índice inicial para paginação
   * @param {string} options.sort - Campo para ordenação (ex: '-timestamp' para decrescente por data)
   * @param {string} options.type - Filtrar por tipo de evento
   * @param {string} options.cameraId - Filtrar por ID da câmera
   * @param {string} options.status - Filtrar por status (pending, confirmed, false_alarm)
   * @returns {Promise<Array>} - Array de eventos
   */
  getEvents: async function(options = {}) {
    try {
      const response = await api.get('/v1/events', { params: options });
      return response.data.items || response.data || [];
    } catch (error) {
      console.error('Erro ao buscar eventos:', error);
      throw error;
    }
  },

  /**
   * Obtém os detalhes de um evento específico
   * @param {string} eventId - ID do evento
   * @returns {Promise<Object>} - Dados do evento
   */
  getEventById: async function(eventId) {
    try {
      const response = await api.get(`/v1/events/${eventId}`);
      return response.data;
    } catch (error) {
      console.error(`Erro ao buscar evento ${eventId}:`, error);
      throw error;
    }
  },

  /**
   * Atualiza o status de um evento
   * @param {string} eventId - ID do evento
   * @param {string} status - Novo status (pending, confirmed, false_alarm)
   * @param {string} comment - Comentário opcional sobre a atualização
   * @returns {Promise<Object>} - Dados atualizados do evento
   */
  updateEventStatus: async function(eventId, status, comment = '') {
    try {
      const response = await api.patch(`/v1/events/${eventId}`, { 
        status,
        comment
      });
      return response.data;
    } catch (error) {
      console.error(`Erro ao atualizar status do evento ${eventId}:`, error);
      throw error;
    }
  },

  /**
   * Exclui um evento
   * @param {string} eventId - ID do evento
   * @returns {Promise<boolean>} - True se a exclusão foi bem-sucedida
   */
  deleteEvent: async function(eventId) {
    try {
      await api.delete(`/v1/events/${eventId}`);
      return true;
    } catch (error) {
      console.error(`Erro ao excluir evento ${eventId}:`, error);
      throw error;
    }
  },

  /**
   * Obtém resumo de estatísticas de eventos 
   * @param {Object} options - Opções de filtragem (período, câmera, etc)
   * @returns {Promise<Object>} - Estatísticas de eventos
   */
  getEventStats: async function(options = {}) {
    try {
      const response = await api.get('/v1/events/stats', { params: options });
      return response.data;
    } catch (error) {
      console.error('Erro ao buscar estatísticas de eventos:', error);
      throw error;
    }
  }
};

export default eventService; 