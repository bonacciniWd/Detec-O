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
  const [newCameraUrl, setNewCameraUrl] = useState('');
  const [newCameraLocation, setNewCameraLocation] = useState('');
  const [isAdding, setIsAdding] = useState(false);
  const [addError, setAddError] = useState(null);

  // Estado para o modal de confirmação de exclusão
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [cameraToDelete, setCameraToDelete] = useState(null); // Guarda { id, name }

  // Obter a URL base da API para construir a URL do stream
  const apiBaseUrl = apiClient.defaults.baseURL;

  // Usar useCallback para evitar recriar a função em cada render
  const fetchCameras = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await cameraService.getCameras();
      // A API agora retorna o status 'running'
      setCameras(data);
    } catch (err) { 
      setError('Falha ao carregar câmeras.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, []); // Dependência vazia, a função não muda

  // Efeito para buscar câmeras ao montar
  useEffect(() => {
    fetchCameras();
  }, [fetchCameras]);

  // Função para lidar com a adição de nova câmera
  const handleAddCamera = async (event) => {
    event.preventDefault();
    setIsAdding(true);
    setAddError(null);
    try {
      const newCameraData = { 
        name: newCameraName, 
        url: newCameraUrl, 
        location: newCameraLocation || undefined, // Envia undefined se vazio
      };
      const addedCamera = await cameraService.addCamera(newCameraData);
      setCameras(prev => [...prev, { ...addedCamera, running: false }]);
      // Limpa o formulário
      setNewCameraName('');
      setNewCameraUrl('');
      setNewCameraLocation('');
      toast.success(`Câmera "${addedCamera.name}" adicionada com sucesso!`);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Erro ao adicionar câmera.';
      setAddError(errorMsg);
      toast.error(`Falha ao adicionar câmera: ${errorMsg}`);
      console.error(err);
    } finally {
      setIsAdding(false);
    }
  };

  // Função para ABRIR o modal de confirmação
  const openDeleteConfirm = (camera) => {
    setCameraToDelete(camera); // Define qual câmera deletar
    setIsDeleteModalOpen(true); // Abre o modal
  };

  // Função para FECHAR o modal
  const closeDeleteModal = () => {
    setIsDeleteModalOpen(false);
    setCameraToDelete(null); // Limpa a câmera selecionada
  };

  // Função que REALMENTE deleta a câmera (chamada pelo onConfirm do modal)
  const confirmDeleteCamera = async () => {
    if (!cameraToDelete) return;

    try {
        await cameraService.deleteCamera(cameraToDelete.id);
        setCameras(cameras.filter(cam => cam.id !== cameraToDelete.id));
        toast.success(`Câmera "${cameraToDelete.name}" removida com sucesso.`);
    } catch (err) {
        const errorMsg = err.response?.data?.detail || err.message;
        toast.error(`Erro ao remover câmera: ${errorMsg}`);
        console.error(err);
    }
    // O modal já se fecha através do onClick no componente ConfirmModal
  };

  // Função para iniciar detecção
  const handleStartDetection = async (cameraId) => {
    setActionLoading(prev => ({ ...prev, [cameraId]: true }));
    const cameraName = cameras.find(cam => cam.id === cameraId)?.name || cameraId;
    try {
      await cameraService.startCameraDetection(cameraId);
      setCameras(prevCameras => 
        prevCameras.map(cam => 
          cam.id === cameraId ? { ...cam, running: true } : cam
        )
      );
      toast.info(`Detecção iniciada para "${cameraName}".`);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message;
      toast.error(`Erro ao iniciar detecção: ${errorMsg}`);
      console.error(err);
    } finally {
      setActionLoading(prev => ({ ...prev, [cameraId]: false }));
    }
  };

  // Função para parar detecção
  const handleStopDetection = async (cameraId) => {
    setActionLoading(prev => ({ ...prev, [cameraId]: true }));
    const cameraName = cameras.find(cam => cam.id === cameraId)?.name || cameraId;
    try {
      await cameraService.stopCameraDetection(cameraId);
      setCameras(prevCameras => 
        prevCameras.map(cam => 
          cam.id === cameraId ? { ...cam, running: false } : cam
        )
      );
      toast.info(`Detecção parada para "${cameraName}".`);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message;
      toast.error(`Erro ao parar detecção: ${errorMsg}`);
      console.error(err);
    } finally {
      setActionLoading(prev => ({ ...prev, [cameraId]: false }));
    }
  };

  // Função para expandir/recolher as configurações de detecção
  const toggleSettings = (cameraId) => {
    setExpandedSettings(prev => prev === cameraId ? null : cameraId);
  };

  // Função para calcular uptime (exemplo)
  const calculateUptime = (startTime) => {
      if (!startTime) return 'N/A';
      const start = new Date(startTime).getTime();
      const now = Date.now();
      const diffSeconds = Math.round((now - start) / 1000);
      
      if (diffSeconds < 60) return `${diffSeconds} seg`;
      if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)} min`;
      // Adicionar horas, dias se necessário
      return `${Math.floor(diffSeconds / 3600)} h ${Math.floor((diffSeconds % 3600) / 60)} min`;
  };

  // Classes reutilizáveis para tema escuro
  const inputClass = "shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full text-base border-gray-700 bg-gray-700 text-white rounded-md disabled:opacity-50 px-3 py-3";
  const buttonClass = (color = 'blue') => 
    `inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-${color}-600 hover:bg-${color}-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-${color}-500 disabled:opacity-50`;
  const cardClass = "bg-gray-800 shadow overflow-hidden sm:rounded-lg";
  const cardHeaderClass = "px-4 py-5 sm:px-6 border-b border-gray-700";
  const cardTitleClass = "text-lg leading-6 font-medium text-white";
  const cardContentClass = "px-4 py-5 sm:p-6";

  return (
    <div className="space-y-6 bg-gray-900 min-h-screen pb-12">
      {/* Cabeçalho */}
      <header className="bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 flex justify-between items-center">
          <h1 className="text-3xl font-bold text-white">Gerenciar Câmeras</h1>
          <button onClick={fetchCameras} disabled={isLoading} className={buttonClass('gray') + " ml-4"}>
            {isLoading ? 'Recarregando...' : 'Recarregar Lista'}
          </button>
        </div>
      </header>

      {/* Conteúdo Principal (Grid Layout) */}
      <div className="max-w-7xl mx-auto sm:px-6 lg:px-8">
         <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Coluna Formulário */} 
            <div className="lg:col-span-1">
               <div className={cardClass}>
                  <div className={cardHeaderClass}>
                     <h3 className={cardTitleClass}>Adicionar Nova Câmera</h3>
                  </div>
                  <form onSubmit={handleAddCamera} className={cardContentClass + " space-y-4"}>
                     <div>
                       <label htmlFor="cam-name" className="block text-sm font-medium text-gray-300">Nome:</label>
                       <input id="cam-name" type="text" value={newCameraName} onChange={(e) => setNewCameraName(e.target.value)} required disabled={isAdding} className={inputClass}/>
                     </div>
                     <div>
                       <label htmlFor="cam-url" className="block text-sm font-medium text-gray-300">URL (RTSP):</label>
                       <input id="cam-url" type="text" value={newCameraUrl} onChange={(e) => setNewCameraUrl(e.target.value)} required placeholder="rtsp://..." disabled={isAdding} className={inputClass}/>
                     </div>
                     <div>
                       <label htmlFor="cam-location" className="block text-sm font-medium text-gray-300">Localização (Opcional):</label>
                       <input id="cam-location" type="text" value={newCameraLocation} onChange={(e) => setNewCameraLocation(e.target.value)} disabled={isAdding} className={inputClass}/>
                     </div>
                     {addError && <p className="text-sm text-red-400">{addError}</p>}
                     <button type="submit" disabled={isAdding} className={buttonClass('blue') + " w-full"}>
                       {isAdding ? 'Adicionando...' : 'Adicionar Câmera'}
                     </button>
                   </form>
                </div>
            </div>

            {/* Coluna Lista de Câmeras */} 
            <div className="lg:col-span-2 space-y-6">
               {isLoading && (
                 <div className="flex justify-center items-center p-6 text-gray-300">
                   <svg className="animate-spin -ml-1 mr-3 h-8 w-8 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                     <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                     <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                   </svg>
                   Carregando câmeras...
                 </div>
               )}
               {error && <p className="text-red-400">{error}</p>}
               {!isLoading && !error && cameras.length === 0 && (
                  <div className={`${cardClass} ${cardContentClass} text-center text-gray-400`}>
                     Você ainda não adicionou nenhuma câmera.
                  </div>
               )}
               {!isLoading && !error && cameras.map((cam) => (
                  <div key={cam.id} className={cardClass}>
                     <div className={cardHeaderClass}>
                        <h3 className={cardTitleClass}>{cam.name}</h3>
                        <p className="mt-1 max-w-2xl text-sm text-gray-400">{cam.location || 'Sem localização'}</p>
                     </div>
                     <div className={cardContentClass}>
                        <p className="text-sm text-gray-400 truncate mb-2">URL: {cam.url}</p>
                        <div className="mb-4">
                           Status: 
                           <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${cam.running ? 'bg-green-900 text-green-200' : 'bg-gray-700 text-gray-200'}`}>
                             {cam.running ? 'Rodando' : 'Parada'}
                           </span>
                           {cam.running && cam.start_time && 
                              <span className="ml-2 text-xs text-gray-400">(Uptime: {calculateUptime(cam.start_time)})</span>}
                        </div>

                        {/* Stream */} 
                        {cam.running && (
                            <div className="mb-4 border border-gray-700 bg-gray-900 min-h-[200px] flex items-center justify-center">
                                <img 
                                    src={`${apiBaseUrl}/api/v1/cameras/${cam.id}/stream`}
                                    alt={`Stream da câmera ${cam.name}`}
                                    className="max-w-full max-h-64 block"
                                    onError={(e) => { 
                                        console.warn(`Erro stream ${cam.id}`); 
                                        e.target.style.display='none';
                                        e.target.nextElementSibling.style.display='flex';
                                    }}
                                />
                                <div className="hidden text-gray-500 flex-col items-center justify-center p-4 text-center">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                    </svg>
                                    <p>Stream não disponível</p>
                                    <p className="text-sm">Processamento em andamento ou falha na conexão</p>
                                </div>
                            </div>
                        )}

                        {/* Botões de Ação */}
                        <div className="flex flex-wrap gap-2">
                            {!cam.running && (
                                <button 
                                    onClick={() => handleStartDetection(cam.id)} 
                                    disabled={actionLoading[cam.id]} 
                                    className={buttonClass('green')}
                                >
                                    {actionLoading[cam.id] ? 'Iniciando...' : 'Iniciar Detecção'}
                                </button>
                            )}
                            {cam.running && (
                                <button 
                                    onClick={() => handleStopDetection(cam.id)} 
                                    disabled={actionLoading[cam.id]} 
                                    className={buttonClass('red')}
                                >
                                    {actionLoading[cam.id] ? 'Parando...' : 'Parar Detecção'}
                                </button>
                            )}
                            <button 
                                onClick={() => toggleSettings(cam.id)}
                                className="inline-flex items-center px-3 py-2 border border-gray-600 text-sm leading-4 font-medium rounded-md text-gray-300 bg-gray-700 hover:bg-gray-600"
                            >
                                {expandedSettings === cam.id ? 'Ocultar Configurações' : 'Configurar Detecção'}
                            </button>
                            <button 
                                onClick={() => openDeleteConfirm(cam)} 
                                className="inline-flex items-center px-3 py-2 border border-gray-600 text-sm leading-4 font-medium rounded-md text-gray-300 bg-gray-700 hover:bg-gray-600"
                            >
                                Remover
                            </button>
                        </div>
                        
                        {/* Configurações de Detecção (expandido/colapsado) */}
                        {expandedSettings === cam.id && (
                            <div className="mt-6">
                                <DetectionSettings cameraId={cam.id} />
                            </div>
                        )}
                     </div>
                  </div>
               ))}
            </div>
         </div>
      </div>

      {/* Modal de Confirmação de Exclusão */}
      <ConfirmModal 
        isOpen={isDeleteModalOpen}
        title="Remover Câmera"
        message={`Tem certeza que deseja remover a câmera "${cameraToDelete?.name}"? Esta ação não pode ser desfeita.`}
        confirmText="Remover"
        cancelText="Cancelar"
        onConfirm={confirmDeleteCamera}
        onCancel={closeDeleteModal}
        theme="dark" // Tema escuro para o modal
      />
    </div>
  );
}

export default CamerasPage; 