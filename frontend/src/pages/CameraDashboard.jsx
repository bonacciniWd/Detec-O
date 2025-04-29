import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import StreamModal from '../components/StreamModal';
import { FaPlus, FaSearch, FaSync, FaList, FaThLarge, FaCog, FaTrash, FaPen, FaPlay, FaStop, FaCircle } from 'react-icons/fa';
import cameraService from '../services/cameraService';
import { toast } from 'react-toastify';
import LiveSnapshotImage from '../components/LiveSnapshotImage';

const CameraDashboard = () => {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [devices, setDevices] = useState([]);
  const [streams, setStreams] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState('grid'); // 'grid' ou 'list'
  const [refreshInterval, setRefreshInterval] = useState(5000); // Intervalo padrão de 5 segundos
  
  // Estado para o modal de stream
  const [streamModal, setStreamModal] = useState({
    isOpen: false,
    deviceId: null,
    streamId: null,
    cameraName: ''
  });

  // Estado para confirmação de exclusão
  const [deleteConfirmation, setDeleteConfirmation] = useState({
    isOpen: false,
    deviceId: null,
    deviceName: ''
  });

  // Novo estado para rastrear status de processamento
  const [processingStatus, setProcessingStatus] = useState({}); // { cameraId: { is_running: boolean, last_error: string | null } }
  const [actionLoading, setActionLoading] = useState({}); // Para loading individual dos botões start/stop { cameraId: true/false }

  // Buscar dispositivos/câmeras do usuário
  useEffect(() => {
    const fetchDevices = async () => {
      try {
        setLoading(true);
        
        // Usar o cameraService para obter câmeras
        const devices = await cameraService.getCameras();
        
        setDevices(devices);
        setLoading(false);
      } catch (err) {
        console.error('Erro ao buscar dispositivos:', err);
        setError('Não foi possível carregar seus dispositivos. Por favor, tente novamente.');
        setLoading(false);
      }
    };
    
    fetchDevices();
  }, []);

  // Buscar streams para cada dispositivo
  useEffect(() => {
    const fetchStreams = async () => {
      const streamsMap = {};
      
      for (const device of devices) {
        try {
          // Usar o método específico para obter streams de dispositivos
          // Comentado temporariamente pois a API não existe
          // const streams = await cameraService.getDeviceStreams(device.id);
          // streamsMap[device.id] = streams;
          streamsMap[device.id] = []; // Definir como array vazio por enquanto
        } catch (err) {
          console.error(`Erro ao buscar streams para dispositivo ${device.id}:`, err);
          streamsMap[device.id] = [];
        }
      }
      
      setStreams(streamsMap);
    };
    
    if (devices.length > 0) {
      fetchStreams();
    }
  }, [devices]);

  // Filtrar dispositivos com base na pesquisa
  const filteredDevices = Array.isArray(devices) ? devices.filter(device => 
    device.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    device.manufacturer.toLowerCase().includes(searchTerm.toLowerCase()) ||
    device.ip_address.includes(searchTerm)
  ) : [];

  // Manipular clique de expansão de câmera
  const handleCameraExpand = (deviceId, streamId, cameraName) => {
    setStreamModal({
      isOpen: true,
      deviceId,
      streamId,
      cameraName
    });
  };

  // Fechar modal de stream
  const closeStreamModal = () => {
    setStreamModal({
      isOpen: false,
      deviceId: null,
      streamId: null,
      cameraName: ''
    });
  };

  // Manipular erro de câmera
  const handleCameraError = (deviceId, errorMessage) => {
    console.warn(`Erro na câmera ${deviceId}: ${errorMessage}`);
    // Você pode atualizar o status do dispositivo ou mostrar uma notificação aqui
  };

  // Manipular exclusão de câmera
  const handleDeleteCamera = async (deviceId, deviceName) => {
    // Abrir modal de confirmação
    setDeleteConfirmation({
      isOpen: true,
      deviceId,
      deviceName
    });
  };

  // Confirmar exclusão de câmera
  const confirmDeleteCamera = async () => {
    try {
      await cameraService.deleteDevice(deleteConfirmation.deviceId);
      toast.success(`Câmera "${deleteConfirmation.deviceName}" excluída com sucesso`);
      
      // Atualizar a lista de dispositivos removendo o excluído
      setDevices(devices.filter(device => device.id !== deleteConfirmation.deviceId));
      
      // Fechar o modal de confirmação
      setDeleteConfirmation({
        isOpen: false,
        deviceId: null,
        deviceName: ''
      });
    } catch (error) {
      console.error('Erro ao excluir câmera:', error);
      toast.error('Falha ao excluir câmera. Tente novamente.');
    }
  };

  // Manipular edição de câmera
  const handleEditCamera = (deviceId) => {
    navigate(`/camera/${deviceId}`);
  };

  // --- Handlers para Start/Stop --- 
  const handleStartProcessing = async (deviceId) => {
    setActionLoading(prev => ({ ...prev, [deviceId]: true }));
    try {
      const status = await cameraService.startProcessing(deviceId);
      setProcessingStatus(prev => ({ ...prev, [deviceId]: status }));
      toast.success(`Processamento iniciado para câmera ${deviceId}`);
    } catch (error) {
      const detail = error.response?.data?.detail || 'Erro desconhecido';
      setProcessingStatus(prev => ({ ...prev, [deviceId]: { is_running: false, last_error: detail } }));
      toast.error(`Erro ao iniciar: ${detail}`);
    } finally {
      setActionLoading(prev => ({ ...prev, [deviceId]: false }));
    }
  };

  const handleStopProcessing = async (deviceId) => {
    setActionLoading(prev => ({ ...prev, [deviceId]: true }));
    try {
      const status = await cameraService.stopProcessing(deviceId);
      // A resposta do stop pode já indicar is_running: false
      setProcessingStatus(prev => ({ ...prev, [deviceId]: { ...status, is_running: false } })); 
      toast.info(`Processamento parado para câmera ${deviceId}`);
    } catch (error) {
      const detail = error.response?.data?.detail || 'Erro desconhecido';
       // Mesmo com erro ao parar, assumir que parou ou está em estado inconsistente
      setProcessingStatus(prev => ({ ...prev, [deviceId]: { is_running: false, last_error: `Erro ao parar: ${detail}` } }));
      toast.error(`Erro ao parar: ${detail}`);
    } finally {
      setActionLoading(prev => ({ ...prev, [deviceId]: false }));
    }
  };

  // Renderizar lista de câmeras
  const renderCameras = () => {
    if (loading) {
      return (
        <div className="flex justify-center items-center h-64">
          <div className="loader"></div>
        </div>
      );
    }
    
    if (error) {
      return (
        <div className="text-center py-8">
          <p className="text-red-500 mb-4">{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Tentar novamente
          </button>
        </div>
      );
    }
    
    if (filteredDevices.length === 0) {
      if (searchTerm) {
        return (
          <div className="text-center py-8">
            <p className="text-gray-400">Nenhum dispositivo encontrado para "{searchTerm}".</p>
          </div>
        );
      }
      
      return (
        <div className="text-center py-8">
          <p className="text-gray-400 mb-4">Você ainda não tem dispositivos configurados.</p>
          <button 
            onClick={() => navigate('/add-camera')} 
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center justify-center mx-auto"
          >
            <FaPlus className="mr-2" />
            Adicionar Câmera
          </button>
        </div>
      );
    }
    
    // Renderizar dispositivos em modo grade ou lista
    return (
      <div className={viewMode === 'grid' ? 'grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4' : 'space-y-4'}>
        {filteredDevices.map(device => {
          const currentStatus = processingStatus[device.id] || { is_running: false, last_error: null };
          const isLoadingAction = actionLoading[device.id];

          return (
            <div 
              key={device.id} 
              className="bg-gray-800 rounded-lg shadow overflow-hidden border border-gray-700 text-gray-200"
            >
              {/* Lógica de exibição (Grid vs List) - Manteremos o Snapshot em ambos? */}
              {/* Exemplo SIMPLIFICADO mostrando snapshot no topo para ambos os modos */}
              <div className="w-full bg-gray-700 flex items-center justify-center text-gray-400 aspect-video"> {/* Aspect ratio */}
                <LiveSnapshotImage 
                  cameraId={device.id}
                  interval={refreshInterval}
                  className="w-full h-full"
                />
              </div>
              
              {/* Informações e Ações abaixo do snapshot */} 
              <div className="p-4">
                <div className="flex items-center justify-between mb-2">
                  {/* Status Indicator + Nome */}
                  <div className="flex items-center min-w-0">
                     <FaCircle 
                        className={`mr-2 flex-shrink-0 ${currentStatus.is_running ? 'text-green-500 animate-pulse' : 'text-red-500'}`}
                        size={10}
                        title={currentStatus.is_running ? 'Processando' : 'Parado'}
                     />
                    <h3 className="text-lg font-medium truncate" title={device.name}>{device.name}</h3>
                  </div>
                   {/* Botões de Ação (Edit/Delete) */}
                  <div className="flex items-center space-x-1 flex-shrink-0">
                    {/* Botão Start/Stop */} 
                    <button
                      onClick={() => currentStatus.is_running ? handleStopProcessing(device.id) : handleStartProcessing(device.id)}
                      disabled={isLoadingAction}
                      className={`p-1.5 rounded ${currentStatus.is_running 
                                      ? 'bg-red-600 hover:bg-red-700' 
                                      : 'bg-green-600 hover:bg-green-700'} 
                                   text-white disabled:opacity-50`}
                      title={currentStatus.is_running ? 'Parar Detecção' : 'Iniciar Detecção'}
                    >
                      {isLoadingAction ? 
                        <FaCog className="animate-spin" size={12}/> : 
                        (currentStatus.is_running ? <FaStop size={12}/> : <FaPlay size={12}/>)
                      }
                    </button>
                    <button 
                      onClick={() => handleEditCamera(device.id)}
                      className="p-1.5 bg-gray-700 text-gray-300 rounded hover:bg-gray-600"
                      title="Editar Configurações"
                    >
                      <FaPen size={12} />
                    </button>
                    <button 
                      onClick={() => handleDeleteCamera(device.id, device.name)}
                      className="p-1.5 bg-gray-700 text-gray-300 rounded hover:bg-gray-600"
                      title="Excluir Câmera"
                    >
                      <FaTrash size={12} />
                    </button>
                  </div>
                </div>
                {/* IP/Porta */} 
                <p className="text-xs text-gray-500 truncate" title={device.ip_address}>{device.ip_address}:{device.port}</p>
                {/* Exibir último erro se houver e não estiver rodando */}
                {!currentStatus.is_running && currentStatus.last_error && (
                    <p className="text-xs text-red-400 mt-1 truncate" title={currentStatus.last_error}>Erro: {currentStatus.last_error}</p>
                )}
              </div>

            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="bg-gray-900 text-gray-200 min-h-screen">
      <div className="container mx-auto px-4 py-6">
        {/* Cabeçalho */}
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-6">
          
          
          <div className="flex flex-col md:flex-row space-y-2 md:space-y-0 md:space-x-4">
            {/* Barra de pesquisa */}
            <div className="relative">
              <input
                type="text"
                placeholder="Buscar câmeras..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-200 w-full md:w-52 focus:outline-none focus:border-blue-500"
              />
              <FaSearch className="absolute left-3 top-3 text-gray-400" />
            </div>
            
            {/* Botões de ação */}
            <div className="flex space-x-2">
              <button 
                onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
                className="p-2 bg-gray-800 text-gray-300 rounded-lg hover:bg-gray-700"
                title={viewMode === 'grid' ? 'Ver como lista' : 'Ver como grade'}
              >
                {viewMode === 'grid' ? <FaList /> : <FaThLarge />}
              </button>
              
              <button 
                onClick={() => window.location.reload()}
                className="p-2 bg-gray-800 text-gray-300 rounded-lg hover:bg-gray-700"
                title="Atualizar"
              >
                <FaSync />
              </button>
              
              <button 
                onClick={() => navigate('/add-camera')}
                className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                title="Adicionar câmera"
              >
                <FaPlus />
              </button>
            </div>
          </div>
        </div>

        {/* Controle de intervalo de atualização */}
        <div className="mb-6 bg-gray-900 p-4 rounded-lg border border-gray-800">
          <label className="text-sm text-gray-400 mb-2 block">
            Intervalo de atualização: {refreshInterval/1000}s
          </label>
          <input
            type="range"
            min="1000"
            max="60000"
            step="1000"
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(parseInt(e.target.value))}
            className="w-full accent-blue-600"
          />
          <div className="flex justify-between text-xs text-gray-500">
            <span>1s</span>
            <span>30s</span>
            <span>60s</span>
          </div>
        </div>
        
        {/* Lista de câmeras */}
        {renderCameras()}
      </div>
      
      {/* Modal de stream */}
      {streamModal.isOpen && (
        <StreamModal
          deviceId={streamModal.deviceId}
          streamId={streamModal.streamId}
          cameraName={streamModal.cameraName}
          onClose={closeStreamModal}
        />
      )}

      {/* Modal de confirmação de exclusão */}
      {deleteConfirmation.isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full">
            <h3 className="text-xl font-semibold mb-4">Confirmar exclusão</h3>
            <p className="mb-6">
              Tem certeza que deseja excluir a câmera "{deleteConfirmation.deviceName}"? 
              Esta ação não pode ser desfeita.
            </p>
            <div className="flex justify-end space-x-3">
              <button 
                className="px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-600"
                onClick={() => setDeleteConfirmation({isOpen: false, deviceId: null, deviceName: ''})}
              >
                Cancelar
              </button>
              <button 
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                onClick={confirmDeleteCamera}
              >
                Excluir
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CameraDashboard; 