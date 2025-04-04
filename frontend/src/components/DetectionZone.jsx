import React, { useState, useRef, useEffect } from 'react';
import PropTypes from 'prop-types';

/**
 * Componente para definir zonas de detecção em uma câmera
 * Permite ao usuário desenhar polígonos para delimitar áreas de interesse
 */
const DetectionZone = ({ imageUrl, initialZones, onChange, readOnly }) => {
  // Estado para armazenar a imagem carregada
  const [image, setImage] = useState(null);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);
  
  // Estado para armazenar as dimensões do contêiner
  const [containerSize, setContainerSize] = useState({ width: 0, height: 0 });
  
  // Estado para armazenar as zonas (polígonos)
  const [zones, setZones] = useState(initialZones || []);
  const [activeZoneIndex, setActiveZoneIndex] = useState(0);
  
  // Estado para rastrear o ponto selecionado (para mover)
  const [selectedPoint, setSelectedPoint] = useState(null);
  const [dragStartPos, setDragStartPos] = useState({ x: 0, y: 0 });
  
  // Estado para rastrear se o usuário está desenhando
  const [isDrawing, setIsDrawing] = useState(false);
  
  // Referências para o contêiner e o canvas
  const containerRef = useRef(null);
  const canvasRef = useRef(null);
  
  // Cores para a interface
  const colors = {
    inactive: 'rgba(100, 100, 255, 0.5)',
    active: 'rgba(255, 100, 100, 0.7)',
    point: 'rgba(255, 255, 255, 0.9)',
    selectedPoint: 'rgba(255, 255, 0, 1)',
    newLine: 'rgba(0, 255, 0, 0.7)'
  };
  
  // Constantes para o tamanho dos pontos
  const POINT_RADIUS = 6;
  const HIT_RADIUS = 10;
  
  // Carregar imagem
  useEffect(() => {
    if (!imageUrl) return;
    
    const img = new Image();
    img.onload = () => {
      setImage(img);
      setImageLoaded(true);
      setImageError(false);
    };
    img.onerror = () => {
      setImageError(true);
      setImageLoaded(false);
    };
    img.src = imageUrl;
  }, [imageUrl]);
  
  // Atualizar dimensões do contêiner
  useEffect(() => {
    const updateContainerSize = () => {
      if (containerRef.current) {
        const { offsetWidth, offsetHeight } = containerRef.current;
        setContainerSize({ width: offsetWidth, height: offsetHeight });
      }
    };
    
    updateContainerSize();
    window.addEventListener('resize', updateContainerSize);
    
    return () => {
      window.removeEventListener('resize', updateContainerSize);
    };
  }, []);
  
  // Efeito para notificar o componente pai sobre alterações nas zonas
  useEffect(() => {
    if (onChange && zones !== initialZones) {
      onChange(zones);
    }
  }, [zones, initialZones, onChange]);
  
  // Desenhar no canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !imageLoaded) return;
    
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Definir dimensões do canvas baseado no contêiner
    canvas.width = containerSize.width;
    canvas.height = containerSize.height;
    
    // Desenhar a imagem como fundo (dimensionada para caber no canvas)
    if (image) {
      const aspectRatio = image.width / image.height;
      let drawWidth, drawHeight;
      
      if (canvas.width / canvas.height > aspectRatio) {
        // Contêiner é mais largo que a imagem
        drawHeight = canvas.height;
        drawWidth = drawHeight * aspectRatio;
      } else {
        // Contêiner é mais alto que a imagem
        drawWidth = canvas.width;
        drawHeight = drawWidth / aspectRatio;
      }
      
      // Centralizar imagem
      const x = (canvas.width - drawWidth) / 2;
      const y = (canvas.height - drawHeight) / 2;
      
      ctx.drawImage(image, x, y, drawWidth, drawHeight);
    }
    
    // Desenhar as zonas existentes
    zones.forEach((zone, index) => {
      if (zone.points.length === 0) return;
      
      const isActive = index === activeZoneIndex;
      ctx.fillStyle = isActive ? colors.active : colors.inactive;
      ctx.strokeStyle = isActive ? colors.active : colors.inactive;
      ctx.lineWidth = 2;
      
      // Desenhar o polígono
      ctx.beginPath();
      ctx.moveTo(zone.points[0].x, zone.points[0].y);
      
      for (let i = 1; i < zone.points.length; i++) {
        ctx.lineTo(zone.points[i].x, zone.points[i].y);
      }
      
      // Fechar o polígono se tiver 3+ pontos
      if (zone.points.length >= 3) {
        ctx.closePath();
        ctx.fill();
      }
      
      ctx.stroke();
      
      // Desenhar os pontos de controle
      zone.points.forEach((point, pointIndex) => {
        ctx.beginPath();
        
        // Destacar ponto selecionado
        if (selectedPoint && selectedPoint.zoneIndex === index && selectedPoint.pointIndex === pointIndex) {
          ctx.fillStyle = colors.selectedPoint;
        } else {
          ctx.fillStyle = colors.point;
        }
        
        ctx.arc(point.x, point.y, POINT_RADIUS, 0, Math.PI * 2);
        ctx.fill();
      });
    });
    
    // Desenhar a linha de preview durante a criação de novo polígono
    if (isDrawing && zones[activeZoneIndex]?.points.length > 0) {
      const points = zones[activeZoneIndex].points;
      const lastPoint = points[points.length - 1];
      
      // Obter posição do mouse
      const canvas = canvasRef.current;
      const rect = canvas.getBoundingClientRect();
      const mouseX = Math.max(0, Math.min(canvas.width, rect.x));
      const mouseY = Math.max(0, Math.min(canvas.height, rect.y));
      
      ctx.beginPath();
      ctx.strokeStyle = colors.newLine;
      ctx.lineWidth = 2;
      ctx.moveTo(lastPoint.x, lastPoint.y);
      ctx.lineTo(mouseX, mouseY);
      ctx.stroke();
    }
  }, [image, imageLoaded, containerSize, zones, activeZoneIndex, selectedPoint, isDrawing, colors]);
  
  // Manipuladores de eventos de mouse
  const handleMouseDown = (e) => {
    if (readOnly) return;
    
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // Verificar se clicou em algum ponto existente
    for (let zIndex = 0; zIndex < zones.length; zIndex++) {
      const zone = zones[zIndex];
      
      for (let pIndex = 0; pIndex < zone.points.length; pIndex++) {
        const point = zone.points[pIndex];
        const distance = Math.sqrt(Math.pow(point.x - x, 2) + Math.pow(point.y - y, 2));
        
        if (distance <= HIT_RADIUS) {
          // Selecionar este ponto para arrastar
          setActiveZoneIndex(zIndex);
          setSelectedPoint({ zoneIndex: zIndex, pointIndex: pIndex });
          setDragStartPos({ x, y });
          return;
        }
      }
    }
    
    // Se não clicou em um ponto existente e está no modo de desenho, adicionar um novo ponto
    if (isDrawing) {
      // Adicionar ponto à zona ativa
      setZones(prev => {
        const newZones = [...prev];
        newZones[activeZoneIndex].points.push({ x, y });
        return newZones;
      });
    } else {
      // Começar uma nova zona se não estiver desenhando
      setIsDrawing(true);
      setZones(prev => [
        ...prev,
        { id: Date.now().toString(), name: `Zona ${prev.length + 1}`, points: [{ x, y }] }
      ]);
      setActiveZoneIndex(zones.length);
    }
  };
  
  const handleMouseMove = (e) => {
    if (readOnly) return;
    
    // Se tiver um ponto selecionado, movê-lo
    if (selectedPoint) {
      const canvas = canvasRef.current;
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      setZones(prev => {
        const newZones = [...prev];
        const { zoneIndex, pointIndex } = selectedPoint;
        
        if (newZones[zoneIndex] && newZones[zoneIndex].points[pointIndex]) {
          newZones[zoneIndex].points[pointIndex] = { x, y };
        }
        
        return newZones;
      });
    }
  };
  
  const handleMouseUp = () => {
    if (readOnly) return;
    
    if (selectedPoint) {
      setSelectedPoint(null);
    }
  };
  
  const handleKeyDown = (e) => {
    if (readOnly) return;
    
    // Tecla Delete ou Backspace para remover pontos selecionados
    if ((e.key === 'Delete' || e.key === 'Backspace') && selectedPoint) {
      const { zoneIndex, pointIndex } = selectedPoint;
      
      setZones(prev => {
        const newZones = [...prev];
        
        // Remover o ponto
        if (newZones[zoneIndex]) {
          newZones[zoneIndex].points.splice(pointIndex, 1);
          
          // Se ficou sem pontos, remover a zona
          if (newZones[zoneIndex].points.length === 0) {
            newZones.splice(zoneIndex, 1);
            setActiveZoneIndex(Math.max(0, newZones.length - 1));
          }
        }
        
        return newZones;
      });
      
      setSelectedPoint(null);
    }
    
    // Tecla Escape para cancelar o desenho atual
    if (e.key === 'Escape') {
      setIsDrawing(false);
      setSelectedPoint(null);
    }
  };
  
  const finishDrawing = () => {
    if (zones[activeZoneIndex]?.points.length < 3) {
      // Não finalizar se tiver menos de 3 pontos
      return;
    }
    
    setIsDrawing(false);
  };
  
  const addNewZone = () => {
    setIsDrawing(true);
    setZones(prev => [
      ...prev,
      { id: Date.now().toString(), name: `Zona ${prev.length + 1}`, points: [] }
    ]);
    setActiveZoneIndex(zones.length);
  };
  
  const deleteZone = (index) => {
    setZones(prev => {
      const newZones = [...prev];
      newZones.splice(index, 1);
      setActiveZoneIndex(Math.max(0, index - 1));
      return newZones;
    });
  };
  
  // Renderizar uma mensagem se a imagem não estiver disponível
  if (imageError) {
    return (
      <div className="bg-gray-800 p-4 rounded-md text-center">
        <p className="text-red-400">Erro ao carregar imagem da câmera</p>
      </div>
    );
  }
  
  // Se a imagem estiver carregando, mostrar mensagem
  if (!imageLoaded && !imageError) {
    return (
      <div className="bg-gray-800 p-4 rounded-md text-center animate-pulse">
        <p className="text-gray-400">Carregando imagem da câmera...</p>
      </div>
    );
  }
  
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-medium text-gray-300">Definir Zonas de Detecção</h3>
        {!readOnly && (
          <div className="flex space-x-2">
            {isDrawing ? (
              <button
                type="button"
                onClick={finishDrawing}
                className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                disabled={zones[activeZoneIndex]?.points.length < 3}
              >
                Finalizar Zona
              </button>
            ) : (
              <button
                type="button"
                onClick={addNewZone}
                className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
              >
                Nova Zona
              </button>
            )}
          </div>
        )}
      </div>
      
      <div 
        ref={containerRef}
        className="relative bg-gray-900 rounded-md overflow-hidden"
        style={{ height: '360px' }}
        tabIndex={0}
        onKeyDown={handleKeyDown}
      >
        <canvas
          ref={canvasRef}
          className="absolute top-0 left-0 w-full h-full cursor-crosshair"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        />
      </div>
      
      {/* Lista de zonas criadas */}
      {zones.length > 0 && (
        <div className="mt-4">
          <h4 className="text-sm font-medium text-gray-300 mb-2">Zonas Definidas</h4>
          <div className="space-y-2">
            {zones.map((zone, index) => (
              <div 
                key={zone.id} 
                className={`flex items-center justify-between p-2 rounded ${
                  index === activeZoneIndex ? 'bg-blue-900' : 'bg-gray-700'
                }`}
                onClick={() => setActiveZoneIndex(index)}
              >
                <span className="text-gray-200 text-sm">{zone.name}</span>
                {!readOnly && (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteZone(index);
                    }}
                    className="text-red-400 hover:text-red-300"
                  >
                    Remover
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
      
      <div className="mt-2 text-sm text-gray-400">
        <p>Clique para adicionar pontos. Arraste para mover.</p>
        <p>Pressione Delete para remover o ponto selecionado.</p>
      </div>
    </div>
  );
};

DetectionZone.propTypes = {
  imageUrl: PropTypes.string,
  initialZones: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
      points: PropTypes.arrayOf(
        PropTypes.shape({
          x: PropTypes.number.isRequired,
          y: PropTypes.number.isRequired
        })
      ).isRequired
    })
  ),
  onChange: PropTypes.func,
  readOnly: PropTypes.bool
};

DetectionZone.defaultProps = {
  initialZones: [],
  readOnly: false
};

export default DetectionZone; 