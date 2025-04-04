import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FaHome, FaVideo, FaBell, FaChartBar, FaDoorOpen, FaCog, FaUser } from 'react-icons/fa';

const Sidebar = () => {
  const location = useLocation();
  const currentPath = location.pathname;
  
  const menuItems = [
    { path: '/dashboard', icon: <FaHome />, text: 'Dashboard' },
    { path: '/cameras', icon: <FaVideo />, text: 'Câmeras' },
    { path: '/camera-dashboard', icon: <FaChartBar />, text: 'Monitoramento' },
    { path: '/events', icon: <FaBell />, text: 'Eventos' },
    { path: '/people', icon: <FaUser />, text: 'Pessoas' },
    { path: '/settings', icon: <FaCog />, text: 'Configurações' },
  ];
  
  return (
    <aside className="bg-gray-800 text-white w-64 min-h-screen p-4">
      <div className="mb-8">
        <h1 className="text-2xl font-bold">Detec-O</h1>
        <p className="text-gray-400 text-sm">Sistema de Monitoramento</p>
      </div>
      
      <nav>
        <ul className="space-y-2">
          {menuItems.map((item) => (
            <li key={item.path}>
              <Link
                to={item.path}
                className={`flex items-center px-4 py-3 rounded-lg hover:bg-gray-700 transition-colors ${
                  currentPath === item.path ? 'bg-blue-600 text-white' : 'text-gray-300'
                }`}
              >
                <span className="mr-3">{item.icon}</span>
                <span>{item.text}</span>
              </Link>
            </li>
          ))}
        </ul>
      </nav>
      
      <div className="mt-auto pt-8">
        <Link
          to="/logout"
          className="flex items-center px-4 py-3 text-red-400 hover:bg-gray-700 rounded-lg"
        >
          <FaDoorOpen className="mr-3" />
          <span>Sair</span>
        </Link>
      </div>
    </aside>
  );
};

export default Sidebar; 