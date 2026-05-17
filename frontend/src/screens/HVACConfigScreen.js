import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
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
        <ActivityIndicator size="large" color="#00E5FF" />
        <Text style={styles.loadingText}>Sincronizando Módulo HVAC...</Text>
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
          <Ionicons name="arrow-back" size={24} color="#00E5FF" />
        </TouchableOpacity>
        <View>
          <Text style={styles.headerSubtitle}>MÓDULO DE CLIMA FÍSICO</Text>
          <Text style={styles.headerTitle}>Control de Climatización</Text>
        </View>
      </View>

      <ScrollView style={styles.content} contentContainerStyle={{ paddingBottom: 40 }}>
        
        {/* Status Card */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>MONITOR DE ESTADO</Text>
            <View style={[styles.badge, isConnected ? styles.badgeSuccess : styles.badgeDanger]}>
              <Text style={styles.badgeText}>{isConnected ? '● SERIAL OK' : '○ DESCONECTADO'}</Text>
            </View>
          </View>
          
          <View style={styles.statusGrid}>
            <View style={styles.statusItem}>
              <Text style={styles.statusLabel}>Marca activa</Text>
              <Text style={styles.statusValue}>{currentBrand.display_name}</Text>
            </View>
            <View style={styles.statusItem}>
              <Text style={styles.statusLabel}>Temp. Objetivo</Text>
              <Text style={[styles.statusValue, { color: '#00E5FF' }]}>{lastDecision.target_temperature_c || '--'}°C</Text>
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
            <Text style={styles.reasonText}>Lógica IA: {lastDecision.reason}</Text>
          )}
        </View>

        {/* Serial Config */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>ENLACE SERIAL (CONEXIÓN USB)</Text>
          
          <Text style={styles.label}>Puerto Serial Detectado</Text>
          <View style={styles.pickerContainer}>
            <Picker
              selectedValue={serialConfig.port}
              onValueChange={(itemValue) => setSerialConfig({ ...serialConfig, port: itemValue })}
              enabled={!isConnected}
              dropdownIconColor="#00E5FF"
              style={{ color: '#FFFFFF', backgroundColor: '#0F172A' }}
            >
              {ports.length === 0 ? (
                <Picker.Item label="Buscando puertos USB..." value="" style={{ color: '#94A3B8', backgroundColor: '#0F172A' }} />
              ) : (
                ports.map(p => (
                  <Picker.Item key={p.device} label={`${p.device} (${p.description})`} value={p.device} style={{ color: '#FFFFFF', backgroundColor: '#0F172A' }} />
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
                {connecting ? <ActivityIndicator color="#080C14" /> : <Text style={styles.buttonText}>CONECTAR HARDWARE</Text>}
              </TouchableOpacity>
            ) : (
              <TouchableOpacity style={[styles.actionButton, styles.disconnectButton]} onPress={handleDisconnect}>
                <Text style={styles.buttonText}>DESCONECTAR HARDWARE</Text>
              </TouchableOpacity>
            )}
            
            <TouchableOpacity style={styles.refreshButton} onPress={loadInitialData}>
              <Ionicons name="refresh" size={20} color="#00E5FF" />
            </TouchableOpacity>
          </View>
        </View>

        {/* Manual Controls */}
        <View style={[styles.card, !isConnected && styles.cardDisabled]}>
          <Text style={styles.cardTitle}>CONSOLA DE COMANDO MANUAL (IR)</Text>
          
          <View style={styles.row}>
            <View style={{ flex: 1 }}>
              <Text style={styles.label}>Fabricante AC</Text>
              <View style={styles.pickerContainerSmall}>
                <Picker
                  selectedValue={manualCmd.brand}
                  onValueChange={(v) => setManualCmd({ ...manualCmd, brand: v })}
                  dropdownIconColor="#00E5FF"
                  style={{ color: '#FFFFFF', backgroundColor: '#0F172A' }}
                >
                  {Object.keys(brands).map(key => (
                    <Picker.Item key={key} label={brands[key].display_name} value={key} style={{ color: '#FFFFFF', backgroundColor: '#0F172A' }} />
                  ))}
                </Picker>
              </View>
            </View>
            
            <View style={{ width: 100, alignItems: 'center' }}>
              <Text style={styles.label}>Estado AC</Text>
              <Switch 
                value={manualCmd.power} 
                onValueChange={(v) => setManualCmd({ ...manualCmd, power: v })}
                trackColor={{ false: '#1E2942', true: '#7C4DFF' }}
                thumbColor={manualCmd.power ? '#00E5FF' : '#94A3B8'}
              />
            </View>
          </View>

          <View style={styles.row}>
            <View style={{ flex: 1 }}>
              <Text style={styles.label}>Modo Climatización</Text>
              <View style={styles.pickerContainerSmall}>
                <Picker
                  selectedValue={manualCmd.mode}
                  onValueChange={(v) => setManualCmd({ ...manualCmd, mode: v })}
                  dropdownIconColor="#00E5FF"
                  style={{ color: '#FFFFFF', backgroundColor: '#0F172A' }}
                >
                  <Picker.Item label="Cool (Frío)" value="cool" style={{ color: '#FFFFFF', backgroundColor: '#0F172A' }} />
                  <Picker.Item label="Heat (Calor)" value="heat" style={{ color: '#FFFFFF', backgroundColor: '#0F172A' }} />
                  <Picker.Item label="Fan (Ventilación)" value="fan" style={{ color: '#FFFFFF', backgroundColor: '#0F172A' }} />
                  <Picker.Item label="Dry (Secado)" value="dry" style={{ color: '#FFFFFF', backgroundColor: '#0F172A' }} />
                </Picker>
              </View>
            </View>
            
            <View style={{ flex: 1, marginLeft: 10 }}>
              <Text style={styles.label}>Temp: <Text style={{ color: '#00E5FF' }}>{manualCmd.temp}°C</Text></Text>
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
            <Ionicons name="send" size={18} color="#080C14" style={{ marginRight: 8 }} />
            <Text style={[styles.buttonText, { color: '#080C14' }]}>TRANSMITIR COMANDO IR</Text>
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
    backgroundColor: '#080C14',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#080C14',
    padding: 24,
  },
  loadingText: {
    marginTop: 15,
    fontSize: 15,
    fontWeight: 'bold',
    color: '#94A3B8',
    letterSpacing: 0.5,
  },
  header: {
    backgroundColor: '#0E1324',
    padding: 20,
    paddingTop: 50,
    flexDirection: 'row',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderColor: '#1E2942',
  },
  backButton: {
    padding: 5,
    marginRight: 15,
  },
  headerSubtitle: {
    fontSize: 9,
    fontWeight: 'bold',
    color: '#64748B',
    letterSpacing: 2,
    marginBottom: 2,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  content: {
    flex: 1,
    padding: 15,
  },
  card: {
    backgroundColor: '#101726',
    borderRadius: 16,
    padding: 22,
    marginBottom: 15,
    borderWidth: 1,
    borderColor: '#1F2942',
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 18,
  },
  cardTitle: {
    fontSize: 11,
    fontWeight: 'bold',
    color: '#94A3B8',
    letterSpacing: 1,
  },
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
    borderWidth: 1,
  },
  badgeSuccess: {
    backgroundColor: 'rgba(0, 230, 118, 0.1)',
    borderColor: '#00E676',
  },
  badgeDanger: {
    backgroundColor: 'rgba(255, 45, 85, 0.1)',
    borderColor: '#FF2D55',
  },
  badgeText: {
    fontSize: 9,
    fontWeight: 'bold',
    color: '#FFFFFF',
    letterSpacing: 0.5,
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
    fontSize: 11,
    color: '#64748B',
    fontWeight: 'bold',
    marginBottom: 4,
    letterSpacing: 0.5,
  },
  statusValue: {
    fontSize: 15,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  reasonText: {
    fontSize: 12,
    color: '#00E5FF',
    fontStyle: 'italic',
    marginTop: 8,
    borderTopWidth: 1,
    borderColor: '#1F2942',
    paddingTop: 8,
  },
  label: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#94A3B8',
    marginBottom: 8,
    marginTop: 12,
    letterSpacing: 0.5,
  },
  pickerContainer: {
    borderWidth: 1,
    borderColor: '#1F2942',
    borderRadius: 12,
    backgroundColor: '#0F172A',
    marginBottom: 15,
    overflow: 'hidden',
  },
  pickerContainerSmall: {
    borderWidth: 1,
    borderColor: '#1F2942',
    borderRadius: 12,
    backgroundColor: '#0F172A',
    overflow: 'hidden',
    height: 50,
    justifyContent: 'center',
  },
  buttonRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginTop: 5,
  },
  actionButton: {
    flex: 1,
    height: 50,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 3,
  },
  connectButton: {
    backgroundColor: '#00E5FF',
    shadowColor: '#00E5FF',
  },
  disconnectButton: {
    backgroundColor: '#FF2D55',
    shadowColor: '#FF2D55',
  },
  refreshButton: {
    width: 50,
    height: 50,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#2D3B5C',
    backgroundColor: '#1E2942',
    justifyContent: 'center',
    alignItems: 'center',
  },
  buttonText: {
    color: '#080C14',
    fontWeight: 'bold',
    fontSize: 13,
    letterSpacing: 1,
  },
  disabledButton: {
    opacity: 0.5,
  },
  cardDisabled: {
    opacity: 0.4,
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
    backgroundColor: '#7C4DFF',
    height: 40,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#7C4DFF',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 2,
  },
  tempBtnText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  sendButton: {
    backgroundColor: '#00E676',
    height: 55,
    borderRadius: 14,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 15,
    shadowColor: '#00E676',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 10,
    elevation: 4,
  },
  sendButtonDisabled: {
    backgroundColor: '#1F2942',
    opacity: 0.5,
  }
});

