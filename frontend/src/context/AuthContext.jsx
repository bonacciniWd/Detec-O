import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api, { authService } from '../services/api';

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
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  // Verificar o token e carregar os dados do usuário
  useEffect(() => {
    const checkAuth = async () => {
      setIsLoading(true);
      
      // Verificar se existe um token antes de tentar validá-lo
      if (!token) {
        console.log("Nenhum token encontrado, não tentando autenticação automática");
        setIsAuthenticated(false);
        setUser(null);
        setIsLoading(false);
        return;
      }
      
      try {
        // Adicionar token ao cabeçalho para esta requisição específica
        const userData = await authService.getUser();
        setUser(userData);
            setIsAuthenticated(true);
          } catch (error) {
        console.error("Erro ao verificar autenticação:", error);
        // Limpar todos os tokens possíveis
        localStorage.removeItem("token");
        localStorage.removeItem("accessToken");
        localStorage.removeItem("refreshToken");
        localStorage.removeItem("authToken");
        setUser(null);
        setIsAuthenticated(false);
        } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, [token]); // Adicionar token como dependência

  // Função de login usando o serviço de API
  const login = async (email, password) => {
      setIsLoading(true);
    setError(null);
    try {
      // 1. Fazer login e obter o token
      const tokenData = await authService.login(email, password);
      
      // 2. Verificar se o token foi recebido
      if (!tokenData || !tokenData.access_token) {
        throw new Error("Token de acesso não recebido após login.");
      }
      
      // 3. Atualizar o estado do token no contexto
      // (localStorage já foi atualizado em authService.login)
      setToken(tokenData.access_token);
      
      // 4. Buscar dados do usuário com o novo token
      // authService.getUser() usará o token do localStorage atualizado
      const userData = await authService.getUser();
      
      // 5. Atualizar o estado do usuário e autenticação
      setUser(userData);
      setIsAuthenticated(true);
      
      return userData; // Retorna os dados do usuário
      
    } catch (error) {
      console.error("Erro no processo de login (AuthContext):", error);
      
      // Limpar tudo em caso de erro no processo
      authService.logout(); // Limpa localStorage
      setToken(null);
      setUser(null);
      setIsAuthenticated(false);
      
      const errorMessage = error?.response?.data?.detail || 
                           error?.message || 
                           "Erro desconhecido no login";
      setError(typeof errorMessage === 'object' ? JSON.stringify(errorMessage) : errorMessage);
      throw error;
    } finally {
       setIsLoading(false); // Garantir que isLoading seja falso
    }
  };

  // Função de registro usando o serviço de API
  const register = async (userData) => {
    if (typeof userData === 'string') {
      // Se for string, assumir que é nome e usar outros argumentos
      // Para compatibilidade com a outra implementação
      const [name, email, password] = arguments;
      userData = { name, email, password };
    }
    
    try {
      await authService.register(userData);
      
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
    authService.logout();
    
    // Limpar o state
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
    
    // Redirecionar para login
    navigate('/login');
  };

  // Valores a serem fornecidos pelo contexto
  const value = {
    isAuthenticated,
    isLoading,
    token,
    user,
    error,
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