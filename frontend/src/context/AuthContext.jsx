import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

// Criação do contexto de autenticação
const AuthContext = createContext();

// Hook personalizado para usar o contexto de autenticação
export const useAuth = () => {
  return useContext(AuthContext);
};

// Provedor do contexto de autenticação
export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [token, setToken] = useState(localStorage.getItem('token') || localStorage.getItem('accessToken') || null);
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  // API base - usando variável central para fácil modificação
  const API_BASE = '';  // Vazio para usar base relativa

  // Verificar o token e carregar os dados do usuário
  useEffect(() => {
    const checkAuth = async () => {
      if (token) {
        try {
          // Configurar o token para todas as requisições
          axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
          
          // Obter informações do usuário
          try {
            // Tentar ambos os endpoints para compatibilidade
            let response;
            try {
              response = await axios.get(`${API_BASE}/auth/me`);
            } catch (e) {
              response = await axios.get(`${API_BASE}/api/v1/auth/me`);
            }
            
            setUser(response.data);
            setIsAuthenticated(true);
          } catch (error) {
            console.error('Erro ao verificar autenticação:', error);
            // Se o token for inválido, fazer logout
            logout();
          }
        } finally {
          setIsLoading(false);
        }
      } else {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, [token]);

  // Função de login mais robusta para lidar com diferentes formatos
  const login = async (email, password) => {
    try {
      let response;
      let responseData;
      
      // Tentar ambos os endpoints
      try {
        // Tentar primeiro endpoint
        try {
          response = await axios.post(`${API_BASE}/auth/token`, { 
            email, 
            password,
            username: email  // Para compatibilidade com OAuth2
          });
          responseData = response.data;
        } catch (e) {
          // Tentar com formato form-urlencoded
          const formData = new URLSearchParams();
          formData.append('username', email);
          formData.append('password', password);
          
          response = await axios.post(`${API_BASE}/auth/token`, formData.toString(), {
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
            },
          });
          responseData = response.data;
        }
      } catch (firstEndpointError) {
        console.log('Primeiro endpoint falhou, tentando alternativa', firstEndpointError);
        
        // Tentar segundo endpoint
        response = await axios.post(`${API_BASE}/api/v1/auth/login`, { 
          email, 
          password 
        });
        responseData = response.data;
      }
      
      console.log('Resposta do login:', responseData);
      
      // Extrair tokens independentemente do formato usado
      const accessToken = responseData.access_token || responseData.authToken || responseData.token;
      const refreshToken = responseData.refresh_token || responseData.refreshToken;
      
      if (!accessToken) {
        throw new Error('Token não encontrado na resposta');
      }
      
      // Salvar tokens em multiple locations para compatibilidade
      localStorage.setItem('token', accessToken);
      localStorage.setItem('accessToken', accessToken);
      if (refreshToken) {
        localStorage.setItem('refreshToken', refreshToken);
      }
      
      // Atualizar o state
      setToken(accessToken);
      setIsAuthenticated(true);
      
      // Configurar o token para todas as requisições
      axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
      
      // Obter informações do usuário se não presentes na resposta
      if (responseData.user) {
        setUser(responseData.user);
      } else {
        try {
          // Tentar ambos os endpoints para compatibilidade
          let userResponse;
          try {
            userResponse = await axios.get(`${API_BASE}/auth/me`);
          } catch (e) {
            userResponse = await axios.get(`${API_BASE}/api/v1/auth/me`);
          }
          setUser(userResponse.data);
        } catch (userError) {
          console.error('Erro ao buscar usuário:', userError);
          // Fallback: criar usuário básico
          setUser({ id: '1', email, name: email.split('@')[0] });
        }
      }
      
      // Redirecionar para o dashboard
      navigate('/dashboard');
      
      return { success: true };
    } catch (error) {
      console.error('Erro ao fazer login:', error);
      return { 
        success: false, 
        message: error.response?.data?.detail || error.message || 'Erro ao fazer login. Verifique suas credenciais.'
      };
    }
  };

  // Função de registro mais robusta
  const register = async (userData) => {
    if (typeof userData === 'string') {
      // Se for string, assumir que é nome e usar outros argumentos
      // Para compatibilidade com a outra implementação
      const [name, email, password] = arguments;
      userData = { name, email, password };
    }
    
    try {
      let response;
      
      // Tentar ambos os endpoints
      try {
        response = await axios.post(`${API_BASE}/auth/register`, userData);
      } catch (e) {
        response = await axios.post(`${API_BASE}/api/v1/auth/register`, userData);
      }
      
      // Após registro, tenta login automaticamente
      return await login(userData.email, userData.password);
    } catch (error) {
      console.error('Erro ao registrar:', error);
      return { 
        success: false, 
        message: error.response?.data?.detail || 'Erro ao criar conta. Tente novamente.'
      };
    }
  };

  // Função de logout
  const logout = () => {
    // Remover tokens do localStorage para garantir limpeza completa
    localStorage.removeItem('token');
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    
    // Limpar o state
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
    
    // Remover token das requisições
    delete axios.defaults.headers.common['Authorization'];
    
    // Redirecionar para login
    navigate('/login');
  };

  // Valores a serem fornecidos pelo contexto
  const value = {
    isAuthenticated,
    isLoading,
    token,
    user,
    login,
    register,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext; 