import React, { useState, useRef } from 'react';
import eventService from '../services/eventService';

/**
 * Componente avançado para visualização de imagens de eventos
 * com suporte a zoom, marcação de regiões e acessibilidade.
 */
const EventImage = ({ 
  eventId, 
  eventData, 
  showBoundingBoxes = true, 
  className = "", 
  altText,
  width = "full",
  height = "auto"
}) => {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [isZoomed, setIsZoomed] = useState(false);
  const imageRef = useRef(null);
  
  // Construir URL da imagem
  const imageUrl = `${eventService.getApiBaseUrl()}/api/v1/events/${eventId}/image`;
  
  // Classe CSS para a largura da imagem
  const widthClass = {
    'full': 'w-full',
    'auto': 'w-auto',
    'screen': 'w-screen'
  }[width] || 'w-full';
  
  // Classe CSS para a altura da imagem
  const heightClass = {
    'full': 'h-full',
    'auto': 'h-auto',
    'screen': 'h-screen'
  }[height] || 'h-auto';
  
  // Alternativa para texto da imagem
  const imageAltText = altText || 
    `Imagem do evento ${eventData?.event_type || 'de detecção'} em ${eventData?.camera_name || 'câmera'}`;
  
  // Fallback image (SVG em base64) para quando a imagem não carregar
  const fallbackImageSrc = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjE1MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjE1MCIgZmlsbD0iIzNiNDI1MiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBkb21pbmFudC1iYXNlbGluZT0ibWlkZGxlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LWZhbWlseT0ibW9ub3NwYWNlIiBmb250LXNpemU9IjE2cHgiIGZpbGw9IiM5ZmEzYjEiPkltYWdlbSBuYW8gZGlzcG9uaXZlbDwvdGV4dD48L3N2Zz4=';
  
  const handleImageLoad = () => {
    setIsLoading(false);
    setHasError(false);
  };
  
  const handleImageError = () => {
    setIsLoading(false);
    setHasError(true);
  };
  
  const toggleZoom = () => {
    setIsZoomed(!isZoomed);
  };
  
  // Renderizar bounding boxes se disponíveis nos dados do evento
  const renderBoundingBoxes = () => {
    if (!showBoundingBoxes || !eventData?.detections || imageRef.current === null) return null;
    
    const imgWidth = imageRef.current.naturalWidth;
    const imgHeight = imageRef.current.naturalHeight;
    const displayWidth = imageRef.current.clientWidth;
    const displayHeight = imageRef.current.clientHeight;
    
    return eventData.detections.map((detection, index) => {
      // Cálculo das coordenadas proporcionais para as bounding boxes
      const x = (detection.bbox.x * displayWidth) / imgWidth;
      const y = (detection.bbox.y * displayHeight) / imgHeight;
      const width = (detection.bbox.width * displayWidth) / imgWidth;
      const height = (detection.bbox.height * displayHeight) / imgHeight;
      
      return (
        <div
          key={`detection-${index}`}
          className="absolute border-2 border-red-500"
          style={{
            left: `${x}px`,
            top: `${y}px`,
            width: `${width}px`,
            height: `${height}px`,
          }}
        >
          <div className="absolute top-0 left-0 bg-red-900 text-white text-xs px-1 opacity-80">
            {detection.label} {detection.confidence ? `${Math.round(detection.confidence * 100)}%` : ''}
          </div>
        </div>
      );
    });
  };
  
  // Classe para quando a imagem está com zoom
  const zoomedClassName = isZoomed ? 
    "fixed top-0 left-0 w-screen h-screen flex items-center justify-center bg-black bg-opacity-90 z-50 cursor-zoom-out p-4" : 
    "relative cursor-zoom-in";
  
  // Construir o JSX completo
  return (
    <div className={`${zoomedClassName} ${className}`} onClick={toggleZoom}>
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-800 bg-opacity-50">
          <div className="animate-pulse text-blue-400">Carregando...</div>
        </div>
      )}
      
      <img
        ref={imageRef}
        src={imageUrl}
        alt={imageAltText}
        className={`${widthClass} ${heightClass} rounded ${hasError ? 'hidden' : 'block'}`}
        onLoad={handleImageLoad}
        onError={handleImageError}
      />
      
      {hasError && (
        <img
          src={fallbackImageSrc}
          alt="Imagem não disponível"
          className={`${widthClass} ${heightClass} rounded`}
        />
      )}
      
      {/* Container para as bounding boxes */}
      {!isLoading && !hasError && renderBoundingBoxes()}
      
      {/* Informações sobre a detecção sobrepostas na imagem */}
      {!isLoading && !hasError && eventData && (
        <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-70 text-white text-xs p-2">
          <div>{eventData.event_type || 'Detecção'}</div>
          <div>Data: {new Date(eventData.timestamp).toLocaleString('pt-BR')}</div>
          <div>Câmera: {eventData.camera_name || 'N/A'}</div>
          {eventData.confidence && (
            <div>Confiança: {Math.round(eventData.confidence * 100)}%</div>
          )}
        </div>
      )}
      
      {/* Botão de zoom apenas visível no modo normal */}
      {!isZoomed && !isLoading && !hasError && (
        <button
          className="absolute top-2 right-2 bg-gray-800 bg-opacity-70 rounded-full p-1 text-white hover:bg-opacity-100"
          onClick={(e) => {
            e.stopPropagation();
            toggleZoom();
          }}
          aria-label="Ampliar imagem"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
          </svg>
        </button>
      )}
      
      {/* Botão para fechar o zoom visível apenas no modo ampliado */}
      {isZoomed && (
        <button
          className="absolute top-4 right-4 bg-gray-800 rounded-full p-2 text-white hover:bg-gray-700"
          onClick={(e) => {
            e.stopPropagation();
            toggleZoom();
          }}
          aria-label="Fechar zoom"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </div>
  );
};

export default EventImage; 