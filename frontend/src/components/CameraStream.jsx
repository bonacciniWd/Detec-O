import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import PropTypes from 'prop-types';
import { FaCompress, FaCog, FaVideo, FaVideoSlash, FaVolumeMute, FaVolumeUp } from 'react-icons/fa';
import axios from 'axios';

/**
 * Componente para exibir um stream de vídeo em tempo real.
 * 
 * Este componente utiliza HLS.js para reproduzir streams HLS ou
 * o player nativo para streams RTSP.
 */
const CameraStream = ({
  deviceId,
  streamId,
  cameraName,
  onClose,
  className = '',
  showControls = true,
  autoPlay = true
}) => {
  const { token } = useAuth();
  const [streamUrl, setStreamUrl] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isMuted, setIsMuted] = useState(true);
  const [isPaused, setIsPaused] = useState(false);
  const videoRef = useRef(null);
  const hlsRef = useRef(null);

  // Buscar URL do stream
  useEffect(() => {
    const fetchStreamUrl = async () => {
      try {
        setLoading(true);
        
        const response = await axios.get(`/api/devices/${deviceId}/streams`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        // Encontrar o stream pelo ID
        const streamInfo = response.data.find(stream => stream.id === streamId);
        
        if (!streamInfo) {
          throw new Error('Stream não encontrado');
        }
        
        setStreamUrl(streamInfo.url);
        setLoading(false);
      } catch (err) {
        console.error('Erro ao obter URL do stream:', err);
        setError(err.message || 'Erro ao carregar stream');
        setLoading(false);
      }
    };
    
    fetchStreamUrl();
    
    // Limpeza ao desmontar
    return () => {
      if (hlsRef.current) {
        hlsRef.current.destroy();
      }
    };
  }, [deviceId, streamId, token]);

  // Inicializar player quando a URL do stream estiver disponível
  useEffect(() => {
    if (!streamUrl || !videoRef.current) return;
    
    // Verificar se é um stream HLS
    if (streamUrl.includes('.m3u8')) {
      // Usar HLS.js para streams HLS
      const initHls = async () => {
        try {
          // Importar HLS.js dinamicamente
          const HLS = await import('hls.js');
          const Hls = HLS.default;
          
          if (Hls.isSupported()) {
            const hls = new Hls({
              maxBufferLength: 5,
              maxMaxBufferLength: 10,
              maxBufferSize: 10 * 1000 * 1000, // 10 MB
              backBufferLength: 0
            });
            
            hls.loadSource(streamUrl);
            hls.attachMedia(videoRef.current);
            
            hls.on(Hls.Events.MEDIA_ATTACHED, () => {
              if (autoPlay) {
                videoRef.current.play().catch(e => {
                  console.warn('Reprodução automática bloqueada:', e);
                });
              }
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
                    console.error('HLS fatal error:', data);
                    setError('Erro ao reproduzir stream');
                    break;
                }
              }
            });
            
            hlsRef.current = hls;
          } else if (videoRef.current.canPlayType('application/vnd.apple.mpegurl')) {
            // Fallback para Safari
            videoRef.current.src = streamUrl;
            if (autoPlay) {
              videoRef.current.play().catch(e => {
                console.warn('Reprodução automática bloqueada:', e);
              });
            }
          } else {
            setError('Seu navegador não suporta reprodução HLS');
          }
        } catch (err) {
          console.error('Erro ao inicializar HLS:', err);
          setError('Erro ao inicializar player de vídeo');
        }
      };
      
      initHls();
    } else if (streamUrl.includes('rtsp://')) {
      // Para RTSP, usamos um proxy ou WebRTC
      // Por enquanto, apenas mostramos um erro informativo
      setError('Streams RTSP requerem configuração adicional no servidor');
    } else {
      // Para outros tipos de stream (HTTP, etc.)
      videoRef.current.src = streamUrl;
      if (autoPlay) {
        videoRef.current.play().catch(e => {
          console.warn('Reprodução automática bloqueada:', e);
        });
      }
    }
  }, [streamUrl, autoPlay]);

  // Controle de pausa/play
  const togglePlay = () => {
    if (!videoRef.current) return;
    
    if (videoRef.current.paused) {
      videoRef.current.play();
      setIsPaused(false);
    } else {
      videoRef.current.pause();
      setIsPaused(true);
    }
  };

  // Controle de mudo
  const toggleMute = () => {
    if (!videoRef.current) return;
    
    videoRef.current.muted = !videoRef.current.muted;
    setIsMuted(videoRef.current.muted);
  };

  return (
    <div className={`camera-stream relative ${className}`}>
      <div className="aspect-video bg-black relative">
        {/* Vídeo */}
        <video
          ref={videoRef}
          className="w-full h-full"
          autoPlay={autoPlay}
          muted={isMuted}
          playsInline
          controls={false}
        />
        
        {/* Estado de carregamento */}
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-70">
            <div className="loader"></div>
          </div>
        )}
        
        {/* Estado de erro */}
        {error && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-black bg-opacity-70 text-red-500 p-4">
            <FaVideoSlash size={32} className="mb-3" />
            <p className="text-center text-sm text-white">{error}</p>
          </div>
        )}
        
        {/* Controles */}
        {showControls && (
          <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-60 text-white p-3 flex justify-between items-center">
            <div className="text-sm">
              <span>{cameraName || 'Stream de câmera'}</span>
            </div>
            <div className="flex gap-3">
              <button 
                onClick={togglePlay} 
                className="p-1 rounded hover:bg-gray-700"
                title={isPaused ? 'Reproduzir' : 'Pausar'}
              >
                {isPaused ? <FaVideo size={18} /> : <FaVideoSlash size={18} />}
              </button>
              <button
                onClick={toggleMute}
                className="p-1 rounded hover:bg-gray-700"
                title={isMuted ? 'Ativar áudio' : 'Desativar áudio'}
              >
                {isMuted ? <FaVolumeMute size={18} /> : <FaVolumeUp size={18} />}
              </button>
              <button
                onClick={() => {/* Configurações futuras */}}
                className="p-1 rounded hover:bg-gray-700"
                title="Configurações"
              >
                <FaCog size={18} />
              </button>
              <button
                onClick={onClose}
                className="p-1 rounded hover:bg-gray-700"
                title="Fechar"
              >
                <FaCompress size={18} />
              </button>
            </div>
          </div>
        )}
      </div>
      
      {/* Informações adicionais do stream */}
      <div className="mt-2 text-xs text-gray-600">
        <p>A visualização em tempo real consome mais banda e recursos do sistema.</p>
      </div>
    </div>
  );
};

CameraStream.propTypes = {
  deviceId: PropTypes.string.isRequired,
  streamId: PropTypes.string.isRequired,
  cameraName: PropTypes.string,
  onClose: PropTypes.func,
  className: PropTypes.string,
  showControls: PropTypes.bool,
  autoPlay: PropTypes.bool
};

export default CameraStream; 