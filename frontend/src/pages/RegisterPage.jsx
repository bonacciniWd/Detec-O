import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import apiClient from '../services/api';

function RegisterPage() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);

    // O endpoint /auth/register espera Form data
    const formData = new FormData();
    formData.append('username', username);
    formData.append('email', email);
    formData.append('password', password);
    if (fullName) formData.append('full_name', fullName);

    try {
      // Fazer a chamada POST para registrar
      await apiClient.post('/auth/register', formData, {
        // Definir explicitamente o cabeçalho, embora Axios deva fazer isso com FormData
        headers: {
          'Content-Type': 'multipart/form-data',
        }
      });
      
      setSuccess('Usuário registrado com sucesso! Redirecionando para login...');
      setError(null);
      // Limpar formulário
      setUsername('');
      setEmail('');
      setPassword('');
      setFullName('');
      
      // Redirecionar para a página de login após um pequeno atraso
      setTimeout(() => {
        navigate('/login');
      }, 2000); // Atraso de 2 segundos

    } catch (err) {
      let errorMsg = 'Falha no registro. Verifique os dados e tente novamente.';
      // Tentar extrair mensagens de erro de validação da API (FastAPI)
      if (err.response?.data?.detail) {
        if (Array.isArray(err.response.data.detail)) {
           // Mapeia os erros de validação para strings legíveis
           errorMsg = err.response.data.detail
             .map(e => `${e.loc?.slice(-1)[0] || 'Campo'}: ${e.msg}`)
             .join('; \n'); // Junta as mensagens
        } else if (typeof err.response.data.detail === 'string') {
           // Caso seja uma string simples (ex: usuário já existe)
           errorMsg = err.response.data.detail;
        }
      }
      
      setError(errorMsg); // Define a mensagem de erro formatada
      console.log("Mensagem de erro formatada:", errorMsg); // Adicionar log da mensagem formatada
      setSuccess(null);
      console.error('Erro no registro:', err.response?.data || err.message);
    } finally {
      setLoading(false);
    }
  };

  // Classes com tema escuro
  const inputClass = "appearance-none relative block w-full px-3 py-3 border border-gray-600 placeholder-gray-400 text-gray-100 bg-gray-700 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 text-base rounded-md";
  const buttonClass = "group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50";

  return (
    // Tema escuro
    <div className="flex items-center justify-center min-h-screen py-12 px-4 sm:px-6 lg:px-8 bg-gray-900">
      <div className="max-w-md w-full space-y-8 p-10 bg-gray-800 rounded-xl shadow-lg text-gray-100">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-white">Crie sua conta</h2>
        </div>

        {/* Mostrar mensagem de sucesso ou erro */} 
        {error && (
          <div className="bg-red-900 border border-red-700 text-red-100 px-4 py-3 rounded relative" role="alert">
            <span className="block sm:inline">{error}</span>
          </div>
        )}
        {success && (
          <div className="bg-green-900 border border-green-700 text-green-100 px-4 py-3 rounded relative" role="alert">
            <span className="block sm:inline">{success}</span>
          </div>
        )}

        {/* Mostrar formulário apenas se não houver sucesso */}
        {!success && (
          <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
            <div className="rounded-md shadow-sm -space-y-px">
              <div>
                <label htmlFor="reg-username" className="sr-only">Usuário</label>
                <input
                  id="reg-username"
                  name="username"
                  type="text"
                  autoComplete="username"
                  required
                  className={inputClass}
                  placeholder="Nome de usuário"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  disabled={loading}
                />
              </div>
              <div>
                <label htmlFor="reg-email" className="sr-only">Email</label>
                <input
                  id="reg-email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  className={inputClass}
                  placeholder="Endereço de email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={loading}
                />
              </div>
              <div>
                <label htmlFor="reg-password" className="sr-only">Senha</label>
                <input
                  id="reg-password"
                  name="password"
                  type="password"
                  autoComplete="new-password"
                  required
                  className={inputClass}
                  placeholder="Senha"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={loading}
                />
              </div>
              <div>
                <label htmlFor="reg-fullname" className="sr-only">Nome Completo</label>
                <input
                  id="reg-fullname"
                  name="full_name"
                  type="text"
                  autoComplete="name"
                  className={inputClass}
                  placeholder="Nome Completo (Opcional)"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  disabled={loading}
                />
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className={buttonClass}
              >
                {loading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Registrando...
                  </>
                ) : (
                  'Registrar'
                )}
              </button>
            </div>
          </form>
        )}

        <p className="mt-2 text-center text-sm text-gray-400">
          Já tem uma conta?{' '}
          <Link to="/login" className="font-medium text-blue-400 hover:text-blue-300">
            Faça login
          </Link>
        </p>
      </div>
    </div>
  );
}

export default RegisterPage; 