import React, { useState, useEffect, useRef } from 'react';
import eventService from '../services/eventService';
import cameraService from '../services/cameraService';
import EventImage from '../components/EventImage';
import FeedbackControl from '../components/FeedbackControl';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';

function EventsPage() {
  const [events, setEvents] = useState([]);
  const [cameras, setCameras] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Estado para mostrar detalhes de um evento específico
  const [selectedEvent, setSelectedEvent] = useState(null);

  // Estado para paginação
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalEvents, setTotalEvents] = useState(0);
  const [eventsPerPage, setEventsPerPage] = useState(10);

  // Estado para filtros
  const [filterDays, setFilterDays] = useState(7);
  const [filterCameraId, setFilterCameraId] = useState('');
  const [filterType, setFilterType] = useState('');
  const [filterDateStart, setFilterDateStart] = useState('');
  const [filterDateEnd, setFilterDateEnd] = useState('');
  const [filterConfidence, setFilterConfidence] = useState(50);
  const [filterFeedback, setFilterFeedback] = useState('');
  // Adicionando estado para controlar quando aplicar filtros
  const [shouldApplyFilters, setShouldApplyFilters] = useState(false);

  // Estado para o modal de detalhes
  const [showModal, setShowModal] = useState(false);
  
  // Estado para o feedback do evento
  const [feedbackConfidence, setFeedbackConfidence] = useState(50);
  const [feedbackType, setFeedbackType] = useState("true_positive");

  // Função para buscar câmeras (para mapear ID para nome)
  const fetchCameras = async () => {
    try {
      const response = await cameraService.getCameras();
      let cameraList = response;
      
      // Verificar formato da resposta
      if (response && response.items) {
        cameraList = response.items;
      }
      
      // Garantir que temos um array
      if (!Array.isArray(cameraList)) {
        console.error("Resposta da API não é um array:", cameraList);
        setCameras({});
        return;
      }
      
      // Mapear câmeras por ID
      const cameraMap = cameraList.reduce((acc, cam) => {
        acc[cam.id] = cam;
        return acc;
      }, {});
      setCameras(cameraMap);
    } catch (err) {
      console.error("Erro ao buscar nomes das câmeras:", err);
    }
  };

  // Função para buscar eventos com base nos filtros e paginação
  const fetchEvents = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Construir parâmetros de filtro
      const params = {
        page: currentPage,
        limit: 10,
      };
      
      // Adicionar filtros condicionalmente
      if (filterDays > 0) {
        const fromDate = new Date();
        fromDate.setDate(fromDate.getDate() - filterDays);
        params.from_date = fromDate.toISOString().split('T')[0];
      } else if (filterDateStart) {
        params.from_date = filterDateStart;
      }
      
      if (filterDateEnd) {
        params.to_date = filterDateEnd;
      }
      
      if (filterCameraId) {
        params.camera_id = filterCameraId;
      }
      
      if (filterType) {
        params.event_type = filterType;
      }
      
      if (filterConfidence > 0) {
        params.min_confidence = filterConfidence / 100;
      }
      
      if (filterFeedback) {
        params.feedback = filterFeedback;
      }
      
      // Buscar dados da API
      const data = await eventService.getEvents(params);
      
      // Atualizar estados com os dados recebidos
      setEvents(data.events || []);
      setTotalPages(data.total_pages || 1);
      setTotalEvents(data.total_events || 0);
      
      // Buscar câmeras se ainda não foram carregadas
      if (Object.keys(cameras).length === 0) {
        fetchCameras();
      }
    } catch (err) {
      console.error("Erro ao buscar eventos:", err);
      setError("Não foi possível carregar os eventos. Tente novamente mais tarde.");
      setEvents([]);
    } finally {
      setIsLoading(false);
      setShouldApplyFilters(false);
    }
  };

  // Efeito para buscar câmeras na montagem inicial
  useEffect(() => {
    fetchCameras();
    setShouldApplyFilters(true);
  }, []);

  // Efeito para re-buscar eventos quando os filtros ou paginação mudam
  useEffect(() => {
    if (shouldApplyFilters || currentPage > 1 || eventsPerPage !== 10) {
      fetchEvents();
    }
  }, [currentPage, eventsPerPage, shouldApplyFilters]);

  // Atualizar o totalPages calculando-o com base no totalEvents
  useEffect(() => {
    // Calcular total de páginas com base no total de eventos e itens por página
    setTotalPages(Math.ceil(totalEvents / eventsPerPage));
  }, [totalEvents, eventsPerPage]);

  // Helper para formatar data
  const formatDate = (dateString) => {
    try {
      return new Date(dateString).toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit'
      });
    } catch (e) {
      return dateString;
    }
  };
  
  // Mostrar/fechar modal de detalhes
  const showEventDetails = (event) => {
    setSelectedEvent(event);
  };
  
  const closeEventDetails = () => {
    setSelectedEvent(null);
  };

  // Navegação de páginas
  const goToPage = (page) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
    }
  };

  // Manipular mudança no tamanho da página
  const handlePerPageChange = (e) => {
    setEventsPerPage(Number(e.target.value));
    setCurrentPage(1); // Resetar para primeira página ao mudar itens por página
  };

  // Lidar com mudança de feedback (usado no modal de detalhes)
  const handleFeedbackChange = (eventId, newFeedback) => {
    setEvents(prev => prev.map(event => 
      event.id === eventId ? { ...event, feedback: newFeedback } : event
    ));
    
    // Se o evento atual estiver aberto no modal, atualizar também
    if (selectedEvent && selectedEvent.id === eventId) {
      setSelectedEvent(prev => ({ ...prev, feedback: newFeedback }));
    }
  };

  // Função para lidar com aplicação de filtros
  const handleApplyFilters = () => {
    setCurrentPage(1);
    setShouldApplyFilters(true);
  };

  // Classes reutilizáveis para tema escuro
  const cardClass = "bg-gray-800 shadow overflow-hidden sm:rounded-lg";
  const cardHeaderClass = "px-4 py-5 sm:px-6 border-b border-gray-700";
  const cardTitleClass = "text-lg leading-6 font-medium text-white";
  const cardContentClass = "px-4 py-5 sm:p-6";
  const labelClass = "block text-sm font-medium text-gray-300 mb-1";
  const inputClass = "shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full text-base border-gray-700 bg-gray-700 text-white rounded-md px-3 py-3";
  const selectClass = "mt-1 block w-full pl-3 pr-10 py-3 text-base border-gray-700 bg-gray-700 text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 rounded-md";
  const buttonClass = "text-gray-300 hover:bg-gray-700 hover:text-white px-3 py-2 rounded-md text-sm font-medium";
  const activeButtonClass = "bg-gray-900 text-white px-3 py-2 rounded-md text-sm font-medium";
  const sliderTrackClass = "w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"; 

  // Função para renderizar indicador de feedback
  const renderFeedbackIndicator = (feedback) => {
    if (!feedback) return null;
    
    const indicators = {
      'true_positive': { color: 'bg-green-500', text: 'Positivo Verdadeiro' },
      'false_positive': { color: 'bg-red-500', text: 'Falso Positivo' },
      'uncertain': { color: 'bg-yellow-500', text: 'Incerto' }
    };
    
    const indicator = indicators[feedback] || { color: 'bg-gray-500', text: feedback };
    
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${indicator.color} text-white`}>
        {indicator.text}
      </span>
    );
  };

  return (
    <div className="space-y-4 bg-gray-900 min-h-screen pb-8">
      {/* Cabeçalho */}
      <header className="bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-white">Log de Eventos</h1>
        </div>
      </header>

      {/* Conteúdo Principal */}
      <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8">
        {/* Card de Filtros */}
        <div className={`${cardClass} mb-4`}>
          <div className={cardHeaderClass}>
            <h3 className={cardTitleClass}>Filtrar Eventos</h3>
          </div>
          <div className={`${cardContentClass} grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4`}>
            <div>
              <label htmlFor="filter-days" className={labelClass}>Dias Anteriores:</label>
              <input 
                type="number" 
                id="filter-days" 
                value={filterDays}
                onChange={(e) => setFilterDays(e.target.value ? Math.max(1, parseInt(e.target.value)) : 1)}
                min="1"
                className={inputClass}
              />
            </div>
            <div>
              <label htmlFor="filter-camera" className={labelClass}>Câmera:</label>
              <select 
                id="filter-camera"
                value={filterCameraId}
                onChange={(e) => setFilterCameraId(e.target.value)}
                className={selectClass}
              >
                <option value="">Todas as Câmeras</option>
                {Object.values(cameras).map(cam => (
                  <option key={cam.id} value={cam.id}>{cam.name} ({cam.location || 'N/A'})</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="filter-type" className={labelClass}>Tipo de Evento:</label>
              <select 
                id="filter-type"
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className={selectClass}
              >
                <option value="">Todos os Tipos</option>
                <option value="motion">Movimento</option>
                <option value="object">Objeto Detectado</option>
                <option value="person">Pessoa</option>
                <option value="car">Veículo</option>
                <option value="animal">Animal</option>
              </select>
            </div>
            <div>
              <label htmlFor="filter-date-start" className={labelClass}>Data Inicial:</label>
              <input 
                type="date" 
                id="filter-date-start" 
                value={filterDateStart}
                onChange={(e) => setFilterDateStart(e.target.value)}
                className={inputClass}
              />
            </div>
            <div>
              <label htmlFor="filter-date-end" className={labelClass}>Data Final:</label>
              <input 
                type="date" 
                id="filter-date-end" 
                value={filterDateEnd}
                onChange={(e) => setFilterDateEnd(e.target.value)}
                className={inputClass}
              />
            </div>
            <div>
              <label htmlFor="filter-confidence" className={labelClass}>
                Confiança Mínima: <span className="text-blue-400 font-bold">{filterConfidence}%</span>
              </label>
              <div className="relative">
                <div className="flex items-center">
                  <input 
                    type="range" 
                    id="filter-confidence" 
                    min="0" 
                    max="95" 
                    step="5"
                    value={filterConfidence}
                    onChange={(e) => setFilterConfidence(parseInt(e.target.value))}
                    className={`${sliderTrackClass} slider-thumb-custom`}
                    style={{
                      background: `linear-gradient(to right, #3B82F6 0%, #3B82F6 ${filterConfidence}%, #374151 ${filterConfidence}%, #374151 100%)`
                    }}
                  />
                </div>
                <style global jsx>{`
                  .slider-thumb-custom::-webkit-slider-thumb {
                    -webkit-appearance: none;
                    appearance: none;
                    width: 16px;
                    height: 16px;
                    border-radius: 50%;
                    background: #3B82F6;
                    box-shadow: 0 0 2px #3B82F6;
                    cursor: pointer;
                    transition: all 0.2s ease;
                  }
                  .slider-thumb-custom::-webkit-slider-thumb:hover {
                    transform: scale(1.2);
                    box-shadow: 0 0 4px #3B82F6;
                  }
                  .slider-thumb-custom::-moz-range-thumb {
                    width: 16px;
                    height: 16px;
                    border-radius: 50%;
                    background: #3B82F6;
                    box-shadow: 0 0 2px #3B82F6;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    border: none;
                  }
                  .slider-thumb-custom::-moz-range-thumb:hover {
                    transform: scale(1.2);
                    box-shadow: 0 0 4px #3B82F6;
                  }
                  /* Para Edge/IE */
                  .slider-thumb-custom::-ms-thumb {
                    width: 16px;
                    height: 16px;
                    border-radius: 50%;
                    background: #3B82F6;
                    box-shadow: 0 0 2px #3B82F6;
                    cursor: pointer;
                    border: none;
                  }
                `}</style>
              </div>
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>0%</span>
                <span>25%</span>
                <span>50%</span>
                <span>75%</span>
                <span>95%</span>
              </div>
            </div>
            <div>
              <label htmlFor="filter-feedback" className={labelClass}>Feedback:</label>
              <select 
                id="filter-feedback"
                value={filterFeedback}
                onChange={(e) => setFilterFeedback(e.target.value)}
                className={selectClass}
              >
                <option value="">Todos</option>
                <option value="true_positive">Positivos Verdadeiros</option>
                <option value="false_positive">Falsos Positivos</option>
                <option value="uncertain">Incertos</option>
                <option value="none">Sem Feedback</option>
              </select>
            </div>
            <div className="flex items-end">
              <button 
                type="button"
                onClick={handleApplyFilters}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Aplicar Filtros
              </button>
            </div>
          </div>
        </div>

        {/* Card Lista de Eventos */}
        <div className={cardClass}>
           <div className={cardHeaderClass}>
              <h3 className={cardTitleClass}>Eventos Detectados</h3>
           </div>
           <div className="overflow-x-auto">
              {isLoading && (
                <div className="flex justify-center items-center p-6">
                  <svg className="animate-spin -ml-1 mr-3 h-8 w-8 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span className="text-gray-300">Carregando eventos...</span>
                </div>
              )}
              
              {error && <p className="p-6 text-red-400">{error}</p>}
              
              {!isLoading && !error && events.length === 0 && (
                <p className="p-6 text-center text-gray-400">Nenhum evento encontrado com os filtros selecionados.</p>
              )}
              
              {!isLoading && !error && events.length > 0 && (
                <>
                  <div className="block lg:hidden">
                    {/* Versão mobile: cards em vez de tabela */}
                    <div className="divide-y divide-gray-700">
                      {events.map((event) => (
                        <div key={event.id} className="p-4 hover:bg-gray-700">
                          <div className="flex justify-between items-start mb-2">
                            <div className="font-medium text-gray-100">
                              {event.detection_type || event.event_type || 'Evento'}
                            </div>
                            <div className="text-xs text-gray-400">
                              {formatDate(event.timestamp)}
                            </div>
                          </div>
                          <div className="flex flex-col space-y-1 text-sm text-gray-300 mb-2">
                            <div>
                              <span className="text-gray-400">Câmera: </span>
                              {cameras[event.camera_id]?.name || event.camera_name || event.camera_id || 'N/A'}
                            </div>
                            {event.confidence && (
                              <div>
                                <span className="text-gray-400">Confiança: </span>
                                {Math.round(event.confidence * 100)}%
                              </div>
                            )}
                            {event.feedback && (
                              <div>
                                <span className="text-gray-400">Feedback: </span>
                                {renderFeedbackIndicator(event.feedback)}
                              </div>
                            )}
                          </div>
                          <button
                            className="mt-1 text-blue-400 hover:text-blue-300 text-sm"
                            onClick={() => showEventDetails(event)}
                          >
                            Ver Detalhes
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Versão desktop: tabela */}
                  <div className="hidden lg:block">
                    <table className="min-w-full divide-y divide-gray-700">
                      <thead className="bg-gray-700">
                        <tr>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Timestamp</th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Tipo</th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Câmera</th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Confiança</th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Feedback</th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Ações</th>
                        </tr>
                      </thead>
                      <tbody className="bg-gray-800 divide-y divide-gray-700">
                        {events.map((event) => (
                          <tr key={event.id} className="hover:bg-gray-700">
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{formatDate(event.timestamp)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-100">
                              {event.detection_type || event.event_type || 'Evento'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                              {cameras[event.camera_id]?.name || event.camera_name || event.camera_id || 'N/A'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                              {event.confidence ? `${Math.round(event.confidence * 100)}%` : 'N/A'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                              {renderFeedbackIndicator(event.feedback)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                              <button
                                className="text-blue-400 hover:text-blue-300"
                                onClick={() => showEventDetails(event)}
                              >
                                Ver Detalhes
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  
                  {/* Controles de Paginação */}
                  <div className="px-4 py-3 flex items-center justify-between border-t border-gray-700 sm:px-6">
                    <div className="flex-1 flex justify-between lg:hidden">
                      {/* Controles Mobile */}
                      <button
                        onClick={() => goToPage(currentPage - 1)}
                        disabled={currentPage === 1}
                        className={currentPage === 1 ? "opacity-50 cursor-not-allowed " + buttonClass : buttonClass}
                      >
                        Anterior
                      </button>
                      <span className="px-3 py-2 text-gray-300">
                        Página {currentPage} de {totalPages}
                      </span>
                      <button
                        onClick={() => goToPage(currentPage + 1)}
                        disabled={currentPage === totalPages}
                        className={currentPage === totalPages ? "opacity-50 cursor-not-allowed " + buttonClass : buttonClass}
                      >
                        Próxima
                      </button>
                    </div>
                    
                    <div className="hidden lg:flex-1 lg:flex lg:items-center lg:justify-between">
                      {/* Controles Desktop */}
                      <div>
                        <p className="text-sm text-gray-400">
                          Mostrando <span className="font-medium">{Math.min((currentPage - 1) * eventsPerPage + 1, totalEvents)}</span> a <span className="font-medium">{Math.min(currentPage * eventsPerPage, totalEvents)}</span> de <span className="font-medium">{totalEvents}</span> resultados
                        </p>
                      </div>
                      
                      <div className="flex items-center space-x-4">
                        <select
                          value={eventsPerPage}
                          onChange={handlePerPageChange}
                          className="mr-2 border-gray-700 bg-gray-700 text-gray-200 rounded-md text-sm"
                        >
                          <option value="10">10 por página</option>
                          <option value="25">25 por página</option>
                          <option value="50">50 por página</option>
                          <option value="100">100 por página</option>
                        </select>
                        
                        <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                          <button
                            onClick={() => goToPage(1)}
                            disabled={currentPage === 1}
                            className={`relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-700 bg-gray-800 text-sm font-medium ${currentPage === 1 ? 'text-gray-500 cursor-not-allowed' : 'text-gray-300 hover:bg-gray-700'}`}
                          >
                            <span className="sr-only">Primeira</span>
                            &laquo;
                          </button>
                          
                          <button
                            onClick={() => goToPage(currentPage - 1)}
                            disabled={currentPage === 1}
                            className={`relative inline-flex items-center px-2 py-2 border border-gray-700 bg-gray-800 text-sm font-medium ${currentPage === 1 ? 'text-gray-500 cursor-not-allowed' : 'text-gray-300 hover:bg-gray-700'}`}
                          >
                            <span className="sr-only">Anterior</span>
                            &lsaquo;
                          </button>
                          
                          {/* Botões de página numerados */}
                          {[...Array(Math.min(5, totalPages))].map((_, i) => {
                            // Mostrar números em torno da página atual
                            let pageNum;
                            if (totalPages <= 5) {
                              pageNum = i + 1;
                            } else if (currentPage <= 3) {
                              pageNum = i + 1;
                            } else if (currentPage >= totalPages - 2) {
                              pageNum = totalPages - 4 + i;
                            } else {
                              pageNum = currentPage - 2 + i;
                            }
                            
                            return (
                              <button
                                key={pageNum}
                                onClick={() => goToPage(pageNum)}
                                className={`relative inline-flex items-center px-4 py-2 border border-gray-700 text-sm font-medium ${
                                  currentPage === pageNum ? 'bg-gray-900 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                                }`}
                              >
                                {pageNum}
                              </button>
                            );
                          })}
                          
                          <button
                            onClick={() => goToPage(currentPage + 1)}
                            disabled={currentPage === totalPages}
                            className={`relative inline-flex items-center px-2 py-2 border border-gray-700 bg-gray-800 text-sm font-medium ${currentPage === totalPages ? 'text-gray-500 cursor-not-allowed' : 'text-gray-300 hover:bg-gray-700'}`}
                          >
                            <span className="sr-only">Próxima</span>
                            &rsaquo;
                          </button>
                          
                          <button
                            onClick={() => goToPage(totalPages)}
                            disabled={currentPage === totalPages}
                            className={`relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-700 bg-gray-800 text-sm font-medium ${currentPage === totalPages ? 'text-gray-500 cursor-not-allowed' : 'text-gray-300 hover:bg-gray-700'}`}
                          >
                            <span className="sr-only">Última</span>
                            &raquo;
                          </button>
                        </nav>
                      </div>
                    </div>
                  </div>
                </>
              )}
           </div>
         </div>
      </div>
      
      {/* Modal de Detalhes do Evento */}
      {selectedEvent && (
        <div className="fixed z-10 inset-0 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            {/* Overlay escuro */}
            <div 
              className="fixed inset-0 bg-gray-900 bg-opacity-75 transition-opacity" 
              aria-hidden="true"
              onClick={closeEventDetails}
            ></div>

            {/* Modal central */}
            <div className="inline-block align-bottom bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-3xl sm:w-full">
              <div className="bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="mt-3 sm:mt-0 sm:ml-4 w-full">
                    <div className="flex justify-between">
                      <h3 className="text-lg leading-6 font-medium text-gray-100" id="modal-title">
                        Detalhes do Evento
                      </h3>
                      <button 
                        onClick={closeEventDetails}
                        className="text-gray-400 hover:text-gray-200"
                      >
                        <span className="sr-only">Fechar</span>
                        <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                    
                    <div className="mt-4 grid grid-cols-1 md:grid-cols-5 gap-4">
                      {/* Coluna da imagem */}
                      <div className="md:col-span-3">
                        <EventImage 
                          eventId={selectedEvent.id} 
                          eventData={selectedEvent}
                          showBoundingBoxes={true}
                          className="bg-gray-900 rounded"
                        />
                        
                        {/* Controle de feedback */}
                        <FeedbackControl 
                          eventId={selectedEvent.id} 
                          initialValue={selectedEvent.feedback}
                          onFeedbackSubmit={(value) => handleFeedbackChange(selectedEvent.id, value)} 
                        />
                      </div>
                      
                      {/* Coluna de informações */}
                      <div className="md:col-span-2 space-y-4">
                        <div>
                          <div className="text-sm font-medium text-gray-400">ID do Evento:</div>
                          <div className="text-sm text-gray-200 break-all">{selectedEvent.id}</div>
                        </div>
                        
                        <div>
                          <div className="text-sm font-medium text-gray-400">Data/Hora:</div>
                          <div className="text-sm text-gray-200">{formatDate(selectedEvent.timestamp)}</div>
                        </div>
                        
                        <div>
                          <div className="text-sm font-medium text-gray-400">Tipo de Evento:</div>
                          <div className="text-sm text-gray-200">{selectedEvent.detection_type || selectedEvent.event_type || 'Evento'}</div>
                        </div>
                        
                        <div>
                          <div className="text-sm font-medium text-gray-400">Câmera:</div>
                          <div className="text-sm text-gray-200">
                            {cameras[selectedEvent.camera_id]?.name || selectedEvent.camera_name || selectedEvent.camera_id || 'N/A'}
                            {cameras[selectedEvent.camera_id]?.location && ` (${cameras[selectedEvent.camera_id].location})`}
                          </div>
                        </div>
                        
                        {selectedEvent.confidence && (
                          <div>
                            <div className="text-sm font-medium text-gray-400">Confiança:</div>
                            <div className="text-sm text-gray-200">{Math.round(selectedEvent.confidence * 100)}%</div>
                          </div>
                        )}
                        
                        {selectedEvent.details && (
                          <div>
                            <div className="text-sm font-medium text-gray-400">Detalhes:</div>
                            <div className="text-sm text-gray-200">{selectedEvent.details}</div>
                          </div>
                        )}
                        
                        {selectedEvent.labels && selectedEvent.labels.length > 0 && (
                          <div>
                            <div className="text-sm font-medium text-gray-400">Rótulos:</div>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {selectedEvent.labels.map((label, idx) => (
                                <span 
                                  key={idx} 
                                  className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-900 text-blue-200"
                                >
                                  {label}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {/* Botões de ação */}
                        <div className="pt-4 border-t border-gray-700">
                          <button
                            className="mt-2 w-full inline-flex justify-center items-center px-4 py-2 border border-gray-700 rounded-md shadow-sm text-sm font-medium text-gray-300 bg-gray-700 hover:bg-gray-600"
                            onClick={() => {/* Implementar download */}}
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                            </svg>
                            Baixar Imagem
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default EventsPage;