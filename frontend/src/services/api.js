import axios from 'axios';
import { API_CONFIG, detectBackend } from '../utils/constants';

let currentBackendUrl = API_CONFIG.BASE_URL;
let retryCount = 0;

// Crear instancia de axios con configuración dinámica
const api = axios.create({
  timeout: API_CONFIG.TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para actualizar baseURL dinámicamente
api.interceptors.request.use(
  (config) => {
    config.baseURL = currentBackendUrl || API_CONFIG.BASE_URL;
    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor para manejar errores de conexión
api.interceptors.response.use(
  (response) => {
    // Resetear contador de reintentos en éxito
    retryCount = 0;
    return response;
  },
  async (error) => {
    // Si hay error de red, intentar reconectar
    if (!error.response && retryCount < API_CONFIG.MAX_RETRIES) {
      retryCount++;
      console.log(`⚠️ Error de conexión. Reintento ${retryCount}/${API_CONFIG.MAX_RETRIES}`);

      // Esperar antes de reintentar
      await new Promise(resolve => setTimeout(resolve, API_CONFIG.RETRY_INTERVAL));

      // Intentar detectar backend nuevamente
      const result = await detectBackend();
      if (result.success) {
        currentBackendUrl = result.url;
        API_CONFIG.BASE_URL = result.url;
        API_CONFIG.WS_URL = result.url.replace('http://', 'ws://').replace('https://', 'wss://');

        // Reintentar la petición original
        return api.request(error.config);
      }
    }

    return Promise.reject(error);
  }
);

// Función para inicializar la conexión
export const initializeConnection = async () => {
  console.log('🔍 Detectando backend disponible...');
  const result = await detectBackend();

  if (result.success) {
    currentBackendUrl = result.url;
    console.log(`✅ Conectado a backend: ${result.url}`);
    return true;
  } else {
    console.error('❌ No se pudo conectar a ningún backend');
    return false;
  }
};

// Servicios de la API
export const apiService = {
  // Obtener estado del sistema
  getStatus: async () => {
    try {
      const response = await api.get('/api/status');
      return response.data;
    } catch (error) {
      console.error('Error getting status:', error);
      throw error;
    }
  },

  // Obtener configuración
  getConfig: async () => {
    try {
      const response = await api.get('/api/config');
      return response.data;
    } catch (error) {
      console.error('Error getting config:', error);
      throw error;
    }
  },

  // Actualizar configuración
  updateConfig: async (config) => {
    try {
      const response = await api.post('/api/config', config);
      return response.data;
    } catch (error) {
      console.error('Error updating config:', error);
      throw error;
    }
  },

  // Obtener información de modelos
  getModels: async () => {
    try {
      const response = await api.get('/api/models');
      return response.data;
    } catch (error) {
      console.error('Error getting models:', error);
      throw error;
    }
  },

  // Iniciar cámara
  startCamera: async () => {
    try {
      const response = await api.post('/api/camera/start');
      return response.data;
    } catch (error) {
      console.error('Error starting camera:', error);
      throw error;
    }
  },

  // Detener cámara
  stopCamera: async () => {
    try {
      const response = await api.post('/api/camera/stop');
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Cambiar cámara
  changeCamera: async (source, type = 'webcam') => {
    try {
      const response = await api.post('/api/camera/change', { source, type });
      return response.data;
    } catch (error) {
      console.error('Error changing camera:', error);
      throw error;
    }
  },

  // Obtener historial
  getHistory: async (startDate = null, endDate = null) => {
    try {
      let url = '/api/history';
      if (startDate && endDate) {
        url += `?start=${startDate}&end=${endDate}`;
      }
      const response = await api.get(url);
      return response.data;
    } catch (error) {
      console.error('Error getting history:', error);
      throw error;
    }
  },
  // --- HVAC SERVICES ---
  
  getHvacStatus: async () => {
    try {
      const response = await api.get('/api/hvac/status');
      return response.data;
    } catch (error) {
      console.error('Error getting HVAC status:', error);
      throw error;
    }
  },

  getHvacBrands: async () => {
    try {
      const response = await api.get('/api/hvac/brands');
      return response.data;
    } catch (error) {
      console.error('Error getting HVAC brands:', error);
      throw error;
    }
  },

  getSerialPorts: async () => {
    try {
      const response = await api.get('/api/hvac/serial/ports');
      return response.data;
    } catch (error) {
      console.error('Error getting serial ports:', error);
      throw error;
    }
  },

  connectSerial: async (port, baudrate = 115200) => {
    try {
      const response = await api.post('/api/hvac/serial/connect', { port, baudrate });
      return response.data;
    } catch (error) {
      console.error('Error connecting serial:', error);
      throw error;
    }
  },

  disconnectSerial: async () => {
    try {
      const response = await api.post('/api/hvac/serial/disconnect');
      return response.data;
    } catch (error) {
      console.error('Error disconnecting serial:', error);
      throw error;
    }
  },

  sendHvacCommand: async (commandData) => {
    try {
      const response = await api.post('/api/hvac/command', commandData);
      return response.data;
    } catch (error) {
      console.error('Error sending HVAC command:', error);
      throw error;
    }
  },
};

export default api;
