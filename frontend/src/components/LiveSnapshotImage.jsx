import React, { useState, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import cameraService from '../services/cameraService'; // Importar o serviço

const LiveSnapshotImage = ({ 
  cameraId, 
  isCameraActive, // Nova prop para indicar se a câmera está ativa
  interval = 5000, 
  className = '' 
}) => {
  const [imageUrl, setImageUrl] = useState('/camera-offline.png'); // Começa com fallback
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const currentObjectURL = useRef(null); // Ref para guardar a URL do objeto atual
  const intervalId = useRef(null); // Ref para guardar o ID do intervalo
  const isMounted = useRef(true); // Ref para verificar se o componente está montado

  const fetchSnapshot = async () => {
    // Não buscar se a câmera não estiver ativa ou não tiver ID
    if (!isCameraActive || !cameraId) {
      // console.log(`[LiveSnapshot ${cameraId}] Skipping fetch, camera inactive or no ID.`);
      // Garantir que a imagem de offline seja exibida se estava mostrando outra coisa
      if (imageUrl !== '/camera-offline.png') {
         setImageUrl('/camera-offline.png');
      }
      // Limpar URL de objeto antiga se existir
      if (currentObjectURL.current) {
        URL.revokeObjectURL(currentObjectURL.current);
        currentObjectURL.current = null;
      }
      setIsLoading(false); // Garantir que loading não fique preso
      setError(null); // Limpar erro anterior
      return;
    }
    
    // console.log(`[LiveSnapshot ${cameraId}] Fetching new snapshot (camera active)...`);
    setIsLoading(true);
    setError(null);
    try {
      // Usar force=true aqui? Ou deixar o backend decidir (placeholder)? 
      // Por enquanto, chamaremos sem force=true, confiando no backend para retornar placeholder se necessário.
      const blob = await cameraService.getCameraSnapshotBlob(cameraId); // <<< Chamada continua aqui

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
    fetchSnapshot(); // Busca inicial (já considera isCameraActive)

    // Limpar intervalo anterior ao reconfigurar
    if (intervalId.current) {
      clearInterval(intervalId.current);
      intervalId.current = null;
    }

    // Configurar intervalo para busca periódica APENAS se a câmera estiver ativa
    if (interval > 0 && isCameraActive) {
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
    // Re-executar se ID, intervalo OU ESTADO DA CÂMERA mudarem
  }, [cameraId, interval, isCameraActive]); 

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
  isCameraActive: PropTypes.bool.isRequired, // Adicionar propType
  interval: PropTypes.number, // Intervalo em ms para refresh
  className: PropTypes.string,
};

export default LiveSnapshotImage;