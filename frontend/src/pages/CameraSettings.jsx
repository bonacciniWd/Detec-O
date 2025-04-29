import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
// Remover apiClient se não for mais usado
// import apiClient from '../services/api';
import cameraService from '../services/cameraService'; // Importar cameraService
import { toast } from 'react-toastify';
import DetectionSettings from '../components/DetectionSettings';
import AIModelSelector from '../components/AIModelSelector';
import { Tab, Tabs, TabList, TabPanel } from 'react-tabs';
import 'react-tabs/style/react-tabs.css';
import './CustomTabs.css';

const CameraSettings = () => {
  const { id: deviceId } = useParams();
  const { token } = useAuth();
  const navigate = useNavigate();
  
  const [camera, setCamera] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('general'); // 'general' ou 'detection'
  const [formData, setFormData] = useState({
    name: '',
    location: '',
    username: '',
    password: '',
    ip_address: '',
    port: 80,
    connector_type: 'rtsp'
  });

  useEffect(() => {
    const fetchCameraDetails = async () => {
      try {
        setLoading(true);
        
        // Usar a função correta do cameraService
        const cameraData = await cameraService.getCamera(deviceId);
        
        setCamera(cameraData);
        // Ajustar preenchimento do formData se os nomes dos campos retornados mudaram
        setFormData({
          name: cameraData.name || '',
          location: cameraData.location || '',
          username: cameraData.username || '',
          password: '', // Manter vazio
          // Usar os campos retornados pela API (ip_address, port)
          ip_address: cameraData.ip_address || '',
          port: cameraData.port || 80,
          connector_type: cameraData.connector_type || 'rtsp' // Ajustar default se necessário
        });
        setLoading(false);
      } catch (err) {
        console.error('Error fetching camera details:', err);
        setError('Não foi possível carregar os detalhes da câmera. Tente novamente mais tarde.');
        setLoading(false);
      }
    };

    if (deviceId) {
      fetchCameraDetails();
    } else {
      setLoading(false);
    }
  }, [deviceId]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null); // Limpar erro anterior
    setLoading(true);
    
    try {
      // Preparar dados para enviar (usando o estado atual do formData)
      // O cameraService.updateCamera já filtra os campos (name, location, etc.)
      console.log("Enviando dados para atualização:", formData); 
      
      await cameraService.updateCamera(deviceId, formData);
      
      setLoading(false);
      toast.success('Configurações da câmera atualizadas com sucesso!');
      // Opcional: Redirecionar ou apenas mostrar sucesso
      // navigate('/cameras'); 

    } catch (err) {
      console.error('Error updating camera:', err);
      const detail = err.response?.data?.detail;
      const errorMessage = typeof detail === 'string' 
                           ? detail 
                           : 'Não foi possível atualizar a câmera. Tente novamente mais tarde.';
      setError(errorMessage);
      toast.error(`Erro ao atualizar: ${errorMessage}`);
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Tem certeza que deseja excluir esta câmera?')) {
      try {
        setLoading(true);
        // Usar a função correta do cameraService
        await cameraService.deleteCamera(deviceId);
        setLoading(false);
        navigate('/cameras'); // Redirecionar para a lista de câmeras
        toast.success('Câmera excluída com sucesso');
      } catch (err) {
        console.error('Error deleting camera:', err);
        setError('Não foi possível excluir a câmera. Tente novamente mais tarde.');
        setLoading(false);
      }
    }
  };

  const handleDetectionSettingsSave = (settings) => {
    toast.success('Configurações de detecção salvas com sucesso');
  };

  const handleAISettingsSave = (settings) => {
    toast.success('Configurações de IA salvas com sucesso');
  };

  if (loading && !camera) {
    return (
      <div className="loading-container">
        <div className="loader"></div>
        <p>Carregando configurações da câmera...</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6">
      {error && (
        <div className="bg-red-100 text-red-700 p-4 rounded mb-6">
          {error}
        </div>
      )}
      
      <div className="camera-settings-tabs">
        <Tabs>
          <div className="overflow-x-auto">
            <TabList className="flex border-b mb-6 min-w-max">
              <Tab className="px-4 py-2 mr-2 cursor-pointer border-b-2 border-transparent hover:text-blue-600 whitespace-nowrap">
                Configurações Gerais
              </Tab>
              <Tab className="px-4 py-2 mr-2 cursor-pointer border-b-2 border-transparent hover:text-blue-600 whitespace-nowrap">
                Configurações de Detecção
              </Tab>
              <Tab className="px-4 py-2 mr-2 cursor-pointer border-b-2 border-transparent hover:text-blue-600 whitespace-nowrap">
                Modelo de IA
              </Tab>
            </TabList>
          </div>
          
          {/* Configurações Gerais */}
          <TabPanel>
            <div className="bg-white rounded-lg shadow p-6">
              <form onSubmit={handleSubmit}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-gray-700 mb-2" htmlFor="name">
                      Nome da Câmera
                    </label>
                    <input
                      id="name"
                      name="name"
                      type="text"
                      value={formData.name}
                      onChange={handleInputChange}
                      className="w-full p-2 border rounded"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-gray-700 mb-2" htmlFor="location">
                      Localização
                    </label>
                    <input
                      id="location"
                      name="location"
                      type="text"
                      value={formData.location}
                      onChange={handleInputChange}
                      className="w-full p-2 border rounded"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-gray-700 mb-2" htmlFor="ip_address">
                      Endereço IP
                    </label>
                    <input
                      id="ip_address"
                      name="ip_address"
                      type="text"
                      value={formData.ip_address}
                      onChange={handleInputChange}
                      className="w-full p-2 border rounded"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-gray-700 mb-2" htmlFor="port">
                      Porta
                    </label>
                    <input
                      id="port"
                      name="port"
                      type="number"
                      value={formData.port}
                      onChange={handleInputChange}
                      className="w-full p-2 border rounded"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-gray-700 mb-2" htmlFor="connector_type">
                      Tipo de Conector
                    </label>
                    <select
                      id="connector_type"
                      name="connector_type"
                      value={formData.connector_type}
                      onChange={handleInputChange}
                      className="w-full p-2 border rounded"
                    >
                      <option value="onvif">ONVIF</option>
                      <option value="hikvision">Hikvision</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-gray-700 mb-2" htmlFor="username">
                      Nome de Usuário
                    </label>
                    <input
                      id="username"
                      name="username"
                      type="text"
                      value={formData.username}
                      onChange={handleInputChange}
                      className="w-full p-2 border rounded"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-gray-700 mb-2" htmlFor="password">
                      Senha
                    </label>
                    <input
                      id="password"
                      name="password"
                      type="password"
                      value={formData.password}
                      onChange={handleInputChange}
                      className="w-full p-2 border rounded"
                      placeholder="Deixe em branco para manter a senha atual"
                    />
                  </div>
                </div>
                
                <div className="mt-6 flex flex-col sm:flex-row justify-between gap-4">
                  <button
                    type="button"
                    onClick={handleDelete}
                    className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded"
                  >
                    Excluir Câmera
                  </button>
                  
                  <button
                    type="submit"
                    disabled={loading}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
                  >
                    {loading ? 'Salvando...' : 'Salvar Alterações'}
                  </button>
                </div>
              </form>
            </div>
          </TabPanel>
          
          {/* Configurações de Detecção */}
          <TabPanel>
            <div className="bg-white rounded-lg shadow ">
              <DetectionSettings 
                cameraId={deviceId} 
                onSave={handleDetectionSettingsSave}
              />
            </div>
          </TabPanel>
          
          {/* Modelo de IA */}
          <TabPanel>
            <div className="bg-white rounded-lg shadow p-6">
              <AIModelSelector 
                cameraId={deviceId}
                onSave={handleAISettingsSave}
              />
            </div>
          </TabPanel>
        </Tabs>
      </div>
    </div>
  );
};

export default CameraSettings; 