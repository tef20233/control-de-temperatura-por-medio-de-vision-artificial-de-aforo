import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Image,
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Progress from 'react-native-progress';
import { LineChart } from 'react-native-chart-kit';
import { Dimensions } from 'react-native';

import wsService from '../services/websocket';
import { apiService, initializeConnection } from '../services/api';
import { COLORS } from '../utils/constants';
import ConnectionStatus from '../components/ConnectionStatus';
import OptimizedVideoFrame from '../components/OptimizedVideoFrame';

const screenWidth = Dimensions.get('window').width;

export default function HomeScreen() {
  const [status, setStatus] = useState(null);
  const [currentFrame, setCurrentFrame] = useState(null);
  const [loading, setLoading] = useState(true);
  const [connected, setConnected] = useState(false);
  const [cameraRunning, setCameraRunning] = useState(false);
  const [historyData, setHistoryData] = useState([0]);

  useEffect(() => {
    // Inicializar conexión con detección automática
    initializeBackend();

    // Listeners para WebSocket
    const handleFrameUpdate = (data) => {
      setCurrentFrame(data.frame);
      
      // Actualizar historial de últimos 60 segundos
      setHistoryData(prev => {
        const newData = [...prev, data.count];
        return newData.slice(-60); // Últimos 60 puntos
      });

      // Actualizar status
      setStatus(prevStatus => ({
        ...prevStatus,
        current_count: data.count,
        fps: data.fps,
        occupancy_rate: data.count / (prevStatus?.max_capacity || 50),
      }));
    };

    const handleConnectionStatus = (data) => {
      setConnected(data.connected);
    };

    wsService.on('frame_update', handleFrameUpdate);
    wsService.on('connection_status', handleConnectionStatus);

    // Obtener status inicial
    loadStatus();

    // Polling cada 5 segundos para status
    const interval = setInterval(loadStatus, 5000);

    return () => {
      clearInterval(interval);
      wsService.off('frame_update', handleFrameUpdate);
      wsService.off('connection_status', handleConnectionStatus);
    };
  }, []);

  const initializeBackend = async () => {
    setLoading(true);
    const connected = await initializeConnection();
    if (connected) {
      setConnected(true);
      // Conectar WebSocket después de verificar backend
      await wsService.connect();
    } else {
      setConnected(false);
      Alert.alert(
        'Error de Conexión',
        'No se pudo conectar al backend. Verifica que esté ejecutándose.',
        [
          { text: 'Reintentar', onPress: () => initializeBackend() },
          { text: 'Cancelar', style: 'cancel' }
        ]
      );
    }
    setLoading(false);
  };

  const loadStatus = async () => {
    try {
      const data = await apiService.getStatus();
      setStatus(data);
      setCameraRunning(data.running);
      setLoading(false);
    } catch (error) {
      console.error('Error loading status:', error);
      setLoading(false);
    }
  };

  const handleToggleCamera = async () => {
    try {
      if (cameraRunning) {
        await apiService.stopCamera();
        setCameraRunning(false);
        Alert.alert('Éxito', 'Cámara detenida');
      } else {
        await apiService.startCamera();
        setCameraRunning(true);
        Alert.alert('Éxito', 'Cámara iniciada');
      }
    } catch (error) {
      Alert.alert('Error', 'No se pudo cambiar el estado de la cámara');
    }
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.loadingText}>Cargando...</Text>
      </View>
    );
  }

  const occupancyRate = status?.occupancy_rate || 0;
  const currentCount = status?.current_count || 0;
  const maxCapacity = status?.max_capacity || 50;
  const isOverCapacity = currentCount > maxCapacity;

  return (
    <ScrollView style={styles.container}>
      {/* Componente de estado de conexión */}
      <ConnectionStatus />
      
      {/* Estado de conexión (movido más abajo) */}
      <View style={[styles.connectionBanner, { marginTop: 30 }]}>
        <Ionicons 
          name={connected ? 'cloud-done' : 'cloud-offline'} 
          size={20} 
          color={connected ? COLORS.success : COLORS.danger} 
        />
        <Text style={styles.connectionText}>
          {connected ? 'Conectado' : 'Desconectado'}
        </Text>
      </View>

      {/* Alerta de aforo excedido */}
      {isOverCapacity && (
        <View style={styles.alertBanner}>
          <Ionicons name="warning" size={24} color="#fff" />
          <Text style={styles.alertText}>
            ⚠️ ALERTA: AFORO EXCEDIDO
          </Text>
        </View>
      )}

      {/* Video en vivo - OPTIMIZADO */}
      <View style={styles.videoContainer}>
        {currentFrame ? (
          <OptimizedVideoFrame
            frameData={currentFrame}
            style={styles.videoFrame}
          />
        ) : (
          <View style={styles.noVideoPlaceholder}>
            <Ionicons name="videocam-off" size={60} color={COLORS.textLight} />
            <Text style={styles.noVideoText}>
              {cameraRunning ? 'Esperando video...' : 'Cámara detenida'}
            </Text>
          </View>
        )}
      </View>

      {/* Control de cámara */}
      <TouchableOpacity 
        style={[styles.cameraButton, cameraRunning && styles.cameraButtonStop]}
        onPress={handleToggleCamera}
      >
        <Ionicons 
          name={cameraRunning ? 'stop-circle' : 'play-circle'} 
          size={24} 
          color="#fff" 
        />
        <Text style={styles.cameraButtonText}>
          {cameraRunning ? 'Detener Cámara' : 'Iniciar Cámara'}
        </Text>
      </TouchableOpacity>

      {/* Aforo actual */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>AFORO ACTUAL</Text>
        <Text style={styles.countText}>
          {currentCount} / {maxCapacity}
        </Text>
        <Text style={styles.countLabel}>personas</Text>
        
        <Progress.Bar
          progress={Math.min(occupancyRate, 1)}
          width={screenWidth - 80}
          height={20}
          color={isOverCapacity ? COLORS.danger : COLORS.primary}
          unfilledColor={COLORS.border}
          borderWidth={0}
          style={styles.progressBar}
        />
        
        <Text style={styles.percentageText}>
          {(occupancyRate * 100).toFixed(0)}% de ocupación
        </Text>
      </View>

      {/* Gráfica de últimos 60 segundos */}
      {historyData.length > 1 && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>📊 ÚLTIMOS 60 SEGUNDOS</Text>
          <LineChart
            data={{
              labels: [],
              datasets: [{ data: historyData }],
            }}
            width={screenWidth - 60}
            height={180}
            chartConfig={{
              backgroundColor: COLORS.card,
              backgroundGradientFrom: COLORS.card,
              backgroundGradientTo: COLORS.card,
              decimalPlaces: 0,
              color: (opacity = 1) => `rgba(59, 130, 246, ${opacity})`,
              labelColor: (opacity = 1) => `rgba(107, 114, 128, ${opacity})`,
              style: {
                borderRadius: 16,
              },
              propsForDots: {
                r: '2',
                strokeWidth: '1',
                stroke: COLORS.primary,
              },
            }}
            bezier
            style={styles.chart}
          />
        </View>
      )}

      {/* Métricas del sistema */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>MÉTRICAS DEL SISTEMA</Text>
        
        <View style={styles.metricsRow}>
          <View style={styles.metricItem}>
            <Ionicons name="speedometer" size={24} color={COLORS.primary} />
            <Text style={styles.metricValue}>{status?.fps?.toFixed(1) || '0.0'}</Text>
            <Text style={styles.metricLabel}>FPS</Text>
          </View>

          <View style={styles.metricItem}>
            <Ionicons name="cube" size={24} color={COLORS.secondary} />
            <Text style={styles.metricValue}>
              {status?.models_loaded?.length || 0}/4
            </Text>
            <Text style={styles.metricLabel}>Modelos</Text>
          </View>

          <View style={styles.metricItem}>
            <Ionicons name="camera" size={24} color={COLORS.success} />
            <Text style={styles.metricValue}>
              {status?.camera_connected ? 'ON' : 'OFF'}
            </Text>
            <Text style={styles.metricLabel}>Cámara</Text>
          </View>
        </View>

        {status?.models_loaded && status.models_loaded.length > 0 && (
          <View style={styles.modelsInfo}>
            <Text style={styles.modelsLabel}>Modelos activos:</Text>
            <Text style={styles.modelsText}>
              {status.models_loaded.join(', ')}
            </Text>
          </View>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.background,
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: COLORS.textLight,
  },
  connectionBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.card,
    padding: 10,
    gap: 8,
  },
  connectionText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
  },
  alertBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.danger,
    padding: 15,
    gap: 10,
  },
  alertText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  videoContainer: {
    backgroundColor: '#000',
    height: 250,
    margin: 20,
    marginBottom: 10,
    borderRadius: 12,
    overflow: 'hidden',
  },
  videoFrame: {
    width: '100%',
    height: '100%',
  },
  noVideoPlaceholder: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  noVideoText: {
    marginTop: 10,
    fontSize: 16,
    color: COLORS.textLight,
  },
  cameraButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.success,
    marginHorizontal: 20,
    marginBottom: 20,
    padding: 15,
    borderRadius: 12,
    gap: 10,
  },
  cameraButtonStop: {
    backgroundColor: COLORS.danger,
  },
  cameraButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  card: {
    backgroundColor: COLORS.card,
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
    color: COLORS.textLight,
    marginBottom: 15,
    letterSpacing: 1,
  },
  countText: {
    fontSize: 48,
    fontWeight: 'bold',
    color: COLORS.text,
    textAlign: 'center',
  },
  countLabel: {
    fontSize: 16,
    color: COLORS.textLight,
    textAlign: 'center',
    marginBottom: 20,
  },
  progressBar: {
    marginVertical: 10,
    alignSelf: 'center',
  },
  percentageText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    textAlign: 'center',
    marginTop: 5,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  metricsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  metricItem: {
    alignItems: 'center',
  },
  metricValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: COLORS.text,
    marginVertical: 5,
  },
  metricLabel: {
    fontSize: 12,
    color: COLORS.textLight,
  },
  modelsInfo: {
    marginTop: 15,
    paddingTop: 15,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  modelsLabel: {
    fontSize: 12,
    color: COLORS.textLight,
    marginBottom: 5,
  },
  modelsText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
  },
});
