import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import eventService from '../services/eventService';
import notificationService from '../services/notificationService';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, AreaChart, Area
} from 'recharts';
import { startOfDay, format, subDays, parseISO } from 'date-fns';
import { ptBR } from 'date-fns/locale';

// Cores para gráficos
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658'];
const SEVERITY_COLORS = {
  red: '#ef4444',
  yellow: '#f59e0b',
  blue: '#3b82f6'
};

function DashboardPage() {
  const { user } = useAuth();
  const [statistics, setStatistics] = useState({
    totalCameras: 0,
    activeCameras: 0,
    totalEvents: 0,
    eventsByType: {},
    recentEvents: [],
    eventsByZone: [],
    eventsBySeverity: [],
    eventsTimeSeries: [],
    detectionAccuracy: 0
  });

  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingEvents, setIsLoadingEvents] = useState(false);
  const [eventsError, setEventsError] = useState(null);
  const [timeRange, setTimeRange] = useState('7d'); // '24h', '7d', '30d'
  const [activeTab, setActiveTab] = useState('overview'); // 'overview', 'cameras', 'events', 'zones'

  useEffect(() => {
    const fetchDashboardData = async () => {
      setIsLoading(true);
      try {
        // Aqui chamaria APIs reais para buscar dados do dashboard
        const camerasResponse = await api.get('/api/v1/cameras');
        const eventsResponse = await api.get('/api/v1/events', { params: { limit: 50 } });
        
        // Processamento simplificado para demonstração
        let cameraList = [];
        if (Array.isArray(camerasResponse.data)) {
          cameraList = camerasResponse.data;
        } else if (camerasResponse.data && camerasResponse.data.items) {
          cameraList = camerasResponse.data.items;
        }
        
        let eventsList = [];
        if (Array.isArray(eventsResponse.data)) {
          eventsList = eventsResponse.data;
        } else if (eventsResponse.data && eventsResponse.data.items) {
          eventsList = eventsResponse.data.items;
        }
        
        // Calcular estatísticas básicas
        const activeCameras = cameraList.filter(cam => cam.running || cam.detection_enabled).length;
        
        // Calcular distribuição por tipo de evento
        const eventsByType = eventsList.reduce((acc, event) => {
          acc[event.event_type] = (acc[event.event_type] || 0) + 1;
          return acc;
        }, {});
        
        // Calcular distribuição por severidade
        const eventsBySeverity = eventsList.reduce((acc, event) => {
          const severity = event.severity || 'blue';
          acc[severity] = (acc[severity] || 0) + 1;
          return acc;
        }, {});

        // Formatar dados para o gráfico de severidade
        const severityChartData = Object.keys(eventsBySeverity).map(key => ({
          name: key === 'red' ? 'Crítico' : key === 'yellow' ? 'Atenção' : 'Informativo',
          value: eventsBySeverity[key],
          color: SEVERITY_COLORS[key] || '#999'
        }));
        
        // Calcular eventos por zona (mock data, em produção viria da API)
        const eventsByZone = [
          { name: 'Entrada Principal', events: 18, trustedEvents: 15 },
          { name: 'Estacionamento', events: 12, trustedEvents: 9 },
          { name: 'Perímetro', events: 8, trustedEvents: 7 },
          { name: 'Recepção', events: 5, trustedEvents: 5 }
        ];
        
        // Calcular série temporal para últimos 7 dias (mock data, em produção viria da API)
        const now = new Date();
        const eventsTimeSeries = Array.from({ length: 7 }, (_, i) => {
          const date = subDays(now, 6 - i);
          return {
            date: format(date, 'dd/MM', { locale: ptBR }),
            eventos: Math.floor(Math.random() * 10) + 1,
            alertas: Math.floor(Math.random() * 5),
          };
        });

        // Calcular taxa de precisão geral (razão entre eventos confirmados e total)
        const totalConfirmed = eventsList.filter(event => event.feedback === true).length;
        const detectionAccuracy = eventsList.length > 0 
          ? (totalConfirmed / eventsList.length) * 100 
          : 0;
        
        setStatistics({
          totalCameras: cameraList.length,
          activeCameras,
          totalEvents: eventsList.length,
          eventsByType,
          recentEvents: eventsList.slice(0, 5),
          eventsByZone,
          eventsBySeverity: severityChartData,
          eventsTimeSeries,
          detectionAccuracy: Math.round(detectionAccuracy)
        });
      } catch (error) {
        console.error("Erro ao buscar dados do dashboard:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, [timeRange]);

  const fetchRecentEvents = async () => {
    setIsLoadingEvents(true);
    try {
      // Buscando os últimos 5 eventos
      const events = await eventService.getEvents({ limit: 5 });
      setStatistics(prev => ({ ...prev, recentEvents: events }));
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

  const formatDate = (dateString) => {
    if (!dateString) return '';
    try {
      return new Date(dateString).toLocaleString('pt-BR');
    } catch (e) {
      return dateString;
    }
  };

  // Formatar dados para gráfico de tipos de eventos
  const getEventTypeChartData = () => {
    return Object.keys(statistics.eventsByType).map((key, index) => ({
      name: key,
      value: statistics.eventsByType[key],
      color: COLORS[index % COLORS.length]
    }));
  };

  // Renderização dos filtros de tempo
  const renderTimeFilters = () => (
    <div className="mb-4 flex space-x-2">
      <button
        className={`px-3 py-1 text-sm rounded-md ${timeRange === '24h' ? 'bg-blue-600 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}`}
        onClick={() => setTimeRange('24h')}
      >
        24 horas
      </button>
      <button
        className={`px-3 py-1 text-sm rounded-md ${timeRange === '7d' ? 'bg-blue-600 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}`}
        onClick={() => setTimeRange('7d')}
      >
        7 dias
      </button>
      <button
        className={`px-3 py-1 text-sm rounded-md ${timeRange === '30d' ? 'bg-blue-600 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}`}
        onClick={() => setTimeRange('30d')}
      >
        30 dias
      </button>
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      {/* Cabeçalho agora é renderizado no MainLayout */}

      {isLoading ? (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
          <span className="ml-2 text-gray-800 dark:text-white">Carregando...</span>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Filtros de navegação e tempo */}
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center space-y-4 sm:space-y-0">
            <div className="flex space-x-2 border-b border-gray-200 dark:border-gray-700 w-full sm:w-auto">
              <button 
                className={`px-4 py-2 font-medium ${activeTab === 'overview' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 dark:text-gray-400'}`}
                onClick={() => setActiveTab('overview')}
              >
                Visão Geral
              </button>
              <button 
                className={`px-4 py-2 font-medium ${activeTab === 'events' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 dark:text-gray-400'}`}
                onClick={() => setActiveTab('events')}
              >
                Eventos
              </button>
              <button 
                className={`px-4 py-2 font-medium ${activeTab === 'zones' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 dark:text-gray-400'}`}
                onClick={() => setActiveTab('zones')}
              >
                Zonas
              </button>
            </div>
            {renderTimeFilters()}
          </div>

          {/* Cartões de Estatísticas */}
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {/* Câmeras Totais */}
            <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0 bg-blue-500 rounded-md p-3">
                    <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Câmeras Totais</dt>
                      <dd className="flex items-baseline">
                        <div className="text-2xl font-semibold text-gray-800 dark:text-white">{statistics.totalCameras}</div>
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            {/* Câmeras Ativas */}
            <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0 bg-green-500 rounded-md p-3">
                    <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Câmeras Ativas</dt>
                      <dd className="flex items-baseline">
                        <div className="text-2xl font-semibold text-gray-800 dark:text-white">{statistics.activeCameras}</div>
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            {/* Total de Eventos */}
            <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0 bg-yellow-500 rounded-md p-3">
                    <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Total de Eventos</dt>
                      <dd className="flex items-baseline">
                        <div className="text-2xl font-semibold text-gray-800 dark:text-white">{statistics.totalEvents}</div>
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            {/* Taxa de Precisão */}
            <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0 bg-indigo-500 rounded-md p-3">
                    <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Taxa de Precisão</dt>
                      <dd className="flex items-baseline">
                        <div className="text-2xl font-semibold text-gray-800 dark:text-white">{statistics.detectionAccuracy}%</div>
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Conteúdo baseado na aba ativa */}
          {activeTab === 'overview' && (
            <>
              {/* Gráficos principais - Linha do tempo e distribuição */}
              <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
                {/* Gráfico de linha de tempo */}
                <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg p-4">
                  <h3 className="text-lg leading-6 font-medium text-gray-800 dark:text-white mb-4">Eventos ao Longo do Tempo</h3>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart
                        data={statistics.eventsTimeSeries}
                        margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="#555" />
                        <XAxis dataKey="date" stroke="#888" />
                        <YAxis stroke="#888" />
                        <Tooltip />
                        <Legend />
                        <Area type="monotone" dataKey="eventos" stroke="#8884d8" fill="#8884d8" fillOpacity={0.2} />
                        <Area type="monotone" dataKey="alertas" stroke="#ff8042" fill="#ff8042" fillOpacity={0.2} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Gráfico de distribuição por severidade */}
                <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg p-4">
                  <h3 className="text-lg leading-6 font-medium text-gray-800 dark:text-white mb-4">Distribuição por Severidade</h3>
                  <div className="h-64 flex justify-center">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={statistics.eventsBySeverity && statistics.eventsBySeverity.length > 0 ? 
                            statistics.eventsBySeverity : 
                            [{ name: 'Sem dados', value: 1, color: '#aaa' }]
                          }
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="value"
                          nameKey="name"
                          label={({ name, percent }) => `${name} ${percent ? (percent * 100).toFixed(0) : 0}%`}
                        >
                          {(statistics.eventsBySeverity && statistics.eventsBySeverity.length > 0 ? 
                            statistics.eventsBySeverity : 
                            [{ name: 'Sem dados', value: 1, color: '#aaa' }]
                          ).map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip contentStyle={{ backgroundColor: 'white', color: '#333' }} />
                        <Legend formatter={(value) => <span style={{ color: '#555' }}>{value}</span>} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>

              {/* Eventos Recentes */}
              <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg">
                <div className="px-4 py-5 sm:px-6 border-b border-gray-200 dark:border-gray-700">
                  <h3 className="text-lg leading-6 font-medium text-gray-800 dark:text-white">Eventos Recentes</h3>
                  <p className="mt-1 max-w-2xl text-sm text-gray-500 dark:text-gray-400">Últimas detecções do sistema.</p>
                </div>
                {statistics.recentEvents.length > 0 ? (
                  <div className="divide-y divide-gray-200 dark:divide-gray-700">
                    {statistics.recentEvents.map((event) => (
                      <div key={event.id} className="px-4 py-4 sm:px-6 hover:bg-gray-50 dark:hover:bg-gray-700">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <div className={`flex-shrink-0 h-3 w-3 rounded-full ${
                              event.severity === 'red' ? 'bg-red-500' : 
                              event.severity === 'yellow' ? 'bg-yellow-500' : 'bg-blue-500'
                            }`}></div>
                            <p className="ml-2 text-sm font-medium text-gray-800 dark:text-white truncate">{event.event_type}</p>
                          </div>
                          <div className="ml-2 flex-shrink-0 flex">
                            <p className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300">
                              {formatDate(event.timestamp)}
                            </p>
                          </div>
                        </div>
                        <div className="mt-2 sm:flex sm:justify-between">
                          <div className="sm:flex">
                            <p className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                              {event.camera_name || 'Câmera desconhecida'}
                              {event.zone_name && (
                                <span className="ml-2 px-2 py-0.5 text-xs rounded bg-gray-200 dark:bg-gray-700">
                                  {event.zone_name}
                                </span>
                              )}
                            </p>
                          </div>
                          <div className="mt-2 flex items-center text-sm text-gray-500 dark:text-gray-400 sm:mt-0">
                            <span className="mr-1">Confiança:</span>
                            <span>{Math.round(event.confidence * 100)}%</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="px-4 py-5 text-center text-gray-500 dark:text-gray-400">
                    Nenhum evento registrado recentemente.
                  </div>
                )}
              </div>
            </>
          )}

          {/* Aba de Eventos */}
          {activeTab === 'events' && (
            <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
              {/* Gráfico de Tipos de Eventos */}
              <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg p-4">
                <h3 className="text-lg leading-6 font-medium text-gray-800 dark:text-white mb-4">Tipos de Eventos</h3>
                <div className="h-64 overflow-x-auto">
                  <ResponsiveContainer width="100%" height="100%" minWidth={300}>
                    <BarChart
                      data={getEventTypeChartData()}
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                      layout="vertical"
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" />
                      <YAxis dataKey="name" type="category" stroke="#555" />
                      <Tooltip contentStyle={{ backgroundColor: 'white', color: '#333' }} />
                      <Legend formatter={(value) => <span style={{ color: '#555' }}>{value}</span>} />
                      <Bar dataKey="value" name="Quantidade">
                        {getEventTypeChartData().map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Gráfico de Eventos por Hora */}
              <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg p-4">
                <h3 className="text-lg leading-6 font-medium text-gray-800 dark:text-white mb-4">Distribuição por Hora do Dia</h3>
                <div className="h-64 overflow-x-auto">
                  <ResponsiveContainer width="100%" height="100%" minWidth={300}>
                    <BarChart
                      data={[
                        { name: '00-04h', eventos: 5 },
                        { name: '04-08h', eventos: 3 },
                        { name: '08-12h', eventos: 12 },
                        { name: '12-16h', eventos: 18 },
                        { name: '16-20h', eventos: 22 },
                        { name: '20-24h', eventos: 10 }
                      ]}
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="eventos" name="Eventos" fill="#8884d8" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}
          
          {/* Aba de Zonas */}
          {activeTab === 'zones' && (
            <div className="space-y-6">
              {/* Eventos por Zona */}
              <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg p-4">
                <h3 className="text-lg leading-6 font-medium text-gray-800 dark:text-white mb-4">Eventos por Zona de Detecção</h3>
                <div className="h-64 overflow-x-auto">
                  <ResponsiveContainer width="100%" height="100%" minWidth={300}>
                    <BarChart
                      data={statistics.eventsByZone && statistics.eventsByZone.length > 0 ? 
                        statistics.eventsByZone : 
                        [{ name: 'Sem dados', events: 0, trustedEvents: 0 }]
                      }
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip 
                        cursor={{fill: 'rgba(0, 0, 0, 0.05)'}} 
                        contentStyle={{ backgroundColor: 'white', color: '#333' }}
                      />
                      <Legend formatter={(value) => <span style={{ color: '#555' }}>{value}</span>} />
                      <Bar dataKey="events" name="Total de Eventos" fill="#8884d8" />
                      <Bar dataKey="trustedEvents" name="Eventos Confirmados" fill="#82ca9d" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Tabela de Zonas */}
              <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg">
                <div className="px-4 py-5 sm:px-6 border-b border-gray-200 dark:border-gray-700">
                  <h3 className="text-lg leading-6 font-medium text-gray-800 dark:text-white">Detalhes por Zona</h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-700">
                      <tr>
                        <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                          Zona
                        </th>
                        <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                          Total
                        </th>
                        <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                          Confirmados
                        </th>
                        <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                          Precisão
                        </th>
                        <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                          Tipo Comum
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                      {(statistics.eventsByZone || []).map((zone) => (
                        <tr key={zone.name} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                          <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                            {zone.name}
                          </td>
                          <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                            {zone.events}
                          </td>
                          <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                            {zone.trustedEvents}
                          </td>
                          <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                            {Math.round((zone.trustedEvents / zone.events) * 100)}%
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                            {zone.name === 'Entrada Principal' ? 'Pessoa' : 
                              zone.name === 'Estacionamento' ? 'Veículo' : 
                              zone.name === 'Perímetro' ? 'Movimento' : 'Pessoa'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default DashboardPage; 