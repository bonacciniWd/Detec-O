import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';
import eventService from '../services/eventService';
import notificationService from '../services/notificationService';

function DashboardPage() {
  const { user } = useAuth();
  const [recentEvents, setRecentEvents] = useState([]);
  const [isLoadingEvents, setIsLoadingEvents] = useState(false);
  const [eventsError, setEventsError] = useState(null);

  const fetchRecentEvents = async () => {
    setIsLoadingEvents(true);
    try {
      // Buscando os últimos 5 eventos
      const events = await eventService.getEvents({ limit: 5 });
      setRecentEvents(events);
    } catch (error) {
      console.error("Erro ao buscar eventos recentes:", error);
      setEventsError("Não foi possível carregar os eventos recentes.");
    } finally {
      setIsLoadingEvents(false);
    }
  };

  // Buscar eventos recentes ao carregar a página
  useEffect(() => {
    fetchRecentEvents();
  }, []);

  // Configurar o callback para atualizações em tempo real
  useEffect(() => {
    const handleNewEvent = (eventData) => {
      console.log("Novo evento detectado, atualizando dashboard:", eventData);
      // Atualizar a lista de eventos recentes
      fetchRecentEvents();
    };
    
    // Registrar o callback no serviço de notificações
    notificationService.addEventCallback(handleNewEvent);
    
    // Limpar quando o componente for desmontado
    return () => {
      notificationService.removeEventCallback(handleNewEvent);
    };
  }, []);

  // Função para formatar data/hora
  const formatDateTime = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    // Container da página com espaçamento e fundo geral - TEMA ESCURO
    <div className="space-y-6 bg-gray-900 min-h-screen pb-12"> {/* Mudado para bg-gray-900 */}
      {/* Cabeçalho da Página - TEMA ESCURO */}
      <header className="bg-gray-800 shadow"> {/* Mudado para bg-gray-800 */}
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-white">Dashboard</h1> {/* Mudado para text-white */}
        </div>
      </header>
      
      {/* Conteúdo Principal */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Saudação */}
        <div className="bg-gray-800 shadow rounded-lg p-6 mb-8"> {/* Atualizado para tema escuro */}
          <h2 className="text-2xl font-semibold mb-2 text-white">Olá, {user?.username || 'Usuário'}</h2> {/* Atualizado para tema escuro */}
          <p className="text-gray-300">Bem-vindo ao sistema de monitoramento.</p> {/* Atualizado para tema escuro */}
        </div>
        
        {/* Cards de Informações */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Card de Eventos Recentes */}
          <div className="bg-gray-800 shadow rounded-lg overflow-hidden">
            <div className="p-5 border-b border-gray-700">
              <h3 className="text-lg font-medium text-white">Eventos Recentes</h3>
            </div>
            <div className="p-4">
              {isLoadingEvents ? (
                <p className="text-gray-400">Carregando eventos...</p>
              ) : eventsError ? (
                <p className="text-red-400">{eventsError}</p>
              ) : recentEvents.length > 0 ? (
                <ul className="divide-y divide-gray-700">
                  {recentEvents.map((event) => (
                    <li key={event.id} className="py-3">
                      <div className="flex flex-col space-y-1">
                        <div className="flex justify-between">
                          <span className="text-sm font-medium text-blue-400">{event.event_type}</span>
                          <span className="text-xs text-gray-400">{formatDateTime(event.timestamp)}</span>
                        </div>
                        <p className="text-sm text-gray-300">
                          Câmera: {event.camera_name || 'Desconhecida'}
                        </p>
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-gray-400">Nenhum evento recente.</p>
              )}
              <div className="mt-4">
                <Link to="/events" className="text-sm text-blue-500 hover:text-blue-400">
                  Ver todos os eventos →
                </Link>
              </div>
            </div>
          </div>
          
          {/* Card de Câmeras */}
          <div className="bg-gray-800 shadow rounded-lg overflow-hidden">
            <div className="p-5 border-b border-gray-700">
              <h3 className="text-lg font-medium text-white">Gerenciar Câmeras</h3>
            </div>
            <div className="p-4">
              <p className="text-gray-300 mb-4">Configure e monitore suas câmeras para detecção de eventos.</p>
              <Link 
                to="/cameras" 
                className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded transition-colors duration-200"
              >
                Ir para Câmeras
              </Link>
            </div>
          </div>
          
          {/* Card de Estatísticas/Ajuda */}
          <div className="bg-gray-800 shadow rounded-lg overflow-hidden">
            <div className="p-5 border-b border-gray-700">
              <h3 className="text-lg font-medium text-white">Informações</h3>
            </div>
            <div className="p-4">
              <p className="text-gray-300 mb-4">
                Este sistema ajuda a detectar e registrar eventos em tempo real.
              </p>
              <div className="text-sm text-gray-400">
                <p className="mb-2">• Configure suas câmeras na página Câmeras</p>
                <p className="mb-2">• Visualize eventos detectados na página Eventos</p>
                <p>• Receba notificações em tempo real de novas detecções</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default DashboardPage; 