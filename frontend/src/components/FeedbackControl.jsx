import React, { useState } from 'react';
import apiClient from '../services/api';
import { toast } from 'react-toastify';

/**
 * Componente de feedback para classificar eventos de detecção
 * como verdadeiros positivos, falsos positivos, ou incertos.
 * Similar ao sistema Veesion para melhorar a qualidade das detecções.
 */
const FeedbackControl = ({ eventId, initialValue = null, onFeedbackSubmit = null, size = "normal" }) => {
  const [feedback, setFeedback] = useState(initialValue);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Classes CSS baseadas no tamanho
  const btnSize = size === "small" ? "p-1 text-xs" : "p-2 text-sm";
  const containerClass = size === "small" ? "flex space-x-1" : "flex space-x-2";

  // Enviar feedback para o backend
  const submitFeedback = async (value) => {
    // Se clicar no mesmo valor já selecionado, desmarca
    if (feedback === value) {
      value = null;
    }

    setIsSubmitting(true);
    try {
      await apiClient.post(`/api/v1/events/${eventId}/feedback`, {
        feedback_value: value
      });
      
      setFeedback(value);
      
      // Mostrar notificação de sucesso
      const messages = {
        'true_positive': 'Marcado como verdadeiro positivo',
        'false_positive': 'Marcado como falso positivo',
        'uncertain': 'Marcado como incerto',
        null: 'Feedback removido'
      };
      toast.success(messages[value] || 'Feedback atualizado');
      
      // Notificar o componente pai se necessário
      if (onFeedbackSubmit) {
        onFeedbackSubmit(value);
      }
    } catch (error) {
      console.error('Erro ao enviar feedback:', error);
      toast.error('Não foi possível enviar seu feedback');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mt-2">
      <div className="text-sm font-medium text-gray-400 mb-1">
        Esta detecção é precisa?
      </div>
      <div className={containerClass}>
        <button
          type="button"
          disabled={isSubmitting}
          onClick={() => submitFeedback('true_positive')}
          className={`${btnSize} rounded-md flex items-center ${
            feedback === 'true_positive'
              ? 'bg-green-700 text-white'
              : 'bg-gray-700 text-gray-300 hover:bg-green-800'
          }`}
        >
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            className={size === "small" ? "h-4 w-4 mr-1" : "h-5 w-5 mr-1"} 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          Sim
        </button>
        
        <button
          type="button"
          disabled={isSubmitting}
          onClick={() => submitFeedback('false_positive')}
          className={`${btnSize} rounded-md flex items-center ${
            feedback === 'false_positive'
              ? 'bg-red-700 text-white'
              : 'bg-gray-700 text-gray-300 hover:bg-red-800'
          }`}
        >
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            className={size === "small" ? "h-4 w-4 mr-1" : "h-5 w-5 mr-1"} 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
          Não
        </button>
        
        <button
          type="button"
          disabled={isSubmitting}
          onClick={() => submitFeedback('uncertain')}
          className={`${btnSize} rounded-md flex items-center ${
            feedback === 'uncertain'
              ? 'bg-yellow-600 text-white'
              : 'bg-gray-700 text-gray-300 hover:bg-yellow-700'
          }`}
        >
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            className={size === "small" ? "h-4 w-4 mr-1" : "h-5 w-5 mr-1"} 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Incerto
        </button>
      </div>
    </div>
  );
};

export default FeedbackControl;