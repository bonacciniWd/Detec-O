/**
 * Mock API para desenvolvimento
 * Simula os endpoints da API para permitir o desenvolvimento da interface
 * sem depender de um backend funcional
 */

// URLs de imagens públicas para preview de câmeras
const cameraPreviewUrls = [
  'https://images.unsplash.com/photo-1506764084-c71deb15aed1?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80', // Câmera de rua
  'https://images.unsplash.com/photo-1495527400402-03a85d6357c1?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80', // Estacionamento
  'https://images.unsplash.com/photo-1535079805273-14ad38fb871f?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80', // Escritório
  'https://images.unsplash.com/photo-1520483601560-389dff434fdf?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80', // Hall de entrada
  'https://images.unsplash.com/photo-1565330520318-f4534005c18d?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80'  // Recepção
];

// Armazenamento local para dados simulados
const mockStorage = {
  detectionSettings: {},
  detectionZones: {}
};

/**
 * Gera um ID aleatório para uso em objetos simulados
 */
const generateId = () => {
  return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
};

/**
 * Simula um atraso de rede para tornar o mock mais realista
 */
const delay = (ms = 300) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Cliente de API simulada
 */
const mockApiClient = {
  // Método para obter a URL base
  getBaseUrl: () => {
    return '/api';
  },
  
  // Obter configurações de detecção para uma câmera
  getDetectionSettings: async (cameraId) => {
    await delay();
    
    // Verificar se já existe configuração para esta câmera
    if (!mockStorage.detectionSettings[cameraId]) {
      // Criar configurações padrão
      mockStorage.detectionSettings[cameraId] = {
        confidenceThreshold: 0.6,
        sensitivity: 0.5,
        minDetectionInterval: 2,
        detectionClasses: ['person', 'car', 'animal'],
        saveAllFrames: false,
        notifyOnDetection: true,
        notificationChannels: ['email'],
        detectionZones: []
      };
    }
    
    return mockStorage.detectionSettings[cameraId];
  },
  
  // Salvar configurações de detecção para uma câmera
  saveDetectionSettings: async (cameraId, settings) => {
    await delay();
    
    // Armazenar as configurações
    mockStorage.detectionSettings[cameraId] = {
      ...mockStorage.detectionSettings[cameraId],
      ...settings
    };
    
    console.log('Configurações salvas:', mockStorage.detectionSettings[cameraId]);
    
    return mockStorage.detectionSettings[cameraId];
  },
  
  // Obter URL de preview para uma câmera
  getCameraPreview: (cameraId) => {
    // Usar hash do ID da câmera para selecionar uma imagem consistente
    const hash = cameraId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    const index = hash % cameraPreviewUrls.length;
    return cameraPreviewUrls[index];
  },
  
  // Obter todas as zonas de detecção de uma câmera
  getDetectionZones: async (cameraId) => {
    await delay();
    
    // Verificar se já existem zonas para esta câmera
    if (!mockStorage.detectionZones[cameraId]) {
      mockStorage.detectionZones[cameraId] = [];
    }
    
    return mockStorage.detectionZones[cameraId];
  },
  
  // Adicionar uma nova zona de detecção
  addDetectionZone: async (cameraId, zone) => {
    await delay();
    
    // Verificar se já existem zonas para esta câmera
    if (!mockStorage.detectionZones[cameraId]) {
      mockStorage.detectionZones[cameraId] = [];
    }
    
    // Adicionar ID se não foi fornecido
    if (!zone.id) {
      zone.id = generateId();
    }
    
    // Adicionar a zona
    mockStorage.detectionZones[cameraId].push(zone);
    
    // Atualizar a lista de zonas nas configurações
    if (mockStorage.detectionSettings[cameraId]) {
      mockStorage.detectionSettings[cameraId].detectionZones = mockStorage.detectionZones[cameraId];
    }
    
    return zone;
  },
  
  // Atualizar uma zona de detecção existente
  updateDetectionZone: async (cameraId, zoneId, zone) => {
    await delay();
    
    // Verificar se já existem zonas para esta câmera
    if (!mockStorage.detectionZones[cameraId]) {
      throw new Error('Zona de detecção não encontrada');
    }
    
    // Encontrar a zona a ser atualizada
    const index = mockStorage.detectionZones[cameraId].findIndex(z => z.id === zoneId);
    if (index === -1) {
      throw new Error('Zona de detecção não encontrada');
    }
    
    // Atualizar a zona
    mockStorage.detectionZones[cameraId][index] = {
      ...mockStorage.detectionZones[cameraId][index],
      ...zone
    };
    
    // Atualizar a lista de zonas nas configurações
    if (mockStorage.detectionSettings[cameraId]) {
      mockStorage.detectionSettings[cameraId].detectionZones = mockStorage.detectionZones[cameraId];
    }
    
    return mockStorage.detectionZones[cameraId][index];
  },
  
  // Excluir uma zona de detecção
  deleteDetectionZone: async (cameraId, zoneId) => {
    await delay();
    
    // Verificar se já existem zonas para esta câmera
    if (!mockStorage.detectionZones[cameraId]) {
      throw new Error('Zona de detecção não encontrada');
    }
    
    // Filtrar a zona a ser excluída
    const filteredZones = mockStorage.detectionZones[cameraId].filter(z => z.id !== zoneId);
    
    // Verificar se alguma zona foi removida
    if (filteredZones.length === mockStorage.detectionZones[cameraId].length) {
      throw new Error('Zona de detecção não encontrada');
    }
    
    // Atualizar a lista de zonas
    mockStorage.detectionZones[cameraId] = filteredZones;
    
    // Atualizar a lista de zonas nas configurações
    if (mockStorage.detectionSettings[cameraId]) {
      mockStorage.detectionSettings[cameraId].detectionZones = mockStorage.detectionZones[cameraId];
    }
    
    return { message: 'Zona de detecção removida com sucesso' };
  },
  
  // Exportar zonas de detecção
  exportDetectionZones: async (cameraId) => {
    await delay();
    
    return {
      camera_id: cameraId,
      detection_zones: mockStorage.detectionZones[cameraId] || [],
      ignore_areas: [],
      exported_at: new Date().toISOString()
    };
  },
  
  // Importar zonas de detecção
  importDetectionZones: async (cameraId, zonesData) => {
    await delay();
    
    // Validar os dados
    if (!zonesData.detection_zones) {
      throw new Error('Formato de importação inválido');
    }
    
    // Atualizar as zonas
    mockStorage.detectionZones[cameraId] = zonesData.detection_zones;
    
    // Atualizar a lista de zonas nas configurações
    if (mockStorage.detectionSettings[cameraId]) {
      mockStorage.detectionSettings[cameraId].detectionZones = mockStorage.detectionZones[cameraId];
    }
    
    return {
      message: 'Zonas de detecção importadas com sucesso',
      detection_zones_count: zonesData.detection_zones.length,
      ignore_areas_count: (zonesData.ignore_areas || []).length
    };
  }
};

export default mockApiClient; 