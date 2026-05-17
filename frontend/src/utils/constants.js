// Configuración de conexión al backend
export const API_CONFIG = {
  // URLs de backend a intentar (orden de prioridad)
  BACKEND_URLS: [
    'http://192.168.18.5:5000',      // IP ACTUAL (Detectada)
    'http://10.0.2.2:5000',           // Android Emulator Host
    'http://localhost:5000',           // Localhost (misma máquina)
    'http://127.0.0.1:5000',          // IPv4 loopback
  ],

  // URL actual en uso (se establece dinámicamente)
  BASE_URL: 'http://192.168.18.5:5000',
  WS_URL: 'ws://192.168.18.5:5000',

  TIMEOUT: 10000, // 10 segundos (aumentado para conexiones más lentas)
  RETRY_INTERVAL: 3000, // Reintentar cada 3 segundos
  MAX_RETRIES: 10, // Máximo de reintentos antes de cambiar de URL
};

// Función para detectar el backend disponible
export const detectBackend = async () => {
  for (const url of API_CONFIG.BACKEND_URLS) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000); // Timeout más agresivo para detección rápida

      const response = await fetch(`${url}/api/status`, {
        method: 'GET',
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        console.log(`✅ Backend encontrado en: ${url}`);
        API_CONFIG.BASE_URL = url;
        API_CONFIG.WS_URL = url.replace('http://', 'ws://').replace('https://', 'wss://');
        return { success: true, url };
      }
    } catch (error) {
      console.log(`⚠️ No se pudo conectar a ${url}`);
    }
  }

  console.error('❌ No se encontró ningún backend disponible');
  return { success: false, url: null };
};

// Estrategias de ensemble disponibles
export const ENSEMBLE_STRATEGIES = [
  { label: 'Promedio', value: 'average', description: 'Promedia conteos de todos los modelos' },
  { label: 'Mayoría', value: 'majority', description: 'Usa el conteo más frecuente' },
  { label: 'Mejor Modelo', value: 'best', description: 'Usa solo el modelo con mayor mAP' },
  { label: 'Unión (NMS)', value: 'union', description: 'Une todas las detecciones con NMS' },
];

// Rangos de tiempo para historial
export const TIME_RANGES = [
  { label: 'Hoy', value: 'today' },
  { label: 'Esta Semana', value: 'week' },
  { label: 'Este Mes', value: 'month' },
];

// Colores del tema
export const COLORS = {
  primary: '#3b82f6',
  secondary: '#8b5cf6',
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  background: '#f3f4f6',
  card: '#ffffff',
  text: '#1f2937',
  textLight: '#6b7280',
  border: '#e5e7eb',
};

// Configuración por defecto
export const DEFAULT_CONFIG = {
  max_capacity: 50,
  ensemble_strategy: 'average',
  confidence_threshold: 0.5,
  enable_privacy: true,
};
