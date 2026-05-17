import io from 'socket.io-client';
import { API_CONFIG, detectBackend } from '../utils/constants';

class WebSocketService {
  constructor() {
    this.socket = null;
    this.connected = false;
    this.listeners = {};
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 15;
    this.currentUrl = null;
    this.heartbeatInterval = null;
    this.isProcessingFrame = false; // Flag para evitar acumulación de frames
    this.lastFrameTime = 0;
  }

  // Conectar al servidor WebSocket con detección automática
  async connect() {
    if (this.socket && this.connected) {
      console.log('✅ WebSocket ya conectado');
      return;
    }

    // Detectar backend disponible si no tenemos URL
    if (!this.currentUrl || !API_CONFIG.WS_URL) {
      console.log('🔍 Detectando backend para WebSocket...');
      const result = await detectBackend();
      if (result.success) {
        this.currentUrl = API_CONFIG.WS_URL;
      } else {
        console.error('❌ No se pudo detectar backend para WebSocket');
        this.emit('connection_status', { connected: false, error: 'Backend no disponible' });
        return;
      }
    }

    console.log(`🔌 Conectando WebSocket a: ${this.currentUrl}`);

    this.socket = io(this.currentUrl, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 2000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: this.maxReconnectAttempts,
      timeout: 10000,
      autoConnect: true,
    });

    this.socket.on('connect', () => {
      console.log('✅ WebSocket conectado');
      this.connected = true;
      this.reconnectAttempts = 0;
      this.emit('connection_status', { connected: true });
      
      // Iniciar heartbeat para detectar desconexiones
      this.startHeartbeat();
    });

    this.socket.on('disconnect', (reason) => {
      console.log(`⚠️ WebSocket desconectado: ${reason}`);
      this.connected = false;
      this.stopHeartbeat();
      this.emit('connection_status', { connected: false, reason });
      
      // Si la desconexión fue por cambio de red, intentar reconectar
      if (reason === 'transport close' || reason === 'ping timeout') {
        this.attemptReconnect();
      }
    });

    this.socket.on('reconnect_attempt', (attemptNumber) => {
      console.log(`🔄 Intento de reconexión #${attemptNumber}`);
      this.reconnectAttempts = attemptNumber;
    });

    this.socket.on('reconnect', (attemptNumber) => {
      console.log(`✅ WebSocket reconectado después de ${attemptNumber} intentos`);
      this.reconnectAttempts = 0;
    });

    this.socket.on('reconnect_failed', async () => {
      console.error('❌ Reconexión de WebSocket falló');
      this.connected = false;
      
      // Intentar detectar backend en otra URL
      await this.attemptReconnect();
    });

    this.socket.on('error', (error) => {
      console.error('❌ WebSocket error:', error);
      this.emit('error', error);
    });

    // Escuchar actualizaciones de frames con throttling
    this.socket.on('frame_update', (data) => {
      const now = Date.now();
      const timeSinceLastFrame = now - this.lastFrameTime;

      // Throttle a 25 FPS (~40ms por frame) para estabilidad en móviles
      if (timeSinceLastFrame < 40) {
        return;
      }

      this.lastFrameTime = now;
      this.emit('frame_update', data);
    });
  }

  // Desconectar del servidor
  disconnect() {
    this.stopHeartbeat();
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.connected = false;
    }
  }

  // Iniciar heartbeat para detectar conexión activa
  startHeartbeat() {
    this.stopHeartbeat(); // Limpiar cualquier heartbeat previo
    
    this.heartbeatInterval = setInterval(() => {
      if (this.socket && this.connected) {
        this.socket.emit('ping');
      }
    }, 5000); // Cada 5 segundos
  }

  // Detener heartbeat
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  // Intentar reconectar con detección de backend
  async attemptReconnect() {
    console.log('🔄 Intentando reconexión con detección de backend...');
    
    // Desconectar socket actual
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    
    // Detectar backend disponible
    const result = await detectBackend();
    
    if (result.success && API_CONFIG.WS_URL !== this.currentUrl) {
      console.log(`🔄 Backend encontrado en nueva URL: ${API_CONFIG.WS_URL}`);
      this.currentUrl = API_CONFIG.WS_URL;
      
      // Esperar un poco antes de reconectar
      setTimeout(() => {
        this.connect();
      }, 1000);
    } else if (result.success) {
      // Reconectar a la misma URL
      setTimeout(() => {
        this.connect();
      }, 2000);
    } else {
      console.error('❌ No se encontró backend disponible');
      this.emit('connection_status', { connected: false, error: 'Backend no disponible' });
    }
  }

  // Forzar reconexión manual
  forceReconnect() {
    console.log('🔄 Forzando reconexión...');
    this.disconnect();
    setTimeout(() => this.connect(), 500);
  }

  // Registrar listener para eventos
  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  // Eliminar listener
  off(event, callback) {
    if (!this.listeners[event]) return;
    
    this.listeners[event] = this.listeners[event].filter(
      listener => listener !== callback
    );
  }

  // Emitir evento a todos los listeners
  emit(event, data) {
    if (!this.listeners[event]) return;
    
    this.listeners[event].forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error(`Error in listener for ${event}:`, error);
      }
    });
  }

  // Verificar si está conectado
  isConnected() {
    return this.connected;
  }
}

// Exportar instancia singleton
const wsService = new WebSocketService();
export default wsService;
