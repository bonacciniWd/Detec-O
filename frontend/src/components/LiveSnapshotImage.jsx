import React, { useState, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import cameraService from '../services/cameraService'; // Importar o serviço

const LiveSnapshotImage = ({ cameraId, interval = 5000, className = '' }) => {
  const [imageUrl, setImageUrl] = useState('/camera-offline.png'); // Começa com fallback
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const currentObjectURL = useRef(null); // Ref para guardar a URL do objeto atual
  const intervalId = useRef(null); // Ref para guardar o ID do intervalo
  const isMounted = useRef(true); // Ref para verificar se o componente está montado

  const fetchSnapshot = async () => {
    if (!cameraId) return;
    // console.log(`[LiveSnapshot ${cameraId}] Fetching new snapshot...`);
    setIsLoading(true);
    setError(null);
    try {
      const blob = await cameraService.getCameraSnapshotBlob(cameraId);

      // Limpar URL antiga antes de criar a nova
      if (currentObjectURL.current) {
        URL.revokeObjectURL(currentObjectURL.current);
      }

      // Criar nova URL de objeto
      const objectURL = URL.createObjectURL(blob);
      currentObjectURL.current = objectURL;

      // Atualizar o estado apenas se o componente ainda estiver montado
      if (isMounted.current) {
        setImageUrl(objectURL);
      }

    } catch (err) {
      // console.error(`[LiveSnapshot ${cameraId}] Error fetching snapshot:`, err);
      setError('Falha ao carregar snapshot');
      // Manter imagem de fallback em caso de erro
      if (isMounted.current) {
         setImageUrl('/camera-offline.png');
      }
      // Parar o intervalo se houver erro para não ficar tentando?
      // if (intervalId.current) clearInterval(intervalId.current);
    } finally {
      if (isMounted.current) {
        setIsLoading(false);
      }
    }
  };

  useEffect(() => {
    isMounted.current = true; // Marcar como montado
    fetchSnapshot(); // Busca inicial

    // Configurar intervalo para busca periódica
    if (interval > 0) {
      intervalId.current = setInterval(fetchSnapshot, interval);
    }

    // Função de limpeza
    return () => {
      isMounted.current = false; // Marcar como desmontado
      if (intervalId.current) {
        clearInterval(intervalId.current);
      }
      // Limpar a última URL de objeto criada
      if (currentObjectURL.current) {
        URL.revokeObjectURL(currentObjectURL.current);
      }
    };
  }, [cameraId, interval]); // Re-executar se ID ou intervalo mudarem

  return (
    <div className={`relative ${className}`}>
      <img
        src={imageUrl}
        alt={`Live snapshot para ${cameraId}`}
        className="w-full h-full object-cover" // Garante que a imagem preencha o container
        // onError já é tratado pela lógica que define a URL de fallback
      />
      {/* Indicador de Loading (Opcional) */}
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50">
          <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-white"></div>
        </div>
      )}
      {/* Indicador de Erro (Opcional) */}
      {error && !isLoading && (
         <div className="absolute bottom-0 left-0 right-0 bg-red-800 bg-opacity-80 text-white text-xs text-center p-1">
            {error}
          </div>
      )}
    </div>
  );
};

LiveSnapshotImage.propTypes = {
  cameraId: PropTypes.string.isRequired,
  interval: PropTypes.number, // Intervalo em ms para refresh
  className: PropTypes.string,
};

export default LiveSnapshotImage;