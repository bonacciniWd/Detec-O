import api from './api';

/**
 * Serviço para gerenciamento de eventos
 */

// Mock de dados para eventos caso a API real ainda não esteja implementada
const mockEvents = [
  {
    id: '101',
    event_type: 'Pessoa',
    camera_id: '1',
    camera_name: 'Câmera Entrada',
    timestamp: new Date().toISOString(),
    confidence: 0.87,
    severity: 'yellow',
    zone_name: 'Entrada Principal'
  },
  {
    id: '102',
    event_type: 'Veículo',
    camera_id: '2',
    camera_name: 'Câmera Estacionamento',
    timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
    confidence: 0.92,
    severity: 'blue',
    zone_name: 'Estacionamento'
  },
  {
    id: '103',
    event_type: 'Objeto Abandonado',
    camera_id: '1',
    camera_name: 'Câmera Entrada',
    timestamp: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
    confidence: 0.78,
    severity: 'red',
    zone_name: 'Entrada Principal'
  },
  {
    id: '104',
    event_type: 'Pessoa',
    camera_id: '1',
    camera_name: 'Câmera Entrada',
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    confidence: 0.85,
    severity: 'yellow',
    zone_name: 'Entrada Principal'
  },
  {
    id: '105',
    event_type: 'Movimento',
    camera_id: '2',
    camera_name: 'Câmera Estacionamento',
    timestamp: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
    confidence: 0.65,
    severity: 'blue',
    zone_name: 'Estacionamento'
  }
];

const eventService = {
  /**
   * Obtém lista de eventos com filtros
   * @param {Object} filters - Objeto com filtros: camera_id, start_date, end_date, limit, event_type, severity
   * @returns {Promise<Array>} Lista de eventos
   */
  getEvents: async (filters = {}) => {
    try {
      console.log("Buscando eventos com filtros:", filters);
      
      const response = await api.get('/api/events/', { params: filters });
      
      if (response.data && Array.isArray(response.data)) {
        console.log("Dados de eventos obtidos da API:", response.data.length);
        return response.data;
      } else if (response.data && response.data.events && Array.isArray(response.data.events)) {
        console.log("Dados de eventos obtidos da API (formato alternativo):", response.data.events.length);
        return response.data.events;
      } else {
        // Verifica se a resposta é HTML
        const isHtmlResponse = typeof response.data === 'string' && 
          (response.data.toLowerCase().startsWith('<!doctype') || 
           response.data.toLowerCase().startsWith('<html'));
           
        if (isHtmlResponse) {
          console.warn("API retornou formato HTML desconhecido");
        } else {
          console.warn("API retornou formato desconhecido:", response.data);
        }
        
        return []; // Retorna array vazio se formato for desconhecido
      }
    } catch (error) {
      console.error("Erro ao buscar eventos:", error.response?.data || error.message);
      throw error; // Re-lança o erro para ser tratado no componente
    }
  },

  /**
   * Obtém detalhes de um evento específico
   * @param {string} eventId - ID do evento
   * @returns {Promise<Object>} Detalhes do evento
   */
  getEventById: async (eventId) => {
    try {
      const response = await api.get(`/api/events/${eventId}`);
      return response.data;
    } catch (error) {
      console.error(`Erro ao buscar evento ${eventId}:`, error.response?.data || error.message);
      throw error; // Re-lança o erro para ser tratado no componente
    }
  },
  
  /**
   * Adiciona feedback a um evento (confirmação ou falso alarme)
   * @param {string} eventId - ID do evento
   * @param {boolean} isConfirmed - Se o evento foi confirmado como verdadeiro
   * @param {string} feedback - Comentário opcional
   * @returns {Promise<Object>} Status da operação
   */
  addFeedback: async (eventId, isConfirmed, feedback = '') => {
    try {
      const response = await api.post(`/api/events/${eventId}/feedback`, {
        is_confirmed: isConfirmed,
        feedback
      });
      return response.data;
    } catch (error) {
      console.error("Erro ao adicionar feedback:", error.response?.data || error.message);
      throw error; // Re-lança o erro para ser tratado no componente
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
      const response = await api.patch(`/api/events/${eventId}`, { 
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
      await api.delete(`/api/events/${eventId}`);
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
      const response = await api.get('/api/events/stats', { params: options });
      return response.data;
    } catch (error) {
      console.error('Erro ao buscar estatísticas de eventos:', error);
      throw error;
    }
  },

  /**
   * Obtém dados da série temporal de eventos por dia.
   * @param {Object} params - Parâmetros como start_date, end_date, camera_id
   * @returns {Promise<Array<{date: string, count: number}>>} - Lista de pontos da série temporal
   */
  getEventTimeSeries: async (params) => {
    try {
      // console.log("[eventService] Buscando série temporal com params:", params);
      const response = await api.get('/api/events/stats/timeseries', { params });
      // console.log("[eventService] Resposta da API para timeseries:", response.data);
      return Array.isArray(response.data) ? response.data : [];
    } catch (error) {
      console.error("[eventService] Erro ao buscar série temporal:", error.response?.data || error.message);
      throw error;
    }
  },

  /**
   * Obtém a distribuição de eventos por hora do dia.
   * @param {Object} params - Parâmetros como start_date, end_date, camera_id
   * @returns {Promise<Array<{hour: number, count: number}>>} - Lista de contagens por hora
   */
  getEventHourlyDistribution: async (params) => {
    try {
      console.log("[eventService] Buscando distribuição horária com params:", params);
      const response = await api.get('/api/events/stats/hourly', { params });
      return Array.isArray(response.data) ? response.data : [];
    } catch (error) {
      console.error("[eventService] Erro ao buscar distribuição horária:", error.response?.data || error.message);
      throw error;
    }
  }
};

export default eventService; 