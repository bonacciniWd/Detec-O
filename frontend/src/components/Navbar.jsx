import React, { useState } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { FaBars, FaBell, FaUser, FaSignOutAlt } from 'react-icons/fa';
import { useAuth } from '../context/AuthContext';

const Navbar = ({ toggleSidebar }) => {
  const location = useLocation();
  const { logout, user } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  // Título da página baseado na rota atual
  const getPageTitle = () => {
    const path = location.pathname;
    
    if (path === '/') return 'Dashboard';
    if (path === '/dashboard') return 'Dashboard';
    if (path === '/cameras' || path === '/camera-dashboard') return 'Câmeras';
    if (path.startsWith('/camera/')) return 'Configuração de Câmera';
    if (path === '/events') return 'Eventos';
    if (path.startsWith('/events/')) return 'Detalhes do Evento';
    if (path === '/settings') return 'Configurações';
    if (path === '/people') return 'Gerenciamento de Pessoas';
    
    return 'Detec-O';
  };

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
      <div className="px-4 py-3 md:px-6 flex justify-between items-center">
        <div className="flex items-center">
          {/* Menu toggle button - visível apenas em mobile */}
          <button 
            onClick={toggleSidebar} 
            className="text-gray-500 mr-4 focus:outline-none md:hidden"
            aria-label="Toggle menu"
          >
            <FaBars className="w-6 h-6" />
          </button>
          
          {/* Título da página */}
          <h1 className="text-xl font-semibold text-gray-800">{getPageTitle()}</h1>
        </div>
        
        <div className="flex items-center space-x-4">
          {/* Notificações */}
          <div className="relative">
            <button 
              onClick={() => setNotificationsOpen(!notificationsOpen)}
              className="text-gray-500 hover:text-gray-700 focus:outline-none relative"
              aria-label="Notifications"
            >
              <FaBell className="w-5 h-5" />
              <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-4 w-4 flex items-center justify-center">
                3
              </span>
            </button>
            
            {/* Dropdown de notificações */}
            {notificationsOpen && (
              <div className="absolute right-0 mt-2 w-80 bg-white rounded-md shadow-lg py-1 z-20">
                <div className="px-4 py-2 border-b border-gray-200">
                  <h3 className="text-sm font-semibold">Notificações</h3>
                </div>
                
                <div className="max-h-60 overflow-y-auto">
                  <div className="px-4 py-2 border-b border-gray-100 hover:bg-gray-50">
                    <p className="text-sm font-medium">Pessoa detectada</p>
                    <p className="text-xs text-gray-500">Câmera frontal - 5 min atrás</p>
                  </div>
                  <div className="px-4 py-2 border-b border-gray-100 hover:bg-gray-50">
                    <p className="text-sm font-medium">Veículo detectado</p>
                    <p className="text-xs text-gray-500">Câmera estacionamento - 15 min atrás</p>
                  </div>
                  <div className="px-4 py-2 hover:bg-gray-50">
                    <p className="text-sm font-medium">Movimento detectado</p>
                    <p className="text-xs text-gray-500">Câmera lateral - 30 min atrás</p>
                  </div>
                </div>
                
                <div className="px-4 py-2 border-t border-gray-200">
                  <Link 
                    to="/events"
                    className="text-sm text-blue-600 hover:text-blue-800"
                    onClick={() => setNotificationsOpen(false)}
                  >
                    Ver todos os eventos
                  </Link>
                </div>
              </div>
            )}
          </div>
          
          {/* Menu do usuário */}
          <div className="relative">
            <button 
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center focus:outline-none"
              aria-label="User menu"
            >
              <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white">
                {user?.name?.charAt(0) || <FaUser />}
              </div>
              <span className="ml-2 text-sm font-medium text-gray-700 hidden md:block">
                {user?.name || 'Usuário'}
              </span>
            </button>
            
            {/* Dropdown do usuário */}
            {dropdownOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-20">
                <div className="px-4 py-2 border-b border-gray-200">
                  <p className="text-sm font-medium text-gray-800">{user?.name || 'Usuário'}</p>
                  <p className="text-xs text-gray-500">{user?.email || ''}</p>
                </div>
                
                <Link 
                  to="/settings" 
                  className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  onClick={() => setDropdownOpen(false)}
                >
                  Configurações
                </Link>
                
                <button 
                  onClick={() => {
                    logout();
                    setDropdownOpen(false);
                  }}
                  className="flex items-center w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100"
                >
                  <FaSignOutAlt className="mr-2" />
                  Sair
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Navbar; 