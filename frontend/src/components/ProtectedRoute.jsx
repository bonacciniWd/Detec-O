import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation(); // Para redirecionar de volta após o login

  // 1. Se ainda estiver carregando a informação de auth, espere
  if (isLoading) {
    return <div>Verificando autenticação...</div>; // Ou um spinner
  }

  // 2. Se não estiver autenticado, redirecione para /login
  if (!isAuthenticated) {
    // Passa a localização atual para que possamos redirecionar de volta após o login
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // 3. Se estiver autenticado, renderize o componente filho (a página protegida)
  return children;
}

export default ProtectedRoute; 