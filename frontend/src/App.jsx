import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { AuthProvider } from './contexts/AuthContext';
import './styles/global.css';

// Pages
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import EventsPage from './pages/EventsPage';
import SettingsPage from './pages/SettingsPage';
import CameraSettings from './pages/CameraSettings.jsx';
import EventDetail from './pages/EventDetail.jsx';
import NotFoundPage from './pages/NotFoundPage';
import LandingPage from './pages/LandingPage';
import CameraDashboard from './pages/CameraDashboard';
import AddCameraPage from './pages/AddCameraPage';

// Layout
import MainLayout from './components/MainLayout';

// Services
import notificationService from './services/notificationService';

// Componente para rotas protegidas
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (isLoading) {
    return <div className="flex justify-center items-center h-screen">Carregando...</div>;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }
  
  return children;
};

// Componente para lidar com a navegação
function ScrollToTop() {
  const location = useLocation();
  
  useEffect(() => {
    // Rolar para o topo da página ao mudar de rota
    window.scrollTo(0, 0);
    
    // Forçar remontagem limpa do componente
    const mainContent = document.getElementById('main-content');
    if (mainContent) {
      // Pequeno hack para forçar o re-render do conteúdo
      mainContent.style.opacity = '0.99';
      setTimeout(() => {
        mainContent.style.opacity = '1';
      }, 0);
    }
  }, [location.pathname]);
  
  return null;
}

function App() {
  const { isAuthenticated, isLoading } = useAuth();
  
  // Iniciar o serviço de notificações quando autenticado
  useEffect(() => {
    // Iniciar notificações apenas quando autenticado e não mais carregando
    if (isAuthenticated && !isLoading) {
      notificationService.startListening();
      console.log('Iniciando serviço de notificações');
    }
    
    // Limpar ao desmontar
    return () => {
      notificationService.stopListening();
      console.log('Parando serviço de notificações');
    };
  }, [isAuthenticated, isLoading]);

  useEffect(() => {
    document.title = 'Detec-o';
  }, []);

  return (
    <BrowserRouter>
      <AuthProvider>
        <ScrollToTop />
        <div id="main-content">
          <Routes>
            {/* Rota pública para a landing page */}
            <Route path="/" element={<LandingPage />} />
            
            {/* Rotas públicas */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            
            {/* Rotas protegidas */}
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <MainLayout>
                  <DashboardPage />
                </MainLayout>
              </ProtectedRoute>
            } />
            
            {/* Rota para visualização de câmeras em grade */}
            <Route path="/cameras" element={
              <ProtectedRoute>
                <CameraDashboard />
              </ProtectedRoute>
            } />
            
            {/* Rota alternativa para câmeras */}
            <Route path="/camera-dashboard" element={
              <ProtectedRoute>
                <CameraDashboard />
              </ProtectedRoute>
            } />
            
            <Route path="/events" element={
              <ProtectedRoute>
                <MainLayout>
                  <EventsPage />
                </MainLayout>
              </ProtectedRoute>
            } />
            
            <Route path="/events/:id" element={
              <ProtectedRoute>
                <MainLayout>
                  <EventDetail />
                </MainLayout>
              </ProtectedRoute>
            } />
            
            <Route path="/settings" element={
              <ProtectedRoute>
                <MainLayout>
                  <SettingsPage />
                </MainLayout>
              </ProtectedRoute>
            } />
            
            <Route path="/camera/:id" element={
              <ProtectedRoute>
                <MainLayout>
                  <CameraSettings />
                </MainLayout>
              </ProtectedRoute>
            } />
            
            {/* Rota para adicionar câmera */}
            <Route path="/add-camera" element={
              <ProtectedRoute>
                <AddCameraPage />
              </ProtectedRoute>
            } />
            
            {/* Rota de fallback */}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
          
          <ToastContainer 
            position="top-right"
            autoClose={5000}
            hideProgressBar={false}
            newestOnTop
            closeOnClick
            rtl={false}
            pauseOnFocusLoss
            draggable
            pauseOnHover
            theme="dark"
          />
        </div>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
