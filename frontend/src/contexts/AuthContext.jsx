import React, { createContext, useState, useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../services/api';

// 1. Criar o Contexto
const AuthContext = createContext(null);

// 2. Criar o Componente Provedor
export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem('authToken'));
  const [refreshToken, setRefreshToken] = useState(localStorage.getItem('refreshToken'));
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('authToken'));
  const [isLoading, setIsLoading] = useState(true); // Começa carregando para verificar token inicial
  const navigate = useNavigate();

  // Configurar o interceptor para usar o token nas requisições
  useEffect(() => {
    if (token) {
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete apiClient.defaults.headers.common['Authorization'];
    }
  }, [token]);

  // Função para atualizar tokens na localStorage e state
  const updateTokens = (accessToken, newRefreshToken) => {
    localStorage.setItem('authToken', accessToken);
    localStorage.setItem('refreshToken', newRefreshToken || refreshToken);
    setToken(accessToken);
    if (newRefreshToken) setRefreshToken(newRefreshToken);
    setIsAuthenticated(true);
  };

  // Função para usar o refresh token e obter um novo access token
  const refreshAccessToken = async () => {
    if (!refreshToken) return false;
    
    try {
      const formData = new URLSearchParams();
      formData.append('refresh_token', refreshToken);
      formData.append('grant_type', 'refresh_token');
      
      const response = await apiClient.post('/auth/refresh', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      
      const { access_token, refresh_token } = response.data;
      updateTokens(access_token, refresh_token);
      return true;
    } catch (error) {
      console.error("Falha ao renovar o token:", error);
      logout();
      return false;
    }
  };

  // Efeito para verificar o token no localStorage na inicialização
  useEffect(() => {
    const verifyToken = async () => {
      const storedToken = localStorage.getItem('authToken');
      if (storedToken) {
        try {
          // Token existe, tentar buscar dados do usuário
          apiClient.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
          const response = await apiClient.get('/auth/users/me');
          setUser(response.data); // Armazena dados do usuário
          setToken(storedToken);
          setIsAuthenticated(true);
          console.log("Token inicial verificado, usuário:", response.data);
        } catch (error) {
          console.error("Falha ao verificar token inicial:", error);
          
          // Tentar usar refresh token
          const refreshSuccess = await refreshAccessToken();
          if (!refreshSuccess) {
            // Se não conseguir renovar, faz logout
            localStorage.removeItem('authToken');
            localStorage.removeItem('refreshToken');
            setToken(null);
            setRefreshToken(null);
            setUser(null);
            setIsAuthenticated(false);
          }
        }
      } else {
        // Não há token armazenado
        setIsAuthenticated(false);
        setUser(null);
      }
      setIsLoading(false); // Terminou a verificação inicial
    };

    verifyToken();
  }, []); // Executa apenas uma vez na montagem

  // Configurar interceptor para renovar token quando expirar
  useEffect(() => {
    const interceptor = apiClient.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        // Se o erro for 401 e não for uma tentativa de refresh
        if (error.response?.status === 401 && !originalRequest._retry && refreshToken) {
          originalRequest._retry = true;
          
          const refreshSuccess = await refreshAccessToken();
          if (refreshSuccess) {
            // Restaurar o header e tentar novamente
            originalRequest.headers['Authorization'] = `Bearer ${token}`;
            return apiClient(originalRequest);
          }
        }
        return Promise.reject(error);
      }
    );

    return () => apiClient.interceptors.response.eject(interceptor);
  }, [refreshToken, token]);

  // Função de Login
  const login = async (username, password) => {
    setIsLoading(true);
    try {
      // O backend espera form-data para /auth/token
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await apiClient.post('/auth/token', formData, {
         headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      
      const { access_token, refresh_token } = response.data;
      updateTokens(access_token, refresh_token);

      // Buscar dados do usuário após login bem-sucedido
      try {
        const userResponse = await apiClient.get('/auth/users/me');
        setUser(userResponse.data);
        console.log("Login bem-sucedido, usuário:", userResponse.data);
        navigate('/'); // Redireciona para a página inicial (ou dashboard)
      } catch (userError) {
         console.error("Erro ao buscar usuário após login:", userError);
         // Mesmo com erro ao buscar user, o login (token) funcionou
         setUser(null); // Define user como null se falhar
         navigate('/'); // Ou talvez mostrar um erro?
      }

      return true; // Indica sucesso no login
    } catch (error) {
      console.error("Erro no login:", error);
      localStorage.removeItem('authToken');
      localStorage.removeItem('refreshToken');
      setToken(null);
      setRefreshToken(null);
      setUser(null);
      setIsAuthenticated(false);
      // Retornar a mensagem de erro da API, se disponível
      throw new Error(error.response?.data?.detail || 'Falha no login. Verifique usuário e senha.');
    } finally {
      setIsLoading(false);
    }
  };

  // Função de Logout
  const logout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('refreshToken');
    setToken(null);
    setRefreshToken(null);
    setUser(null);
    setIsAuthenticated(false);
    delete apiClient.defaults.headers.common['Authorization']; // Limpa o header no cliente axios
    console.log("Usuário deslogado.");
    navigate('/login'); // Redireciona para a página de login
  };

  // Valor fornecido pelo Contexto
  const value = {
    token,
    refreshToken,
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    refreshAccessToken,
    // register (pode ser adicionado se necessário)
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// 3. Criar o Hook Customizado para usar o Contexto
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth deve ser usado dentro de um AuthProvider');
  }
  return context;
}; 