/**
 * Serviço para gerenciamento de notificações em tempo real
 */
import { useState, useEffect } from 'react';
import { toast } from 'react-toastify';

// Armazenar callbacks para eventos
const eventCallbacks = [];
// Armazenar callbacks para notificações
const notificationCallbacks = [];

// Simular notificações a cada 45 segundos para demonstração
let simulationInterval = null;

const notificationService = {
  /**
   * Inicializa o serviço de notificações
   */
  init: () => {
    console.log('Inicializando serviço de notificações...');
    
    // Simular recebimento de notificações para demonstração
    if (!simulationInterval) {
      simulationInterval = setInterval(() => {
        const randomEvent = {
          id: `sim-${Date.now()}`,
          event_type: ['Pessoa', 'Veículo', 'Objeto Abandonado', 'Movimento'][Math.floor(Math.random() * 4)],
          camera_id: ['1', '2', '3'][Math.floor(Math.random() * 3)],
          camera_name: ['Câmera Entrada', 'Câmera Estacionamento', 'Câmera Perímetro'][Math.floor(Math.random() * 3)],
          timestamp: new Date().toISOString(),
          confidence: Math.random() * 0.4 + 0.6, // Valor entre 0.6 e 1.0
          severity: ['red', 'yellow', 'blue'][Math.floor(Math.random() * 3)]
        };
        
        console.log('Simulando novo evento recebido:', randomEvent);
        
        // Notificar callbacks de eventos
        eventCallbacks.forEach(callback => {
          try {
            callback(randomEvent);
          } catch (error) {
            console.error('Erro ao executar callback de evento:', error);
          }
        });
        
        // Notificar callbacks de notificações
        const notification = {
          id: `notif-${Date.now()}`,
          title: `Novo evento: ${randomEvent.event_type}`,
          message: `Detectado em ${randomEvent.camera_name} com confiança de ${Math.round(randomEvent.confidence * 100)}%`,
          severity: randomEvent.severity,
          timestamp: randomEvent.timestamp,
          read: false,
          data: { eventId: randomEvent.id }
        };
        
        notificationCallbacks.forEach(callback => {
          try {
            callback(notification);
          } catch (error) {
            console.error('Erro ao executar callback de notificação:', error);
          }
        });
      }, 45000); // 45 segundos
    }
  },
  
  /**
   * Adiciona um callback para novos eventos
   * @param {Function} callback - Função a ser chamada quando um novo evento for recebido
   */
  addEventCallback: (callback) => {
    if (typeof callback === 'function' && !eventCallbacks.includes(callback)) {
      eventCallbacks.push(callback);
      console.log('Callback de evento adicionado, total:', eventCallbacks.length);
    }
  },
  
  /**
   * Remove um callback de eventos
   * @param {Function} callback - Função a ser removida
   */
  removeEventCallback: (callback) => {
    const index = eventCallbacks.indexOf(callback);
    if (index !== -1) {
      eventCallbacks.splice(index, 1);
      console.log('Callback de evento removido, restantes:', eventCallbacks.length);
    }
  },
  
  /**
   * Adiciona um callback para novas notificações
   * @param {Function} callback - Função a ser chamada quando uma nova notificação for recebida
   */
  addNotificationCallback: (callback) => {
    if (typeof callback === 'function' && !notificationCallbacks.includes(callback)) {
      notificationCallbacks.push(callback);
      console.log('Callback de notificação adicionado, total:', notificationCallbacks.length);
    }
  },
  
  /**
   * Remove um callback de notificações
   * @param {Function} callback - Função a ser removida
   */
  removeNotificationCallback: (callback) => {
    const index = notificationCallbacks.indexOf(callback);
    if (index !== -1) {
      notificationCallbacks.splice(index, 1);
      console.log('Callback de notificação removido, restantes:', notificationCallbacks.length);
    }
  },
  
  /**
   * Encerra o serviço de notificações
   */
  dispose: () => {
    console.log('Encerrando serviço de notificações...');
    
    if (simulationInterval) {
      clearInterval(simulationInterval);
      simulationInterval = null;
    }
    
    // Limpar arrays de callbacks
    eventCallbacks.length = 0;
    notificationCallbacks.length = 0;
  },
  
  success: function(message, options = {}) {
    return toast.success(message, {
      position: "top-right",
      autoClose: 5000,
      hideProgressBar: false,
      closeOnClick: true,
      pauseOnHover: true,
      draggable: true,
      ...options
    });
  },
  
  error: function(message, options = {}) {
    return toast.error(message, {
      position: "top-right",
      autoClose: 5000,
      hideProgressBar: false,
      closeOnClick: true,
      pauseOnHover: true,
      draggable: true,
      ...options
    });
  },
  
  info: function(message, options = {}) {
    return toast.info(message, {
      position: "top-right",
      autoClose: 5000,
      hideProgressBar: false,
      closeOnClick: true,
      pauseOnHover: true,
      draggable: true,
      ...options
    });
  },
  
  warning: function(message, options = {}) {
    return toast.warning(message, {
      position: "top-right",
      autoClose: 5000,
      hideProgressBar: false,
      closeOnClick: true,
      pauseOnHover: true,
      draggable: true,
      ...options
    });
  }
};

// Inicializar o serviço automaticamente
notificationService.init();

/**
 * Hook para usar notificações em componentes de função
 * @returns {Array} [notifications, markAsRead, clearAll]
 */
export const useNotifications = () => {
  const [notifications, setNotifications] = useState([]);
  
  useEffect(() => {
    const handleNotification = (notification) => {
      setNotifications(prev => [notification, ...prev].slice(0, 50)); // Manter no máximo 50 notificações
    };
    
    notificationService.addNotificationCallback(handleNotification);
    
    return () => {
      notificationService.removeNotificationCallback(handleNotification);
    };
  }, []);
  
  const markAsRead = (notificationId) => {
    setNotifications(prev => 
      prev.map(notif => 
        notif.id === notificationId 
          ? { ...notif, read: true } 
          : notif
      )
    );
  };
  
  const clearAll = () => {
    setNotifications([]);
  };
  
  return [notifications, markAsRead, clearAll];
};

export default notificationService; 