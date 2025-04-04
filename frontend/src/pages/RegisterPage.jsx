import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import apiClient from '../services/api';

function RegisterPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const canvasRef = useRef(null);

  // Efeito para configurar o canvas de fundo
  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    function resizeCanvas() {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    }

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    const particles = [];
    const numParticles = 100;

    class Particle {
      constructor(x, y, radius, speed) {
        this.x = x;
        this.y = y;
        this.radius = radius;
        this.speed = speed;
        this.angle = Math.random() * Math.PI * 2;
      }

      update() {
        this.x += Math.cos(this.angle) * this.speed;
        this.y += Math.sin(this.angle) * this.speed;

        // Bounce off edges
        if (this.x < 0 || this.x > canvas.width) this.angle = Math.PI - this.angle;
        if (this.y < 0 || this.y > canvas.height) this.angle = -this.angle;
      }

      draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
        ctx.fill();
      }
    }

    // Initialize particles
    for (let i = 0; i < numParticles; i++) {
      particles.push(
        new Particle(
          Math.random() * canvas.width,
          Math.random() * canvas.height,
          Math.random() * 4 + 1,
          Math.random() * 0.5 + 0.2
        )
      );
    }

    // Connect particles
    function connectParticles() {
      for (let a = 0; a < particles.length; a++) {
        for (let b = a + 1; b < particles.length; b++) {
          const dist = Math.hypot(
            particles[a].x - particles[b].x,
            particles[a].y - particles[b].y
          );

          if (dist < 120) {
            ctx.strokeStyle = `rgba(255, 255, 255, ${1 - dist / 120})`;
            ctx.lineWidth = 0.7;
            ctx.beginPath();
            ctx.moveTo(particles[a].x, particles[a].y);
            ctx.lineTo(particles[b].x, particles[b].y);
            ctx.stroke();
          }
        }
      }
    }

    // Animation Loop
    function animate() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      particles.forEach(particle => {
        particle.update();
        particle.draw();
      });
      connectParticles();
      requestAnimationFrame(animate);
    }

    // Start Animation
    animate();

    // Cleanup
    return () => {
      window.removeEventListener('resize', resizeCanvas);
    };
  }, []);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);

    try {
      // Fazer a chamada POST para registrar usando JSON em vez de FormData
      await apiClient.post('/auth/register', {
        email,
        password,
        name: fullName || email.split('@')[0] // Usar parte do email como nome se não fornecido
      });
      
      setSuccess('Usuário registrado com sucesso! Redirecionando para login...');
      setError(null);
      // Limpar formulário
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
      setSuccess(null);
      console.error('Erro no registro:', err.response?.data || err.message);
    } finally {
      setLoading(false);
    }
  };

  // Classes com tema escuro
  const inputClass = "appearance-none relative block w-full px-3 py-3 border border-gray-600 placeholder-gray-400 text-gray-100 bg-gray-700 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 text-base rounded-md mb-4";
  const buttonClass = "group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50";

  return (
    <div className="relative min-h-screen w-full overflow-hidden" style={{ background: 'radial-gradient(circle, #1b2735, #090a0f)' }}>
      {/* Background Canvas */}
      <canvas 
        ref={canvasRef} 
        className="absolute top-0 left-0 w-full h-full"
      />
      
      {/* Register Form */}
      <div className="relative flex items-center justify-center min-h-screen py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-6 p-10 bg-gray-800 bg-opacity-80 backdrop-filter backdrop-blur-sm rounded-xl shadow-lg text-gray-100">
          <div className="flex flex-col items-center">
            <img
              src="/logo.png"
              alt="Detec-o Logo"
              className="h-16 mx-auto mb-4"
            />
            <h2 className="text-center text-2xl font-medium text-white">Cadastre-se no Sistema</h2>
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
            <form className="mt-6 space-y-6" onSubmit={handleSubmit}>
              <div>
                <input
                  id="reg-fullname"
                  name="full_name"
                  type="text"
                  autoComplete="name"
                  className={inputClass}
                  placeholder="Nome Completo"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  disabled={loading}
                />
              </div>
              <div>
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
    </div>
  );
}

export default RegisterPage; 