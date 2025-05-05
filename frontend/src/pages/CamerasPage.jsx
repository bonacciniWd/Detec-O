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

  // Estado para o formulário de adicionar câmera (adaptado para conexão externa)
  const [newCameraName, setNewCameraName] = useState('');
  const [newCameraIp, setNewCameraIp] = useState('');
  const [newCameraPort, setNewCameraPort] = useState('554');
  const [newCameraRtspPath, setNewCameraRtspPath] = useState('');
  const [newCameraUsername, setNewCameraUsername] = useState('');
  const [newCameraPassword, setNewCameraPassword] = useState('');
  const [newCameraLocation, setNewCameraLocation] = useState('');
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
      const result = await apiClient.discoverCameras();
      setDiscoveredDevices(result);
      
      if (result.length === 0) {
        toast.info('Nenhum dispositivo encontrado na rede.');
      }
    } catch (error) {
      console.error('Erro ao descobrir dispositivos:', error);
      toast.error('Não foi possível descobrir dispositivos na rede.');
    } finally {
      setIsDiscovering(false);
    }
  };

  // Selecionar dispositivo descoberto (PRECISA AJUSTAR se a descoberta retornar os novos campos)
  const handleSelectDevice = (device) => {
    setNewCameraName(device.name || '');
    // Ajustar aqui se a descoberta retornar host/porta/path
    setNewCameraIp(device.ip_address || '');
    setNewCameraPort(device.port?.toString() || '554'); 
    setNewCameraRtspPath(''); // A descoberta geralmente não fornece o path completo
  };
  
  // Validar formulário (Ajustar para novos campos obrigatórios)
  const validateForm = () => {
    if (!newCameraName.trim()) {
      toast.error('O nome da câmera é obrigatório');
      return false;
    }
    if (!newCameraIp.trim()) {
      toast.error('O Endereço IP Local é obrigatório');
      return false;
    }
    if (!newCameraRtspPath.trim()) {
      toast.error('O Caminho RTSP é obrigatório');
      return false;
    }
    // Validação da porta pode ser adicionada se necessário
    return true;
  };

  // Adicionar câmera (Atualizado para novos campos e tratamento de erro)
  const handleAddCamera = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setIsAdding(true);
    setAddError(null);
    
    try {
      // Usar os novos nomes de estado e campos esperados pela API
      const cameraData = {
        name: newCameraName,
        ip: newCameraIp,
        port: parseInt(newCameraPort) || 554,
        rtsp_path: newCameraRtspPath,
        username: newCameraUsername || null, // Enviar null se vazio
        password: newCameraPassword || null, // Enviar null se vazio
        location: newCameraLocation || null,
        // Adicionar outros campos opcionais se mantidos no schema CameraBase
        // model: ..., 
        // manufacturer: ..., 
        // connector_type: 'rtsp',
        // detection_enabled: ..., 
        // detection_confidence: ..., 
        // detection_objects: ...
      };
      
      console.log("Enviando dados da câmera para API:", cameraData); // Log para debug
      await cameraService.addCamera(cameraData);
      
      // Limpar formulário
      setNewCameraName('');
      setNewCameraIp('');
      setNewCameraPort('554');
      setNewCameraRtspPath('');
      setNewCameraUsername('');
      setNewCameraPassword('');
      setNewCameraLocation('');
      
      // Recarregar lista de câmeras
      loadCameras();
      
      toast.success('Câmera adicionada com sucesso! A validação da conexão RTSP foi bem-sucedida.');

    } catch (error) {
      console.error('Erro ao adicionar câmera (handleAddCamera):', error);
      // Exibir erro específico do backend (validação RTSP ou outro)
      const detail = error.response?.data?.detail;
      const errorMessage = typeof detail === 'string' 
                           ? detail 
                           : 'Não foi possível adicionar a câmera. Verifique os dados ou o log do backend.';
      setAddError(errorMessage);
      toast.error(`Erro ao adicionar câmera: ${errorMessage}`);
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

  // Helper para extrair nome do arquivo do path completo
  const getSnapshotFilename = (fullPath) => {
    if (!fullPath || typeof fullPath !== 'string') return null;
    return fullPath.split(/\/|\\\\/).pop(); // Funciona para / e \\\
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
                className="w-full p-2 border rounded text-gray-900"
                placeholder="Ex: Câmera Garagem Externa"
                required
              />
            </div>
            
            <div className="mb-4">
              <label className="block text-gray-700 mb-2" htmlFor="camera-location">
                Localização (Opcional)
              </label>
              <input
                id="camera-location"
                type="text"
                value={newCameraLocation}
                onChange={(e) => setNewCameraLocation(e.target.value)}
                className="w-full p-2 border rounded text-gray-900"
                placeholder="Ex: Portão dos Fundos"
              />
            </div>
            
            <div className="mb-4">
              <label className="block text-gray-700 mb-2" htmlFor="camera-ip">
                Endereço IP Local <span className="text-red-500">*</span>
              </label>
              <input
                id="camera-ip"
                type="text"
                value={newCameraIp}
                onChange={(e) => setNewCameraIp(e.target.value)}
                className="w-full p-2 border rounded text-gray-900"
                placeholder="Ex: 192.168.0.120"
                required
              />
            </div>
            
            <div className="mb-4">
              <label className="block text-gray-700 mb-2" htmlFor="camera-port">
                Porta RTSP
              </label>
              <input
                id="camera-port"
                type="number"
                value={newCameraPort}
                onChange={(e) => setNewCameraPort(e.target.value)}
                className="w-full p-2 border rounded text-gray-900"
                placeholder="Ex: 554 (Padrão)"
              />
            </div>
            
            <div className="mb-4 md:col-span-2">
              <label className="block text-gray-700 mb-2" htmlFor="camera-rtsp-path">
                Caminho RTSP <span className="text-red-500">*</span>
              </label>
              <input
                id="camera-rtsp-path"
                type="text"
                value={newCameraRtspPath}
                onChange={(e) => setNewCameraRtspPath(e.target.value)}
                className="w-full p-2 border rounded text-gray-900"
                placeholder="Ex: /cam/realmonitor?channel=1&subtype=0"
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                Consulte a documentação do seu NVR/Câmera.
              </p>
            </div>
            
            <div className="mb-4 md:col-span-2">
              <button
                type="button"
                onClick={() => setIsShowingAdvanced(!isShowingAdvanced)}
                className="text-blue-500 hover:underline text-sm"
              >
                {isShowingAdvanced ? '- Ocultar Credenciais RTSP (Opcional)' : '+ Informar Credenciais RTSP (Opcional)'}
              </button>
            </div>
          </div>
          
          {isShowingAdvanced && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2 p-4 bg-gray-50 rounded border border-gray-200">
              <div className="mb-4">
                <label className="block text-gray-700 mb-2" htmlFor="camera-username">
                  Usuário RTSP
                </label>
                <input
                  id="camera-username"
                  type="text"
                  value={newCameraUsername}
                  onChange={(e) => setNewCameraUsername(e.target.value)}
                  className="w-full p-2 border rounded text-gray-900"
                  placeholder="Ex: admin (deixe em branco se não usar)"
                />
              </div>
              
              <div className="mb-4">
                <label className="block text-gray-700 mb-2" htmlFor="camera-password">
                  Senha RTSP
                </label>
                <input
                  id="camera-password"
                  type="password"
                  value={newCameraPassword}
                  onChange={(e) => setNewCameraPassword(e.target.value)}
                  className="w-full p-2 border rounded text-gray-900"
                  placeholder="Senha para autenticação RTSP"
                />
              </div>
            </div>
          )}
          
          {addError && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative my-4" role="alert">
              <strong className="font-bold">Erro ao adicionar: </strong>
              <span className="block sm:inline">{addError}</span>
            </div>
          )}
          
          <div className="mt-6">
            <button
              type="submit"
              disabled={isAdding}
              className="bg-green-500 hover:bg-green-600 text-white px-6 py-2 rounded mr-2 disabled:opacity-50 flex items-center"
            >
              {isAdding ? (
                 <>
                   <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                     <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                     <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                   </svg>
                   Validando e Adicionando...
                 </>
              ) : 'Adicionar Câmera'}
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
            {cameras.map(camera => {
              // Obter apenas o nome do arquivo do snapshot
              const snapshotFilename = getSnapshotFilename(camera.latest_snapshot_path); // <<< Assumindo que a API retorna este campo
              // OU se a API retorna o image_path do *último evento*:
              // const snapshotFilename = getSnapshotFilename(camera.last_event?.image_path); 

              return (
              <div key={camera.id} className="border rounded-lg overflow-hidden">
                <div className="flex flex-col md:flex-row">
                  {/* Thumbnail da câmera */}
                    <div className="w-full md:w-1/3 lg:w-1/4 bg-gray-700 flex items-center justify-center text-gray-400">
                      {/* Tentar exibir snapshot se path existir */}
                      {snapshotFilename ? (
                        <img 
                          // Construir URL pública para o snapshot
                          src={`/snapshots/${snapshotFilename}`} 
                          alt={`Snapshot de ${camera.name}`}
                          className="w-full h-full object-cover"
                          // Adicionar onError para imagem de fallback
                        onError={(e) => {
                            e.target.onerror = null; // Previne loop de erro
                            e.target.src = '/camera-offline.png'; // Imagem de fallback genérica
                            e.target.alt = `${camera.name} (Snapshot indisponível)`
                        }}
                      />
                      ) : (
                        // Placeholder se não houver snapshot
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                      )}
                  </div>
                  
                  {/* Informações da câmera */}
                    <div className="p-4 flex-1 bg-gray-800 text-white">
                    <div className="flex flex-wrap justify-between items-start">
                      <div>
                        <h3 className="text-lg font-medium">{camera.name}</h3>
                        <p className="text-sm text-gray-500">
                          {camera.location && `${camera.location} • `}
                          {camera.manufacturer} {camera.model || ''}
                        </p>
                        <p className="text-xs text-gray-400">
                            {camera.ip_address}:{camera.port} {/* Usar ip_address e port */} 
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
              );
            })}
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