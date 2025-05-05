import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import cameraService from '../services/cameraService';
import { useAuth } from '../context/AuthContext';
import { toast } from 'react-toastify';

const AddCameraPage = () => {
  const { token } = useAuth();
  const navigate = useNavigate();
  
  const [name, setName] = useState('');
  const [ipAddress, setIpAddress] = useState('');
  const [rtspPort, setRtspPort] = useState('554');
  const [rtspPath, setRtspPath] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [location, setLocation] = useState('');
  const [model, setModel] = useState('');
  const [manufacturer, setManufacturer] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [discoveredCameras, setDiscoveredCameras] = useState([]);
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    if (name === 'name') {
      setName(value);
    } else if (name === 'ipAddress') {
      setIpAddress(value);
    } else if (name === 'rtspPort') {
      setRtspPort(value);
    } else if (name === 'rtspPath') {
      setRtspPath(value);
    } else if (name === 'username') {
      setUsername(value);
    } else if (name === 'password') {
      setPassword(value);
    } else if (name === 'location') {
      setLocation(value);
    } else if (name === 'model') {
      setModel(value);
    } else if (name === 'manufacturer') {
      setManufacturer(value);
    }
  };
  
  const discoverCameras = async () => {
    console.warn("Função discoverCameras em AddCameraPage precisa ser revisada/removida.");
  };
  
  const selectDiscoveredCamera = (camera) => {
    console.warn("Função selectDiscoveredCamera em AddCameraPage precisa ser revisada/removida.");
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    if (!name || !ipAddress || !rtspPath) {
      setError("Nome, Endereço IP Local e Caminho RTSP são obrigatórios.");
      setLoading(false);
      toast.error("Preencha os campos obrigatórios.");
      return;
    }
    
    try {
      const cameraData = {
        name: name,
        ip_address: ipAddress,
        rtsp_port: parseInt(rtspPort) || 554,
        rtsp_path: rtspPath,
        username: username || null,
        password: password || null,
        location: location || null,
        model: model || null,
        manufacturer: manufacturer || null,
      };
      
      console.log("Enviando dados da câmera (local) para API:", cameraData); 
      
      await cameraService.addCamera(cameraData);
      
      toast.success('Câmera adicionada com sucesso! Conexão RTSP validada.');
      navigate('/cameras');

    } catch (err) {
      console.error('Erro ao adicionar câmera (AddCameraPage):', err);
      const detail = err.response?.data?.detail;
      const errorMessage = typeof detail === 'string' 
                           ? detail 
                           : 'Não foi possível adicionar a câmera. Verifique os dados ou o log do backend.';
      setError(errorMessage);
      toast.error(`Erro ao adicionar câmera: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="max-w-2xl mx-auto p-4 sm:p-6 lg:p-8">
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-800">Adicionar Nova Câmera</h1>
        </div>
        
        {error && (
          <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6" role="alert">
            <p className="font-bold">Erro</p>
            <p>{error}</p>
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          <div className="space-y-4 mb-6">
            <div>
              <label className="block text-gray-700 text-sm font-medium mb-2" htmlFor="name">
                Nome da Câmera *
              </label>
              <input
                id="name"
                name="name"
                type="text"
                value={name}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                placeholder="Ex: Câmera Corredor Interno"
              />
            </div>
            
            <div>
              <label className="block text-gray-700 text-sm font-medium mb-2" htmlFor="ipAddress">
                Endereço IP Local *
              </label>
              <input
                id="ipAddress"
                name="ipAddress"
                type="text"
                value={ipAddress}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                placeholder="Ex: 192.168.1.105"
              />
            </div>

            <div>
              <label className="block text-gray-700 text-sm font-medium mb-2" htmlFor="rtspPort">
                Porta RTSP *
              </label>
              <input
                id="rtspPort"
                name="rtspPort"
                type="number"
                value={rtspPort}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                placeholder="Ex: 554"
              />
            </div>
            
            <div>
              <label className="block text-gray-700 text-sm font-medium mb-2" htmlFor="rtspPath">
                Caminho RTSP *
              </label>
              <input
                id="rtspPath"
                name="rtspPath"
                type="text"
                value={rtspPath}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                placeholder="Ex: /cam/realmonitor?channel=1&subtype=0"
              />
            </div>
            
            <div>
              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="'text-blue-600 text-slate-900 text-sm flex items-center focus:outline-none hover:underline"
              >
                {showAdvanced ? (
                  <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 15l7-7 7 7"></path></svg>
                ) : (
                  <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
                )}
                {showAdvanced ? 'Ocultar Opções Avançadas' : 'Mostrar Opções Avançadas'}
              </button>
            </div>
            
            {showAdvanced && (
              <div className="space-y-4 pt-4 border-t border-gray-200">
                <div>
                  <label className="block text-gray-700 text-sm font-medium mb-2" htmlFor="username">
                    Usuário RTSP (Opcional)
                  </label>
                  <input
                    id="username"
                    name="username"
                    type="text"
                    value={username}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                    placeholder="Usuário da câmera (se houver)"
                  />
                </div>
                
                <div>
                  <label className="block text-gray-700 text-sm font-medium mb-2" htmlFor="password">
                    Senha RTSP (Opcional)
                  </label>
                  <input
                    id="password"
                    name="password"
                    type="password"
                    value={password}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                    placeholder="Senha da câmera (se houver)"
                  />
                </div>
                
                <div>
                  <label className="block text-gray-700 text-sm font-medium mb-2" htmlFor="location">
                    Localização (Opcional)
                  </label>
                  <input
                    id="location"
                    name="location"
                    type="text"
                    value={location}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                    placeholder="Ex: Corredor Principal"
                  />
                </div>
                
                <div>
                  <label className="block text-gray-700 text-sm font-medium mb-2" htmlFor="manufacturer">
                    Fabricante (Opcional)
                  </label>
                  <input
                    id="manufacturer"
                    name="manufacturer"
                    type="text"
                    value={manufacturer}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                    placeholder="Ex: Intelbras, Hikvision"
                  />
                </div>
                
                <div>
                  <label className="block text-gray-700 text-sm font-medium mb-2" htmlFor="model">
                    Modelo (Opcional)
                  </label>
                  <input
                    id="model"
                    name="model"
                    type="text"
                    value={model}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                    placeholder="Ex: VIP 3230 B"
                  />
                </div>
              </div>
            )}
          </div>
          
          <div className="flex justify-end space-x-3 border-t border-gray-200 pt-4 mt-6">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-100 focus:outline-none disabled:opacity-50"
              disabled={loading}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 flex items-center"
              disabled={loading}
            >
               {loading ? (
                 <>
                   <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                     <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                     <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                   </svg>
                   Adicionando...
                 </>
              ) : 'Adicionar Câmera'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddCameraPage; 