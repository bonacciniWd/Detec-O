// Adicionar classes para controlar o overflow e dimensões
<div className="zone-editor-modal w-full max-w-full overflow-x-hidden">
  {/* Conteúdo do modal de zonas */}
  <div className="zone-editor-container relative w-full max-w-full">
    {/* Conteúdo existente */}
    
    {/* Garanta que o canvas tenha um tamanho máximo */}
    <canvas 
      ref={canvasRef}
      className="max-w-full object-contain"
      style={{ 
        maxWidth: '100%',
        height: 'auto',
        touchAction: 'none'  // Melhora a experiência em dispositivos touch
      }}
      // ... outras props
    />
    
    {/* Resto do código existente */}
  </div>
</div> 