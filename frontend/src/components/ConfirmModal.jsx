import React, { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';

function ConfirmModal({ 
  isOpen,         // Controla se o modal está aberto
  onClose,        // Função para fechar o modal (chamada ao cancelar ou clicar fora)
  onConfirm,      // Função a ser chamada ao confirmar
  title,          // Título do modal
  message,        // Mensagem/pergunta de confirmação
  confirmText = 'Confirmar',
  cancelText = 'Cancelar',
  confirmButtonColor = 'red', // Cor do botão de confirmação (blue, red, green, gray)
  theme = 'light' // Novo prop para tema: 'light' ou 'dark'
}) {

  // Definindo classes base
  const baseButtonClass = `inline-flex justify-center rounded-md border px-4 py-2 text-sm font-medium shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2`;

  // Classes de botão específicas do tema
  const themeClasses = {
    light: {
      panel: 'bg-white',
      title: 'text-gray-900',
      message: 'text-gray-500',
      overlay: 'bg-black bg-opacity-25',
      confirm: {
        red: `bg-red-600 text-white border-transparent hover:bg-red-700 focus:ring-red-500`,
        blue: `bg-blue-600 text-white border-transparent hover:bg-blue-700 focus:ring-blue-500`,
        green: `bg-green-600 text-white border-transparent hover:bg-green-700 focus:ring-green-500`,
        gray: `bg-gray-600 text-white border-transparent hover:bg-gray-700 focus:ring-gray-500`
      },
      cancel: `bg-white text-gray-700 border-gray-300 hover:bg-gray-50 focus:ring-blue-500`,
    },
    dark: {
      panel: 'bg-gray-800',
      title: 'text-gray-100',
      message: 'text-gray-400',
      overlay: 'bg-gray-900 bg-opacity-75',
      confirm: {
        red: `bg-red-700 text-white border-transparent hover:bg-red-800 focus:ring-red-500 focus:ring-offset-gray-800`,
        blue: `bg-blue-600 text-white border-transparent hover:bg-blue-700 focus:ring-blue-500 focus:ring-offset-gray-800`,
        green: `bg-green-600 text-white border-transparent hover:bg-green-700 focus:ring-green-500 focus:ring-offset-gray-800`,
        gray: `bg-gray-600 text-white border-transparent hover:bg-gray-700 focus:ring-gray-500 focus:ring-offset-gray-800`
      },
      cancel: `bg-gray-700 text-gray-200 border-gray-600 hover:bg-gray-600 focus:ring-blue-500 focus:ring-offset-gray-800`,
    }
  };

  const currentTheme = themeClasses[theme] || themeClasses.light;
  const confirmColor = currentTheme.confirm[confirmButtonColor] || currentTheme.confirm.blue;
  const cancelColor = currentTheme.cancel;

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}> {/* Aumentado z-index */} 
        {/* Overlay */}
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className={`fixed inset-0 ${currentTheme.overlay}`} />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            {/* Painel do Modal */}
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className={`w-full max-w-md transform overflow-hidden rounded-lg ${currentTheme.panel} p-6 text-left align-middle shadow-xl transition-all`}>
                <Dialog.Title
                  as="h3"
                  className={`text-lg font-medium leading-6 ${currentTheme.title}`}
                >
                  {title}
                </Dialog.Title>
                <div className="mt-2">
                  <p className={`text-sm ${currentTheme.message}`}>
                    {message}
                  </p>
                </div>

                {/* Botões */}
                <div className="mt-6 flex justify-end space-x-3">
                  <button
                    type="button"
                    className={`${baseButtonClass} ${cancelColor}`}
                    onClick={onClose}
                  >
                    {cancelText}
                  </button>
                  <button
                    type="button"
                    className={`${baseButtonClass} ${confirmColor}`}
                    onClick={() => {
                        onConfirm();
                        onClose(); // Fecha o modal após confirmar
                    }}
                  >
                    {confirmText}
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}

export default ConfirmModal; 