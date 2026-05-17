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
  Animated,
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

  // Pulse animation for offline video feed
  const placeholderPulse = useRef(new Animated.Value(0.9)).current;
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(placeholderPulse, {
          toValue: 1.15,
          duration: 1800,
          useNativeDriver: true,
        }),
        Animated.timing(placeholderPulse, {
          toValue: 0.9,
          duration: 1800,
          useNativeDriver: true,
        }),
      ])
    ).start();
  }, []);

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
        <ActivityIndicator size="large" color="#00E5FF" />
        <Text style={styles.loadingText}>Sincronizando con el Núcleo IA...</Text>
      </View>
    );
  }

  if (!connected) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorIcon}>📡</Text>
        <Text style={styles.errorTitle}>Enlace Fuera de Línea</Text>
        <Text style={styles.errorText}>
          No se detecta conexión con el servidor IA en la dirección:
        </Text>
        <Text style={styles.urlText}>{backendUrl || API_BASE_URL}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={checkConnection}>
          <Text style={styles.retryButtonText}>REINTENTAR ENLACE</Text>
        </TouchableOpacity>
        <View style={styles.helpBox}>
          <Text style={styles.helpTitle}>💡 Diagnóstico de Red:</Text>
          <Text style={styles.helpText}>
            1. Abre una terminal en tu PC.{'\n'}
            2. Ejecuta: <Text style={{ fontFamily: 'monospace', color: '#00E5FF' }}>cd backend && python app.py</Text>{'\n'}
            3. Asegúrate de que el celular y la PC compartan la misma red WiFi.
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
    <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 40 }}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.headerSubtitle}>SISTEMA DE SEGURIDAD</Text>
          <Text style={styles.title}>🤖 Aforo Inteligente</Text>
        </View>
        <View style={styles.statusContainer}>
          <View style={[styles.statusBadge, connected ? styles.statusConnected : styles.statusDisconnected]}>
            <Text style={styles.statusText}>
              {connected ? '● API OK' : '○ API ERR'}
            </Text>
          </View>
          <View style={[styles.statusBadge, wsConnected ? styles.statusConnected : styles.statusDisconnected]}>
            <Text style={styles.statusText}>
              {wsConnected ? '● LIVE' : '○ OFFLINE'}
            </Text>
          </View>
        </View>
      </View>
 
      {/* Alert Banner */}
      {isOverCapacity && (
        <View style={styles.alertBanner}>
          <Text style={styles.alertText}>🚨 ALERTA: AFORO MÁXIMO EXCEDIDO</Text>
        </View>
      )}
 
      {/* Video Preview - WebSocket Tiempo Real */}
      <View style={styles.videoContainer}>
        {frameData && frameData.frame ? (
          <View style={[styles.videoWrapper, isOverCapacity && styles.videoWrapperDanger]}>
            <Image
              source={{ 
                uri: `data:image/jpeg;base64,${frameData.frame}`,
                cache: 'reload'
              }}
              style={styles.videoImage}
              resizeMode="contain"
              fadeDuration={0}
            />
            <View style={styles.videoOverlay}>
              <View style={styles.detectionBadge}>
                <Text style={styles.detectionText}>
                  👤 {frameData.count || 0} Pers.
                </Text>
              </View>
              <View style={styles.fpsBadge}>
                <Text style={styles.fpsText}>
                  {actualFps > 0 ? actualFps.toFixed(1) : (frameData.fps?.toFixed(1) || '0')} FPS
                </Text>
              </View>
              {wsConnected && (
                <View style={styles.wsIndicator}>
                  <Text style={styles.wsText}>⚡ TIEMPO REAL</Text>
                </View>
              )}
            </View>
          </View>
        ) : (
          <View style={[styles.videoPlaceholder, cameraActive && styles.videoPlaceholderActive]}>
            <View style={styles.radarPlaceholderWrapper}>
              <Animated.View 
                style={[
                  styles.radarPlaceholderRing, 
                  { transform: [{ scale: placeholderPulse }] }
                ]} 
              />
              <Animated.View 
                style={[
                  styles.radarPlaceholderRingInner, 
                  { transform: [{ scale: placeholderPulse }] }
                ]} 
              />
              <View style={styles.radarPlaceholderCenter}>
                <Text style={styles.radarCenterIcon}>{cameraActive ? '📡' : '🛰️'}</Text>
              </View>
            </View>
            <Text style={styles.videoText}>
              {cameraActive ? 'Sincronizando flujo de video...' : 'Monitoreo Inactivo'}
            </Text>
            {cameraActive ? (
              <>
                <ActivityIndicator 
                  size="small" 
                  color="#00E5FF" 
                  style={{ marginTop: 10 }}
                />
                <Text style={styles.videoSubText}>
                  {wsConnected ? 'Canal WebSocket Abierto' : 'Estableciendo enlace de video...'}
                </Text>
              </>
            ) : (
              <Text style={styles.videoSubText}>Presiona el botón de abajo para iniciar la transmisión IA</Text>
            )}
          </View>
        )}
      </View>
 
      {/* Camera Controls */}
      <View style={styles.controlsRow}>
        <TouchableOpacity
          style={[styles.button, cameraActive ? styles.buttonDanger : styles.buttonSuccess]}
          onPress={cameraActive ? stopCamera : startCamera}
        >
          <Text style={styles.buttonText}>
            {cameraActive ? '⏹ DETENER CAPTURA' : '▶ INICIAR CÁMARA IA'}
          </Text>
        </TouchableOpacity>
        
        <View style={styles.dualRow}>
          <TouchableOpacity
            style={styles.configButton}
            onPress={() => setShowCameraConfig(true)}
          >
            <Text style={styles.buttonText}>⚙ CONFIGURAR</Text>
          </TouchableOpacity>
 
          <TouchableOpacity
            style={styles.hvacButton}
            onPress={() => setShowHvacConfig(true)}
          >
            <Text style={styles.buttonText}>❄ CLIMATIZACIÓN (IR)</Text>
          </TouchableOpacity>
        </View>
      </View>
 
      {/* Occupancy Card */}
      <View style={[styles.card, isOverCapacity && styles.cardDanger]}>
        <Text style={styles.cardTitle}>OCUPACIÓN DE SALA</Text>
        <View style={styles.countContainer}>
          <Text style={[styles.countNumber, isOverCapacity && styles.countNumberDanger]}>{currentCount}</Text>
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
        <Text style={styles.percentageText}>Capacidad Utilizada: {percentage.toFixed(0)}%</Text>
      </View>
 
      {/* Metrics Grid */}
      <View style={styles.metricsGrid}>
        <View style={styles.metricCard}>
          <Text style={styles.metricValue}>
            {actualFps > 0 ? actualFps.toFixed(1) : (status?.fps?.toFixed(1) || '0.0')}
          </Text>
          <Text style={styles.metricLabel}>FPS Promedio</Text>
        </View>
        
        <View style={styles.metricCard}>
          <Text style={styles.metricValue}>
            {status?.models_loaded || 0}
          </Text>
          <Text style={styles.metricLabel}>Redes YOLO</Text>
        </View>
 
        <View style={styles.metricCard}>
          <Text style={[styles.metricValue, { fontSize: 13, textTransform: 'uppercase' }]}>
            {status?.config?.ensemble_strategy || 'PROMEDIO'}
          </Text>
          <Text style={styles.metricLabel}>Mapeo IA</Text>
        </View>
      </View>
 
      {/* Info Card */}
      <View style={styles.infoCard}>
        <Text style={styles.infoTitle}>📋 Diagnóstico de Enlace</Text>
        <Text style={styles.infoText}>
          • Motor de Visión: <Text style={{ color: '#00E5FF', fontWeight: 'bold' }}>YOLOv11s Activo</Text>
        </Text>
        <Text style={styles.infoText}>
          • Canal Físico: {cameraActive ? 'Transmitiendo ✅' : 'En Espera ⏸️'}
        </Text>
        <Text style={styles.infoText}>
          • Umbral de Filtro: {status?.config?.confidence_threshold || 0.5} (50% Confianza)
        </Text>
        <Text style={styles.infoText}>
          • Climatizador Serial: {status?.serial?.connected ? 'Arduino Conectado 🟢' : 'Modo Simulación 📡'}
        </Text>
      </View>
 
      {/* Footer */}
      <View style={styles.footer}>
        <Text style={styles.footerText}>
          SALA DE CONTROL INTELIGENTE DE AFORO & HVAC v2.0
        </Text>
      </View>
    </ScrollView>
  );
}
 
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#080C14',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
    backgroundColor: '#080C14',
  },
  loadingText: {
    marginTop: 15,
    fontSize: 15,
    fontWeight: 'bold',
    color: '#94A3B8',
    letterSpacing: 0.5,
  },
  errorIcon: {
    fontSize: 54,
    marginBottom: 20,
  },
  errorTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 10,
    letterSpacing: 0.5,
  },
  errorText: {
    fontSize: 14,
    color: '#94A3B8',
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 8,
  },
  urlText: {
    fontSize: 14,
    color: '#00E5FF',
    fontWeight: 'bold',
    marginBottom: 25,
    fontFamily: 'monospace',
  },
  retryButton: {
    backgroundColor: '#00E5FF',
    paddingHorizontal: 30,
    paddingVertical: 14,
    borderRadius: 12,
    marginBottom: 30,
    shadowColor: '#00E5FF',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 10,
    elevation: 5,
  },
  retryButtonText: {
    color: '#080C14',
    fontSize: 14,
    fontWeight: 'bold',
    letterSpacing: 1,
  },
  helpBox: {
    backgroundColor: '#101726',
    padding: 20,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#1E2942',
    width: '100%',
  },
  helpTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#F59E0B',
    marginBottom: 10,
  },
  helpText: {
    fontSize: 13,
    color: '#94A3B8',
    lineHeight: 20,
  },
  header: {
    backgroundColor: '#0E1324',
    padding: 20,
    paddingTop: 50,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderColor: '#1E2942',
  },
  headerSubtitle: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#94A3B8',
    letterSpacing: 2,
    marginBottom: 2,
  },
  title: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  statusContainer: {
    flexDirection: 'column',
    alignItems: 'flex-end',
    gap: 5,
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1,
  },
  statusConnected: {
    backgroundColor: 'rgba(0, 230, 118, 0.1)',
    borderColor: '#00E676',
  },
  statusDisconnected: {
    backgroundColor: 'rgba(255, 45, 85, 0.1)',
    borderColor: '#FF2D55',
  },
  statusText: {
    color: '#FFFFFF',
    fontSize: 9,
    fontWeight: 'bold',
    letterSpacing: 1,
  },
  alertBanner: {
    backgroundColor: '#FF2D55',
    padding: 12,
    alignItems: 'center',
    shadowColor: '#FF2D55',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 10,
    elevation: 4,
  },
  alertText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: 'bold',
    letterSpacing: 1,
  },
  videoContainer: {
    margin: 20,
    marginBottom: 15,
  },
  videoPlaceholder: {
    backgroundColor: '#0F1524',
    height: 260,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#1E2942',
    justifyContent: 'center',
    alignItems: 'center',
  },
  videoPlaceholderActive: {
    borderColor: '#00E5FF',
    shadowColor: '#00E5FF',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.15,
    shadowRadius: 15,
  },
  videoIcon: {
    fontSize: 48,
    marginBottom: 10,
  },
  videoText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: 'bold',
    letterSpacing: 0.5,
  },
  videoSubText: {
    color: '#64748B',
    fontSize: 12,
    marginTop: 10,
    textAlign: 'center',
  },
  videoWrapper: {
    position: 'relative',
    height: 260,
    borderRadius: 16,
    overflow: 'hidden',
    backgroundColor: '#000',
    borderWidth: 2,
    borderColor: '#1E2942',
  },
  videoWrapperDanger: {
    borderColor: '#FF2D55',
  },
  videoImage: {
    width: '100%',
    height: '100%',
  },
  videoOverlay: {
    position: 'absolute',
    top: 12,
    left: 12,
    right: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  detectionBadge: {
    backgroundColor: 'rgba(8, 12, 20, 0.8)',
    borderWidth: 1,
    borderColor: '#00E5FF',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
  },
  detectionText: {
    color: '#00E5FF',
    fontSize: 12,
    fontWeight: 'bold',
  },
  fpsBadge: {
    backgroundColor: 'rgba(8, 12, 20, 0.8)',
    borderWidth: 1,
    borderColor: '#00E676',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
  },
  fpsText: {
    color: '#00E676',
    fontSize: 11,
    fontWeight: 'bold',
  },
  wsIndicator: {
    backgroundColor: 'rgba(255, 45, 85, 0.8)',
    borderWidth: 1,
    borderColor: '#FF2D55',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
  },
  wsText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: 'bold',
    letterSpacing: 0.5,
  },
  controlsRow: {
    marginHorizontal: 20,
    marginBottom: 20,
  },
  button: {
    padding: 16,
    borderRadius: 14,
    alignItems: 'center',
    marginBottom: 10,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 3,
  },
  buttonSuccess: {
    backgroundColor: '#00E676',
    shadowColor: '#00E676',
  },
  buttonDanger: {
    backgroundColor: '#FF2D55',
    shadowColor: '#FF2D55',
  },
  dualRow: {
    flexDirection: 'row',
    gap: 10,
  },
  configButton: {
    flex: 1,
    backgroundColor: '#1E2942',
    padding: 16,
    borderRadius: 14,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#2D3B5C',
  },
  hvacButton: {
    flex: 1.2,
    backgroundColor: '#7C4DFF',
    padding: 16,
    borderRadius: 14,
    alignItems: 'center',
    shadowColor: '#7C4DFF',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: 'bold',
    letterSpacing: 1,
  },
  card: {
    backgroundColor: '#101726',
    marginHorizontal: 20,
    marginBottom: 20,
    padding: 22,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#1F2942',
  },
  cardDanger: {
    borderColor: '#FF2D55',
    backgroundColor: '#1C121F',
  },
  cardTitle: {
    fontSize: 11,
    fontWeight: 'bold',
    color: '#94A3B8',
    marginBottom: 15,
    letterSpacing: 2,
  },
  countContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'baseline',
    marginBottom: 20,
  },
  countNumber: {
    fontSize: 72,
    fontWeight: 'bold',
    color: '#00E5FF',
    textShadowColor: 'rgba(0, 229, 255, 0.3)',
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 15,
  },
  countNumberDanger: {
    color: '#FF2D55',
    textShadowColor: 'rgba(255, 45, 85, 0.3)',
  },
  countSeparator: {
    fontSize: 32,
    color: '#334155',
    marginHorizontal: 10,
  },
  countMax: {
    fontSize: 32,
    color: '#64748B',
    fontWeight: 'bold',
  },
  progressBar: {
    height: 12,
    backgroundColor: '#1E2942',
    borderRadius: 6,
    overflow: 'hidden',
    marginBottom: 12,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#00E5FF',
    borderRadius: 6,
  },
  progressDanger: {
    backgroundColor: '#FF2D55',
  },
  percentageText: {
    textAlign: 'center',
    fontSize: 12,
    fontWeight: '500',
    color: '#64748B',
    letterSpacing: 0.5,
  },
  metricsGrid: {
    flexDirection: 'row',
    marginHorizontal: 20,
    marginBottom: 20,
    gap: 10,
  },
  metricCard: {
    flex: 1,
    backgroundColor: '#101726',
    padding: 16,
    borderRadius: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#1F2942',
  },
  metricValue: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#00E5FF',
    marginBottom: 6,
  },
  metricLabel: {
    fontSize: 10,
    color: '#64748B',
    fontWeight: 'bold',
    letterSpacing: 0.5,
    textAlign: 'center',
  },
  infoCard: {
    backgroundColor: '#0F1A2C',
    marginHorizontal: 20,
    marginBottom: 20,
    padding: 22,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#1E3A8A',
  },
  infoTitle: {
    fontSize: 15,
    fontWeight: 'bold',
    color: '#3B82F6',
    marginBottom: 12,
    letterSpacing: 0.5,
  },
  infoText: {
    fontSize: 13,
    color: '#94A3B8',
    marginVertical: 4,
    lineHeight: 20,
  },
  footer: {
    padding: 25,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 9,
    fontWeight: 'bold',
    color: '#334155',
    letterSpacing: 2,
    textAlign: 'center',
  },
  radarPlaceholderWrapper: {
    width: 120,
    height: 120,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  radarPlaceholderRing: {
    position: 'absolute',
    width: 110,
    height: 110,
    borderRadius: 55,
    borderWidth: 2,
    borderColor: 'rgba(0, 229, 255, 0.15)',
  },
  radarPlaceholderRingInner: {
    position: 'absolute',
    width: 80,
    height: 80,
    borderRadius: 40,
    borderWidth: 1.5,
    borderColor: 'rgba(124, 77, 255, 0.25)',
  },
  radarPlaceholderCenter: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#0F172A',
    borderWidth: 1.5,
    borderColor: '#00E5FF',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#00E5FF',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 3,
  },
  radarCenterIcon: {
    fontSize: 20,
  },
});
