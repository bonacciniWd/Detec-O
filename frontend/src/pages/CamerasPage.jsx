import React, { useState, useEffect, useCallback } from 'react';
import cameraService from '../services/cameraService';
import apiClient from '../services/api';
import { toast } from 'react-toastify';
import ConfirmModal from '../components/ConfirmModal';
import DetectionSettings from '../components/DetectionSettings';

function CamerasPage() {
  const [cameras, setCameras] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  // Estado para controlar loading de ações individuais (start/stop)
  const [actionLoading, setActionLoading] = useState({}); // Ex: { cameraId: true }
  // Estado para controlar qual câmera está com configurações expandidas
  const [expandedSettings, setExpandedSettings] = useState(null);

  // Estado para o formulário de adicionar câmera
  const [newCameraName, setNewCameraName] = useState('');
  const [newCameraIp, setNewCameraIp] = useState('');
  const [newCameraPort, setNewCameraPort] = useState('80');
  const [newCameraUsername, setNewCameraUsername] = useState('');
  const [newCameraPassword, setNewCameraPassword] = useState('');
  const [newCameraLocation, setNewCameraLocation] = useState('');
  const [newCameraConnectorType, setNewCameraConnectorType] = useState('onvif');
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [discoveredDevices, setDiscoveredDevices] = useState([]);
  const [isShowingAdvanced, setIsShowingAdvanced] = useState(false);
  const [isAdding, setIsAdding] = useState(false);
  const [addError, setAddError] = useState(null);

  // Estado para o modal de confirmação de exclusão
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [cameraToDelete, setCameraToDelete] = useState(null); // Guarda { id, name }

  // Obter a URL base da API para construir a URL do stream
  const apiBaseUrl = apiClient.defaults.baseURL;

  // Carregar câmeras
  const loadCameras = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const camerasData = await cameraService.getCameras();
      setCameras(camerasData);
    } catch (error) {
      console.error("Erro ao carregar câmeras:", error);
      setError("Não foi possível carregar as câmeras. Tente novamente mais tarde.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCameras();
  }, [loadCameras]);

  // Iniciar descoberta de dispositivos na rede
  const handleDiscoverDevices = async () => {
    setIsDiscovering(true);
    setDiscoveredDevices([]);
    
    try {
      const response = await apiClient.get('/api/v1/devices/discover');
      setDiscoveredDevices(response.data);
      
      if (response.data.length === 0) {
        toast.info('Nenhum dispositivo encontrado na rede.');
      }
    } catch (error) {
      console.error('Erro ao descobrir dispositivos:', error);
      toast.error('Não foi possível descobrir dispositivos na rede.');
    } finally {
      setIsDiscovering(false);
    }
  };

  // Selecionar dispositivo descoberto
  const handleSelectDevice = (device) => {
    setNewCameraName(device.name || '');
    setNewCameraIp(device.ip_address || '');
    setNewCameraPort(device.port?.toString() || '80');
    setNewCameraConnectorType(device.type || 'onvif');
  };
  
  // Validar formulário
  const validateForm = () => {
    if (!newCameraName.trim()) {
      toast.error('O nome da câmera é obrigatório');
      return false;
    }
    
    if (!newCameraIp.trim()) {
      toast.error('O endereço IP da câmera é obrigatório');
      return false;
    }
    
    return true;
  };

  // Adicionar câmera
  const handleAddCamera = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setIsAdding(true);
    setAddError(null);
    
    try {
      const cameraData = {
        name: newCameraName,
        ip_address: newCameraIp,
        port: parseInt(newCameraPort) || 80,
        username: newCameraUsername,
        password: newCameraPassword,
        location: newCameraLocation,
        connector_type: newCameraConnectorType
      };
      
      await cameraService.addCamera(cameraData);
      
      // Limpar formulário
      setNewCameraName('');
      setNewCameraIp('');
      setNewCameraPort('80');
      setNewCameraUsername('');
      setNewCameraPassword('');
      setNewCameraLocation('');
      setNewCameraConnectorType('onvif');
      
      // Recarregar lista de câmeras
      loadCameras();
      
      toast.success('Câmera adicionada com sucesso!');
    } catch (error) {
      console.error('Erro ao adicionar câmera:', error);
      setAddError('Não foi possível adicionar a câmera. Verifique as informações e tente novamente.');
      toast.error('Erro ao adicionar câmera');
    } finally {
      setIsAdding(false);
    }
  };

  // Confirmar exclusão de câmera
  const confirmDeleteCamera = (camera) => {
    setCameraToDelete(camera);
    setIsDeleteModalOpen(true);
  };

  // Excluir câmera
  const handleDeleteCamera = async () => {
    if (!cameraToDelete) return;
    
    try {
      await cameraService.deleteCamera(cameraToDelete.id);
      
      // Remover da lista local
      setCameras(prev => prev.filter(cam => cam.id !== cameraToDelete.id));
      
      toast.success(`Câmera ${cameraToDelete.name} excluída com sucesso`);
    } catch (error) {
      console.error('Erro ao excluir câmera:', error);
      toast.error('Não foi possível excluir a câmera');
    } finally {
      // Fechar modal e limpar estado
      setIsDeleteModalOpen(false);
      setCameraToDelete(null);
    }
  };

  // Toggle expandir configurações
  const toggleExpandSettings = (cameraId) => {
    setExpandedSettings(prev => prev === cameraId ? null : cameraId);
  };

  // Salvar configurações de detecção
  const handleSaveDetectionSettings = async (cameraId, settings) => {
    try {
      await cameraService.updateDetectionSettings(cameraId, settings);
      toast.success('Configurações de detecção salvas com sucesso');
    } catch (error) {
      console.error('Erro ao salvar configurações:', error);
      toast.error('Erro ao salvar configurações de detecção');
    }
  };

  return (
    <div className="container mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-6">Gerenciamento de Câmeras</h1>
      
      {/* Formulário para adicionar câmera */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Adicionar Nova Câmera</h2>
        
        {/* Descoberta de dispositivos */}
        <div className="mb-4">
          <button 
            onClick={handleDiscoverDevices}
            disabled={isDiscovering}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded mr-2 flex items-center"
          >
            {isDiscovering ? (
              <>
                <svg className="animate-spin h-4 w-4 mr-2" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Descobrindo...
              </>
            ) : "Descobrir Dispositivos na Rede"}
          </button>
          <small className="text-gray-500 block mt-1">
            Procura por dispositivos compatíveis ONVIF e Hikvision na rede local.
          </small>
        </div>
        
        {/* Lista de dispositivos descobertos */}
        {discoveredDevices.length > 0 && (
          <div className="mb-6">
            <h3 className="text-md font-medium mb-2">Dispositivos Encontrados:</h3>
            <div className="max-h-40 overflow-y-auto border rounded p-2">
              {discoveredDevices.map((device, index) => (
                <div 
                  key={index}
                  className="flex justify-between items-center p-2 hover:bg-gray-100 cursor-pointer"
                  onClick={() => handleSelectDevice(device)}
                >
                  <div>
                    <p className="font-medium">{device.name || 'Dispositivo ' + (index + 1)}</p>
                    <p className="text-sm text-gray-600">{device.ip_address} - {device.type || 'Desconhecido'}</p>
                  </div>
                  <button 
                    className="text-blue-500 hover:text-blue-700"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSelectDevice(device);
                    }}
                  >
                    Selecionar
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
        
        <form onSubmit={handleAddCamera}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="mb-4">
              <label className="block text-gray-700 mb-2" htmlFor="camera-name">
                Nome da Câmera <span className="text-red-500">*</span>
              </label>
              <input
                id="camera-name"
                type="text"
                value={newCameraName}
                onChange={(e) => setNewCameraName(e.target.value)}
                className="w-full p-2 border rounded"
                placeholder="Ex: Câmera Entrada Principal"
                required
              />
            </div>
            
            <div className="mb-4">
              <label className="block text-gray-700 mb-2" htmlFor="camera-location">
                Localização
              </label>
              <input
                id="camera-location"
                type="text"
                value={newCameraLocation}
                onChange={(e) => setNewCameraLocation(e.target.value)}
                className="w-full p-2 border rounded"
                placeholder="Ex: Portão de Entrada"
              />
            </div>
            
            <div className="mb-4">
              <label className="block text-gray-700 mb-2" htmlFor="camera-ip">
                Endereço IP <span className="text-red-500">*</span>
              </label>
              <input
                id="camera-ip"
                type="text"
                value={newCameraIp}
                onChange={(e) => setNewCameraIp(e.target.value)}
                className="w-full p-2 border rounded"
                placeholder="Ex: 192.168.1.100"
                required
              />
            </div>
            
            <div className="mb-4">
              <label className="block text-gray-700 mb-2" htmlFor="camera-port">
                Porta
              </label>
              <input
                id="camera-port"
                type="number"
                value={newCameraPort}
                onChange={(e) => setNewCameraPort(e.target.value)}
                className="w-full p-2 border rounded"
                placeholder="Ex: 80"
              />
            </div>
            
            <div className="mb-4">
              <label className="block text-gray-700 mb-2" htmlFor="camera-connector">
                Tipo de Conector
              </label>
              <select
                id="camera-connector"
                value={newCameraConnectorType}
                onChange={(e) => setNewCameraConnectorType(e.target.value)}
                className="w-full p-2 border rounded"
              >
                <option value="onvif">ONVIF</option>
                <option value="hikvision">Hikvision</option>
              </select>
            </div>
            
            <div className="mb-4">
              <button
                type="button"
                onClick={() => setIsShowingAdvanced(!isShowingAdvanced)}
                className="text-blue-500 hover:underline text-sm"
              >
                {isShowingAdvanced ? '- Ocultar opções avançadas' : '+ Mostrar opções avançadas'}
              </button>
            </div>
          </div>
          
          {isShowingAdvanced && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2 p-4 bg-gray-50 rounded">
              <div className="mb-4">
                <label className="block text-gray-700 mb-2" htmlFor="camera-username">
                  Nome de Usuário
                </label>
                <input
                  id="camera-username"
                  type="text"
                  value={newCameraUsername}
                  onChange={(e) => setNewCameraUsername(e.target.value)}
                  className="w-full p-2 border rounded"
                  placeholder="Ex: admin"
                />
              </div>
              
              <div className="mb-4">
                <label className="block text-gray-700 mb-2" htmlFor="camera-password">
                  Senha
                </label>
                <input
                  id="camera-password"
                  type="password"
                  value={newCameraPassword}
                  onChange={(e) => setNewCameraPassword(e.target.value)}
                  className="w-full p-2 border rounded"
                  placeholder="Senha do dispositivo"
                />
              </div>
            </div>
          )}
          
          {addError && (
            <div className="text-red-500 my-2">{addError}</div>
          )}
          
          <div className="mt-4">
            <button
              type="submit"
              disabled={isAdding}
              className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded mr-2"
            >
              {isAdding ? 'Adicionando...' : 'Adicionar Câmera'}
            </button>
          </div>
        </form>
      </div>
      
      {/* Lista de câmeras */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4">Câmeras Configuradas</h2>
        
        {isLoading ? (
          <div className="text-center py-4">
            <div className="loader mx-auto"></div>
            <p className="mt-2">Carregando câmeras...</p>
          </div>
        ) : error ? (
          <div className="text-red-500 text-center py-4">{error}</div>
        ) : cameras.length === 0 ? (
          <div className="text-gray-500 text-center py-4">
            Nenhuma câmera configurada. Adicione sua primeira câmera usando o formulário acima.
          </div>
        ) : (
          // Lista de câmeras
          <div className="space-y-4">
            {cameras.map(camera => (
              <div key={camera.id} className="border rounded-lg overflow-hidden">
                <div className="flex flex-col md:flex-row">
                  {/* Thumbnail da câmera */}
                  <div className="w-full md:w-1/3 lg:w-1/4 bg-gray-200">
                    <div className="relative pt-[56.25%]"> {/* Aspect ratio 16:9 */}
                      <img 
                        src={`${apiBaseUrl}/api/v1/devices/${camera.id}/cached-snapshot/1?max_age=60`} 
                        alt={camera.name}
                        className="absolute inset-0 w-full h-full object-cover"
                        onError={(e) => {
                          e.target.src = '/images/camera-offline.jpg'; // Imagem de fallback
                        }}
                      />
                      <div className={`absolute top-2 right-2 w-3 h-3 rounded-full ${camera.status === 'online' ? 'bg-green-500' : 'bg-red-500'}`}></div>
                    </div>
                  </div>
                  
                  {/* Informações da câmera */}
                  <div className="p-4 flex-1">
                    <div className="flex flex-wrap justify-between items-start">
                      <div>
                        <h3 className="text-lg font-medium">{camera.name}</h3>
                        <p className="text-sm text-gray-500">
                          {camera.location && `${camera.location} • `}
                          {camera.manufacturer} {camera.model || ''}
                        </p>
                        <p className="text-xs text-gray-400">
                          {camera.ip_address}:{camera.port} • {camera.connector_type?.toUpperCase() || 'ONVIF'}
                        </p>
                      </div>
                      
                      <div className="flex items-center space-x-2 mt-2 md:mt-0">
                        <button 
                          className={`px-3 py-1 rounded text-sm ${expandedSettings === camera.id ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
                          onClick={() => toggleExpandSettings(camera.id)}
                        >
                          Configurações
                        </button>
                        <button 
                          className="bg-red-100 text-red-700 hover:bg-red-200 px-3 py-1 rounded text-sm"
                          onClick={() => confirmDeleteCamera(camera)}
                        >
                          Excluir
                        </button>
                      </div>
                    </div>
                    
                    {/* Settings expandidos */}
                    {expandedSettings === camera.id && (
                      <div className="mt-4 border-t pt-4">
                        <DetectionSettings 
                          cameraId={camera.id}
                          onSave={(settings) => handleSaveDetectionSettings(camera.id, settings)}
                        />
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Modal de confirmação de exclusão */}
      <ConfirmModal
        isOpen={isDeleteModalOpen}
        title="Excluir Câmera"
        message={`Tem certeza que deseja excluir a câmera ${cameraToDelete?.name}? Esta ação não pode ser desfeita.`}
        confirmText="Excluir"
        cancelText="Cancelar"
        onConfirm={handleDeleteCamera}
        onCancel={() => {
          setIsDeleteModalOpen(false);
          setCameraToDelete(null);
        }}
      />
    </div>
  );
}

export default CamerasPage; 