import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Lottie from 'lottie-react';
import cameraAnimation from '../assets/lottie/splash-animation.json';

function LandingPage() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleAccessClick = () => {
    if (isAuthenticated) {
      navigate('/dashboard');
    } else {
      navigate('/login');
    }
  };

  return (
    <div className="bg-gray-100">
      {/* Header/Navbar */}
      <nav className="bg-slate-900/40 backdrop-blur-sm text-white shadow-lg top-0 fixed w-full z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <img src="/logo.png" alt="Detec-o Logo" className="h-10" />
              </div>
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                <a href="#sobre" className="border-transparent text-white hover:border-white hover:text-white inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium">
                  Sobre Nós
                </a>
                <a href="#servicos" className="border-transparent text-white hover:border-white hover:text-white inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium">
                  Serviços
                </a>
                <a href="#tecnologia" className="border-transparent text-white hover:border-white hover:text-white inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium">
                  Tecnologia
                </a>
                <a href="#integracao" className="border-transparent text-white hover:border-white hover:text-white inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium">
                  Integração
                </a>
                <a href="#contato" className="border-transparent text-white hover:border-white hover:text-white inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium">
                  Contato
                </a>
              </div>
            </div>
            <div className="flex items-center">
              <button
                onClick={handleAccessClick}
                className="bg-blue-700 hover:bg-blue-600 text-white py-2 px-4 rounded-md text-sm font-medium"
              >
                {isAuthenticated ? 'Acessar Dashboard' : 'Acessar Sistema'}
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="relative bg-blue-800 overflow-hidden sm:rounded-br-full md:rounded-br-full rounded-br-[280px]">
        <div className="absolute inset-0">
          <img
            className="w-full h-full object-cover animate-zoom"
            src="/images/hero-image.webp"
            alt="Sistema de monitoramento inteligente"
          />
          <div className="absolute inset-0 bg-blue-900 opacity-75"></div>
        </div>
        <div className="relative max-w-7xl mx-auto py-24 px-4 sm:py-32 sm:px-6 lg:px-8">
          <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl lg:text-6xl">
            Detectamos. Prevenimos. Protegemos.
          </h1>
          <p className="mt-6 text-xl text-blue-100 max-w-3xl">
            O sistema de monitoramento inteligente Detec-o utiliza inteligência artificial avançada para detectar comportamentos suspeitos e garantir a segurança em tempo real.
          </p>
          <div className="mt-10">
            <a
              href="#contato"
              className="inline-block bg-white py-3 px-8 border border-transparent rounded-md text-base font-medium text-blue-900 hover:bg-blue-50"
            >
              Solicitar Demonstração
            </a>
          </div>
        </div>
      </div>

      {/* Sobre Nós Section */}
      <div id="sobre" className="py-16 bg-white overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="lg:text-center">
            <h2 className="text-base text-blue-600 font-semibold tracking-wide uppercase">Sobre Nós</h2>
            <p className="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-gray-900 sm:text-4xl">
              Soluções inteligentes para segurança moderna
            </p>
            <p className="mt-4 max-w-2xl text-xl text-gray-600 lg:mx-auto">
              Desenvolvemos tecnologia de ponta para monitoramento e detecção automática, garantindo segurança com eficiência e precisão.
            </p>
          </div>

          <div className="mt-16">
            <div className="lg:grid lg:grid-cols-2 lg:gap-8 lg:items-center">
              <div className="relative">
                <div className="aspect-w-3 aspect-h-2 rounded-lg shadow-lg overflow-hidden">
                  <img
                    className="object-cover"
                    src="/images/about-image.jpg"
                    alt="Nossa equipe"
                  />
                </div>
              </div>
              <div className="mt-10 lg:mt-0">
                <h3 className="text-2xl font-extrabold text-gray-900">
                  Nossa missão
                </h3>
                <p className="mt-3 text-lg text-gray-600">
                </p>
                <p className="mt-3 text-lg text-gray-600">
                  Fundada em 2024, a Detec-o nasceu da visão de tornar os ambientes mais seguros através de tecnologia acessível e eficiente. Nosso foco é entregar soluções de monitoramento inteligente que vão além da simples vigilância.
                </p>
                <p className="mt-3 text-lg text-gray-600">
                 Devido aos recentes aumentos nas taxas de criminalidade e atentados violentos, a nossa empresa foi fundada com o objetivo de ajudar a proteger tudo aquilo que zelamos e aqueles que amamos.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Serviços Section */}
      <div id="servicos" className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="lg:text-center">
            <h2 className="text-base text-blue-600 font-semibold tracking-wide uppercase">Serviços</h2>
            <p className="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-gray-900 sm:text-4xl">
              Soluções completas para segurança
            </p>
            <p className="mt-4 max-w-2xl text-xl text-gray-600 lg:mx-auto">
              Oferecemos serviços especializados para diferentes necessidades de segurança.
            </p>
          </div>

          <div className="mt-16">
            <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
              {/* Serviço 1 */}
              <div className="flex flex-col bg-white rounded-lg shadow-lg overflow-hidden">
                <div className="flex-1 p-6 flex flex-col justify-between">
                  <div>
                    <div className="w-10 h-10 rounded-md bg-blue-700 flex items-center justify-center">
                      <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                      </svg>
                    </div>
                    <h3 className="mt-4 text-xl font-semibold text-gray-900">Monitoramento Inteligente</h3>
                    <p className="mt-3 text-base text-gray-600">
                      Detectamos automaticamente comportamentos suspeitos, como agressões, uso de armas e situações de perigo, enviando alertas em tempo real.
                    </p>
                  </div>
                </div>
              </div>

              {/* Serviço 2 */}
              <div className="flex flex-col bg-white rounded-lg shadow-lg overflow-hidden">
                <div className="flex-1 p-6 flex flex-col justify-between">
                  <div>
                    <div className="w-10 h-10 rounded-md bg-blue-700 flex items-center justify-center">
                      <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                      </svg>
                    </div>
                    <h3 className="mt-4 text-xl font-semibold text-gray-900">Controle de Acesso</h3>
                    <p className="mt-3 text-base text-gray-600">
                      Identificação e controle de acesso de pessoas, com registro automático de entrada e saída, tempo de permanência e detecção de áreas restritas.
                    </p>
                  </div>
                </div>
              </div>

              {/* Serviço 3 */}
              <div className="flex flex-col bg-white rounded-lg shadow-lg overflow-hidden">
                <div className="flex-1 p-6 flex flex-col justify-between">
                  <div>
                    <div className="w-10 h-10 rounded-md bg-blue-700 flex items-center justify-center">
                      <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <h3 className="mt-4 text-xl font-semibold text-gray-900">Análise e Relatórios</h3>
                    <p className="mt-3 text-base text-gray-600">
                      Dashboard analítico com estatísticas de ocorrências, relatórios personalizados e análise de tendências para tomada de decisão.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tecnologia Section */}
      <div id="tecnologia" className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="lg:text-center">
            <h2 className="text-base text-blue-600 font-semibold tracking-wide uppercase">Nossa Tecnologia</h2>
            <p className="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-gray-900 sm:text-4xl">
              Inteligência artificial a serviço da segurança
            </p>
            <p className="mt-4 max-w-2xl text-xl text-gray-600 lg:mx-auto">
              Utilizamos algoritmos avançados para garantir detecções precisas e relevantes.
            </p>
          </div>

          <div className="mt-16">
            <div className="lg:grid lg:grid-cols-3 lg:gap-8">
              {/* Tecnologia 1 */}
              <div>
                <div className="flex items-center justify-center h-12 w-12 rounded-md bg-blue-700 text-white">
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                  </svg>
                </div>
                <div className="mt-5">
                  <h3 className="text-lg font-medium text-gray-900">Alertas em Tempo Real</h3>
                  <p className="mt-2 text-base text-gray-600">
                    Receba notificações imediatas quando eventos relevantes são detectados, permitindo resposta rápida.
                  </p>
                </div>
              </div>

              {/* Tecnologia 2 */}
              <div className="mt-10 lg:mt-0">
                <div className="flex items-center justify-center h-12 w-12 rounded-md bg-blue-700 text-white">
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                  </svg>
                </div>
                <div className="mt-5">
                  <h3 className="text-lg font-medium text-gray-900">Categorização por Cores</h3>
                  <p className="mt-2 text-base text-gray-600">
                    Eventos são categorizados por cores para indicar diferentes níveis de atenção: vermelho (perigo), amarelo (suspeito) e azul (informativo).
                  </p>
                </div>
              </div>

              {/* Tecnologia 3 */}
              <div className="mt-10 lg:mt-0">
                <div className="flex items-center justify-center h-12 w-12 rounded-md bg-blue-700 text-white">
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <div className="mt-5">
                  <h3 className="text-lg font-medium text-gray-900">Sistema de Feedback</h3>
                  <p className="mt-2 text-base text-gray-600">
                    Confirme ou corrija detecções para melhorar continuamente a precisão do sistema através de machine learning.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Integração com Equipamentos Existentes */}
      <div id="integracao" className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="lg:text-center">
            <h2 className="text-base text-blue-600 font-semibold tracking-wide uppercase">Integração Universal</h2>
            <p className="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-gray-900 sm:text-4xl">
              Use com o equipamento que você já possui
            </p>
            <p className="mt-4 max-w-2xl text-xl text-gray-600 lg:mx-auto">
              O Detec-O se integra facilmente aos seus sistemas de câmeras existentes, sem necessidade de substituir equipamentos.
            </p>
          </div>

          <div className="mt-16">
            <div className="lg:grid lg:grid-cols-2 lg:gap-8 lg:items-center">
              <div className="mt-10 lg:mt-0 order-first lg:order-last">
                <img 
                  src="/images/integration.jpg" 
                  alt="Diagrama de integração" 
                  className="mx-auto rounded-lg shadow-lg"
                />
              </div>
              <div>
                <h3 className="text-2xl font-extrabold text-gray-900">
                  Compatibilidade ampla para economia real
                </h3>
                <div className="mt-6">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <div className="flex items-center justify-center h-12 w-12 rounded-md bg-blue-700 text-white">
                        <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                    </div>
                    <div className="ml-4">
                      <h4 className="text-lg font-medium text-gray-900">Compatível com múltiplos fabricantes</h4>
                      <p className="mt-2 text-base text-gray-600">
                        Funciona com câmeras e DVRs/NVRs de fabricantes populares como Hikvision, Dahua, Intelbras e qualquer dispositivo compatível com ONVIF.
                      </p>
                    </div>
                  </div>
                  <div className="flex mt-6">
                    <div className="flex-shrink-0">
                      <div className="flex items-center justify-center h-12 w-12 rounded-md bg-blue-700 text-white">
                        <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                      </div>
                    </div>
                    <div className="ml-4">
                      <h4 className="text-lg font-medium text-gray-900">Descoberta automática de dispositivos</h4>
                      <p className="mt-2 text-base text-gray-600">
                        O sistema detecta automaticamente câmeras e gravadores na sua rede, facilitando a configuração sem necessidade de conhecimentos técnicos avançados.
                      </p>
                    </div>
                  </div>
                  <div className="flex mt-6">
                    <div className="flex-shrink-0">
                      <div className="flex items-center justify-center h-12 w-12 rounded-md bg-blue-700 text-white">
                        <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                        </svg>
                      </div>
                    </div>
                    <div className="ml-4">
                      <h4 className="text-lg font-medium text-gray-900">API aberta para integrações</h4>
                      <p className="mt-2 text-base text-gray-600">
                        Integre com outros sistemas de segurança, automação residencial ou comercial através de nossa API aberta e bem documentada.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="mt-16">
              <h3 className="text-xl font-bold text-center text-gray-900 mb-8">Compatível com os principais fabricantes</h3>
              <div className="grid grid-cols-2 gap-8 md:grid-cols-6">
                <div className="col-span-1 flex justify-center">
                  <img className="h-8 sm-12 md:h-12" src="/images/hikvisioon.png" alt="Hikvision" />
                </div>
                <div className="col-span-1 flex justify-center">
                  <img className="h-8 sm-12 md:h-12" src="/images/axis.png" alt="Axis" />
                </div>
                <div className="col-span-1 flex justify-center">
                  <img className="h-8 sm-12 md:h-12" src="/images/dahua.png" alt="Dahua" />
                </div>
               
                <div className="col-span-1 flex justify-center">
                  <img className="h-8 sm-12 md:h-12" src="/images/intelbras.png" alt="Intelbras" />
                </div>
                <div className="col-span-1 flex justify-center">
                  <img className="h-8 sm-12 md:h-12" src="/images/onvif.png" alt="ONVIF" />
                </div>
                <div className="col-span-1 flex justify-center">
                  <img className="h-8 sm-12 md:h-12" src="/images/add.png" alt="Outros fabricantes" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Galeria / Casos de Uso */}
      <div className="bg-gray-100 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="lg:text-center">
            <h2 className="text-base text-blue-600 font-semibold tracking-wide uppercase">Galeria</h2>
            <p className="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-gray-900 sm:text-4xl">
              Casos de Uso
            </p>
            <p className="mt-4 max-w-2xl text-xl text-gray-600 lg:mx-auto">
              Conheça como o sistema Detec-o está sendo utilizado em diferentes cenários.
            </p>
          </div>

          <div className="mt-16 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {/* As imagens foram adicionadas pelo cliente */}
            <div className="relative h-64 rounded-lg overflow-hidden">
              <img src="/images/caso1.webp" alt="Caso 1" className="absolute inset-0 w-full h-full object-cover" />
              <p className="absolute bottom-0 left-0 bg-black top text-white bg-opacity-50 p-2">Prevenção de furtos</p>
            </div>
            <div className="relative h-64 rounded-lg overflow-hidden">
              <img src="/images/caso7.webp" alt="Caso" className="absolute inset-0 w-full h-full object-cover" />
              <p className="absolute bottom-0 left-0 bg-black text-white bg-opacity-50 p-2">Prevenção de atentados</p>
            </div>
            <div className="relative h-64 rounded-lg overflow-hidden">
              <img src="/images/caso7.jpg" alt="Caso 2" className="absolute inset-0 w-full h-full object-cover" />
              <p className="absolute bottom-0 left-0 bg-black text-white bg-opacity-50 p-2">Prevenção de afogamentos</p>
            </div>
            <div className="relative h-64 rounded-lg overflow-hidden">
              <img src="/images/caso2.webp" alt="Caso 3" className="absolute inset-0 w-full h-full object-cover" />
              <p className="absolute bottom-0 left-0 bg-black text-white bg-opacity-50 p-2">Notifação de encomendas</p>
            </div>
            <div className="relative h-64 rounded-lg overflow-hidden">
              <img src="/images/caso3.webp" alt="Caso 4" className="absolute inset-0 w-full h-full object-cover" />
              <p className="absolute bottom-0 left-0 bg-black text-white bg-opacity-50 p-2">Identificação de itens perdidos</p>
            </div>
            <div className="relative h-64 rounded-lg overflow-hidden">
              <img src="/images/caso4.webp" alt="Caso 5" className="absolute inset-0 w-full h-full object-cover" />
              <p className="absolute bottom-0 left-0 bg-black text-white bg-opacity-50 p-2">Monitoramento comportamental</p>
            </div>
            <div className="relative h-64 rounded-lg overflow-hidden">
              <img src="/images/caso5.webp" alt="Caso 6" className="absolute inset-0 w-full h-full object-cover" />
              <p className="absolute bottom-0 left-0 bg-black text-white bg-opacity-50 p-2">Vigilancias em aeroportos</p>
            </div>
            <div className="relative h-64 rounded-lg overflow-hidden">
              <img src="/images/caso6.webp" alt="Caso 7" className="absolute inset-0 w-full h-full object-cover" />
              <p className="absolute bottom-0 left-0 bg-black text-white bg-opacity-50 p-2">Identificação de buracos</p>
            </div>
          </div>
        </div>
      </div>

      {/* Contato/CTA Section */}
      <div id="contato" className="bg-blue-700">
        <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:py-16 lg:px-8 lg:flex lg:items-center lg:justify-between">
          <h2 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
            <span className="block">Pronto para melhorar sua segurança?</span>
            <span className="block text-blue-200">Entre em contato para um orçamento personalizado.</span>
          </h2>
          <div className="mt-8 flex lg:mt-0 lg:flex-shrink-0">
            <div className="inline-flex rounded-md shadow">
              <a
                href="#"
                className="inline-flex items-center justify-center px-5 py-3 border border-transparent text-base font-medium rounded-md text-blue-700 bg-white hover:bg-blue-50"
                onClick={(e) => {
                  e.preventDefault();
                  // Aqui poderia abrir um modal com formulário
                  alert('Em breve: formulário de contato para orçamento!');
                }}
              >
                Solicitar Orçamento
              </a>
            </div>
            <div className="ml-3 inline-flex rounded-md shadow">
              <a
                href="tel:+5547989279037"
                className="inline-flex items-center justify-center px-5 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-800 hover:bg-blue-900"
              >
                Fale Conosco
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-900">
        <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <h3 className="text-sm font-semibold text-gray-400 tracking-wider uppercase">Sobre a Empresa</h3>
              <p className="mt-4 text-base text-gray-300">
                A Detec-o é especializada em soluções de monitoramento inteligente, usando inteligência artificial para detecção automática de eventos relevantes.
              </p>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-400 tracking-wider uppercase">Contato</h3>
              <ul className="mt-4 space-y-4">
                <li>
                  <a href="mailto:contato@detec-o.com.br" className="text-base text-gray-300 hover:text-white">
                    contato@detec-o.com.br
                  </a>
                </li>
                <li>
                  <a href="tel:+551140028922" className="text-base text-gray-300 hover:text-white">
                    (47) 98927-9037
                  </a>
                </li>
                <li className="text-base text-gray-300">
                  Santa Catarina - SC, Brasil
                </li>
              </ul>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-400 tracking-wider uppercase">Legal</h3>
              <ul className="mt-4 space-y-4">
                <li>
                  <a href="#" className="text-base text-gray-300 hover:text-white">
                    Política de Privacidade
                  </a>
                </li>
                <li>
                  <a href="#" className="text-base text-gray-300 hover:text-white">
                    Termos de Uso
                  </a>
                </li>
              </ul>
            </div>
          </div>
          <div className="flex mt-8 justify-center">
          <Lottie 
            animationData={cameraAnimation} 
            style={{ width: 280, height: 120 }} 
            loop={true}
            autoplay={true}
          />
        </div>
          
          <div className="mt-8 border-t border-gray-800 pt-8">
            <p className="text-base text-gray-400 text-center">
              &copy; 2025 Detec-o. Todos os direitos reservados.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default LandingPage; 