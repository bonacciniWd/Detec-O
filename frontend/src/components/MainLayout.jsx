import React, { useState } from 'react';
import Sidebar from './Sidebar';
import Navbar from './Navbar';
import { useMediaQuery } from 'react-responsive';
import AccessibilityMenu from './AccessibilityMenu';

const MainLayout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const isMobile = useMediaQuery({ maxWidth: 768 });

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <div className="flex h-screen bg-gray-100 overflow-hidden">
      {/* Sidebar - escondida em mobile quando fechada */}
      <div 
        className={`${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } fixed inset-y-0 left-0 transform z-30 w-64 transition duration-300 ease-in-out md:translate-x-0 md:static md:inset-0`}
      >
        <Sidebar />
      </div>

      {/* Overlay para fechar sidebar em mobile */}
      {sidebarOpen && isMobile && (
        <div 
          className="fixed inset-0 bg-gray-600 bg-opacity-50 z-20 md:hidden"
          onClick={toggleSidebar}
        />
      )}

      {/* Conteúdo principal */}
      <div className="flex flex-col flex-1 overflow-hidden">
        <Navbar toggleSidebar={toggleSidebar} />
        
        <main className="flex-1 overflow-y-auto overflow-x-hidden bg-gray-100 pb-safe">
          <div className="container mx-auto px-4 py-6 page-container">
            {children}
          </div>
        </main>
      </div>

      {/* Componente de acessibilidade */}
      <AccessibilityMenu />
    </div>
  );
};

export default MainLayout; 