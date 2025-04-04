import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { toast } from 'react-toastify';
import MainLayout from '../components/MainLayout';

const AddCameraPage = () => {
  const { token } = useAuth();
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    name: '',
    ip_address: '',
    rtsp_url: '',
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [discoveredCameras, setDiscoveredCameras] = useState([]);
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  const discoverCameras = async () => {
    setIsDiscovering(true);
    setError(null);
    
    try {
      // A implementação real dependeria da API backend
      // Simulação para exemplo:
      setTimeout(() => {
        setDiscoveredCameras([
          {
            name: 'Câmera Hikvision',
            ip_address: '192.168.1.101',
            rtsp_url: 'rtsp://192.168.1.101:554/Streaming/Channels/101',
            manufacturer: 'Hikvision',
            model: 'DS-2CD2143G0-I'
          },
          {
            name: 'Câmera Dahua',
            ip_address: '192.168.1.102',
            rtsp_url: 'rtsp://192.168.1.102:554/cam/realmonitor',
            manufacturer: 'Dahua',
            model: 'IPC-HDW1230S'
          }
        ]);
        setIsDiscovering(false);
      }, 2000);
      
      // Implementação real seria algo como:
      // const response = await axios.get('/api/discover-cameras', {
      //   headers: { 'Authorization': `Bearer ${token}` }
      // });
      // setDiscoveredCameras(response.data);
      
    } catch (err) {
      console.error('Erro ao descobrir câmeras na rede:', err);
      setError('Não foi possível descobrir câmeras na sua rede. Verifique se estão ligadas e conectadas.');
      setIsDiscovering(false);
    }
  };
  
  const selectDiscoveredCamera = (camera) => {
    setFormData({
      name: camera.name || '',
      ip_address: camera.ip_address || '',
      rtsp_url: camera.rtsp_url || '',
      manufacturer: camera.manufacturer || '',
      model: camera.model || ''
    });
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('/api/devices', formData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      toast.success('Câmera adicionada com sucesso!');
      navigate('/camera-dashboard');
    } catch (err) {
      console.error('Erro ao adicionar câmera:', err);
      setError(err.response?.data?.message || 'Não foi possível adicionar a câmera. Por favor, tente novamente.');
      toast.error('Erro ao adicionar câmera');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <MainLayout>
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl font-bold text-gray-800">Adicionar Nova Câmera</h1>
          </div>
          
          {/* Botão de descoberta automática */}
          <div className="mb-6">
            <button
              onClick={discoverCameras}
              disabled={isDiscovering}
              className="w-full bg-gradient-to-r from-blue-500 to-indigo-600 text-white py-3 rounded-lg font-medium shadow hover:from-blue-600 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 transition-all"
            >
              {isDiscovering ? (
                <div className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Buscando câmeras na rede...
                </div>
              ) : (
                <div className="flex items-center justify-center">
                  <svg className="mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                  </svg>
                  Descobrir Câmeras Automaticamente
                </div>
              )}
            </button>
          </div>
          
          {/* Lista de câmeras descobertas */}
          {discoveredCameras.length > 0 && (
            <div className="mb-6">
              <h2 className="text-lg font-medium text-gray-700 mb-2">Câmeras Encontradas</h2>
              <div className="bg-gray-50 rounded-lg overflow-hidden">
                {discoveredCameras.map((camera, index) => (
                  <div 
                    key={index}
                    className="p-3 border-b border-gray-200 last:border-0 hover:bg-gray-100 cursor-pointer transition"
                    onClick={() => selectDiscoveredCamera(camera)}
                  >
                    <div className="flex items-center">
                      <div className="flex-shrink-0 mr-3">
                        <svg className="h-6 w-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                        </svg>
                      </div>
                      <div>
                        <p className="font-medium text-gray-800">{camera.name || 'Câmera sem nome'}</p>
                        <p className="text-sm text-gray-500">{camera.ip_address} {camera.manufacturer ? `- ${camera.manufacturer}` : ''}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {error && (
            <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-4 mb-6">
              <p>{error}</p>
            </div>
          )}
          
          <form onSubmit={handleSubmit}>
            <div className="space-y-4 mb-6">
              <div>
                <label className="block text-gray-700 text-sm font-medium mb-2">
                  Nome da Câmera *
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Ex: Câmera Entrada Principal"
                />
              </div>
              
              <div>
                <label className="block text-gray-700 text-sm font-medium mb-2">
                  Endereço IP *
                </label>
                <input
                  type="text"
                  name="ip_address"
                  value={formData.ip_address}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Ex: 192.168.1.100"
                />
              </div>
              
              <div>
                <label className="block text-gray-700 text-sm font-medium mb-2">
                  URL RTSP *
                </label>
                <input
                  type="text"
                  name="rtsp_url"
                  value={formData.rtsp_url}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Ex: rtsp://192.168.1.100:554/stream1"
                />
              </div>
              
              {/* Opção para mostrar/esconder campos avançados */}
              <div>
                <button
                  type="button"
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="text-blue-600 text-sm flex items-center focus:outline-none"
                >
                  {showAdvanced ? (
                    <>
                      <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 15l7-7 7 7"></path>
                      </svg>
                      Ocultar opções avançadas
                    </>
                  ) : (
                    <>
                      <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
                      </svg>
                      Mostrar opções avançadas
                    </>
                  )}
                </button>
              </div>
              
              {/* Campos avançados */}
              {showAdvanced && (
                <div className="space-y-4 pt-2 border-t border-gray-200">
                  <div>
                    <label className="block text-gray-700 text-sm font-medium mb-2">
                      Fabricante
                    </label>
                    <input
                      type="text"
                      name="manufacturer"
                      value={formData.manufacturer || ''}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Ex: Hikvision, Dahua, etc."
                    />
                  </div>
                  
                  <div>
                    <label className="block text-gray-700 text-sm font-medium mb-2">
                      Modelo
                    </label>
                    <input
                      type="text"
                      name="model"
                      value={formData.model || ''}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Ex: DS-2CD2143G0-I"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-gray-700 text-sm font-medium mb-2">
                      Localização
                    </label>
                    <input
                      type="text"
                      name="location"
                      value={formData.location || ''}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Ex: Entrada Principal"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-gray-700 text-sm font-medium mb-2">
                      Usuário
                    </label>
                    <input
                      type="text"
                      name="username"
                      value={formData.username || ''}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Nome de usuário da câmera"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-gray-700 text-sm font-medium mb-2">
                      Senha
                    </label>
                    <input
                      type="password"
                      name="password"
                      value={formData.password || ''}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Senha da câmera"
                    />
                  </div>
                </div>
              )}
            </div>
            
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => navigate(-1)}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-100 focus:outline-none"
                disabled={loading}
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={loading}
              >
                {loading ? 'Adicionando...' : 'Adicionar Câmera'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </MainLayout>
  );
};

export default AddCameraPage; 