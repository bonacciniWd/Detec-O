import React, { useState, useEffect } from 'react';

/**
 * Menu de acessibilidade que fornece opções para melhorar
 * a usabilidade da aplicação para usuários com diferentes necessidades
 */
const AccessibilityMenu = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [settings, setSettings] = useState({
    fontSize: 'default',
    contrast: 'default',
    reduceMotion: false,
    focusHighlight: false,
    monochrome: false
  });

  // Carregar configurações salvas no localStorage
  useEffect(() => {
    const savedSettings = localStorage.getItem('accessibility_settings');
    if (savedSettings) {
      try {
        const parsedSettings = JSON.parse(savedSettings);
        setSettings(parsedSettings);
        applySettings(parsedSettings);
      } catch (e) {
        console.error('Erro ao carregar configurações de acessibilidade:', e);
      }
    }
  }, []);

  // Efeito para aplicar estilos CSS dinâmicos
  useEffect(() => {
    // Criar ou obter o elemento de estilo para acessibilidade
    let styleEl = document.getElementById('accessibility-styles');
    if (!styleEl) {
      styleEl = document.createElement('style');
      styleEl.id = 'accessibility-styles';
      document.head.appendChild(styleEl);
    }

    // Definir o conteúdo CSS com base nas configurações atuais
    const fontSizeMultiplier = settings.fontSize === 'small' ? '0.85' : 
                              settings.fontSize === 'large' ? '1.15' : 
                              settings.fontSize === 'x-large' ? '1.3' : '1';
    
    const reduceMotionValue = settings.reduceMotion ? '1' : '0';
    
    styleEl.textContent = `
      :root {
        --font-size-multiplier: ${fontSizeMultiplier};
        --reduce-motion: ${reduceMotionValue};
      }
      
      /* Aplicar multiplicador de tamanho de fonte */
      html {
        font-size: calc(16px * var(--font-size-multiplier));
      }
      
      /* Alto contraste */
      body.high-contrast {
        filter: contrast(1.4);
      }
      
      /* Cores invertidas */
      body.inverted-colors {
        filter: invert(1) hue-rotate(180deg);
      }
      
      /* Destaque de foco para teclado */
      body.focus-highlight *:focus {
        outline: 3px solid #4299e1 !important;
        outline-offset: 2px !important;
      }
      
      /* Modo monocromático */
      body.monochrome {
        filter: grayscale(1);
      }
      
      /* Reduzir animações */
      @media (prefers-reduced-motion: reduce), (--reduce-motion: 1) {
        *, ::before, ::after {
          animation-duration: 0.01ms !important;
          animation-iteration-count: 1 !important;
          transition-duration: 0.01ms !important;
          scroll-behavior: auto !important;
        }
      }
    `;

    // Limpar o elemento de estilo quando o componente for desmontado
    return () => {
      if (styleEl && styleEl.parentNode) {
        styleEl.parentNode.removeChild(styleEl);
      }
    };
  }, [settings]); // Executar novamente quando as configurações mudarem

  // Aplicar configurações ao documento HTML
  const applySettings = (newSettings) => {
    // Aplicar contraste
    document.body.classList.remove(
      'high-contrast', 
      'inverted-colors'
    );
    if (newSettings.contrast === 'high') {
      document.body.classList.add('high-contrast');
    } else if (newSettings.contrast === 'inverted') {
      document.body.classList.add('inverted-colors');
    }
    
    // Destaque de foco
    document.body.classList.toggle(
      'focus-highlight', 
      newSettings.focusHighlight
    );
    
    // Modo monocromático
    document.body.classList.toggle(
      'monochrome', 
      newSettings.monochrome
    );

    // Salvar configurações no localStorage
    localStorage.setItem('accessibility_settings', JSON.stringify(newSettings));
  };

  // Atualizar uma configuração específica
  const updateSetting = (key, value) => {
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);
    applySettings(newSettings);
  };

  // Resetar todas as configurações
  const resetSettings = () => {
    const defaultSettings = {
      fontSize: 'default',
      contrast: 'default',
      reduceMotion: false,
      focusHighlight: false,
      monochrome: false
    };
    setSettings(defaultSettings);
    applySettings(defaultSettings);
  };

  // Alternar visibilidade do menu
  const toggleMenu = () => {
    setIsOpen(!isOpen);
  };

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {/* Botão flutuante para abrir o menu */}
      <button
        onClick={toggleMenu}
        className="flex items-center justify-center w-12 h-12 p-3 bg-blue-600 text-white rounded-full shadow-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        aria-label="Configurações de acessibilidade"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      </button>

      {/* Menu de acessibilidade */}
      {isOpen && (
        <div className="absolute bottom-16 right-0 w-72 bg-gray-800 border border-gray-700 rounded-lg shadow-xl p-4">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium text-white">Acessibilidade</h3>
            <button
              onClick={toggleMenu}
              className="text-gray-400 hover:text-gray-300"
              aria-label="Fechar menu de acessibilidade"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="space-y-4">
            {/* Tamanho da fonte */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Tamanho da Fonte
              </label>
              <div className="grid grid-cols-4 gap-2">
                {['small', 'default', 'large', 'x-large'].map((size) => (
                  <button
                    key={size}
                    onClick={() => updateSetting('fontSize', size)}
                    className={`px-2 py-1 text-sm rounded ${
                      settings.fontSize === size
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    {size === 'small' && 'A-'}
                    {size === 'default' && 'A'}
                    {size === 'large' && 'A+'}
                    {size === 'x-large' && 'A++'}
                  </button>
                ))}
              </div>
            </div>

            {/* Contraste */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Contraste
              </label>
              <div className="grid grid-cols-3 gap-2">
                {['default', 'high', 'inverted'].map((contrast) => (
                  <button
                    key={contrast}
                    onClick={() => updateSetting('contrast', contrast)}
                    className={`px-2 py-1 text-sm rounded ${
                      settings.contrast === contrast
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    {contrast === 'default' && 'Normal'}
                    {contrast === 'high' && 'Alto'}
                    {contrast === 'inverted' && 'Invertido'}
                  </button>
                ))}
              </div>
            </div>

            {/* Opções adicionais de acessibilidade */}
            <div className="space-y-2">
              <div className="flex items-center">
                <input
                  id="reduce-motion"
                  type="checkbox"
                  checked={settings.reduceMotion}
                  onChange={(e) => updateSetting('reduceMotion', e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-600 rounded"
                />
                <label htmlFor="reduce-motion" className="ml-2 block text-sm text-gray-300">
                  Reduzir animações
                </label>
              </div>
              
              <div className="flex items-center">
                <input
                  id="focus-highlight"
                  type="checkbox"
                  checked={settings.focusHighlight}
                  onChange={(e) => updateSetting('focusHighlight', e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-600 rounded"
                />
                <label htmlFor="focus-highlight" className="ml-2 block text-sm text-gray-300">
                  Destacar foco do teclado
                </label>
              </div>
              
              <div className="flex items-center">
                <input
                  id="monochrome"
                  type="checkbox"
                  checked={settings.monochrome}
                  onChange={(e) => updateSetting('monochrome', e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-600 rounded"
                />
                <label htmlFor="monochrome" className="ml-2 block text-sm text-gray-300">
                  Modo monocromático
                </label>
              </div>
            </div>

            {/* Botão para resetar configurações */}
            <button
              onClick={resetSettings}
              className="w-full mt-2 px-3 py-2 text-sm text-white bg-gray-700 hover:bg-gray-600 rounded"
            >
              Resetar Configurações
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AccessibilityMenu; 