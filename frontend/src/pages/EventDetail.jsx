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

  // Estados específicos para o vídeo
  const [videoUrl, setVideoUrl] = useState(null);
  const [videoLoading, setVideoLoading] = useState(false);
  const [videoError, setVideoError] = useState(null);

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

  // Efeito para buscar o vídeo quando o evento for carregado
  useEffect(() => {
    // Só busca o vídeo se tivermos o ID do evento e o token
    if (id && token) {
      setVideoLoading(true);
      setVideoError(null);
      setVideoUrl(null); // Limpa URL anterior
      let currentVideoUrl = null; // Variável para guardar a URL e revogar na limpeza

      const fetchVideo = async () => {
        try {
          console.log('Token usado para buscar vídeo:', token);
          const response = await axios.get(`/api/events/${id}/video`, {
            headers: { Authorization: `Bearer ${token}` },
            responseType: 'blob', // Essencial para receber dados binários
          });

          const blob = new Blob([response.data], { type: 'video/mp4' });
          currentVideoUrl = URL.createObjectURL(blob);
          setVideoUrl(currentVideoUrl);

        } catch (err) {
          console.error('Error fetching video:', err);
          if (err.response && err.response.status === 404) {
            setVideoError('Vídeo não encontrado para este evento.');
          } else {
            setVideoError('Não foi possível carregar o vídeo.');
          }
          setVideoUrl(null); // Garantir que não haja URL antiga em caso de erro
        } finally {
          setVideoLoading(false);
        }
      };

      fetchVideo();

      // Função de limpeza para revogar a Object URL
      return () => {
        if (currentVideoUrl) {
          console.log("Revogando Object URL:", currentVideoUrl); // Log para debug
          URL.revokeObjectURL(currentVideoUrl);
        }
      };
    }
  }, [id, token]); // Depende de id e token

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
            <div className="bg-gray-100 dark:bg-gray-700 p-4 rounded-lg text-sm text-gray-800 dark:text-gray-200">
              <p className="mb-2">
                <span className="font-semibold">Tipo:</span> {event.event_type || 'Não especificado'}
              </p>
              <p className="mb-2">
                <span className="font-semibold">Câmera:</span> {event.camera_name || event.camera_id || 'Desconhecida'}
              </p>
              {event.detected_person_name && (
                <p className="mb-2">
                  <span className="font-semibold">Pessoa Detectada:</span> {event.detected_person_name}
                </p>
              )}
              <p className="mb-2">
                <span className="font-semibold">Zona:</span> {event.zone || 'Não especificada'}
              </p>
              <p className="mb-2">
                <span className="font-semibold">Confiança:</span> {event.confidence ? `${(event.confidence * 100).toFixed(1)}%` : 'Não disponível'}
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
              Vídeo do Evento
            </h2>
            <div className="bg-gray-100 dark:bg-gray-700 p-4 rounded-lg flex items-center justify-center min-h-[200px]">
              {videoLoading && (
                <div className="text-center py-10">
                  <div className="loader-small mx-auto mb-2"></div> {/* Usar classe de loader se houver */} 
                  <p className="text-gray-500 dark:text-gray-400">Carregando vídeo...</p>
                </div>
              )}
              {videoError && !videoLoading && (
                <div className="text-red-500 dark:text-red-400 text-center py-10">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto mb-2 opacity-75" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p>{videoError}</p>
                </div>
              )}
              {videoUrl && !videoLoading && !videoError && (
                <video 
                  controls
                  src={videoUrl} 
                  className="max-w-full max-h-64 rounded"
                >
                  Seu navegador não suporta o elemento de vídeo.
                </video>
              )}
              {!videoLoading && !videoError && !videoUrl && (
                <div className="text-gray-500 dark:text-gray-400 text-center py-10">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mx-auto mb-2 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M4 18h11a1 1 0 001-1V7a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1z" />
                  </svg>
                  <p>Vídeo indisponível ou carregando...</p>
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

            {/* Botão de Download - agora usa videoUrl */}
            <a
              href={videoUrl} // Usa a URL do blob
              download={`evento_${event?.id || id}.mp4`} // Nome do arquivo sugerido
              target="_blank"
              rel="noopener noreferrer"
              // Desabilita o botão/link se não houver URL
              className={`inline-flex items-center px-4 py-2 rounded-md text-sm font-medium 
                ${videoUrl ? 
                  'bg-green-600 text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500' : 
                  'bg-gray-500 text-gray-300 cursor-not-allowed'}
              `}
              // Impede o clique se não houver URL
              onClick={(e) => !videoUrl && e.preventDefault()}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Baixar Vídeo
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EventDetail; 