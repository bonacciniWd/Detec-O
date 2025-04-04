import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import axios from 'axios';
import { toast } from 'react-toastify';

/**
 * Componente para selecionar e configurar modelos de IA para uma câmera específica
 */
const AIModelSelector = ({ cameraId, onSave }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [currentSettings, setCurrentSettings] = useState({
    enabled: true,
    model_id: '',
    confidence_threshold: 0.4,
    use_gpu: true,
    enable_tracking: true
  });
  
  // Carregar modelos disponíveis e configurações atuais
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        // Buscar modelos disponíveis
        const modelsResponse = await axios.get('/api/v1/ai/models');
        setModels(modelsResponse.data);
        
        // Buscar configurações atuais da câmera
        const settingsResponse = await axios.get(`/api/v1/cameras/${cameraId}/ai-settings`);
        const settings = settingsResponse.data;
        
        setCurrentSettings({
          enabled: settings.enabled !== false,
          model_id: settings.model_id || '',
          confidence_threshold: settings.confidence_threshold || 0.4,
          use_gpu: settings.use_gpu !== false,
          enable_tracking: settings.enable_tracking !== false
        });
        
        // Definir modelo selecionado
        if (settings.model_id) {
          setSelectedModel(settings.model_id);
        } else if (modelsResponse.data.length > 0) {
          // Selecionar o primeiro modelo como padrão
          setSelectedModel(modelsResponse.data[0].id);
        }
      } catch (err) {
        console.error('Erro ao carregar dados:', err);
        setError('Não foi possível carregar os modelos ou configurações. Tente novamente.');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchData();
  }, [cameraId]);
  
  // Atualizar as configurações locais quando o modelo selecionado muda
  useEffect(() => {
    if (selectedModel) {
      setCurrentSettings(prev => ({
        ...prev,
        model_id: selectedModel
      }));
    }
  }, [selectedModel]);
  
  // Lidar com mudanças nos campos
  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    
    setCurrentSettings(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : 
              type === 'number' ? parseFloat(value) : 
              value
    }));
  };
  
  // Salvar configurações
  const handleSave = async () => {
    setIsLoading(true);
    
    try {
      await axios.put(`/api/v1/cameras/${cameraId}/ai-settings`, currentSettings);
      toast.success('Configurações de IA salvas com sucesso');
      
      if (onSave) {
        onSave(currentSettings);
      }
    } catch (err) {
      console.error('Erro ao salvar configurações:', err);
      setError('Não foi possível salvar as configurações. Tente novamente.');
      toast.error('Erro ao salvar configurações de IA');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Renderizar card para cada modelo com detalhes
  const renderModelCard = (model) => {
    const isSelected = selectedModel === model.id;
    
    return (
      <div 
        key={model.id}
        className={`border rounded-lg p-4 cursor-pointer transition-all ${
          isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-blue-300'
        }`}
        onClick={() => setSelectedModel(model.id)}
      >
        <div className="flex items-start justify-between">
          <div>
            <h3 className="font-medium text-gray-900">{model.name}</h3>
            <p className="text-sm text-gray-600">{model.description}</p>
            <div className="mt-2 text-xs text-gray-500">
              <p>Classes: {model.classes?.length || 0}</p>
              <p>Tamanho: {model.size_mb ? `${model.size_mb} MB` : 'N/A'}</p>
              <p>Velocidade: {model.speed_rating || 'N/A'}</p>
            </div>
          </div>
          <div className="flex items-center h-full">
            <input
              type="radio"
              checked={isSelected}
              onChange={() => setSelectedModel(model.id)}
              className="h-5 w-5 text-blue-600"
            />
          </div>
        </div>
      </div>
    );
  };
  
  if (isLoading && models.length === 0) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
        <span className="ml-2">Carregando modelos...</span>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Configurações de Inteligência Artificial</h3>
        <p className="text-sm text-gray-600">
          Selecione e configure o modelo de detecção para esta câmera.
        </p>
      </div>
      
      {error && (
        <div className="bg-red-50 p-4 rounded-md">
          <p className="text-red-700">{error}</p>
        </div>
      )}
      
      <div className="flex items-center mb-4">
        <input
          type="checkbox"
          id="ai-enabled"
          name="enabled"
          checked={currentSettings.enabled}
          onChange={handleInputChange}
          className="h-4 w-4 text-blue-600 focus:ring-blue-500"
        />
        <label htmlFor="ai-enabled" className="ml-2 text-gray-700">
          Habilitar processamento de IA para esta câmera
        </label>
      </div>
      
      {currentSettings.enabled && (
        <>
          <div className="border-t border-gray-200 pt-4">
            <h4 className="font-medium text-gray-700 mb-3">Selecione o Modelo:</h4>
            
            {models.length === 0 ? (
              <p className="text-gray-500">Nenhum modelo disponível</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {models.map(model => renderModelCard(model))}
              </div>
            )}
          </div>
          
          <div className="border-t border-gray-200 pt-4">
            <h4 className="font-medium text-gray-700 mb-3">Ajustes de Detecção:</h4>
            
            <div className="space-y-4">
              <div>
                <label htmlFor="confidence-threshold" className="block text-sm font-medium text-gray-700">
                  Limiar de Confiança: {currentSettings.confidence_threshold.toFixed(2)}
                </label>
                <input
                  type="range"
                  id="confidence-threshold"
                  name="confidence_threshold"
                  min="0.1"
                  max="0.9"
                  step="0.05"
                  value={currentSettings.confidence_threshold}
                  onChange={handleInputChange}
                  className="mt-1 w-full"
                />
                <div className="flex justify-between text-xs text-gray-500">
                  <span>Mais Detecções (0.1)</span>
                  <span>Mais Precisão (0.9)</span>
                </div>
              </div>
              
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="use-gpu"
                  name="use_gpu"
                  checked={currentSettings.use_gpu}
                  onChange={handleInputChange}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500"
                />
                <label htmlFor="use-gpu" className="ml-2 text-gray-700">
                  Usar GPU para processamento (recomendado se disponível)
                </label>
              </div>
              
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="enable-tracking"
                  name="enable_tracking"
                  checked={currentSettings.enable_tracking}
                  onChange={handleInputChange}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500"
                />
                <label htmlFor="enable-tracking" className="ml-2 text-gray-700">
                  Habilitar rastreamento de objetos entre frames
                </label>
              </div>
            </div>
          </div>
        </>
      )}
      
      <div className="pt-4 flex justify-end">
        <button
          type="button"
          onClick={handleSave}
          disabled={isLoading}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md disabled:opacity-50"
        >
          {isLoading ? 'Salvando...' : 'Salvar Configurações'}
        </button>
      </div>
    </div>
  );
};

AIModelSelector.propTypes = {
  cameraId: PropTypes.string.isRequired,
  onSave: PropTypes.func
};

export default AIModelSelector; 