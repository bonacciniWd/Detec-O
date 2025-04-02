import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

function NotFoundPage() {
  const { isAuthenticated } = useAuth();
  
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900 px-4">
      <div className="max-w-md w-full text-center space-y-6">
        <div className="space-y-2">
          <h1 className="text-6xl font-extrabold text-white">404</h1>
          <h2 className="text-3xl font-bold text-blue-500">Página Não Encontrada</h2>
          <p className="text-gray-300 mt-4">
            Oops! O recurso que você está procurando não existe ou foi movido.
          </p>
        </div>
        
        <div className="flex flex-col space-y-3 mt-8">
          <Link
            to={isAuthenticated ? "/" : "/login"}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-md transition duration-200"
          >
            {isAuthenticated ? "Voltar ao Dashboard" : "Voltar ao Login"}
          </Link>
          
          {isAuthenticated && (
            <Link
              to="/cameras"
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white font-medium rounded-md transition duration-200"
            >
              Gerenciar Câmeras
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}

export default NotFoundPage; 