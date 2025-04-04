import { toast } from 'react-toastify';

// Defina o serviço como um objeto
const notificationService = {
  // Armazenar callbacks de eventos
  _eventCallbacks: [],
  
  startListening: function() {
    console.log("Notification service started");
  },
  
  stopListening: function() {
    console.log("Notification service stopped");
  },
  
  // Adicionar callback para eventos
  addEventCallback: function(callback) {
    if (typeof callback === 'function' && !this._eventCallbacks.includes(callback)) {
      this._eventCallbacks.push(callback);
      return true;
    }
    return false;
  },
  
  // Remover callback
  removeEventCallback: function(callback) {
    const index = this._eventCallbacks.indexOf(callback);
    if (index !== -1) {
      this._eventCallbacks.splice(index, 1);
      return true;
    }
    return false;
  },
  
  // Notificar todos os callbacks registrados
  notifyEventCallbacks: function(eventData) {
    this._eventCallbacks.forEach(callback => {
            try {
              callback(eventData);
      } catch (error) {
        console.error('Erro ao executar callback de evento:', error);
      }
    });
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

// Exportar funções individuais
export const { 
  startListening, 
  stopListening, 
  addEventCallback, 
  removeEventCallback, 
  notifyEventCallbacks,
  success,
  error,
  info,
  warning
} = notificationService;

// Exportar o serviço como default
export default notificationService; 