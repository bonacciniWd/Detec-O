import React, { useState, useEffect } from 'react';
import { FiSettings, FiBell, FiSliders, FiMonitor, FiSave, FiUser } from 'react-icons/fi';
import { toast } from 'react-toastify';
import { getUserSettings, updateUserSettings } from '../services/settingsService';
import { useAuth } from '../contexts/AuthContext';
import LoadingSpinner from '../components/LoadingSpinner';

const SettingsPage = () => {
  // Salvamos o resultado completo do hook useAuth para evitar problemas de desestruturação
  const authContext = useAuth();
  // Obtemos user somente quando precisamos e com verificação de null
  const user = authContext?.user;
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [settings, setSettings] = useState({
    user: {
      name: '',
      email: '',
      password: '',
      newPassword: '',
      confirmPassword: '',
    },
    notifications: {
      email: false,
      browser: true,
      mobile: false,
      frequency: 'immediate', // immediate, hourly, daily
    },
    detection: {
      confidenceThreshold: 0.6,
      minDetectionInterval: 30, // seconds
      motionSensitivity: 5, // scale 1-10
      enableWeaponDetection: true,
      enableFaceDetection: true,
      enableBehaviorAnalysis: true,
    },
    interface: {
      darkMode: true,
      compactView: false,
      showStatistics: true,
      highlightDetections: true,
    }
  });

  // Inicializar as configurações quando o usuário estiver disponível
  useEffect(() => {
    const fetchSettings = async () => {
      try {
        setLoading(true);
        // Verificar se o usuário existe antes de tentar obter as configurações
        if (!user || !user.id) {
          console.warn('User not available yet, using default settings');
          // Atualizamos os dados do usuário nas configurações aqui também
          setSettings(prevSettings => ({
            ...prevSettings,
            user: {
              ...prevSettings.user,
              name: '',
              email: ''
            }
          }));
          setLoading(false);
          return;
        }

        const data = await getUserSettings(user.id);
        if (data) {
          // Preencher as informações do usuário com verificação de null/undefined
          const updatedSettings = {
            ...data,
            user: {
              name: user?.name || '',
              email: user?.email || '',
              password: '',
              newPassword: '',
              confirmPassword: '',
            }
          };
          setSettings(updatedSettings);
        }
      } catch (error) {
        console.error('Error fetching settings:', error);
        toast.error('Não foi possível carregar as configurações');
      } finally {
        setLoading(false);
      }
    };

    // Iniciar carregamento das configurações
    fetchSettings();
  }, [user]);

  const handleSaveSettings = async () => {
    try {
      // Verificar se o usuário existe
      if (!user || !user.id) {
        toast.error('Usuário não autenticado. Faça login novamente.');
        return;
      }

      // Validar nova senha, se fornecida
      if (settings.user.newPassword) {
        if (settings.user.newPassword !== settings.user.confirmPassword) {
          toast.error('As senhas não coincidem');
          return;
        }
        if (settings.user.newPassword.length < 6) {
          toast.error('A nova senha deve ter pelo menos 6 caracteres');
          return;
        }
      }

      setSaving(true);
      
      // Remover informações sensíveis antes de enviar
      const settingsToSave = {
        ...settings,
        user: undefined // Não salvar informações do usuário aqui
      };
      
      await updateUserSettings(user.id, settingsToSave);
      toast.success('Configurações salvas com sucesso!');
    } catch (error) {
      console.error('Error saving settings:', error);
      toast.error('Erro ao salvar configurações');
    } finally {
      setSaving(false);
    }
  };

  const handleUserInfoChange = (field, value) => {
    setSettings(prev => ({
      ...prev,
      user: {
        ...prev.user,
        [field]: value
      }
    }));
  };

  const handleNotificationChange = (field, value) => {
    setSettings(prev => ({
      ...prev,
      notifications: {
        ...prev.notifications,
        [field]: value
      }
    }));
  };

  const handleDetectionChange = (field, value) => {
    setSettings(prev => ({
      ...prev,
      detection: {
        ...prev.detection,
        [field]: value
      }
    }));
  };

  const handleInterfaceChange = (field, value) => {
    setSettings(prev => ({
      ...prev,
      interface: {
        ...prev.interface,
        [field]: value
      }
    }));
  };

  // Mostrar carregamento
  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen bg-gray-900">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  // Mostrar mensagem se não houver usuário
  if (!user) {
    return (
      <div className="flex flex-col justify-center items-center h-screen bg-gray-900 text-white">
        <div className="text-xl mb-4">Usuário não autenticado</div>
        <p className="text-gray-400">Faça login para acessar as configurações</p>
      </div>
    );
  }

  // Classes reutilizáveis para tema escuro
  const cardClass = "bg-gray-800 rounded-lg shadow-md p-6 mb-6";
  const headerClass = "flex items-center mb-4";
  const iconClass = "text-blue-500 text-xl mr-2";
  const titleClass = "text-xl font-semibold text-white";
  const sectionTitleClass = "font-medium mb-3 text-gray-300";
  const labelClass = "text-gray-300";
  const inputClass = "mt-1 block w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500";
  const checkboxClass = "mr-2 h-4 w-4 rounded bg-gray-700 border-gray-500 text-blue-500 focus:ring-blue-500";
  const sliderClass = "w-full h-4 bg-gray-700 rounded-md mt-2 accent-blue-500";
  const helpTextClass = "text-sm text-gray-400 mt-2";

  try {
    // Renderização do componente com verificações de segurança adicionais
    return (
      <div className="bg-gray-900 min-h-screen pb-8">
        <div className="container mx-auto py-8 px-4">
          <div className="flex items-center mb-8">
            <FiSettings className="text-blue-500 text-3xl mr-3" />
            <h1 className="text-2xl font-bold text-white">Configurações</h1>
          </div>

          {/* Seção de Perfil do Usuário */}
          <div className={cardClass}>
            <div className={headerClass}>
              <FiUser className={iconClass} />
              <h2 className={titleClass}>Perfil do Usuário</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className={sectionTitleClass}>Informações Pessoais</h3>
                <div className="space-y-4">
                  <div>
                    <label htmlFor="userName" className={labelClass}>Nome</label>
                    <input
                      type="text"
                      id="userName"
                      value={settings?.user?.name || ''}
                      onChange={(e) => handleUserInfoChange('name', e.target.value)}
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label htmlFor="userEmail" className={labelClass}>Email</label>
                    <input
                      type="email"
                      id="userEmail"
                      value={settings?.user?.email || ''}
                      onChange={(e) => handleUserInfoChange('email', e.target.value)}
                      className={inputClass}
                    />
                  </div>
                </div>
              </div>
              
              <div>
                <h3 className={sectionTitleClass}>Alterar Senha</h3>
                <div className="space-y-4">
                  <div>
                    <label htmlFor="currentPassword" className={labelClass}>Senha Atual</label>
                    <input
                      type="password"
                      id="currentPassword"
                      value={settings?.user?.password || ''}
                      onChange={(e) => handleUserInfoChange('password', e.target.value)}
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label htmlFor="newPassword" className={labelClass}>Nova Senha</label>
                    <input
                      type="password"
                      id="newPassword"
                      value={settings?.user?.newPassword || ''}
                      onChange={(e) => handleUserInfoChange('newPassword', e.target.value)}
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label htmlFor="confirmPassword" className={labelClass}>Confirmar Nova Senha</label>
                    <input
                      type="password"
                      id="confirmPassword"
                      value={settings?.user?.confirmPassword || ''}
                      onChange={(e) => handleUserInfoChange('confirmPassword', e.target.value)}
                      className={inputClass}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Seção de Notificações */}
          <div className={cardClass}>
            <div className={headerClass}>
              <FiBell className={iconClass} />
              <h2 className={titleClass}>Notificações</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className={sectionTitleClass}>Canais de Notificação</h3>
                <div className="space-y-3">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="emailNotif"
                      checked={settings?.notifications?.email || false}
                      onChange={(e) => handleNotificationChange('email', e.target.checked)}
                      className={checkboxClass}
                    />
                    <label htmlFor="emailNotif" className={labelClass}>Notificações por Email</label>
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="browserNotif"
                      checked={settings?.notifications?.browser || false}
                      onChange={(e) => handleNotificationChange('browser', e.target.checked)}
                      className={checkboxClass}
                    />
                    <label htmlFor="browserNotif" className={labelClass}>Notificações no Navegador</label>
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="mobileNotif"
                      checked={settings?.notifications?.mobile || false}
                      onChange={(e) => handleNotificationChange('mobile', e.target.checked)}
                      className={checkboxClass}
                    />
                    <label htmlFor="mobileNotif" className={labelClass}>Notificações no Celular</label>
                  </div>
                </div>
              </div>
              
              <div>
                <h3 className={sectionTitleClass}>Frequência de Notificações</h3>
                <div className="space-y-3">
                  <div className="flex items-center">
                    <input
                      type="radio"
                      id="freqImmediate"
                      name="frequency"
                      value="immediate"
                      checked={settings?.notifications?.frequency === 'immediate'}
                      onChange={() => handleNotificationChange('frequency', 'immediate')}
                      className={checkboxClass}
                    />
                    <label htmlFor="freqImmediate" className={labelClass}>Imediata</label>
                  </div>
                  <div className="flex items-center">
                    <input
                      type="radio"
                      id="freqHourly"
                      name="frequency"
                      value="hourly"
                      checked={settings?.notifications?.frequency === 'hourly'}
                      onChange={() => handleNotificationChange('frequency', 'hourly')}
                      className={checkboxClass}
                    />
                    <label htmlFor="freqHourly" className={labelClass}>Resumo Horário</label>
                  </div>
                  <div className="flex items-center">
                    <input
                      type="radio"
                      id="freqDaily"
                      name="frequency"
                      value="daily"
                      checked={settings?.notifications?.frequency === 'daily'}
                      onChange={() => handleNotificationChange('frequency', 'daily')}
                      className={checkboxClass}
                    />
                    <label htmlFor="freqDaily" className={labelClass}>Resumo Diário</label>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Seção de Detecção */}
          <div className={cardClass}>
            <div className={headerClass}>
              <FiSliders className={iconClass} />
              <h2 className={titleClass}>Parâmetros de Detecção</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className={sectionTitleClass}>Limiar de Confiança ({Math.round((settings?.detection?.confidenceThreshold || 0.6) * 100)}%)</h3>
                <input
                  type="range"
                  min="0.1"
                  max="0.9"
                  step="0.05"
                  value={settings?.detection?.confidenceThreshold || 0.6}
                  onChange={(e) => handleDetectionChange('confidenceThreshold', parseFloat(e.target.value))}
                  className={sliderClass}
                  style={{
                    background: `linear-gradient(to right, #3B82F6 0%, #3B82F6 ${(settings?.detection?.confidenceThreshold || 0.6) * 100}%, #374151 ${(settings?.detection?.confidenceThreshold || 0.6) * 100}%, #374151 100%)`
                  }}
                />
                <p className={helpTextClass}>Ajuste o nível de confiança necessário para considerar uma detecção válida</p>
              </div>
              
              <div>
                <h3 className={sectionTitleClass}>Intervalo Entre Detecções ({settings?.detection?.minDetectionInterval || 30}s)</h3>
                <input
                  type="range"
                  min="5"
                  max="300"
                  step="5"
                  value={settings?.detection?.minDetectionInterval || 30}
                  onChange={(e) => handleDetectionChange('minDetectionInterval', parseInt(e.target.value))}
                  className={sliderClass}
                  style={{
                    background: `linear-gradient(to right, #3B82F6 0%, #3B82F6 ${((settings?.detection?.minDetectionInterval || 30) - 5) / 295 * 100}%, #374151 ${((settings?.detection?.minDetectionInterval || 30) - 5) / 295 * 100}%, #374151 100%)`
                  }}
                />
                <p className={helpTextClass}>Tempo mínimo entre notificações para o mesmo tipo de evento</p>
              </div>
              
              <div>
                <h3 className={sectionTitleClass}>Sensibilidade ao Movimento ({settings?.detection?.motionSensitivity || 5}/10)</h3>
                <input
                  type="range"
                  min="1"
                  max="10"
                  step="1"
                  value={settings?.detection?.motionSensitivity || 5}
                  onChange={(e) => handleDetectionChange('motionSensitivity', parseInt(e.target.value))}
                  className={sliderClass}
                  style={{
                    background: `linear-gradient(to right, #3B82F6 0%, #3B82F6 ${((settings?.detection?.motionSensitivity || 5) - 1) / 9 * 100}%, #374151 ${((settings?.detection?.motionSensitivity || 5) - 1) / 9 * 100}%, #374151 100%)`
                  }}
                />
                <p className={helpTextClass}>Ajuste o nível de sensibilidade para detecção de movimento</p>
              </div>
              
              <div>
                <h3 className={sectionTitleClass}>Habilitar Detecções</h3>
                <div className="space-y-3 mt-2">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="weaponDetection"
                      checked={settings?.detection?.enableWeaponDetection || false}
                      onChange={(e) => handleDetectionChange('enableWeaponDetection', e.target.checked)}
                      className={checkboxClass}
                    />
                    <label htmlFor="weaponDetection" className={labelClass}>Detecção de Armas</label>
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="faceDetection"
                      checked={settings?.detection?.enableFaceDetection || false}
                      onChange={(e) => handleDetectionChange('enableFaceDetection', e.target.checked)}
                      className={checkboxClass}
                    />
                    <label htmlFor="faceDetection" className={labelClass}>Reconhecimento Facial</label>
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="behaviorAnalysis"
                      checked={settings?.detection?.enableBehaviorAnalysis || false}
                      onChange={(e) => handleDetectionChange('enableBehaviorAnalysis', e.target.checked)}
                      className={checkboxClass}
                    />
                    <label htmlFor="behaviorAnalysis" className={labelClass}>Análise de Comportamento</label>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Seção de Interface */}
          <div className={cardClass}>
            <div className={headerClass}>
              <FiMonitor className={iconClass} />
              <h2 className={titleClass}>Personalização da Interface</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className={sectionTitleClass}>Aparência</h3>
                <div className="space-y-3">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="darkMode"
                      checked={settings?.interface?.darkMode || false}
                      onChange={(e) => handleInterfaceChange('darkMode', e.target.checked)}
                      className={checkboxClass}
                    />
                    <label htmlFor="darkMode" className={labelClass}>Modo Escuro</label>
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="compactView"
                      checked={settings?.interface?.compactView || false}
                      onChange={(e) => handleInterfaceChange('compactView', e.target.checked)}
                      className={checkboxClass}
                    />
                    <label htmlFor="compactView" className={labelClass}>Visualização Compacta</label>
                  </div>
                </div>
              </div>
              
              <div>
                <h3 className={sectionTitleClass}>Exibição</h3>
                <div className="space-y-3">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="showStatistics"
                      checked={settings?.interface?.showStatistics || false}
                      onChange={(e) => handleInterfaceChange('showStatistics', e.target.checked)}
                      className={checkboxClass}
                    />
                    <label htmlFor="showStatistics" className={labelClass}>Mostrar Estatísticas</label>
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="highlightDetections"
                      checked={settings?.interface?.highlightDetections || false}
                      onChange={(e) => handleInterfaceChange('highlightDetections', e.target.checked)}
                      className={checkboxClass}
                    />
                    <label htmlFor="highlightDetections" className={labelClass}>Destacar Detecções</label>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              onClick={handleSaveSettings}
              disabled={saving}
              className="flex items-center bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 transition-colors"
            >
              {saving ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  <span>Salvando...</span>
                </>
              ) : (
                <>
                  <FiSave className="mr-2" />
                  <span>Salvar Configurações</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    );
  } catch (error) {
    // Tratamento de erro de renderização
    console.error('Error rendering settings page:', error);
    return (
      <div className="flex flex-col justify-center items-center h-screen bg-gray-900 text-white">
        <div className="text-xl mb-4">Erro ao carregar configurações</div>
        <p className="text-gray-400">{error.message || 'Ocorreu um erro desconhecido'}</p>
      </div>
    );
  }
};

export default SettingsPage; 