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
  const [isPositive, setIsPositive] = useState(initialValue === 'true_positive');
  const [notes, setNotes] = useState('');

  // Classes CSS baseadas no tamanho
  const btnSize = size === "small" ? "p-1 text-xs" : "p-2 text-sm";
  const containerClass = size === "small" ? "flex space-x-1" : "flex space-x-2";

  // Enviar feedback
  const submitFeedback = async (feedbackValue) => {
    try {
      setIsSubmitting(true);

      // Mapear valor do botão para o status esperado pela API
      let statusToSend;
      if (feedbackValue === true) {
        statusToSend = 'true_positive';
      } else if (feedbackValue === false) {
        statusToSend = 'false_positive';
      } else { // Assume 'uncertain'
        statusToSend = 'uncertain';
      }
      
      // Enviar para a API com os nomes corretos
      await apiClient.post(`/api/events/${eventId}/feedback`, {
        feedback_status: statusToSend,
        feedback_notes: notes
      });
      
      // Atualizar estado e notificar
      setFeedback(statusToSend);
      setIsPositive(feedbackValue === true);
      toast.success(`Feedback '${statusToSend}' enviado com sucesso!`);
      
      // Notificar componente pai
      if (onFeedbackSubmit) {
        onFeedbackSubmit(statusToSend, notes);
      }
    } catch (error) {
      console.error('Erro ao enviar feedback:', error);
      // Exibir detalhes do erro de validação se disponíveis
      const errorDetail = error.response?.data?.detail;
      let errorMessage = 'Não foi possível enviar o feedback.';
      if (typeof errorDetail === 'string') {
        errorMessage += ` Detalhe: ${errorDetail}`;
      } else if (Array.isArray(errorDetail)) {
        // Formatar erros de validação Pydantic
        const validationErrors = errorDetail.map(err => `${err.loc.join('.')} - ${err.msg}`).join(', ');
        errorMessage += ` Erros: ${validationErrors}`;
      }
      toast.error(errorMessage);
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
          onClick={() => submitFeedback(true)}
          className={`${btnSize} rounded-md flex items-center ${
            isPositive
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
          onClick={() => submitFeedback(false)}
          className={`${btnSize} rounded-md flex items-center ${
            !isPositive
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