import React, { useState, useEffect, useRef } from 'react';
import apiClient from '../services/api';
import { toast } from 'react-toastify';
import { FaLock, FaUnlock, FaPersonWalking, FaCar, FaPlus, FaMinus } from 'react-icons/fa6';
import DetectionZone from './DetectionZone';
// Importar API mockada para desenvolvimento
import mockApiClient from '../services/mock-api';

// Escolher qual API usar com base no ambiente
const client = process.env.NODE_ENV === 'development' ? mockApiClient : apiClient;

/**
 * Componente de configurações avançadas para ajustar parâmetros 
 * de detecção e reduzir falsos positivos.
 */
const DetectionSettings = ({ cameraId }) => {
  const [settings, setSettings] = useState({
    confidence_threshold: 0.5, // 0.0 - 1.0 (padrão: 0.5)
    min_detection_interval: 1, // segundos
    motion_sensitivity: 0.3, // 0.0 - 1.0 (padrão: 0.3)
    detection_classes: ['person', 'car', 'animal'], // classes a detectar
    notifications_enabled: true,
    save_all_frames: false,
    detection_zone: null, // zona de detecção personalizada
    detectionZones: []
  });

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [advanced, setAdvanced] = useState(false);
  // Detecta se é dispositivo móvel
  const [isMobile, setIsMobile] = useState(false);
  // Referências para os sliders
  const confidenceSliderRef = useRef(null);
  const motionSliderRef = useRef(null);
  
  const [cameraPreviewUrl, setCameraPreviewUrl] = useState('');
  const [detectionZones, setDetectionZones] = useState([]);
  
  // Verificar se é dispositivo móvel na montagem
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.matchMedia('(max-width: 768px)').matches;
      setIsMobile(mobile);
    };
    
    // Verificar inicialmente
    checkMobile();
    
    // Verificar em redimensionamentos
    window.addEventListener('resize', checkMobile);
    
    return () => {
      window.removeEventListener('resize', checkMobile);
    };
  }, []);
  
  // Classes para detecção disponíveis
  const availableClasses = [
    { value: 'person', label: 'Pessoas' },
    { value: 'car', label: 'Veículos' },
    { value: 'animal', label: 'Animais' },
    { value: 'bird', label: 'Pássaros' },
    { value: 'cat', label: 'Gatos' },
    { value: 'dog', label: 'Cães' },
    { value: 'bicycle', label: 'Bicicletas' },
    { value: 'motorcycle', label: 'Motos' }
  ];

  // Carregar configurações da câmera
  useEffect(() => {
    const loadSettings = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        if (cameraId) {
          // Usar cliente API escolhido com base no ambiente
          const response = await client.getDetectionSettings(cameraId);
          setSettings(response);
          
          // Carregar preview da câmera para usar com as zonas
          setCameraPreviewUrl(client.getCameraPreview(cameraId));
        }
      } catch (error) {
        console.error('Erro ao carregar configurações:', error);
        setError('Não foi possível carregar as configurações. Tente novamente.');
      } finally {
        setIsLoading(false);
      }
    };
    
    loadSettings();
  }, [cameraId]);

  // Salvar configurações
  const handleSave = async () => {
    setIsSaving(true);
    try {
      const updatedSettings = {
        ...settings,
        detectionZones // Incluir as zonas de detecção que foram modificadas
      };
      
      // Salvar usando o cliente API escolhido
      await client.saveDetectionSettings(cameraId, updatedSettings);
      toast.success('Configurações de detecção atualizadas com sucesso');
      
      if (onSave) {
        onSave(updatedSettings);
      }
    } catch (error) {
      console.error('Erro ao salvar configurações:', error);
      toast.error('Falha ao salvar configurações. Tente novamente.');
    } finally {
      setIsSaving(false);
    }
  };

  // Lidar com mudanças nos controles
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    
    // Usar parseFloat para valores numéricos
    const processedValue = type === 'checkbox' ? checked : 
                          (type === 'number' || type === 'range') ? parseFloat(value) : value;
    
    // Atualiza o estado
    setSettings(prev => ({
      ...prev,
      [name]: processedValue
    }));
    
    // Log para debug em dispositivos móveis
    if (isMobile) {
      console.log(`${name} alterado para ${processedValue}`);
    }
  };
  
  // Atualizar classes de detecção
  const handleClassToggle = (classValue) => {
    setSettings(prev => {
      const classes = [...prev.detection_classes];
      
      if (classes.includes(classValue)) {
        return {
          ...prev,
          detection_classes: classes.filter(c => c !== classValue)
        };
      } else {
        return {
          ...prev,
          detection_classes: [...classes, classValue]
        };
      }
    });
  };

  // Tratamento especial para sliders em dispositivos móveis
  const handleSliderTouchEnd = (e) => {
    if (!isMobile) return;
    
    const { name, value } = e.target;
    const numValue = parseFloat(value);
    
    // Força a atualização no fim do toque
    setSettings(prev => ({
      ...prev,
      [name]: numValue
    }));
    
    console.log(`Slider ${name} finalizado em ${numValue}`);
  };

  // Função para tratar mudanças nas zonas de detecção
  const handleZonesChange = (zones) => {
    setDetectionZones(zones);
  };

  // Classes reutilizáveis para tema escuro
  const labelClass = "block text-sm font-medium text-gray-300 mb-1";
  const inputClass = "mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-700 bg-gray-700 text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 rounded-md";
  const sliderClass = "w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer";
  const checkboxClass = "focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-700 bg-gray-700 rounded";
  const buttonClass = "inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500";

  if (isLoading) {
    return (
      <div className="p-4 bg-gray-800 rounded-lg animate-pulse">
        <div className="h-4 bg-gray-700 rounded w-3/4 mb-4"></div>
        <div className="h-8 bg-gray-700 rounded mb-4"></div>
        <div className="h-4 bg-gray-700 rounded w-1/2 mb-4"></div>
        <div className="h-8 bg-gray-700 rounded mb-4"></div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 shadow rounded-lg overflow-hidden">
      <div className="px-4 py-5 border-b border-gray-700 sm:px-6">
        <h3 className="text-lg leading-6 font-medium text-white">
          Configurações de Detecção
        </h3>
        <p className="mt-1 text-sm text-gray-400">
          Ajuste os parâmetros para reduzir falsos positivos e melhorar a precisão.
        </p>
      </div>
      
      <div className="px-4 py-5 sm:p-6 space-y-6">
        {/* Threshold de Confiança */}
        <div>
          <label htmlFor="confidence_threshold" className={labelClass}>
            Limiar de Confiança: {Math.round(settings.confidence_threshold * 100)}%
          </label>
          <div className="flex items-center space-x-2">
            <span className="text-xs text-gray-400">10%</span>
            <input
              type="range"
              id="confidence_threshold"
              name="confidence_threshold"
              min="0.1"
              max="0.95"
              step="0.05"
              value={settings.confidence_threshold}
              onChange={handleChange}
              onTouchEnd={handleSliderTouchEnd}
              ref={confidenceSliderRef}
              className={sliderClass}
              aria-describedby="confidence_help"
            />
            <span className="text-xs text-gray-400">95%</span>
          </div>
          <p className="mt-1 text-xs text-gray-400" id="confidence_help">
            Valor mais alto = menos falsos positivos, mas pode perder algumas detecções reais
          </p>
        </div>
        
        {/* Sensibilidade de Movimento */}
        <div>
          <label htmlFor="motion_sensitivity" className={labelClass}>
            Sensibilidade ao Movimento: {Math.round(settings.motion_sensitivity * 100)}%
          </label>
          <div className="flex items-center space-x-2">
            <span className="text-xs text-gray-400">Baixa</span>
            <input
              type="range"
              id="motion_sensitivity"
              name="motion_sensitivity"
              min="0.1"
              max="0.9"
              step="0.1"
              value={settings.motion_sensitivity}
              onChange={handleChange}
              onTouchEnd={handleSliderTouchEnd}
              ref={motionSliderRef}
              className={sliderClass}
            />
            <span className="text-xs text-gray-400">Alta</span>
          </div>
          <p className="mt-1 text-xs text-gray-400">
            Sensibilidade mais baixa ignora pequenos movimentos (folhas, sombras)
          </p>
        </div>
        
        {/* Intervalo Mínimo Entre Detecções */}
        <div>
          <label htmlFor="min_detection_interval" className={labelClass}>
            Intervalo Mínimo Entre Detecções (segundos)
          </label>
          <input
            type="number"
            id="min_detection_interval"
            name="min_detection_interval"
            min="1"
            max="60"
            value={settings.min_detection_interval}
            onChange={handleChange}
            className={inputClass}
          />
          <p className="mt-1 text-xs text-gray-400">
            Evita múltiplas notificações para o mesmo objeto
          </p>
        </div>
        
        {/* Classes para Detectar */}
        <div>
          <span className={labelClass}>Classes de Objetos para Detectar</span>
          <div className="mt-2 grid grid-cols-2 gap-2">
            {availableClasses.map(cls => (
              <div key={cls.value} className="flex items-center">
                <input
                  id={`class-${cls.value}`}
                  type="checkbox"
                  className={checkboxClass}
                  checked={settings.detection_classes.includes(cls.value)}
                  onChange={() => handleClassToggle(cls.value)}
                />
                <label htmlFor={`class-${cls.value}`} className="ml-2 text-sm text-gray-300">
                  {cls.label}
                </label>
              </div>
            ))}
          </div>
        </div>
        
        {/* Notificações */}
        <div>
          <div className="flex items-center">
            <input
              id="notifications_enabled"
              name="notifications_enabled"
              type="checkbox"
              className={checkboxClass}
              checked={settings.notifications_enabled}
              onChange={handleChange}
            />
            <label htmlFor="notifications_enabled" className="ml-2 text-sm text-gray-300">
              Enviar notificações para estas detecções
            </label>
          </div>
        </div>
        
        {/* Toggle para Configurações Avançadas */}
        <div className="pt-4 border-t border-gray-700">
          <button
            type="button"
            className="text-sm text-blue-400 hover:text-blue-300"
            onClick={() => setAdvanced(!advanced)}
          >
            {advanced ? 'Ocultar configurações avançadas' : 'Mostrar configurações avançadas'}
          </button>
        </div>
        
        {/* Configurações Avançadas */}
        {advanced && (
          <div className="space-y-4 pt-4 border-t border-gray-700">
            <div>
              <div className="flex items-center">
                <input
                  id="save_all_frames"
                  name="save_all_frames"
                  type="checkbox"
                  className={checkboxClass}
                  checked={settings.save_all_frames}
                  onChange={handleChange}
                />
                <label htmlFor="save_all_frames" className="ml-2 text-sm text-gray-300">
                  Salvar todos os frames (consome mais espaço)
                </label>
              </div>
            </div>
            
            <div>
              <span className={labelClass}>Zona de Detecção</span>
              <div className="bg-gray-700 p-4 rounded-md text-center">
                <DetectionZone 
                  imageUrl={cameraPreviewUrl}
                  initialZones={settings.detectionZones || []}
                  onChange={handleZonesChange}
                  readOnly={isLoading}
                />
              </div>
            </div>
          </div>
        )}
        
        {/* Botões de Ação */}
        <div className="pt-5 border-t border-gray-700">
          <div className="flex justify-end">
            <button
              type="button"
              className={buttonClass}
              onClick={handleSave}
              disabled={isSaving}
            >
              {isSaving ? 'Salvando...' : 'Salvar Configurações'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DetectionSettings; 