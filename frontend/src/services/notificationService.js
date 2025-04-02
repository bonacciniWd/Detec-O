import { toast } from 'react-toastify';
import eventService from './eventService';

// Intervalo de polling em milissegundos (default: 10 segundos)
const DEFAULT_POLLING_INTERVAL = 10000;

let pollingInterval = null;
let lastEventId = null;
let eventCallbacks = [];

/**
 * Verifica se o usuário está autenticado
 * @returns {boolean} - Verdadeiro se o usuário estiver autenticado
 */
const isAuthenticated = () => {
  return !!localStorage.getItem('authToken');
};

/**
 * Serviço de Notificações em Tempo Real usando polling periódico
 */
const notificationService = {
  /**
   * Iniciar o polling para eventos recentes
   * @param {Function} onEventCallback - Callback opcional para processar eventos
   * @param {number} interval - Intervalo de polling em milissegundos
   * @returns {boolean} - Sucesso da inicialização
   */
  startListening: (onEventCallback = null, interval = DEFAULT_POLLING_INTERVAL) => {
    // Verificar se o usuário está autenticado
    if (!isAuthenticated()) {
      console.warn('Tentativa de iniciar polling sem autenticação');
      return false;
    }

    if (pollingInterval) {
      console.warn('Polling de eventos já está ativo');
      if (onEventCallback) eventCallbacks.push(onEventCallback);
      return false;
    }

    try {
      // Registrar callback (opcional)
      if (onEventCallback) eventCallbacks.push(onEventCallback);
      
      // Primeiro, buscar o ID do evento mais recente
      notificationService.checkForNewEvents();
      
      // Iniciar polling periódico
      pollingInterval = setInterval(() => {
        // Verificar novamente a autenticação a cada intervalo
        if (!isAuthenticated()) {
          console.warn('Usuário não está mais autenticado. Parando polling.');
          notificationService.stopListening();
          return;
        }
        notificationService.checkForNewEvents();
      }, interval);
      
      console.log(`Polling de eventos iniciado com intervalo de ${interval}ms`);
      return true;
    } catch (error) {
      console.error('Falha ao iniciar polling de eventos:', error);
      return false;
    }
  },
  
  /**
   * Verificar se há novos eventos desde o último check
   */
  checkForNewEvents: async () => {
    // Verificar autenticação antes de fazer a requisição
    if (!isAuthenticated()) {
      console.warn('Tentativa de verificar eventos sem autenticação');
      return;
    }

    try {
      // Obter eventos mais recentes (limitado a 5 para performance)
      const recentEvents = await eventService.getEvents({ limit: 5 });
      
      if (recentEvents.length === 0) return;
      
      // Se for a primeira chamada, apenas armazenar o ID mais recente
      if (lastEventId === null) {
        lastEventId = recentEvents[0].id;
        console.log('ID inicial do último evento:', lastEventId);
        return;
      }
      
      // Verificar se há eventos mais recentes que o último conhecido
      const newEvents = recentEvents.filter(event => event.id > lastEventId);
      
      if (newEvents.length > 0) {
        console.log(`${newEvents.length} novos eventos detectados:`, newEvents);
        
        // Atualizar o ID do evento mais recente
        lastEventId = newEvents[0].id;
        
        // Processar novos eventos (do mais recente para o mais antigo)
        newEvents.reverse().forEach(eventData => {
          // Mostrar notificação para o usuário
          toast.info(`Nova detecção: ${eventData.event_type || 'Objeto'} em ${eventData.camera_name || 'câmera'}`);
          
          // Executar todos os callbacks registrados
          eventCallbacks.forEach(callback => {
            try {
              callback(eventData);
            } catch (callbackError) {
              console.error('Erro ao executar callback de evento:', callbackError);
            }
          });
        });
      }
    } catch (error) {
      console.error('Erro ao verificar novos eventos:', error);
      
      // Se receber erro 401, parar o polling
      if (error.response?.status === 401) {
        console.warn('Erro de autenticação ao verificar eventos. Parando polling.');
        notificationService.stopListening();
      }
    }
  },
  
  /**
   * Parar de verificar novos eventos
   */
  stopListening: () => {
    if (pollingInterval) {
      clearInterval(pollingInterval);
      pollingInterval = null;
      lastEventId = null;
      eventCallbacks = [];
      console.log('Polling de eventos encerrado');
    }
  },
  
  /**
   * Adicionar um callback para processar eventos
   * @param {Function} callback - Função para processar eventos recebidos
   */
  addEventCallback: (callback) => {
    if (typeof callback === 'function') {
      eventCallbacks.push(callback);
    }
  },
  
  /**
   * Remover um callback específico
   * @param {Function} callback - Callback a ser removido
   */
  removeEventCallback: (callback) => {
    eventCallbacks = eventCallbacks.filter(cb => cb !== callback);
  }
};

export default notificationService; 