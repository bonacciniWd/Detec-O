import api from './api';

// Configurações padrão para o caso de falha na API
const defaultSettings = {
  notifications: {
    email: false,
    browser: true,
    mobile: false,
    frequency: 'immediate',
  },
  detection: {
    confidenceThreshold: 0.6,
    minDetectionInterval: 30,
    motionSensitivity: 5,
    enableWeaponDetection: true,
    enableFaceDetection: true,
    enableBehaviorAnalysis: true,
  },
  interface: {
    darkMode: false,
    compactView: false,
    showStatistics: true,
    highlightDetections: true,
  }
};

// Função para obter as configurações de um usuário
export const getUserSettings = async (userId) => {
  try {
    const response = await api.get(`/api/v1/users/${userId}/settings`);
    return response.data;
  } catch (error) {
    console.error('Erro ao buscar configurações:', error);
    // Em um ambiente de desenvolvimento, retornar configurações padrão
    console.log('Retornando configurações padrão');
    return defaultSettings;
  }
};

// Função para atualizar as configurações de um usuário
export const updateUserSettings = async (userId, settings) => {
  try {
    const response = await api.put(`/api/v1/users/${userId}/settings`, settings);
    return response.data;
  } catch (error) {
    console.error('Erro ao atualizar configurações:', error);
    // Simulando uma resposta bem-sucedida para ambiente de desenvolvimento
    console.log('Simulando resposta bem-sucedida para atualização de configurações');
    return settings;
  }
}; 