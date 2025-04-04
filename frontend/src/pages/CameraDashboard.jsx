import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import MainLayout from '../components/MainLayout';
import CameraSnapshot from '../components/CameraSnapshot';
import StreamModal from '../components/StreamModal';
import { FaPlus, FaSearch, FaSync, FaList, FaThLarge } from 'react-icons/fa';
import axios from 'axios';

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

  // Buscar dispositivos/câmeras do usuário
  useEffect(() => {
    const fetchDevices = async () => {
      try {
        setLoading(true);
        
        const response = await axios.get('/api/devices', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        setDevices(response.data);
        setLoading(false);
      } catch (err) {
        console.error('Erro ao buscar dispositivos:', err);
        setError('Não foi possível carregar seus dispositivos. Por favor, tente novamente.');
        setLoading(false);
      }
    };
    
    fetchDevices();
  }, [token]);

  // Buscar streams para cada dispositivo
  useEffect(() => {
    const fetchStreams = async () => {
      const streamsMap = {};
      
      for (const device of devices) {
        try {
          const response = await axios.get(`/api/devices/${device.id}/streams`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          
          streamsMap[device.id] = response.data;
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
  }, [devices, token]);

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
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
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
            <p className="text-gray-500">Nenhum dispositivo encontrado para "{searchTerm}".</p>
          </div>
        );
      }
      
      return (
        <div className="text-center py-8">
          <p className="text-gray-500 mb-4">Você ainda não tem dispositivos configurados.</p>
          <button 
            onClick={() => navigate('/add-camera')} 
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 flex items-center justify-center mx-auto"
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
                className="bg-white rounded-lg shadow overflow-hidden border border-gray-200"
              >
                <div className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-lg font-medium">{device.name}</h3>
                    <span className={`status-indicator ${device.status === 'online' ? 'status-online' : 'status-offline'}`}></span>
                  </div>
                  <p className="text-sm text-gray-500">{device.manufacturer} {device.model}</p>
                  <p className="text-xs text-gray-400">{device.ip_address}</p>
                  <div className="mt-4 p-8 bg-gray-100 rounded flex items-center justify-center">
                    <p className="text-gray-500">Nenhum stream disponível</p>
                  </div>
                </div>
              </div>
            );
          }
          
          // Mostrar dispositivo com snapshot
          return (
            <div 
              key={device.id} 
              className="bg-white rounded-lg shadow overflow-hidden border border-gray-200"
            >
              {viewMode === 'grid' ? (
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
                      <span className={`status-indicator ${device.status === 'online' ? 'status-online' : 'status-offline'}`}></span>
                    </div>
                    <p className="text-sm text-gray-500">{device.manufacturer} {device.model}</p>
                    <p className="text-xs text-gray-400">{device.ip_address}</p>
                    <div className="mt-2 flex">
                      <button 
                        onClick={() => handleCameraExpand(device.id, primaryStream.id, device.name)}
                        className="text-xs text-blue-500 hover:underline"
                      >
                        Ver Stream
                      </button>
                      <span className="mx-2 text-gray-300">|</span>
                      <button 
                        onClick={() => navigate(`/camera/${device.id}`)}
                        className="text-xs text-blue-500 hover:underline"
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
    <MainLayout>
      <div className="container mx-auto px-2 sm:px-4 py-4 sm:py-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-4 md:mb-6">
          <div className="flex flex-col sm:flex-row gap-3">
            {/* Barra de pesquisa */}
            <div className="relative w-full sm:w-auto">
              <input
                type="text"
                placeholder="Buscar câmeras..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border rounded-lg w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <FaSearch className="absolute left-3 top-3 text-gray-400" />
            </div>
            
            {/* Controles de visualização */}
            <div className="flex space-x-2">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 rounded ${viewMode === 'grid' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-600'}`}
                title="Visualização em grade"
              >
                <FaThLarge />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 rounded ${viewMode === 'list' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-600'}`}
                title="Visualização em lista"
              >
                <FaList />
              </button>
              <button
                onClick={() => window.location.reload()}
                className="p-2 rounded bg-gray-200 text-gray-600 hover:bg-gray-300"
                title="Atualizar"
              >
                <FaSync />
              </button>
              <button
                onClick={() => navigate('/add-camera')}
                className="p-2 rounded bg-blue-500 text-white hover:bg-blue-600"
                title="Adicionar câmera"
              >
                <FaPlus />
              </button>
            </div>
          </div>
        </div>
        
        {/* Controle de intervalo de atualização */}
        <div className="mb-4 sm:mb-6">
          <label className="flex items-center text-sm text-gray-600">
            <span className="mr-3">Intervalo de atualização:</span>
            <select 
              value={refreshInterval} 
              onChange={(e) => setRefreshInterval(Number(e.target.value))}
              className="border rounded p-1"
            >
              <option value={2000}>2 segundos</option>
              <option value={5000}>5 segundos</option>
              <option value={10000}>10 segundos</option>
              <option value={30000}>30 segundos</option>
              <option value={60000}>1 minuto</option>
            </select>
          </label>
        </div>
        
        {/* Grid/Lista de câmeras */}
        {renderCameras()}
      </div>
      
      {/* Modal para exibir stream */}
      <StreamModal 
        isOpen={streamModal.isOpen}
        onClose={closeStreamModal}
        deviceId={streamModal.deviceId}
        streamId={streamModal.streamId}
        cameraName={streamModal.cameraName}
      />
    </MainLayout>
  );
};

export default CameraDashboard; 