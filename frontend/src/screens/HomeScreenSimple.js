import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import axios from 'axios';
import io from 'socket.io-client';
import CameraConfigScreen from './CameraConfigScreen';
import HVACConfigScreen from './HVACConfigScreen';
import { API_CONFIG, detectBackend } from '../utils/constants';

// IP de tu PC en la red local
// Cambia esto si tu IP cambia (ejecuta 'ipconfig' para verificar)
const API_BASE_URL = API_CONFIG.BASE_URL;

export default function HomeScreenSimple() {
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [backendUrl, setBackendUrl] = useState(API_BASE_URL);
  const [status, setStatus] = useState(null);
  const [frameData, setFrameData] = useState(null);
  const [showCameraConfig, setShowCameraConfig] = useState(false);
  const [showHvacConfig, setShowHvacConfig] = useState(false);
  const [actualFps, setActualFps] = useState(0);
  const [wsConnected, setWsConnected] = useState(false);
  const frameTimestamps = useRef([]);
  const lastFrameId = useRef(null);
  const socketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  useEffect(() => {
    const init = async () => {
      try {
        setLoading(true);
        const result = await detectBackend();
        if (result.success) {
          setBackendUrl(result.url);
        }
      } catch (error) {
        console.log('Error detectando backend:', error);
      } finally {
        await checkConnection();
        setLoading(false);
      }
    };

    init();

    const interval = setInterval(() => {
      checkConnection();
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  // WebSocket en tiempo real - Más eficiente y robusto
  useEffect(() => {
    if (!connected || !status?.camera_active) {
      // Desconectar WebSocket si no está activo
      if (socketRef.current) {
        console.log('� Desconectando WebSocket (cámara inactiva)');
        socketRef.current.disconnect();
        socketRef.current = null;
        setWsConnected(false);
      }
      return;
    }

    console.log('🚀 Iniciando conexión WebSocket en tiempo real');

    // Crear conexión WebSocket
    const wsUrl = (backendUrl || API_BASE_URL)
      .replace('http://', 'ws://')
      .replace('https://', 'wss://');

    const socket = io(wsUrl, {
      transports: ['websocket', 'polling'], // Probar websocket primero, luego polling
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5,
      timeout: 10000,
    });

    socketRef.current = socket;

    // Evento: Conectado
    socket.on('connect', () => {
      console.log('✅ WebSocket conectado - ID:', socket.id);
      setWsConnected(true);
    });

    // Evento: Frame update (tiempo real)
    socket.on('frame_update', (data) => {
      if (data && data.timestamp !== lastFrameId.current) {
        lastFrameId.current = data.timestamp;
        
        // Actualizar frameData de manera segura
        setFrameData(prevData => {
          // Liberar memoria del frame anterior
          if (prevData?.frame) {
            prevData.frame = null;
          }
          return data;
        });
        
        // Calcular FPS real del frontend
        const now = Date.now();
        frameTimestamps.current.push(now);
        
        // Mantener solo últimos 30 timestamps
        if (frameTimestamps.current.length > 30) {
          frameTimestamps.current.shift();
        }
        
        // Calcular FPS promedio
        if (frameTimestamps.current.length >= 2) {
          const timeDiff = (now - frameTimestamps.current[0]) / 1000;
          const fps = (frameTimestamps.current.length - 1) / timeDiff;
          setActualFps(fps);
        }
      }
    });

    // Evento: Desconectado
    socket.on('disconnect', (reason) => {
      console.log('❌ WebSocket desconectado:', reason);
      setWsConnected(false);
      
      // Si fue desconexión por el servidor, intentar reconectar
      if (reason === 'io server disconnect') {
        socket.connect();
      }
    });

    // Evento: Error de conexión
    socket.on('connect_error', (error) => {
      console.log('⚠️ Error de conexión WebSocket:', error.message);
      setWsConnected(false);
    });

    // Limpieza al desmontar
    return () => {
      console.log('🔌 Limpiando conexión WebSocket');
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      socket.disconnect();
      socketRef.current = null;
      frameTimestamps.current = [];
      setWsConnected(false);
    };
  }, [connected, status?.camera_active, backendUrl]);

  const checkConnection = async () => {
    try {
      const baseUrl = backendUrl || API_BASE_URL;
      const response = await axios.get(`${baseUrl}/api/status`, {
        timeout: 10000, // Aumentado a 10s para servidores ocupados
      });
      setStatus(response.data);
      setConnected(true);
      setLoading(false);
    } catch (error) {
      console.error('Error conectando:', error.message);
      // No mostrar error si es timeout (servidor ocupado procesando)
      if (error.code !== 'ECONNABORTED') {
        setConnected(false);
      }
      setLoading(false);
    }
  };

  const startCamera = async () => {
    try {
      const baseUrl = backendUrl || API_BASE_URL;
      await axios.post(`${baseUrl}/api/camera/start`);
      Alert.alert('✅ Éxito', 'Cámara iniciada. Los frames aparecerán en unos segundos.');
      checkConnection();
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'No se pudo iniciar la cámara';
      Alert.alert('❌ Error', errorMsg);
    }
  };

  const stopCamera = async () => {
    try {
      const baseUrl = backendUrl || API_BASE_URL;
      await axios.post(`${baseUrl}/api/camera/stop`);
      setFrameData(null); // Limpiar frame
      Alert.alert('✅ Éxito', 'Cámara detenida');
      checkConnection();
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'No se pudo detener la cámara';
      Alert.alert('❌ Error', errorMsg);
    }
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#3b82f6" />
        <Text style={styles.loadingText}>Conectando con el backend...</Text>
      </View>
    );
  }

  if (!connected) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorIcon}>⚠️</Text>
        <Text style={styles.errorTitle}>No se puede conectar</Text>
        <Text style={styles.errorText}>
          Verifica que el backend esté ejecutándose en:
        </Text>
        <Text style={styles.urlText}>{backendUrl || API_BASE_URL}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={checkConnection}>
          <Text style={styles.retryButtonText}>REINTENTAR</Text>
        </TouchableOpacity>
        <View style={styles.helpBox}>
          <Text style={styles.helpTitle}>💡 Solución:</Text>
          <Text style={styles.helpText}>
            1. Abre una terminal{'\n'}
            2. cd backend{'\n'}
            3. python app.py{'\n'}
            4. Verifica que tu celular y PC estén en la misma WiFi
          </Text>
        </View>
      </View>
    );
  }

  const currentCount =
    typeof frameData?.count === 'number'
      ? frameData.count
      : (typeof status?.current_count === 'number' ? status.current_count : 0);

  const maxCapacity =
    typeof frameData?.max_capacity === 'number'
      ? frameData.max_capacity
      : (typeof status?.max_capacity === 'number' ? status.max_capacity : 50);
  const percentage = (currentCount / maxCapacity) * 100;
  const isOverCapacity = currentCount > maxCapacity;
  const cameraActive = status?.camera_active || false;

  // Mostrar pantalla de configuración de cámara
  if (showCameraConfig) {
    return <CameraConfigScreen onBack={() => setShowCameraConfig(false)} />;
  }

  // Mostrar pantalla de configuración de HVAC
  if (showHvacConfig) {
    return <HVACConfigScreen onBack={() => setShowHvacConfig(false)} />;
  }

  return (
    <ScrollView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>🎥 Control de Aforo</Text>
        <View style={styles.statusContainer}>
          <View style={[styles.statusBadge, connected && styles.statusConnected]}>
            <Text style={styles.statusText}>
              {connected ? '🟢 API' : '🔴 API'}
            </Text>
          </View>
          <View style={[styles.statusBadge, wsConnected && styles.statusConnected]}>
            <Text style={styles.statusText}>
              {wsConnected ? '🟢 WS' : '🔴 WS'}
            </Text>
          </View>
        </View>
      </View>

      {/* Alert Banner */}
      {isOverCapacity && (
        <View style={styles.alertBanner}>
          <Text style={styles.alertText}>⚠️ ALERTA: AFORO EXCEDIDO</Text>
        </View>
      )}

      {/* Video Preview - WebSocket Tiempo Real */}
      <View style={styles.videoContainer}>
        {frameData && frameData.frame ? (
          <View style={styles.videoWrapper}>
            <Image
              source={{ 
                uri: `data:image/jpeg;base64,${frameData.frame}`,
                cache: 'reload' // Evitar caché para mejor rendimiento en tiempo real
              }}
              style={styles.videoImage}
              resizeMode="contain"
              fadeDuration={0} // Sin animación de fade para mejor FPS
            />
            <View style={styles.videoOverlay}>
              <View style={styles.detectionBadge}>
                <Text style={styles.detectionText}>
                  👤 {frameData.count || 0} personas
                </Text>
              </View>
              <View style={styles.fpsBadge}>
                <Text style={styles.fpsText}>
                  {actualFps > 0 ? actualFps.toFixed(1) : (frameData.fps?.toFixed(1) || '0')} FPS
                </Text>
              </View>
              {wsConnected && (
                <View style={styles.wsIndicator}>
                  <Text style={styles.wsText}>⚡ LIVE</Text>
                </View>
              )}
            </View>
          </View>
        ) : (
          <View style={styles.videoPlaceholder}>
            <Text style={styles.videoIcon}>📹</Text>
            <Text style={styles.videoText}>
              {cameraActive ? 'Esperando frames...' : 'Cámara Detenida'}
            </Text>
            {cameraActive && (
              <>
                <ActivityIndicator 
                  size="large" 
                  color="#3b82f6" 
                  style={{ marginTop: 10 }}
                />
                <Text style={styles.videoSubText}>
                  {wsConnected ? 'WebSocket conectado' : 'Conectando...'}
                </Text>
              </>
            )}
          </View>
        )}
      </View>

      {/* Camera Controls */}
      <View style={styles.controlsRow}>
        <TouchableOpacity
          style={[styles.button, cameraActive && styles.buttonDanger]}
          onPress={cameraActive ? stopCamera : startCamera}
        >
          <Text style={styles.buttonText}>
            {cameraActive ? '⏹️ DETENER CÁMARA' : '▶️ INICIAR CÁMARA'}
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={styles.configButton}
          onPress={() => setShowCameraConfig(true)}
        >
          <Text style={styles.buttonText}>⚙️ CONFIGURAR CÁMARA</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.configButton, { backgroundColor: '#10b981', marginTop: 10 }]}
          onPress={() => setShowHvacConfig(true)}
        >
          <Text style={styles.buttonText}>❄️ PANEL AIRE (HVAC)</Text>
        </TouchableOpacity>
      </View>

      {/* Occupancy Card */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>AFORO ACTUAL</Text>
        <View style={styles.countContainer}>
          <Text style={styles.countNumber}>{currentCount}</Text>
          <Text style={styles.countSeparator}>/</Text>
          <Text style={styles.countMax}>{maxCapacity}</Text>
        </View>
        
        {/* Progress Bar */}
        <View style={styles.progressBar}>
          <View
            style={[
              styles.progressFill,
              { width: `${Math.min(percentage, 100)}%` },
              isOverCapacity && styles.progressDanger,
            ]}
          />
        </View>
        <Text style={styles.percentageText}>{percentage.toFixed(0)}%</Text>
      </View>

      {/* Metrics Grid */}
      <View style={styles.metricsGrid}>
        <View style={styles.metricCard}>
          <Text style={styles.metricValue}>
            {actualFps > 0 ? actualFps.toFixed(1) : (status?.fps?.toFixed(1) || '0.0')}
          </Text>
          <Text style={styles.metricLabel}>FPS Real</Text>
        </View>
        
        <View style={styles.metricCard}>
          <Text style={styles.metricValue}>
            {status?.models_loaded || 0}/{status?.models_total || 4}
          </Text>
          <Text style={styles.metricLabel}>Modelos</Text>
        </View>

        <View style={styles.metricCard}>
          <Text style={styles.metricValue}>
            {status?.config?.ensemble_strategy || 'N/A'}
          </Text>
          <Text style={styles.metricLabel}>Estrategia</Text>
        </View>
      </View>

      {/* Info Card */}
      <View style={styles.infoCard}>
        <Text style={styles.infoTitle}>ℹ️ Estado del Sistema</Text>
        <Text style={styles.infoText}>
          • Backend: {connected ? 'Funcionando ✅' : 'Desconectado ❌'}
        </Text>
        <Text style={styles.infoText}>
          • Cámara: {cameraActive ? 'Activa ✅' : 'Detenida ⏸️'}
        </Text>
        <Text style={styles.infoText}>
          • Modelos cargados: {status?.models_loaded || 0}
        </Text>
        <Text style={styles.infoText}>
          • Umbral de confianza: {status?.config?.confidence_threshold || 0.5}
        </Text>
      </View>

      {/* Footer */}
      <View style={styles.footer}>
        <Text style={styles.footerText}>
          Sistema de Control de Aforo v1.0
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f3f4f6',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#f3f4f6',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#6b7280',
  },
  errorIcon: {
    fontSize: 64,
    marginBottom: 20,
  },
  errorTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 10,
  },
  errorText: {
    fontSize: 16,
    color: '#6b7280',
    textAlign: 'center',
    marginBottom: 10,
  },
  urlText: {
    fontSize: 14,
    color: '#3b82f6',
    fontWeight: 'bold',
    marginBottom: 20,
  },
  retryButton: {
    backgroundColor: '#3b82f6',
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 8,
    marginBottom: 30,
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  helpBox: {
    backgroundColor: '#fef3c7',
    padding: 20,
    borderRadius: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#f59e0b',
    maxWidth: 300,
  },
  helpTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  helpText: {
    fontSize: 14,
    lineHeight: 22,
  },
  header: {
    backgroundColor: '#3b82f6',
    padding: 20,
    paddingTop: 40,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  statusContainer: {
    flexDirection: 'row',
    gap: 8,
  },
  statusBadge: {
    backgroundColor: '#ef4444',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  statusConnected: {
    backgroundColor: '#10b981',
  },
  statusText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  alertBanner: {
    backgroundColor: '#ef4444',
    padding: 15,
    alignItems: 'center',
  },
  alertText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  videoContainer: {
    margin: 20,
    marginBottom: 10,
  },
  videoPlaceholder: {
    backgroundColor: '#1f2937',
    height: 250,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  videoIcon: {
    fontSize: 64,
    marginBottom: 10,
  },
  videoText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  videoSubText: {
    color: '#9ca3af',
    fontSize: 14,
    marginTop: 10,
    textAlign: 'center',
  },
  videoWrapper: {
    position: 'relative',
    height: 250,
    borderRadius: 12,
    overflow: 'hidden',
    backgroundColor: '#000',
  },
  videoImage: {
    width: '100%',
    height: '100%',
  },
  videoOverlay: {
    position: 'absolute',
    top: 10,
    left: 10,
    right: 10,
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  detectionBadge: {
    backgroundColor: 'rgba(59, 130, 246, 0.9)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  detectionText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  fpsBadge: {
    backgroundColor: 'rgba(16, 185, 129, 0.9)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  fpsText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  wsIndicator: {
    backgroundColor: 'rgba(239, 68, 68, 0.9)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  wsText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  videoSubText: {
    color: '#9ca3af',
    fontSize: 14,
    marginTop: 10,
    textAlign: 'center',
  },
  controlsRow: {
    marginHorizontal: 20,
    marginBottom: 20,
  },
  button: {
    backgroundColor: '#10b981',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 10,
  },
  buttonDanger: {
    backgroundColor: '#ef4444',
  },
  configButton: {
    backgroundColor: '#6366f1',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  card: {
    backgroundColor: '#fff',
    marginHorizontal: 20,
    marginBottom: 20,
    padding: 20,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#6b7280',
    marginBottom: 15,
    letterSpacing: 1,
  },
  countContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'baseline',
    marginBottom: 20,
  },
  countNumber: {
    fontSize: 64,
    fontWeight: 'bold',
    color: '#3b82f6',
  },
  countSeparator: {
    fontSize: 32,
    color: '#6b7280',
    marginHorizontal: 5,
  },
  countMax: {
    fontSize: 32,
    color: '#6b7280',
  },
  progressBar: {
    height: 16,
    backgroundColor: '#e5e7eb',
    borderRadius: 8,
    overflow: 'hidden',
    marginBottom: 10,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#3b82f6',
  },
  progressDanger: {
    backgroundColor: '#ef4444',
  },
  percentageText: {
    textAlign: 'center',
    fontSize: 14,
    color: '#6b7280',
  },
  metricsGrid: {
    flexDirection: 'row',
    marginHorizontal: 20,
    marginBottom: 20,
    gap: 10,
  },
  metricCard: {
    flex: 1,
    backgroundColor: '#fff',
    padding: 15,
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  metricValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#3b82f6',
    marginBottom: 5,
  },
  metricLabel: {
    fontSize: 12,
    color: '#6b7280',
  },
  infoCard: {
    backgroundColor: '#dbeafe',
    marginHorizontal: 20,
    marginBottom: 20,
    padding: 20,
    borderRadius: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#3b82f6',
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  infoText: {
    fontSize: 14,
    marginVertical: 3,
    lineHeight: 20,
  },
  footer: {
    padding: 20,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 12,
    color: '#6b7280',
  },
});
