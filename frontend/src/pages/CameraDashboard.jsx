import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import CameraSnapshot from '../components/CameraSnapshot';
import StreamModal from '../components/StreamModal';
import { FaPlus, FaSearch, FaSync, FaList, FaThLarge, FaCog, FaTrash, FaPen } from 'react-icons/fa';
import apiClient from '../services/api';
import { toast } from 'react-toastify';

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

  // Buscar dispositivos/câmeras do usuário
  useEffect(() => {
    const fetchDevices = async () => {
      try {
        setLoading(true);
        
        // Usar o método específico para obter lista de dispositivos
        const devices = await apiClient.getDevices();
        
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
          const streams = await apiClient.getDeviceStreams(device.id);
          
          streamsMap[device.id] = streams;
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
      await apiClient.deleteDevice(deleteConfirmation.deviceId);
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
          // Pegar o primeiro stream disponível para este dispositivo
          const deviceStreams = streams[device.id] || [];
          const primaryStream = deviceStreams.length > 0 ? deviceStreams[0] : null;
          
          if (!primaryStream) {
            // Mostrar um dispositivo sem streams
            return (
              <div 
                key={device.id} 
                className="bg-gray-800 rounded-lg shadow overflow-hidden border border-gray-700 text-gray-200"
              >
                <div className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-lg font-medium">{device.name}</h3>
                    <div className="flex items-center space-x-2">
                      <span className={`status-indicator ${device.status === 'online' ? 'status-online' : 'status-offline'}`}></span>
                      <button 
                        onClick={() => handleEditCamera(device.id)}
                        className="p-1 text-gray-400 hover:text-blue-400"
                        title="Editar câmera"
                      >
                        <FaPen size={14} />
                      </button>
                      <button 
                        onClick={() => handleDeleteCamera(device.id, device.name)}
                        className="p-1 text-gray-400 hover:text-red-400"
                        title="Excluir câmera"
                      >
                        <FaTrash size={14} />
                      </button>
                    </div>
                  </div>
                  <p className="text-sm text-gray-400">{device.manufacturer} {device.model}</p>
                  <p className="text-xs text-gray-500">{device.ip_address}</p>
                  <div className="mt-4 p-8 bg-gray-700 rounded flex items-center justify-center">
                    <p className="text-gray-400">Nenhum stream disponível</p>
                  </div>
                </div>
              </div>
            );
          }
          
          // Mostrar dispositivo com snapshot
          return (
            <div 
              key={device.id} 
              className="bg-gray-800 rounded-lg shadow overflow-hidden border border-gray-700 text-gray-200"
            >
              {viewMode === 'grid' ? (
                <>
                  <div className="relative">
                    <CameraSnapshot 
                      deviceId={device.id}
                      streamId={primaryStream.id}
                      cameraName={device.name}
                      interval={refreshInterval}
                      onExpand={handleCameraExpand}
                      onError={handleCameraError}
                      showControls={true}
                      autoRefresh={true}
                    />
                    <div className="absolute top-2 right-2 flex space-x-1">
                      <button 
                        onClick={() => handleEditCamera(device.id)}
                        className="p-1 bg-gray-900 bg-opacity-70 text-white rounded hover:bg-opacity-90"
                        title="Editar câmera"
                      >
                        <FaPen size={12} />
                      </button>
                      <button 
                        onClick={() => handleDeleteCamera(device.id, device.name)}
                        className="p-1 bg-gray-900 bg-opacity-70 text-white rounded hover:bg-opacity-90"
                        title="Excluir câmera"
                      >
                        <FaTrash size={12} />
                      </button>
                    </div>
                  </div>
                </>
              ) : (
                <div className="flex">
                  <div className="w-48">
                    <CameraSnapshot 
                      deviceId={device.id}
                      streamId={primaryStream.id}
                      cameraName={device.name}
                      interval={refreshInterval}
                      onExpand={handleCameraExpand}
                      onError={handleCameraError}
                      showControls={false}
                      autoRefresh={true}
                    />
                  </div>
                  <div className="p-4 flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-lg font-medium">{device.name}</h3>
                      <div className="flex items-center space-x-2">
                        <span className={`status-indicator ${device.status === 'online' ? 'status-online' : 'status-offline'}`}></span>
                        <button 
                          onClick={() => handleEditCamera(device.id)}
                          className="p-1 text-gray-400 hover:text-blue-400"
                          title="Editar câmera"
                        >
                          <FaPen size={14} />
                        </button>
                        <button 
                          onClick={() => handleDeleteCamera(device.id, device.name)}
                          className="p-1 text-gray-400 hover:text-red-400"
                          title="Excluir câmera"
                        >
                          <FaTrash size={14} />
                        </button>
                      </div>
                    </div>
                    <p className="text-sm text-gray-400">{device.manufacturer} {device.model}</p>
                    <p className="text-xs text-gray-500">{device.ip_address}</p>
                    <div className="mt-2 flex">
                      <button 
                        onClick={() => handleCameraExpand(device.id, primaryStream.id, device.name)}
                        className="text-xs text-blue-400 hover:underline"
                      >
                        Ver Stream
                      </button>
                      <span className="mx-2 text-gray-600">|</span>
                      <button 
                        onClick={() => navigate(`/camera/${device.id}`)}
                        className="text-xs text-blue-400 hover:underline"
                      >
                        Configurações
                      </button>
                    </div>
                  </div>
                </div>
              )}
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