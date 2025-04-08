import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import apiClient from '../services/api';

const DetectionSettings = ({ cameraId, onSave }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [settings, setSettings] = useState({
    enabled: false,
    confidence_threshold: 0.5,
    iou_threshold: 0.45,
    detect_objects: true,
    detect_behaviors: true,
    detection_interval: 5,
    alert_on_detection: true,
    object_classes: ["knife", "gun", "scissors"],
    behavior_classes: ["aggressive_posture", "running", "fighting"]
  });
  
  const [isUploading, setIsUploading] = useState(false);
  const [testImage, setTestImage] = useState(null);
  const [testImagePreview, setTestImagePreview] = useState(null);
  const [detectionResult, setDetectionResult] = useState(null);
  
  // Carregar configurações existentes
  useEffect(() => {
    const fetchSettings = async () => {
      try {
        setIsLoading(true);
        const response = await apiClient.get(`/v1/detection/settings/${cameraId}`);
        if (response.data && response.data.settings) {
          setSettings(response.data.settings);
        }
      } catch (error) {
        console.error('Erro ao carregar configurações de detecção:', error);
        toast.error('Erro ao carregar configurações de detecção');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchSettings();
  }, [cameraId]);
  
  // Atualizar settings quando um campo for alterado
  const handleSettingChange = (name, value) => {
    setSettings(prevSettings => ({
      ...prevSettings,
      [name]: value
    }));
  };
  
  // Alternar classes a serem detectadas
  const toggleObjectClass = (className) => {
    const classes = [...settings.object_classes];
    const index = classes.indexOf(className);
    
    if (index >= 0) {
      classes.splice(index, 1);
    } else {
      classes.push(className);
    }
    
    setSettings(prevSettings => ({
      ...prevSettings,
      object_classes: classes
    }));
  };
  
  // Alternar classes de comportamento a serem detectadas
  const toggleBehaviorClass = (className) => {
    const classes = [...settings.behavior_classes];
    const index = classes.indexOf(className);
    
    if (index >= 0) {
      classes.splice(index, 1);
    } else {
      classes.push(className);
    }
    
    setSettings(prevSettings => ({
      ...prevSettings,
      behavior_classes: classes
    }));
  };

  // Salvar configurações
  const saveSettings = async () => {
    try {
      setIsLoading(true);
      await apiClient.post(`/v1/detection/configure/${cameraId}`, settings);
      toast.success('Configurações salvas com sucesso');
      
      if (onSave) {
        onSave(settings);
      }
    } catch (error) {
      console.error('Erro ao salvar configurações:', error);
      toast.error('Erro ao salvar configurações');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Lidar com upload de imagem para teste
  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    setTestImage(file);
    
    // Criar preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setTestImagePreview(reader.result);
    };
    reader.readAsDataURL(file);
    
    // Limpar resultado anterior
    setDetectionResult(null);
  };
  
  // Testar detecção com uma imagem
  const handleTestDetection = async () => {
    if (!testImage) {
      toast.warning('Selecione uma imagem para teste');
      return;
    }
    
    try {
      setIsUploading(true);
      
      const formData = new FormData();
      formData.append('file', testImage);
      
      const response = await apiClient.post(
        `/v1/detection/analyze?confidence=${settings.confidence_threshold}&camera_id=${cameraId}`, 
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      );
      
      setDetectionResult(response.data);
      toast.success(`Detecção concluída. ${response.data.detections.length} objetos encontrados.`);
    } catch (error) {
      console.error('Erro ao testar detecção:', error);
      toast.error('Erro ao processar imagem');
    } finally {
      setIsUploading(false);
    }
  };
  
  // Lista de classes disponíveis
  const availableObjectClasses = [
    { id: "person", label: "Pessoa" },
    { id: "knife", label: "Faca" },
    { id: "gun", label: "Arma" },
    { id: "scissors", label: "Tesoura" },
    { id: "backpack", label: "Mochila" },
    { id: "sports ball", label: "Bola" },
    { id: "bottle", label: "Garrafa" }
  ];
  
  const availableBehaviorClasses = [
    { id: "aggressive_posture", label: "Postura Agressiva" },
    { id: "running", label: "Correndo" },
    { id: "fighting", label: "Briga" },
    { id: "falling_person", label: "Pessoa Caindo" }
  ];

  return (
    <div className="bg-gray-800 rounded-lg p-4 mt-4">
      {isLoading ? (
        <div className="flex justify-center py-4">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      ) : (
        <>
          {/* Status da detecção */}
          <div className="mb-4">
            <label className="block text-gray-300 mb-2">
              Status da Detecção
            </label>
            <div className="flex items-center">
              <button
                onClick={() => handleSettingChange('enabled', !settings.enabled)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
                  settings.enabled ? 'bg-blue-600' : 'bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.enabled ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
              <span className="ml-2 text-gray-300">
                {settings.enabled ? 'Ativada' : 'Desativada'}
              </span>
            </div>
      </div>
      
          {/* Threshold de confiança */}
          <div className="mb-4">
            <label className="block text-gray-300 mb-2">
              Limiar de Confiança: {settings.confidence_threshold.toFixed(2)}
          </label>
            <input
              type="range"
              min="0.1"
              max="1"
              step="0.05"
              value={settings.confidence_threshold}
              onChange={(e) => handleSettingChange('confidence_threshold', parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-400 px-1">
              <span>0.1</span>
              <span>0.5</span>
              <span>1.0</span>
          </div>
        </div>
        
          {/* Intervalo de detecção */}
          <div className="mb-4">
            <label className="block text-gray-300 mb-2">
              Intervalo de Detecção: {settings.detection_interval} frames
          </label>
            <input
              type="range"
              min="1"
              max="30"
              step="1"
              value={settings.detection_interval}
              onChange={(e) => handleSettingChange('detection_interval', parseInt(e.target.value))}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-400 px-1">
              <span>1</span>
              <span>15</span>
              <span>30</span>
          </div>
        </div>
        
          {/* Classes de objetos */}
          <div className="mb-4">
            <label className="block text-gray-300 mb-2">
              Objetos a Detectar
          </label>
            <div className="grid grid-cols-2 gap-2">
              {availableObjectClasses.map(objectClass => (
                <div key={objectClass.id} className="flex items-center">
          <input
                    type="checkbox"
                    id={`object-${objectClass.id}`}
                    checked={settings.object_classes.includes(objectClass.id)}
                    onChange={() => toggleObjectClass(objectClass.id)}
                    className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-600"
                  />
                  <label
                    htmlFor={`object-${objectClass.id}`}
                    className="ml-2 text-sm text-gray-300"
                  >
                    {objectClass.label}
                  </label>
                </div>
              ))}
            </div>
        </div>
        
          {/* Classes de comportamento */}
          <div className="mb-4">
            <label className="block text-gray-300 mb-2">
              Comportamentos a Detectar
            </label>
            <div className="grid grid-cols-2 gap-2">
              {availableBehaviorClasses.map(behaviorClass => (
                <div key={behaviorClass.id} className="flex items-center">
                <input
                  type="checkbox"
                    id={`behavior-${behaviorClass.id}`}
                    checked={settings.behavior_classes.includes(behaviorClass.id)}
                    onChange={() => toggleBehaviorClass(behaviorClass.id)}
                    className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-600"
                  />
                  <label
                    htmlFor={`behavior-${behaviorClass.id}`}
                    className="ml-2 text-sm text-gray-300"
                  >
                    {behaviorClass.label}
                </label>
              </div>
            ))}
          </div>
        </div>
        
          {/* Ações */}
          <div className="mb-4">
            <label className="block text-gray-300 mb-2">
              Ações
            </label>
            <div className="flex items-center mb-2">
            <input
              type="checkbox"
                id="alert-on-detection"
                checked={settings.alert_on_detection}
                onChange={(e) => handleSettingChange('alert_on_detection', e.target.checked)}
                className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-600"
              />
              <label
                htmlFor="alert-on-detection"
                className="ml-2 text-sm text-gray-300"
              >
                Alertar quando objetos perigosos forem detectados
            </label>
          </div>
        </div>
        
          {/* Botão de salvar */}
          <div className="mt-6">
          <button
              onClick={saveSettings}
              disabled={isLoading}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md"
            >
              {isLoading ? 'Salvando...' : 'Salvar Configurações'}
          </button>
        </div>
        
          {/* Testes de Detecção */}
          <div className="mt-8 border-t border-gray-700 pt-4">
            <h4 className="text-lg font-medium text-white mb-4">Teste de Detecção</h4>
            
            <div className="mb-4">
              <label className="block text-gray-300 mb-2">
                Upload de Imagem para Teste
              </label>
                <input
                type="file"
                accept="image/*"
                onChange={handleImageChange}
                className="block w-full text-sm text-gray-300 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-medium file:bg-blue-600 file:text-white hover:file:bg-blue-700"
              />
            </div>
            
            {testImagePreview && (
              <div className="mb-4">
                <p className="text-gray-300 mb-2">Imagem selecionada:</p>
                <div className="relative">
                  <img 
                    src={testImagePreview} 
                    alt="Preview" 
                    className="max-h-64 rounded-md" 
                  />
                  <button
                    onClick={handleTestDetection}
                    disabled={isUploading}
                    className="mt-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md"
                  >
                    {isUploading ? 'Processando...' : 'Testar Detecção'}
                  </button>
                </div>
              </div>
            )}
            
            {detectionResult && (
              <div className="mt-4">
                <h5 className="text-white font-medium mb-2">Resultado da Detecção:</h5>
                
                <div className="bg-gray-700 p-3 rounded-md mb-4">
                  <p className="text-gray-300">
                    <span className="font-medium">Objetos Detectados:</span> {detectionResult.detections.length}
                  </p>
                  <p className="text-gray-300">
                    <span className="font-medium">Comportamentos:</span> {detectionResult.behaviors.length}
                  </p>
                  <p className="text-gray-300">
                    <span className="font-medium">Tempo de Inferência:</span> {(detectionResult.statistics.inference_time * 1000).toFixed(1)}ms
                  </p>
            </div>
                
                {detectionResult.image_result && (
                  <div>
                    <p className="text-gray-300 mb-2">Imagem com detecções:</p>
                    <img 
                      src={detectionResult.image_result} 
                      alt="Detection Result" 
                      className="max-w-full rounded-md" 
                    />
          </div>
        )}
        
                {detectionResult.detections.length > 0 && (
                  <div className="mt-4">
                    <p className="text-white font-medium mb-2">Detecções:</p>
                    <div className="max-h-60 overflow-y-auto">
                      {detectionResult.detections.map((detection, index) => (
                        <div key={index} className={`mb-2 p-2 rounded ${detection.is_dangerous ? 'bg-red-900/40' : 'bg-gray-700'}`}>
                          <p className="text-gray-300">
                            <span className="font-medium">Classe:</span> {detection.class_name}
                          </p>
                          <p className="text-gray-300">
                            <span className="font-medium">Confiança:</span> {(detection.confidence * 100).toFixed(1)}%
                          </p>
                          {detection.is_dangerous && (
                            <p className="text-red-400 font-medium">Objeto Perigoso! Severidade: {detection.severity}</p>
                          )}
                        </div>
                      ))}
          </div>
        </div>
                )}
              </div>
            )}
      </div>
        </>
      )}
    </div>
  );
};

export default DetectionSettings; 