import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
// import axios from 'axios'; // Remover se não usado diretamente
// import apiClient from '../services/api'; // Remover
import cameraService from '../services/cameraService'; // Importar
import { toast } from 'react-toastify';

// Lista fixa de modelos disponíveis (AJUSTADA)
const availableModels = [
    // Manter apenas os modelos que existem em api/ai_models/
    // Exemplo: Se só temos o yolov8s.pt
    { id: "yolov8s.pt", name: "YOLOv8 Small", description: "Bom equilíbrio entre velocidade e precisão.", classes: ["pessoa", "carro"], size_mb: 22, speed_rating: "Médio-Alto" },
    // Comentar ou remover os outros que não estão disponíveis no backend agora
    // { id: "yolov8n.pt", name: "YOLOv8 Nano", description: "Leve e rápido, bom para CPUs ou edge.", classes: ["pessoa", "carro"], size_mb: 6, speed_rating: "Alto" },
    // { id: "yolov8m.pt", name: "YOLOv8 Medium", description: "Mais preciso, requer mais recursos.", classes: ["pessoa", "carro"], size_mb: 50, speed_rating: "Médio" },
];

/**
 * Componente para selecionar e configurar modelos de IA para uma câmera específica
 */
const AIModelSelector = ({ cameraId, onSave }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [models, setModels] = useState(availableModels);
  const [selectedModel, setSelectedModel] = useState(availableModels.length > 0 ? availableModels[0].id : '');
  const [currentSettings, setCurrentSettings] = useState({
    enabled: true,
    model_id: availableModels.length > 0 ? availableModels[0].id : '',
    confidence_threshold: 0.4,
    use_gpu: true,
    enable_tracking: false
  });
  
  // Carregar configurações atuais
  useEffect(() => {
    const fetchData = async () => {
      if (!cameraId) {
        console.warn("AIModelSelector: cameraId não fornecido.");
        setIsLoading(false);
        return;
      }
      
      setIsLoading(true);
      setError(null);
      
      try {
        const settings = await cameraService.getCameraAISettings(cameraId);
        
        setCurrentSettings({
          enabled: settings.enabled !== false,
          model_id: settings.model_id || (availableModels.length > 0 ? availableModels[0].id : ''),
          confidence_threshold: typeof settings.confidence_threshold === 'number' && settings.confidence_threshold >= 0.1 && settings.confidence_threshold <= 0.9 
                                  ? settings.confidence_threshold 
                                  : 0.4,
          use_gpu: settings.use_gpu !== false,
          enable_tracking: settings.enable_tracking === true
        });
        
        setSelectedModel(settings.model_id || (availableModels.length > 0 ? availableModels[0].id : ''));
        
      } catch (err) {
        console.error('Erro ao carregar dados de IA:', err);
        setError('Não foi possível carregar as configurações de IA. Usando padrões.');
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
    
    let processedValue;
    if (type === 'checkbox') {
      processedValue = checked;
    } else if (name === 'confidence_threshold') { 
      // Tratar especificamente o range slider, converter para float
      processedValue = parseFloat(value);
    } else {
      processedValue = value;
    }
    
    setCurrentSettings(prev => ({
      ...prev,
      [name]: processedValue
    }));
  };
  
  // Salvar configurações
  const handleSave = async () => {
    if (!cameraId) {
        toast.error("ID da câmera não encontrado para salvar configurações.");
        return;
    }
    setIsLoading(true);
    setError(null);
    
    try {
      // Log antes de enviar
      console.log("[AIModelSelector] Enviando currentSettings:", JSON.stringify(currentSettings)); 
      console.log("[AIModelSelector] Tipo de confidence_threshold antes de enviar:", typeof currentSettings.confidence_threshold);

      await cameraService.updateCameraAISettings(cameraId, currentSettings);
      toast.success('Configurações de IA salvas com sucesso (simulado no backend)');
      
      if (onSave) {
        onSave(currentSettings);
      }
    } catch (err) {
      console.error('Erro ao salvar configurações de IA:', err);
      const detail = err.response?.data?.detail;
      setError(`Não foi possível salvar as configurações: ${detail || 'Erro desconhecido'}`);
      toast.error(`Erro ao salvar configurações de IA: ${detail || 'Erro desconhecido'}`);
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
  
  if (isLoading && (!models || !Array.isArray(models) || models.length === 0)) {
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
            
            {!models || models.length === 0 ? (
              <p className="text-gray-500">Nenhum modelo disponível</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Array.isArray(models) && models.map(model => renderModelCard(model))}
              </div>
            )}
          </div>
          
          <div className="border-t border-gray-200 pt-4">
            <h4 className="font-medium text-gray-700 mb-3">Ajustes de Detecção:</h4>
            
            <div className="space-y-4">
              <div>
                <label htmlFor="confidence-threshold" className="block text-sm font-medium text-gray-700">
                  Limiar de Confiança: {typeof currentSettings.confidence_threshold === 'number' 
                                        ? currentSettings.confidence_threshold.toFixed(2) 
                                        : 'N/A'}
                </label>
                <input
                  type="range"
                  id="confidence-threshold"
                  name="confidence_threshold"
                  min="0.1"
                  max="0.9"
                  step="0.05"
                  value={typeof currentSettings.confidence_threshold === 'number' ? currentSettings.confidence_threshold : 0.4}
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
                  checked={!!currentSettings.use_gpu}
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
                  checked={!!currentSettings.enable_tracking}
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