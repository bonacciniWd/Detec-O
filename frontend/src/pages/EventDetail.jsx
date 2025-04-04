import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import MainLayout from '../components/MainLayout';

const EventDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [event, setEvent] = useState(null);

  useEffect(() => {
    const fetchEventDetails = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`/api/events/${id}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        setEvent(response.data);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching event details:', err);
        setError('Não foi possível carregar os detalhes do evento. Tente novamente mais tarde.');
        setLoading(false);
      }
    };

    if (id) {
      fetchEventDetails();
    } else {
      setLoading(false);
    }
  }, [id, token]);

  const handleDelete = async () => {
    if (window.confirm('Tem certeza que deseja excluir este evento?')) {
      try {
        setLoading(true);
        await axios.delete(`/api/events/${id}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setLoading(false);
        navigate('/events');
      } catch (err) {
        console.error('Error deleting event:', err);
        setError('Não foi possível excluir o evento. Tente novamente mais tarde.');
        setLoading(false);
      }
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loader"></div>
        <p>Carregando detalhes do evento...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-4">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
        <button
          onClick={() => navigate('/events')}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Voltar para Eventos
        </button>
      </div>
    );
  }

  if (!event) {
    return (
      <div className="container mx-auto p-4">
        <p>Evento não encontrado</p>
        <button
          onClick={() => navigate('/events')}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Voltar para Eventos
        </button>
      </div>
    );
  }

  // Formato da data e hora
  const formatDateTime = (dateTimeStr) => {
    const date = new Date(dateTimeStr);
    return date.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  return (
    <div className="container mx-auto p-4">
      <div className="max-w-4xl mx-auto bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-2 text-gray-900 dark:text-white">
          Evento {event.id}
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
          Detectado em {formatDateTime(event.timestamp)}
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div>
            <h2 className="text-lg font-semibold mb-3 text-gray-900 dark:text-white">
              Detalhes do Evento
            </h2>
            <div className="bg-gray-100 dark:bg-gray-700 p-4 rounded-lg">
              <p className="mb-2">
                <span className="font-semibold">Tipo:</span> {event.type || 'Não especificado'}
              </p>
              <p className="mb-2">
                <span className="font-semibold">Câmera:</span> {event.camera_name || event.camera_id || 'Desconhecida'}
              </p>
              <p className="mb-2">
                <span className="font-semibold">Zona:</span> {event.zone || 'Não especificada'}
              </p>
              <p className="mb-2">
                <span className="font-semibold">Confiança:</span> {event.confidence ? `${event.confidence}%` : 'Não disponível'}
              </p>
              <p>
                <span className="font-semibold">Status:</span> {' '}
                <span className={`inline-block px-2 py-1 rounded text-xs ${
                  event.status === 'confirmed' ? 'bg-green-100 text-green-800' : 
                  event.status === 'false_alarm' ? 'bg-red-100 text-red-800' : 
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {event.status === 'confirmed' ? 'Confirmado' : 
                   event.status === 'false_alarm' ? 'Falso Alarme' : 
                   'Pendente'}
                </span>
              </p>
            </div>
          </div>
          
          <div>
            <h2 className="text-lg font-semibold mb-3 text-gray-900 dark:text-white">
              Imagem Capturada
            </h2>
            <div className="bg-gray-100 dark:bg-gray-700 p-4 rounded-lg flex items-center justify-center">
              {event.image_url ? (
                <img 
                  src={event.image_url} 
                  alt="Imagem do evento" 
                  className="max-w-full max-h-64 rounded"
                />
              ) : (
                <div className="text-gray-500 dark:text-gray-400 text-center py-10">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mx-auto mb-2 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <p>Nenhuma imagem disponível</p>
                </div>
              )}
            </div>
          </div>
        </div>
        
        {event.description && (
          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-3 text-gray-900 dark:text-white">
              Descrição
            </h2>
            <div className="bg-gray-100 dark:bg-gray-700 p-4 rounded-lg">
              <p>{event.description}</p>
            </div>
          </div>
        )}
        
        <div className="flex justify-between">
          <button
            onClick={() => navigate('/events')}
            className="px-4 py-2 bg-gray-300 text-gray-800 rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500"
          >
            Voltar
          </button>
          
          <div className="flex space-x-2">
            <button
              onClick={handleDelete}
              className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
            >
              Excluir
            </button>
            
            <button
              onClick={() => {
                const newStatus = event.status === 'pending' ? 'confirmed' : 
                                 event.status === 'confirmed' ? 'false_alarm' : 'pending';
                // Implementar atualização de status aqui
                alert(`Mudança de status para ${newStatus} - Implementação pendente`);
              }}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {event.status === 'pending' ? 'Confirmar' : 
               event.status === 'confirmed' ? 'Marcar como Falso' : 'Restaurar Pendência'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EventDetail; 