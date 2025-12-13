import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import wsService from '../services/websocket';
import { initializeConnection } from '../services/api';
import { COLORS } from '../utils/constants';

const ConnectionStatus = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [currentUrl, setCurrentUrl] = useState('');
  const [reconnecting, setReconnecting] = useState(false);

  useEffect(() => {
    // Escuchar cambios en el estado de conexión
    const handleConnectionStatus = (status) => {
      setIsConnected(status.connected);
      if (status.error) {
        console.error('Error de conexión:', status.error);
      }
    };

    wsService.on('connection_status', handleConnectionStatus);

    // Verificar conexión inicial
    checkConnection();

    return () => {
      wsService.off('connection_status', handleConnectionStatus);
    };
  }, []);

  const checkConnection = async () => {
    setReconnecting(true);
    try {
      const connected = await initializeConnection();
      setIsConnected(connected);
      if (connected) {
        // Conectar WebSocket
        await wsService.connect();
      }
    } catch (error) {
      console.error('Error al verificar conexión:', error);
      setIsConnected(false);
    } finally {
      setReconnecting(false);
    }
  };

  const handleReconnect = async () => {
    setReconnecting(true);
    await checkConnection();
    wsService.forceReconnect();
  };

  if (!isConnected && !reconnecting) {
    return (
      <View style={styles.container}>
        <View style={styles.disconnectedBar}>
          <Text style={styles.statusText}>❌ Sin conexión al backend</Text>
          <TouchableOpacity style={styles.reconnectButton} onPress={handleReconnect}>
            <Text style={styles.buttonText}>🔄 Reconectar</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  if (reconnecting) {
    return (
      <View style={styles.container}>
        <View style={styles.reconnectingBar}>
          <Text style={styles.statusText}>🔄 Reconectando...</Text>
        </View>
      </View>
    );
  }

  // Mostrar banner verde pequeño cuando está conectado
  return (
    <View style={styles.container}>
      <View style={styles.connectedBar}>
        <Text style={styles.connectedText}>✅ Conectado</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    zIndex: 1000,
  },
  disconnectedBar: {
    backgroundColor: COLORS.danger,
    padding: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  reconnectingBar: {
    backgroundColor: COLORS.warning,
    padding: 12,
    alignItems: 'center',
  },
  connectedBar: {
    backgroundColor: COLORS.success,
    padding: 6,
    alignItems: 'center',
  },
  statusText: {
    color: 'white',
    fontSize: 14,
    fontWeight: 'bold',
  },
  connectedText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  reconnectButton: {
    backgroundColor: 'white',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  buttonText: {
    color: COLORS.danger,
    fontSize: 12,
    fontWeight: 'bold',
  },
});

export default ConnectionStatus;
