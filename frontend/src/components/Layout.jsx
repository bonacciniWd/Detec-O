import React, { useState } from 'react';
import { Link } from 'react-router-dom'; 
import { useAuth } from '../context/AuthContext';

function Layout({ children }) { // Aceitar children como prop
  const { isAuthenticated, user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Barra de Navegação */}
      <nav className="bg-gray-800 shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              {/* Logo/Brand */}
              <div className="flex-shrink-0 flex items-center">
                 <Link to="/" className="font-bold text-xl">
                    <span className="text-blue-400">Detec</span><span className="text-gray-300">-o</span>
                 </Link>
              </div>
              {/* Links Principais (logado) - Visível apenas em telas maiores (sm+) */}
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                 {isAuthenticated && (
                    <>
                      <Link to="/" className="inline-flex items-center px-1 pt-1 border-b-2 border-transparent text-sm font-medium text-gray-300 hover:border-gray-600 hover:text-gray-100">Dashboard</Link>
                      <Link to="/camera-dashboard" className="inline-flex items-center px-1 pt-1 border-b-2 border-transparent text-sm font-medium text-gray-300 hover:border-gray-600 hover:text-gray-100">Minhas Câmeras</Link>
                      <Link to="/events" className="inline-flex items-center px-1 pt-1 border-b-2 border-transparent text-sm font-medium text-gray-300 hover:border-gray-600 hover:text-gray-100">Log de Eventos</Link>
                    </>
                 )}
              </div>
            </div>
            
            {/* Direita: Login/Registro ou Info Usuário/Logout - Visível apenas em telas maiores (sm+) */}
            <div className="hidden sm:ml-6 sm:flex sm:items-center">
              {!isAuthenticated ? (
                <div className="flex space-x-4">
                  <Link to="/login" className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-blue-100 bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">Login</Link>
                  <Link to="/register" className="inline-flex items-center px-3 py-2 border border-gray-600 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-200 bg-gray-700 hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">Registrar</Link>
                </div>
              ) : (
                <div className="flex items-center space-x-4">
                  <span className="text-sm font-medium text-gray-300">Bem-vindo, {user?.username || 'Usuário'}!</span>
                  <button 
                    onClick={logout}
                    className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-red-100 bg-red-700 hover:bg-red-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                    >Logout
                   </button>
                </div>
              )}
            </div>

            {/* Botão de Menu Mobile - Visível apenas em telas pequenas */}
            <div className="flex items-center sm:hidden">
              <button 
                type="button" 
                className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-200 hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
                aria-controls="mobile-menu"
                aria-expanded="false"
                onClick={toggleMobileMenu}
              >
                <span className="sr-only">Abrir menu principal</span>
                {/* Ícone de menu (3 linhas) quando fechado */}
                <svg 
                  className={`${mobileMenuOpen ? 'hidden' : 'block'} h-6 w-6`}
                  xmlns="http://www.w3.org/2000/svg" 
                  fill="none" 
                  viewBox="0 0 24 24" 
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
                </svg>
                {/* Ícone X quando aberto */}
                <svg 
                  className={`${mobileMenuOpen ? 'block' : 'hidden'} h-6 w-6`}
                  xmlns="http://www.w3.org/2000/svg" 
                  fill="none" 
                  viewBox="0 0 24 24" 
                  stroke="currentColor" 
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* Menu Mobile - Expandido quando mobileMenuOpen é true */}
        <div 
          className={`${mobileMenuOpen ? 'block' : 'hidden'} sm:hidden`} 
          id="mobile-menu"
        >
          <div className="pt-2 pb-3 space-y-1 border-t border-gray-700">
            {isAuthenticated ? (
              <>
                <Link 
                  to="/" 
                  className="block px-3 py-2 text-base font-medium text-gray-300 hover:bg-gray-700 hover:text-white"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Dashboard
                </Link>
                <Link 
                  to="/camera-dashboard" 
                  className="block px-3 py-2 text-base font-medium text-gray-300 hover:bg-gray-700 hover:text-white"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Minhas Câmeras
                </Link>
                <Link 
                  to="/events" 
                  className="block px-3 py-2 text-base font-medium text-gray-300 hover:bg-gray-700 hover:text-white"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Log de Eventos
                </Link>
                <div className="px-3 py-2 border-t border-gray-700">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-400">Logado como: <span className="text-gray-300">{user?.username || 'Usuário'}</span></span>
                    <button 
                      onClick={() => {
                        logout();
                        setMobileMenuOpen(false);
                      }}
                      className="ml-2 inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md text-red-100 bg-red-700 hover:bg-red-800 focus:outline-none"
                    >
                      Logout
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <>
                <Link 
                  to="/login" 
                  className="block px-3 py-2 text-base font-medium text-gray-300 hover:bg-gray-700 hover:text-white"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Login
                </Link>
                <Link 
                  to="/register" 
                  className="block px-3 py-2 text-base font-medium text-gray-300 hover:bg-gray-700 hover:text-white"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Registrar
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* Conteúdo Principal da Rota Atual */}
      <main className="pt-2 pb-2 sm:pt-4 sm:pb-4">
        <div className="md:flex w-full">
          {/* Conteúdo principal, ajuste para tela inteira em mobile */}
          <div className="w-full">
            {children}
          </div>
        </div>
      </main>
    </div>
  );
}

export default Layout; 