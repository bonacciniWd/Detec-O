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
import { startOfDay, format, subDays, parseISO, formatISO } from 'date-fns';
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
    eventsBySeverity: [],
    eventsTimeSeries: [],
    eventsByHour: [],
    detectionAccuracy: 0
  });

  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingEvents, setIsLoadingEvents] = useState(false);
  const [eventsError, setEventsError] = useState(null);
  const [timeRange, setTimeRange] = useState('30d');
  const [activeTab, setActiveTab] = useState('overview'); // 'overview', 'cameras', 'events', 'zones'

  const fetchDashboardData = async (rangeOverride = null) => {
    const currentRange = rangeOverride || timeRange;
    
    if (rangeOverride) {
      setIsLoading(true);
    }

    try {
      setEventsError(null);
      
      const endDate = new Date();
      let startDate;
      switch (currentRange) {
        case '24h':
          startDate = subDays(endDate, 1);
          break;
        case '30d':
          startDate = subDays(endDate, 30);
          break;
        case '7d':
        default:
          startDate = subDays(endDate, 7);
      }
      const paramsDateFilter = {
        start_date: formatISO(startDate, { representation: 'date' }),
        end_date: formatISO(endDate, { representation: 'date' })
      };

      const [camerasResponse, generalEventsResponse, timeSeriesResponse, hourlyResponse] = await Promise.all([
        api.get('/api/cameras/'),
        api.get('/api/events/', { params: { limit: 50 } }),
        eventService.getEventTimeSeries(paramsDateFilter),
        eventService.getEventHourlyDistribution(paramsDateFilter)
      ]).catch(error => {
        console.error("[DashboardPage] Erro no Promise.all:", error);
        return [{ data: [] }, { data: [] }, [], []]; 
      });

      const cameraList = Array.isArray(camerasResponse.data) ? camerasResponse.data : [];
      const eventsList = Array.isArray(generalEventsResponse.data) ? generalEventsResponse.data : [];
      const activeCameras = cameraList.filter(cam => cam.running || cam.detection_enabled).length;
      const eventsByType = eventsList.reduce((acc, event) => {
        acc[event.event_type] = (acc[event.event_type] || 0) + 1;
        return acc;
      }, {});
      const eventsBySeverity = eventsList.reduce((acc, event) => {
        const severity = event.severity || 'blue';
        acc[severity] = (acc[severity] || 0) + 1;
        return acc;
      }, {});
      const severityChartData = Object.keys(eventsBySeverity).map(key => ({
        name: key === 'red' ? 'Crítico' : key === 'yellow' ? 'Atenção' : 'Informativo',
        value: eventsBySeverity[key],
        color: SEVERITY_COLORS[key] || '#999'
      }));
      const totalFeedbackGiven = eventsList.filter(event => event.feedback_status).length;
      const totalConfirmed = eventsList.filter(event => event.feedback_status === 'true_positive').length;
      const detectionAccuracy = totalFeedbackGiven > 0 ? (totalConfirmed / totalFeedbackGiven) * 100 : 0;

      const formattedTimeSeries = timeSeriesResponse.map(point => {
        try {
          return {
            date: format(parseISO(point.date + 'T00:00:00'), 'dd/MM', { locale: ptBR }), 
            eventos: point.count,
            alertas: 0
          };
        } catch (e) {
          return null;
        }
      }).filter(point => point !== null);

      const formattedHourlyData = hourlyResponse.map(item => ({
        name: `${String(item.hour).padStart(2, '0')}h`,
        eventos: item.count
      }));

      setStatistics(prev => ({
        ...prev,
        totalCameras: cameraList.length,
        activeCameras,
        totalEvents: eventsList.length,
        eventsByType,
        eventsBySeverity: severityChartData,
        eventsTimeSeries: formattedTimeSeries,
        eventsByHour: formattedHourlyData,
        detectionAccuracy: Math.round(detectionAccuracy)
      }));
    } catch (err) {
      console.error('\n[DashboardPage] Erro geral em fetchDashboardData:', err);
      setEventsError('Não foi possível carregar os dados do dashboard. Tente recarregar.');
    } finally {
      if (rangeOverride) {
        setIsLoading(false);
      }
    }
  };

  const fetchRecentEvents = async () => {
    setIsLoadingEvents(true);
    try {
      const events = await eventService.getEvents({ limit: 5 });
      const safeEvents = Array.isArray(events) ? events : [];
      setStatistics(prev => ({ ...prev, recentEvents: safeEvents }));
    } catch (error) {
      console.error("Erro ao buscar eventos recentes:", error);
      setEventsError("Não foi possível carregar os eventos recentes.");
      setStatistics(prev => ({ ...prev, recentEvents: [] }));
    } finally {
      setIsLoadingEvents(false);
    }
  };

  useEffect(() => {
    const intervalId = setInterval(() => {
      fetchDashboardData();
    }, 30000);
    return () => clearInterval(intervalId);
  }, []);

  useEffect(() => {
    const initialFetch = async () => {
      setIsLoading(true);
      await fetchDashboardData();
      await fetchRecentEvents();
      setIsLoading(false);
    };
    initialFetch();
  }, []);

  useEffect(() => {
    const handleNewEvent = (eventData) => {
      console.log("Novo evento detectado via callback, atualizando recentes:", eventData);
      fetchRecentEvents();
    };
    notificationService.addEventCallback(handleNewEvent);
    return () => {
      notificationService.removeEventCallback(handleNewEvent);
    };
  }, []);

  const handleTimeRangeChange = (newRange) => {
    setTimeRange(newRange);
    fetchDashboardData(newRange);
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    try {
      return new Date(dateString).toLocaleString('pt-BR');
    } catch (e) {
      return dateString;
    }
  };

  const getEventTypeChartData = () => {
    return Object.keys(statistics.eventsByType).map((key, index) => ({
      name: key,
      value: statistics.eventsByType[key],
      color: COLORS[index % COLORS.length]
    }));
  };

  const renderTimeFilters = () => (
    <div className="mb-4 flex space-x-2">
      <button
        className={`px-3 py-1 text-sm rounded-md ${timeRange === '24h' ? 'bg-blue-600 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}`}
        onClick={() => handleTimeRangeChange('24h')}
      >
        24 horas
      </button>
      <button
        className={`px-3 py-1 text-sm rounded-md ${timeRange === '7d' ? 'bg-blue-600 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}`}
        onClick={() => handleTimeRangeChange('7d')}
      >
        7 dias
      </button>
      <button
        className={`px-3 py-1 text-sm rounded-md ${timeRange === '30d' ? 'bg-blue-600 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}`}
        onClick={() => handleTimeRangeChange('30d')}
      >
        30 dias
      </button>
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <style global jsx>{`
        @media (max-width: 640px) { 
          .pie-chart-label {
            font-size: 10px !important; 
          }
        }
      `}</style>

      {isLoading ? (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
          <span className="ml-2 text-gray-800 dark:text-white">Carregando...</span>
        </div>
      ) : (
        <div className="space-y-6">
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
            </div>
            {renderTimeFilters()}
          </div>

          <div className="grid grid-cols-2 gap-4 md:gap-5 lg:grid-cols-4">
            <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
              <div className="px-3 py-4 sm:px-4 sm:py-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0 bg-blue-500 rounded-md p-2 sm:p-3">
                    <svg className="h-5 w-5 sm:h-6 sm:w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <div className="ml-3 sm:ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-xs sm:text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Câmeras Totais</dt>
                      <dd className="flex items-baseline">
                        <div className="text-xl sm:text-2xl font-semibold text-gray-800 dark:text-white">{statistics.totalCameras}</div>
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
              <div className="px-3 py-4 sm:px-4 sm:py-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0 bg-green-500 rounded-md p-2 sm:p-3">
                    <svg className="h-5 w-5 sm:h-6 sm:w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="ml-3 sm:ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-xs sm:text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Câmeras Ativas</dt>
                      <dd className="flex items-baseline">
                        <div className="text-xl sm:text-2xl font-semibold text-gray-800 dark:text-white">{statistics.activeCameras}</div>
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
              <div className="px-3 py-4 sm:px-4 sm:py-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0 bg-yellow-500 rounded-md p-2 sm:p-3">
                    <svg className="h-5 w-5 sm:h-6 sm:w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  </div>
                  <div className="ml-3 sm:ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-xs sm:text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Total de Eventos</dt>
                      <dd className="flex items-baseline">
                        <div className="text-xl sm:text-2xl font-semibold text-gray-800 dark:text-white">{statistics.totalEvents}</div>
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
              <div className="px-3 py-4 sm:px-4 sm:py-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0 bg-indigo-500 rounded-md p-2 sm:p-3">
                    <svg className="h-5 w-5 sm:h-6 sm:w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <div className="ml-3 sm:ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-xs sm:text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Taxa de Precisão</dt>
                      <dd className="flex items-baseline">
                        <div className="text-xl sm:text-2xl font-semibold text-gray-800 dark:text-white">{statistics.detectionAccuracy}%</div>
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {activeTab === 'overview' && (
            <>
              <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
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

                <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg p-4 flex flex-col">
                  <h3 className="text-lg leading-6 font-medium text-gray-800 dark:text-white mb-4">Distribuição por Severidade</h3>
                  <div className="h-64 flex justify-center flex-grow">
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
                        >
                          {(statistics.eventsBySeverity && statistics.eventsBySeverity.length > 0 ? 
                            statistics.eventsBySeverity : 
                            [{ name: 'Sem dados', value: 1, color: '#aaa' }]
                          ).map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip contentStyle={{ backgroundColor: 'white', color: '#333' }} />
                        <Legend formatter={(value) => <span style={{ color: '#9ca3af' }}>{value}</span>} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="mt-4 pt-4 border-t border-gray-700">
                    <ul className="space-y-2">
                      {(statistics.eventsBySeverity && statistics.eventsBySeverity.length > 0 ? 
                        statistics.eventsBySeverity : 
                        [{ name: 'Sem dados', value: 'N/A', color: '#aaa' }]
                      ).map((entry, index) => (
                        <li key={`severity-item-${index}`} className="flex items-center justify-between text-sm">
                          <div className="flex items-center">
                            <span 
                              className="inline-block h-3 w-3 rounded-full mr-2"
                              style={{ backgroundColor: entry.color }}
                            ></span>
                            <span className="text-gray-400">{entry.name}:</span>
                          </div>
                          <span className="font-medium text-gray-300">{entry.value}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg">
                <div className="px-4 py-5 sm:px-6 border-b border-gray-200 dark:border-gray-700">
                  <h3 className="text-lg leading-6 font-medium text-gray-800 dark:text-white">Eventos Recentes</h3>
                  <p className="mt-1 max-w-2xl text-sm text-gray-500 dark:text-gray-400">Últimas detecções do sistema.</p>
                </div>
                {Array.isArray(statistics.recentEvents) && statistics.recentEvents.length > 0 ? (
                  <div className="divide-y divide-gray-200 dark:divide-gray-700">
                    {statistics.recentEvents.map((event) => (
                      <div key={event.id || Math.random()} className="px-4 py-4 sm:px-6 hover:bg-gray-50 dark:hover:bg-gray-700">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <div className={`flex-shrink-0 h-3 w-3 rounded-full ${
                              event.severity === 'red' ? 'bg-red-500' : 
                              event.severity === 'yellow' ? 'bg-yellow-500' : 'bg-blue-500'
                            }`}></div>
                            <p className="ml-2 text-sm font-medium text-gray-800 dark:text-white truncate">{event.event_type || 'Evento'}</p>
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
                            <span>{Math.round((event.confidence || 0) * 100)}%</span>
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

          {activeTab === 'events' && (
            <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
              <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg p-4">
                <h3 className="text-lg leading-6 font-medium text-gray-800 dark:text-white mb-4">Tipos de Eventos</h3>
                <div className="h-64 overflow-x-auto">
                  <ResponsiveContainer width="100%" height="100%" minWidth={300}>
                    <BarChart
                      data={getEventTypeChartData()}
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                      layout="vertical"
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#555"/>
                      <XAxis type="number" stroke="#888" />
                      <YAxis dataKey="name" type="category" stroke="#888" width={40} />
                      <Tooltip 
                        cursor={{fill: 'rgba(100, 100, 100, 0.1)'}} 
                        contentStyle={{ backgroundColor: '#2d3748', border: 'none', borderRadius: '4px'}}
                        itemStyle={{ color: '#cbd5e0' }}
                        labelStyle={{ color: '#e2e8f0', fontWeight: 'bold' }}
                      />
                      <Bar dataKey="value" name="Quantidade">
                        {getEventTypeChartData().map((entry, index) => (
                          <Cell key={`cell-type-${index}`} fill={entry.color} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg p-4">
                <h3 className="text-lg leading-6 font-medium text-gray-800 dark:text-white mb-4">Distribuição por Hora do Dia</h3>
                <div className="h-64 overflow-x-auto">
                  <ResponsiveContainer width="100%" height="100%" minWidth={300}>
                    <BarChart
                      data={statistics.eventsByHour}
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#555" />
                      <XAxis dataKey="name" stroke="#888"/>
                      <YAxis stroke="#888" />
                      <Tooltip 
                        cursor={{fill: 'rgba(100, 100, 100, 0.1)'}} 
                        contentStyle={{ backgroundColor: '#2d3748', border: 'none', borderRadius: '4px'}}
                        itemStyle={{ color: '#cbd5e0' }}
                        labelStyle={{ color: '#e2e8f0', fontWeight: 'bold' }}
                      />
                      <Bar dataKey="eventos" name="Eventos">
                        {(statistics.eventsByHour || []).map((entry, index) => (
                          <Cell key={`cell-hour-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
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