import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
  TextInput,
  Switch,
} from 'react-native';
import { Picker } from '@react-native-picker/picker';
import { Ionicons } from '@expo/vector-icons';
import { apiService } from '../services/api';
import { COLORS } from '../utils/constants';

export default function HVACConfigScreen({ onBack }) {
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState(null);
  const [brands, setBrands] = useState({});
  const [ports, setPorts] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [connecting, setConnecting] = useState(false);
  
  // Form states for manual command
  const [manualCmd, setManualCmd] = useState({
    power: true,
    mode: 'cool',
    temp: 24,
    fan: 'auto',
    brand: 'lg'
  });

  const [serialConfig, setSerialConfig] = useState({
    port: '',
    baudrate: '115200'
  });

  useEffect(() => {
    loadInitialData();
    const interval = setInterval(loadStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      const [statusData, brandsData, portsData] = await Promise.all([
        apiService.getHvacStatus(),
        apiService.getHvacBrands(),
        apiService.getSerialPorts()
      ]);
      
      setStatus(statusData);
      setBrands(brandsData.brands || brandsData || {});
      const portsList = portsData.ports || (Array.isArray(portsData) ? portsData : []);
      setPorts(portsList);
      
      const activePort = statusData.serial?.port || statusData.port;
      if (activePort) {
        setSerialConfig(prev => ({ ...prev, port: activePort }));
      } else if (portsList.length > 0) {
        setSerialConfig(prev => ({ ...prev, port: portsList[0].device }));
      }
      
      if (statusData.config?.brand) {
        setManualCmd(prev => ({ ...prev, brand: statusData.config.brand }));
      }

    } catch (error) {
      console.error('Error loading HVAC data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadStatus = async () => {
    try {
      const statusData = await apiService.getHvacStatus();
      setStatus(statusData);
    } catch (error) {
      console.log('Error refreshing status');
    }
  };

  const handleConnect = async () => {
    if (!serialConfig.port) {
      Alert.alert('Error', 'Selecciona un puerto serial');
      return;
    }
    setConnecting(true);
    try {
      const result = await apiService.connectSerial(serialConfig.port, parseInt(serialConfig.baudrate));
      if (result.success) {
        Alert.alert('✅ Conectado', result.simulated ? 'Modo simulación activo' : `Conectado a ${serialConfig.port}`);
        loadStatus();
      } else {
        Alert.alert('❌ Error', result.error || 'No se pudo conectar');
      }
    } catch (error) {
      Alert.alert('❌ Error', 'Error de red al conectar');
    } finally {
      setConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      await apiService.disconnectSerial();
      Alert.alert('ℹ️ Info', 'Desconectado');
      loadStatus();
    } catch (error) {
      Alert.alert('❌ Error', 'No se pudo desconectar');
    }
  };

  const sendManualCommand = async () => {
    try {
      const result = await apiService.sendHvacCommand({
        power: manualCmd.power,
        mode: manualCmd.mode,
        target_temperature_c: manualCmd.temp,
        fan_speed: manualCmd.fan,
        brand: manualCmd.brand
      });
      
      if (result.result?.success || result.transport?.success) {
        Alert.alert('🚀 Comando Enviado', `Marca: ${manualCmd.brand.toUpperCase()}\nTemp: ${manualCmd.temp}°C`);
      } else {
        const errorMsg = result.result?.error || result.transport?.error || 'Verifica la conexión serial';
        Alert.alert('⚠️ Fallo el envío', errorMsg);
      }
      loadStatus();
    } catch (error) {
      Alert.alert('❌ Error', 'No se pudo enviar el comando');
    }
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.loadingText}>Cargando módulo HVAC...</Text>
      </View>
    );
  }

  const isConnected = status?.serial?.connected || status?.connected || false;
  const lastDecision = status?.hvac?.last_decision || status?.last_decision || {};
  const currentBrand = brands[status?.config?.brand] || brands[status?.hvac?.config?.brand] || brands['generic'] || { display_name: 'Genérico' };

  return (
    <View style={styles.container}>
      {/* Header Custom */}
      <View style={styles.header}>
        <TouchableOpacity onPress={onBack} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Control de Climatización (HVAC)</Text>
      </View>

      <ScrollView style={styles.content}>
        
        {/* Status Card */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>ESTADO ACTUAL</Text>
            <View style={[styles.badge, isConnected ? styles.badgeSuccess : styles.badgeDanger]}>
              <Text style={styles.badgeText}>{isConnected ? 'SERIAL OK' : 'DESCONECTADO'}</Text>
            </View>
          </View>
          
          <View style={styles.statusGrid}>
            <View style={styles.statusItem}>
              <Text style={styles.statusLabel}>Marca activa</Text>
              <Text style={styles.statusValue}>{currentBrand.display_name}</Text>
            </View>
            <View style={styles.statusItem}>
              <Text style={styles.statusLabel}>Temp. Objetivo</Text>
              <Text style={styles.statusValue}>{lastDecision.target_temperature_c || '--'}°C</Text>
            </View>
            <View style={styles.statusItem}>
              <Text style={styles.statusLabel}>Modo Auto</Text>
              <Text style={styles.statusValue}>{status?.config?.enabled ? 'ACTIVADO' : 'DESACTIVADO'}</Text>
            </View>
            <View style={styles.statusItem}>
              <Text style={styles.statusLabel}>Aforo medido</Text>
              <Text style={styles.statusValue}>{lastDecision.occupancy_count || 0}</Text>
            </View>
          </View>
          
          {lastDecision.reason && (
            <Text style={styles.reasonText}>Motivo: {lastDecision.reason}</Text>
          )}
        </View>

        {/* Serial Config */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>CONFIGURACIÓN SERIAL (ARDUINO)</Text>
          
          <Text style={styles.label}>Puerto USB / Serial</Text>
          <View style={styles.pickerContainer}>
            <Picker
              selectedValue={serialConfig.port}
              onValueChange={(itemValue) => setSerialConfig({ ...serialConfig, port: itemValue })}
              enabled={!isConnected}
            >
              {ports.length === 0 ? (
                <Picker.Item label="No se detectan puertos" value="" />
              ) : (
                ports.map(p => (
                  <Picker.Item key={p.device} label={`${p.device} (${p.description})`} value={p.device} />
                ))
              )}
            </Picker>
          </View>

          <View style={styles.buttonRow}>
            {!isConnected ? (
              <TouchableOpacity 
                style={[styles.actionButton, styles.connectButton, connecting && styles.disabledButton]} 
                onPress={handleConnect}
                disabled={connecting}
              >
                {connecting ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>CONECTAR</Text>}
              </TouchableOpacity>
            ) : (
              <TouchableOpacity style={[styles.actionButton, styles.disconnectButton]} onPress={handleDisconnect}>
                <Text style={styles.buttonText}>DESCONECTAR</Text>
              </TouchableOpacity>
            )}
            
            <TouchableOpacity style={styles.refreshButton} onPress={loadInitialData}>
              <Ionicons name="refresh" size={20} color={COLORS.primary} />
            </TouchableOpacity>
          </View>
        </View>

        {/* Manual Controls */}
        <View style={[styles.card, !isConnected && styles.cardDisabled]}>
          <Text style={styles.cardTitle}>CONTROL MANUAL IR</Text>
          
          <View style={styles.row}>
            <View style={{ flex: 1 }}>
              <Text style={styles.label}>Marca AC</Text>
              <View style={styles.pickerContainerSmall}>
                <Picker
                  selectedValue={manualCmd.brand}
                  onValueChange={(v) => setManualCmd({ ...manualCmd, brand: v })}
                >
                  {Object.keys(brands).map(key => (
                    <Picker.Item key={key} label={brands[key].display_name} value={key} />
                  ))}
                </Picker>
              </View>
            </View>
            
            <View style={{ width: 100, alignItems: 'center' }}>
              <Text style={styles.label}>Power</Text>
              <Switch 
                value={manualCmd.power} 
                onValueChange={(v) => setManualCmd({ ...manualCmd, power: v })}
                trackColor={{ false: '#767577', true: COLORS.primary }}
              />
            </View>
          </View>

          <View style={styles.row}>
            <View style={{ flex: 1 }}>
              <Text style={styles.label}>Modo</Text>
              <View style={styles.pickerContainerSmall}>
                <Picker
                  selectedValue={manualCmd.mode}
                  onValueChange={(v) => setManualCmd({ ...manualCmd, mode: v })}
                >
                  <Picker.Item label="Cool (Frío)" value="cool" />
                  <Picker.Item label="Heat (Calor)" value="heat" />
                  <Picker.Item label="Fan (Vent.)" value="fan" />
                  <Picker.Item label="Dry (Seco)" value="dry" />
                </Picker>
              </View>
            </View>
            
            <View style={{ flex: 1, marginLeft: 10 }}>
              <Text style={styles.label}>Temp: {manualCmd.temp}°C</Text>
              <View style={styles.tempButtons}>
                <TouchableOpacity onPress={() => setManualCmd(p => ({ ...p, temp: Math.max(16, p.temp - 1) }))} style={styles.tempBtn}>
                  <Text style={styles.tempBtnText}>-</Text>
                </TouchableOpacity>
                <TouchableOpacity onPress={() => setManualCmd(p => ({ ...p, temp: Math.min(30, p.temp + 1) }))} style={styles.tempBtn}>
                  <Text style={styles.tempBtnText}>+</Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>

          <TouchableOpacity 
            style={[styles.sendButton, !isConnected && styles.sendButtonDisabled]} 
            onPress={sendManualCommand}
            disabled={!isConnected}
          >
            <Ionicons name="send" size={20} color="#fff" style={{ marginRight: 8 }} />
            <Text style={styles.buttonText}>ENVIAR COMANDO IR</Text>
          </TouchableOpacity>
        </View>

        <View style={{ height: 40 }} />
      </ScrollView>
    </View>
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
    backgroundColor: '#f3f4f6',
  },
  loadingText: {
    marginTop: 10,
    color: '#6b7280',
  },
  header: {
    backgroundColor: COLORS.primary,
    padding: 20,
    paddingTop: 40,
    flexDirection: 'row',
    alignItems: 'center',
  },
  backButton: {
    padding: 5,
    marginRight: 10,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
  content: {
    flex: 1,
    padding: 15,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    marginBottom: 15,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  cardTitle: {
    fontSize: 13,
    fontWeight: 'bold',
    color: '#6b7280',
    letterSpacing: 0.5,
  },
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 10,
  },
  badgeSuccess: {
    backgroundColor: '#dcfce7',
  },
  badgeDanger: {
    backgroundColor: '#fee2e2',
  },
  badgeText: {
    fontSize: 11,
    fontWeight: 'bold',
    color: '#166534',
  },
  statusGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  statusItem: {
    width: '50%',
    marginBottom: 15,
  },
  statusLabel: {
    fontSize: 12,
    color: '#9ca3af',
    marginBottom: 2,
  },
  statusValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1f2937',
  },
  reasonText: {
    fontSize: 12,
    color: COLORS.primary,
    fontStyle: 'italic',
    marginTop: 5,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  pickerContainer: {
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    backgroundColor: '#f9fafb',
    marginBottom: 15,
    overflow: 'hidden',
  },
  pickerContainerSmall: {
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    backgroundColor: '#f9fafb',
    overflow: 'hidden',
    height: 50,
    justifyContent: 'center',
  },
  buttonRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  actionButton: {
    flex: 1,
    height: 50,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  connectButton: {
    backgroundColor: COLORS.primary,
  },
  disconnectButton: {
    backgroundColor: '#ef4444',
  },
  refreshButton: {
    width: 50,
    height: 50,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 15,
  },
  disabledButton: {
    opacity: 0.6,
  },
  cardDisabled: {
    opacity: 0.6,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 15,
  },
  tempButtons: {
    flexDirection: 'row',
    gap: 10,
  },
  tempBtn: {
    flex: 1,
    backgroundColor: '#e5e7eb',
    height: 40,
    borderRadius: 6,
    justifyContent: 'center',
    alignItems: 'center',
  },
  tempBtnText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1f2937',
  },
  sendButton: {
    backgroundColor: '#10b981',
    height: 55,
    borderRadius: 10,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 10,
  },
  sendButtonDisabled: {
    backgroundColor: '#9ca3af',
  }
});
