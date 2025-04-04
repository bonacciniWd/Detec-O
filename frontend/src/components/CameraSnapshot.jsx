import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';

/**
 * Componente para exibir snapshots de câmeras com atualização periódica.
 */
const CameraSnapshot = ({
  deviceId,
  streamId,
  cameraName = '',
  interval = 5000,
  onExpand,
  onError,
  className = '',
  showControls = true,
  autoRefresh = true,
  quality = 'medium'
}) => {
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [imageUrl, setImageUrl] = useState(null);
  const [timestamp, setTimestamp] = useState(Date.now());
  const intervalRef = useRef(null);
  const [updating, setUpdating] = useState(false);

  // Função para buscar o snapshot da câmera
  const fetchSnapshot = async () => {
    if (updating) return; // Evita múltiplas requisições simultâneas
    
    try {
      setUpdating(true);
      
      // Construir a URL com cache-busting
      const url = `/api/devices/${deviceId}/cached-snapshot/${streamId}?quality=${quality}&t=${Date.now()}`;
      
      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      
      // Cria uma URL para o blob e atualiza o estado
      const blob = new Blob([response.data], { type: 'image/jpeg' });
      const imageObjectUrl = URL.createObjectURL(blob);
      
      // Limpa a URL anterior para evitar vazamento de memória
      if (imageUrl) {
        URL.revokeObjectURL(imageUrl);
      }
      
      setImageUrl(imageObjectUrl);
      setTimestamp(Date.now());
      setLoading(false);
      setError(null);
    } catch (err) {
      console.error('Error fetching camera snapshot:', err);
      setError('Não foi possível carregar a imagem');
      setLoading(false);
    } finally {
      setUpdating(false);
    }
  };

  // Configurar o intervalo de atualização
  useEffect(() => {
    if (autoRefresh) {
      fetchSnapshot(); // Busca inicial
      
      // Configura o intervalo para atualizações periódicas
      intervalRef.current = setInterval(fetchSnapshot, interval);
    } else {
      fetchSnapshot(); // Busca única
    }
    
    // Limpar o intervalo ao desmontar o componente
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      
      // Limpar URL do objeto ao desmontar
      if (imageUrl) {
        URL.revokeObjectURL(imageUrl);
      }
    };
  }, [deviceId, streamId, interval, autoRefresh, quality]);

  // Calcular tempo desde a última atualização
  const getTimeSinceUpdate = () => {
    const seconds = Math.floor((Date.now() - timestamp) / 1000);
    if (seconds < 60) return `${seconds}s atrás`;
    return `${Math.floor(seconds / 60)}m ${seconds % 60}s atrás`;
  };

  return (
    <div className={`relative bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden ${className}`}>
      <div className="aspect-video relative">
        {loading && !imageUrl && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-100 dark:bg-gray-700">
            <div className="loader"></div>
          </div>
        )}
        
        {error && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <p>{error}</p>
          </div>
        )}
        
        {imageUrl && (
          <img
            src={imageUrl}
            alt={cameraName || 'Snapshot da câmera'}
            className="w-full h-full object-cover cursor-pointer"
            onClick={() => onExpand && onExpand(deviceId, streamId, cameraName)}
          />
        )}
        
        {updating && (
          <div className="absolute bottom-0 left-0 right-0 h-1">
            <div className="loading-bar"></div>
          </div>
        )}
      </div>
      
      {showControls && (
        <div className="p-3 flex justify-between items-center border-t border-gray-200 dark:border-gray-700">
          <div className="text-xs text-gray-500 dark:text-gray-400">
            {getTimeSinceUpdate()}
          </div>
          
          <div className="flex space-x-2">
            <button
              onClick={fetchSnapshot}
              className="p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              title="Atualizar"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
            
            <button
              onClick={() => onExpand && onExpand(deviceId, streamId, cameraName)}
              className="p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              title="Expandir"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5v-4m0 4h-4m4 0l-5-5" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default CameraSnapshot; 