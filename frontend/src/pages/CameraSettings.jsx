import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import MainLayout from '../components/MainLayout';
import DetectionSettings from '../components/DetectionSettings';
import { toast } from 'react-toastify';
import AIModelSelector from '../components/AIModelSelector';
import { Tab, Tabs, TabList, TabPanel } from 'react-tabs';
import 'react-tabs/style/react-tabs.css';

const CameraSettings = () => {
  const { deviceId } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [camera, setCamera] = useState(null);
  const [activeTab, setActiveTab] = useState('general'); // 'general' ou 'detection'
  const [formData, setFormData] = useState({
    name: '',
    location: '',
    username: '',
    password: '',
    ip_address: '',
    port: 80,
    connector_type: 'onvif'
  });

  useEffect(() => {
    const fetchCameraDetails = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`/api/devices/${deviceId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        setCamera(response.data);
        setFormData({
          name: response.data.name || '',
          location: response.data.location || '',
          username: response.data.username || '',
          password: '',  // Não preenchemos a senha por segurança
          ip_address: response.data.ip_address || '',
          port: response.data.port || 80,
          connector_type: response.data.connector_type || 'onvif'
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
  }, [deviceId, token]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      await axios.put(`/api/devices/${deviceId}`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setLoading(false);
      toast.success('Configurações da câmera atualizadas com sucesso');
    } catch (err) {
      console.error('Error updating camera:', err);
      setError('Não foi possível atualizar a câmera. Tente novamente mais tarde.');
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Tem certeza que deseja excluir esta câmera?')) {
      try {
        setLoading(true);
        await axios.delete(`/api/devices/${deviceId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setLoading(false);
        navigate('/camera-dashboard');
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
    <MainLayout>
      <div className="container mx-auto px-4 py-6">
        <h1 className="text-2xl font-bold mb-6">Configurações da Câmera</h1>
        
        {error && (
          <div className="bg-red-100 text-red-700 p-4 rounded mb-6">
            {error}
          </div>
        )}
        
        <Tabs>
          <TabList className="flex border-b mb-6">
            <Tab className="px-4 py-2 mr-2 cursor-pointer border-b-2 border-transparent hover:text-blue-600">
              Configurações Gerais
            </Tab>
            <Tab className="px-4 py-2 mr-2 cursor-pointer border-b-2 border-transparent hover:text-blue-600">
              Configurações de Detecção
            </Tab>
            <Tab className="px-4 py-2 mr-2 cursor-pointer border-b-2 border-transparent hover:text-blue-600">
              Modelo de IA
            </Tab>
          </TabList>
          
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
                
                <div className="mt-6 flex justify-between">
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
            <div className="bg-white rounded-lg shadow p-6">
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
    </MainLayout>
  );
};

export default CameraSettings; 