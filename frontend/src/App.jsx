import { Routes, Route, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import CamerasPage from './pages/CamerasPage';
import EventsPage from './pages/EventsPage';
import NotFoundPage from './pages/NotFoundPage';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import AccessibilityMenu from './components/AccessibilityMenu';
import { useAuth } from './contexts/AuthContext';
import { ToastContainer } from 'react-toastify';
import notificationService from './services/notificationService';
import 'react-toastify/dist/ReactToastify.css';

function App() {
  const { isAuthenticated, isLoading } = useAuth();

  // Iniciar o serviço de notificações apenas quando o usuário estiver autenticado
  useEffect(() => {
    // Garantir que o usuário está autenticado e o carregamento inicial foi concluído
    if (isAuthenticated && !isLoading) {
      console.log('Iniciando serviço de notificações - usuário autenticado');
      notificationService.startListening();
      
      // Limpar quando o componente for desmontado
      return () => {
        console.log('Parando serviço de notificações');
        notificationService.stopListening();
      };
    } else if (!isAuthenticated && !isLoading) {
      // Parar serviço de notificações se o usuário não estiver autenticado
      console.log('Usuário não autenticado - garantindo que o serviço de notificações esteja parado');
      notificationService.stopListening();
    }
  }, [isAuthenticated, isLoading]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-900">
        <div className="text-xl font-semibold text-white">Carregando aplicação...</div>
      </div>
    );
  }

  return (
    <>
      <Routes>
        <Route 
          path="/login" 
          element={!isAuthenticated ? <LoginPage /> : <Navigate to="/" replace />}
        />
        <Route 
          path="/register" 
          element={!isAuthenticated ? <RegisterPage /> : <Navigate to="/" replace />}
        />

        <Route 
          element={
              <ProtectedRoute>
                <Layout /> 
              </ProtectedRoute>
          }
        >
          <Route path="/" element={<DashboardPage />} />
          <Route path="/cameras" element={<CamerasPage />} />
          <Route path="/events" element={<EventsPage />} />
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
      
      {/* Componente de acessibilidade */}
      <AccessibilityMenu />
      
      <ToastContainer 
        position="bottom-right"
        autoClose={5000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="dark"
      />
    </>
  );
}

export default App;
