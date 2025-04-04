import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import Hls from 'hls.js';

/**
 * Modal para exibir streams de vídeo em tela cheia ou grande.
 */
const StreamModal = ({ isOpen, deviceId, streamId, cameraName = 'Câmera', onClose }) => {
  const { token } = useAuth();
  const videoRef = useRef(null);
  const hlsRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [streamUrl, setStreamUrl] = useState(null);
  
  // Efeito para bloquear scroll quando modal estiver aberto
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'auto';
    }
    
    return () => {
      document.body.style.overflow = 'auto';
    };
  }, [isOpen]);
  
  useEffect(() => {
    // Retornar se o modal não estiver aberto
    if (!isOpen || !deviceId || !streamId) return;
    
    const fetchStreamUrl = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Requisição para obter a URL do stream
        const response = await axios.get(`/api/devices/${deviceId}/stream/${streamId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        setStreamUrl(response.data.url);
      } catch (err) {
        console.error('Erro ao obter URL do stream:', err);
        setError('Não foi possível obter o stream de vídeo.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchStreamUrl();
    
    // Configurar tecla ESC para fechar o modal
    const handleEscKey = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    
    document.addEventListener('keydown', handleEscKey);
    
    return () => {
      document.removeEventListener('keydown', handleEscKey);
      destroyHlsPlayer();
    };
  }, [isOpen, deviceId, streamId, token, onClose]);
  
  useEffect(() => {
    // Inicializar o player quando tivermos uma URL de stream
    if (streamUrl && videoRef.current) {
      initializePlayer(streamUrl);
    }
    
    return () => {
      destroyHlsPlayer();
    };
  }, [streamUrl]);
  
  const initializePlayer = (url) => {
    const video = videoRef.current;
    
    if (!video) return;
    
    // Verificar se o navegador suporta HLS nativamente
    if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = url;
      video.addEventListener('loadedmetadata', () => {
        video.play().catch(err => {
          console.error('Erro ao iniciar reprodução:', err);
        });
      });
    } 
    // Usar a biblioteca HLS.js para navegadores que não suportam HLS nativamente
    else if (Hls.isSupported()) {
      destroyHlsPlayer(); // Limpar qualquer instância anterior
      
      const hls = new Hls({
        startLevel: 0,
        capLevelToPlayerSize: true,
        maxBufferLength: 30,
        maxMaxBufferLength: 60
      });
      
      hlsRef.current = hls;
      hls.loadSource(url);
      hls.attachMedia(video);
      
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        video.play().catch(err => {
          console.error('Erro ao iniciar reprodução:', err);
        });
      });
      
      hls.on(Hls.Events.ERROR, (event, data) => {
        if (data.fatal) {
          switch(data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
              console.error('HLS fatal network error', data);
              hls.startLoad();
              break;
            case Hls.ErrorTypes.MEDIA_ERROR:
              console.error('HLS fatal media error', data);
              hls.recoverMediaError();
              break;
            default:
              destroyHlsPlayer();
              setError('Erro fatal na reprodução do vídeo.');
              break;
          }
        }
      });
    } else {
      setError('Seu navegador não suporta a reprodução deste stream.');
    }
  };
  
  const destroyHlsPlayer = () => {
    if (hlsRef.current) {
      hlsRef.current.destroy();
      hlsRef.current = null;
    }
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-80">
      <div className="relative w-full max-w-6xl mx-auto rounded-lg overflow-hidden">
        {/* Botão de fechar */}
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 z-10 bg-black bg-opacity-50 text-white rounded-full p-2 hover:bg-opacity-70"
          aria-label="Fechar"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
        
        {/* Título da câmera */}
        <div className="absolute top-0 left-0 right-0 bg-gradient-to-b from-black to-transparent text-white p-4 z-10">
          <h3 className="text-lg font-semibold">{cameraName}</h3>
        </div>
        
        {/* Área do vídeo */}
        <div className="relative bg-black aspect-video">
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="loader"></div>
            </div>
          )}
          
          {error && (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-red-400 p-4">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <p className="text-center">{error}</p>
            </div>
          )}
          
          <video 
            ref={videoRef}
            className="w-full h-full object-contain"
            autoPlay
            playsInline
            muted
            controls
          ></video>
        </div>
        
        {/* Controles do reprodutor */}
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-4 z-10">
          {/* Aqui podem ser adicionados controles adicionais no futuro */}
        </div>
      </div>
    </div>
  );
};

export default StreamModal; 