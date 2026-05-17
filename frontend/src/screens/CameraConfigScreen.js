import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import axios from 'axios';
import { API_CONFIG } from '../utils/constants';

const API_BASE_URL = API_CONFIG.BASE_URL;

export default function CameraConfigScreen({ onBack }) {
  const [cameraSource, setCameraSource] = useState('');
  const [cameraType, setCameraType] = useState('auto');
  const [loading, setLoading] = useState(false);
  const [currentConfig, setCurrentConfig] = useState(null);
  const [scanResults, setScanResults] = useState([]);
  const [scanning, setScanning] = useState(false);
  const [maxCapacity, setMaxCapacity] = useState('');

  useEffect(() => {
    loadCurrentConfig();
  }, []);

  const loadCurrentConfig = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/config`, { timeout: 5000 });
      setCurrentConfig(response.data);
      setCameraSource(String(response.data.camera_source));
      setCameraType(response.data.camera_type);
      if (typeof response.data.max_capacity !== 'undefined') {
        setMaxCapacity(String(response.data.max_capacity));
      } else {
        setMaxCapacity('');
      }
    } catch (error) {
      console.error('Error loading config:', error);
      if (error.code === 'ECONNABORTED') {
        Alert.alert('⚠️ Timeout', 'El backend no responde. Verifica que esté ejecutándose.');
      } else if (error.message.includes('Network Error')) {
        Alert.alert('⚠️ Error de Red', 'No se puede conectar al backend. Verifica la IP y que estés en la misma WiFi.');
      }
    }
  };

  const scanNetwork = async () => {
    try {
      setScanning(true);
      setScanResults([]);

      const response = await axios.post(`${API_BASE_URL}/api/camera/scan`, {
        timeout: 3,
      });

      if (response.data.found > 0) {
        setScanResults(response.data.cameras);
        Alert.alert(
          '🔍 Escaneo Completo',
          `Se encontraron ${response.data.found} cámara(s)`
        );
      } else {
        Alert.alert('🔍 Escaneo Completo', 'No se encontraron cámaras en la red');
      }
    } catch (error) {
      let errorMsg = 'Error al escanear la red';
      if (error.message.includes('Network Error')) {
        errorMsg = 'No se puede conectar al backend. Verifica la conexión.';
      } else if (error.response) {
        errorMsg = error.response.data.error || errorMsg;
      }
      Alert.alert('❌ Error', errorMsg);
    } finally {
      setScanning(false);
    }
  };

  const changeCamera = async (source, type) => {
    try {
      setLoading(true);

      console.log('Cambiando cámara:', { source, type });

      const response = await axios.post(`${API_BASE_URL}/api/camera/change`, {
        source: source,
        type: type,
      });

      if (response.data.message) {
        Alert.alert('✅ Éxito', 'Cámara cambiada correctamente');
        loadCurrentConfig();
      }
    } catch (error) {
      let errorMsg = 'No se pudo cambiar la cámara';
      if (error.response && error.response.data) {
        errorMsg = error.response.data.error || errorMsg;
      } else if (error.message.includes('Network Error')) {
        errorMsg = 'Error de red. Verifica la conexión al backend.';
      }
      console.error('Error al cambiar cámara:', error);
      Alert.alert('❌ Error al Cambiar Cámara', errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const saveMaxCapacity = async () => {
    if (!maxCapacity) {
      Alert.alert('⚠️ Campo Requerido', 'Por favor ingresa un valor de aforo máximo');
      return;
    }

    const parsed = parseInt(maxCapacity, 10);
    if (isNaN(parsed) || parsed <= 0) {
      Alert.alert('⚠️ Valor inválido', 'Ingresa un número entero mayor que 0');
      return;
    }

    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE_URL}/api/config`, {
        max_capacity: parsed,
      });

      setCurrentConfig((prev) => ({
        ...(prev || {}),
        max_capacity: parsed,
      }));

      Alert.alert('✅ Éxito', 'Aforo máximo actualizado correctamente');
    } catch (error) {
      let errorMsg = 'No se pudo actualizar el aforo máximo';
      if (error.response && error.response.data) {
        errorMsg = error.response.data.error || errorMsg;
      } else if (error.message.includes('Network Error')) {
        errorMsg = 'Error de red. Verifica la conexión al backend.';
      }
      Alert.alert('❌ Error', errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const applyCameraConfig = () => {
    if (!cameraSource) {
      Alert.alert('⚠️ Campo Requerido', 'Por favor ingresa una fuente de cámara');
      return;
    }

    Alert.alert(
      'Confirmar Cambio',
      `¿Deseas cambiar a la fuente: ${cameraSource}?`,
      [
        { text: 'Cancelar', style: 'cancel' },
        { text: 'Cambiar', onPress: () => changeCamera(cameraSource, cameraType) }
      ]
    );
  };

  const usePhoneCamera = () => {
    Alert.alert(
      '📱 Usar Cámara del Celular',
      'Para usar la cámara de este celular:\n\n1. Instala una app de streaming (ej: IP Webcam)\n2. Inicia el stream en la app\n3. Ingresa la URL que proporciona la app\n\nEjemplo: http://192.168.1.X:8080',
      [{ text: 'Entendido' }]
    );
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 40 }}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={onBack} style={styles.backButton}>
          <Text style={styles.backButtonText}>← Volver al Panel</Text>
        </TouchableOpacity>
        <View>
          <Text style={styles.headerSubtitle}>PARÁMETROS DEL SENSOR IA</Text>
          <Text style={styles.title}>⚙ Configurar Cámara</Text>
        </View>
      </View>

      {/* Current Configuration */}
      {currentConfig && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>ESTADO ACTUAL DE LA FUENTE</Text>
          <View style={styles.configRow}>
            <Text style={styles.configLabel}>Canal Activo:</Text>
            <Text style={[styles.configValue, { color: '#00E5FF' }]}>{currentConfig.camera_source}</Text>
          </View>
          <View style={styles.configRow}>
            <Text style={styles.configLabel}>Algoritmo de Entrada:</Text>
            <Text style={styles.configValue}>{currentConfig.camera_type.toUpperCase()}</Text>
          </View>
          <View style={styles.configRow}>
            <Text style={styles.configLabel}>Aforo Límite:</Text>
            <Text style={[styles.configValue, { color: '#00E676' }]}>
              {currentConfig.max_capacity !== undefined ? `${currentConfig.max_capacity} Personas` : 'Sin definir'}
            </Text>
          </View>
        </View>
      )}

      {/* Quick Options */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>ENLACES RÁPIDOS DE VIDEO</Text>

        <View style={styles.gridRow}>
          <TouchableOpacity
            style={[styles.gridItem, { borderColor: '#7C4DFF' }]}
            onPress={() => {
              setCameraSource('0');
              setCameraType('webcam');
            }}
          >
            <View style={[styles.gridIconCircle, { backgroundColor: 'rgba(124, 77, 255, 0.15)', borderColor: '#7C4DFF' }]}>
              <Text style={styles.gridIcon}>💻</Text>
            </View>
            <Text style={styles.gridTitle}>Webcam de PC</Text>
            <Text style={styles.gridSubtitle}>Cámara física directa de la PC</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.gridItem, { borderColor: '#00E5FF' }]}
            onPress={usePhoneCamera}
          >
            <View style={[styles.gridIconCircle, { backgroundColor: 'rgba(0, 229, 255, 0.15)', borderColor: '#00E5FF' }]}>
              <Text style={styles.gridIcon}>📱</Text>
            </View>
            <Text style={styles.gridTitle}>Cámara Celular</Text>
            <Text style={styles.gridSubtitle}>Usar smartphone como sensor</Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity
          style={[styles.scanFullCard, scanning && styles.scanningActive]}
          onPress={scanNetwork}
          disabled={scanning}
        >
          <View style={styles.scanHeader}>
            <Text style={styles.scanIcon}>{scanning ? '📡' : '🔍'}</Text>
            <View style={{ flex: 1, marginLeft: 15 }}>
              <Text style={styles.scanTitle}>
                {scanning ? 'Escaneando subred local...' : 'Escanear Red WiFi Local'}
              </Text>
              <Text style={styles.scanSubtitle}>
                {scanning ? 'Buscando puertos activos en la red...' : 'Localizar cámaras IP automáticas en tu red'}
              </Text>
            </View>
            {scanning && <ActivityIndicator color="#00E676" style={{ marginLeft: 10 }} />}
          </View>
        </TouchableOpacity>
      </View>

      {/* Scan Results */}
      {scanResults.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>CÁMARAS LOCALES ENCONTRADAS</Text>
          {scanResults.map((camera, index) => (
            <TouchableOpacity
              key={index}
              style={styles.resultItem}
              onPress={() => {
                setCameraSource(camera.url);
                setCameraType('auto');
              }}
            >
              <Text style={styles.resultIcon}>📹</Text>
              <View style={styles.resultTextContainer}>
                <Text style={styles.resultTitle}>{camera.url}</Text>
                <Text style={styles.resultSubtitle}>
                  Latencia de red: {camera.response_time}ms
                </Text>
              </View>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {/* Manual Configuration */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>CONSOLA DE AJUSTES MANUALES</Text>

        <Text style={styles.label}>Dirección / Índice de la Cámara</Text>
        <TextInput
          style={styles.input}
          value={cameraSource}
          onChangeText={setCameraSource}
          placeholder="0 (Webcam) | http://..."
          placeholderTextColor="#64748B"
        />

        <Text style={styles.label}>Tipo de Decodificador</Text>
        <View style={styles.typeSelector}>
          {['auto', 'webcam'].map((type) => (
            <TouchableOpacity
              key={type}
              style={[
                styles.typeButton,
                cameraType === type && styles.typeButtonActive,
              ]}
              onPress={() => setCameraType(type)}
            >
              <Text
                style={[
                  styles.typeButtonText,
                  cameraType === type && styles.typeButtonTextActive,
                ]}
              >
                {type.toUpperCase()}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <Text style={styles.label}>Aforo Límite de Sala (personas)</Text>
        <TextInput
          style={styles.input}
          value={maxCapacity}
          onChangeText={setMaxCapacity}
          placeholder="Ej: 50"
          placeholderTextColor="#64748B"
          keyboardType="numeric"
        />

        <TouchableOpacity
          style={styles.applyButton}
          onPress={saveMaxCapacity}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#080C14" />
          ) : (
            <Text style={styles.buttonTextDark}>💾 GUARDAR AFORO MÁXIMO</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.applyButton, { backgroundColor: '#00E676' }]}
          onPress={applyCameraConfig}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#080C14" />
          ) : (
            <Text style={styles.buttonTextDark}>✅ APLICAR NUEVA CÁMARA</Text>
          )}
        </TouchableOpacity>
      </View>

      {/* Instructions for Phone Camera */}
      <View style={styles.infoCard}>
        <Text style={styles.infoTitle}>📱 Pasos para Enlazar tu Celular</Text>
        <Text style={styles.instructionText}>
          1. Descarga la aplicación gratis "IP Webcam" en tu Play Store / App Store.
        </Text>
        <Text style={styles.instructionText}>
          2. Abre la aplicación y presiona la última opción: "Iniciar servidor".
        </Text>
        <Text style={styles.instructionText}>
          3. La cámara se abrirá y mostrará una IP local en pantalla (ej: http://192.168.1.100:8080).
        </Text>
        <Text style={styles.instructionText}>
          4. Copia esa misma dirección agregando "/video" al final en la consola de arriba y presiona Aplicar.
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
  header: {
    backgroundColor: '#0E1324',
    padding: 20,
    paddingTop: 50,
    borderBottomWidth: 1,
    borderColor: '#1E2942',
  },
  backButton: {
    marginBottom: 10,
  },
  backButtonText: {
    color: '#00E5FF',
    fontSize: 14,
    fontWeight: 'bold',
  },
  headerSubtitle: {
    fontSize: 9,
    fontWeight: 'bold',
    color: '#64748B',
    letterSpacing: 2,
    marginBottom: 2,
  },
  title: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  card: {
    backgroundColor: '#101726',
    marginHorizontal: 20,
    marginTop: 20,
    padding: 22,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#1F2942',
  },
  cardTitle: {
    fontSize: 11,
    fontWeight: 'bold',
    color: '#94A3B8',
    marginBottom: 18,
    letterSpacing: 1,
  },
  configRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginVertical: 6,
    borderBottomWidth: 1,
    borderColor: '#1F2942',
    paddingBottom: 6,
  },
  configLabel: {
    fontSize: 13,
    color: '#64748B',
    fontWeight: 'bold',
  },
  configValue: {
    fontSize: 13,
    color: '#FFFFFF',
    fontWeight: 'bold',
  },
  gridRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 15,
  },
  gridItem: {
    flex: 1,
    backgroundColor: '#0F172A',
    borderRadius: 14,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1.5,
  },
  gridIconCircle: {
    width: 50,
    height: 50,
    borderRadius: 25,
    borderWidth: 1.5,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 10,
  },
  gridIcon: {
    fontSize: 22,
  },
  gridTitle: {
    fontSize: 13,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 4,
    textAlign: 'center',
  },
  gridSubtitle: {
    fontSize: 9,
    color: '#64748B',
    textAlign: 'center',
    lineHeight: 12,
  },
  scanFullCard: {
    backgroundColor: '#0F172A',
    borderRadius: 14,
    padding: 16,
    borderWidth: 1.5,
    borderColor: '#00E676',
    shadowColor: '#00E676',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 6,
    elevation: 2,
  },
  scanningActive: {
    borderColor: '#FFD600',
    shadowColor: '#FFD600',
  },
  scanHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  scanIcon: {
    fontSize: 26,
  },
  scanTitle: {
    fontSize: 13,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  scanSubtitle: {
    fontSize: 10,
    color: '#64748B',
    marginTop: 2,
  },
  resultItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 14,
    backgroundColor: 'rgba(0, 229, 255, 0.1)',
    borderRadius: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#00E5FF',
  },
  resultIcon: {
    fontSize: 20,
    marginRight: 12,
  },
  resultTextContainer: {
    flex: 1,
  },
  resultTitle: {
    fontSize: 13,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  resultSubtitle: {
    fontSize: 11,
    color: '#94A3B8',
  },
  label: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#94A3B8',
    marginTop: 15,
    marginBottom: 8,
    letterSpacing: 0.5,
  },
  input: {
    backgroundColor: '#0F172A',
    padding: 14,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#1F2942',
    fontSize: 14,
    color: '#FFFFFF',
  },
  typeSelector: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 15,
  },
  typeButton: {
    backgroundColor: '#0F172A',
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 10,
    marginRight: 8,
    marginTop: 8,
    borderWidth: 1,
    borderColor: '#1F2942',
  },
  typeButtonActive: {
    backgroundColor: '#00E5FF',
    borderColor: '#00E5FF',
  },
  typeButtonText: {
    fontSize: 11,
    fontWeight: 'bold',
    color: '#64748B',
  },
  typeButtonTextActive: {
    color: '#080C14',
  },
  applyButton: {
    backgroundColor: '#00E5FF',
    padding: 16,
    borderRadius: 14,
    alignItems: 'center',
    marginTop: 10,
    shadowColor: '#00E5FF',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 3,
  },
  buttonTextDark: {
    color: '#080C14',
    fontSize: 13,
    fontWeight: 'bold',
    letterSpacing: 1,
  },
  disabledButton: {
    opacity: 0.4,
  },
  infoCard: {
    backgroundColor: '#0F1A2C',
    marginHorizontal: 20,
    marginTop: 20,
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
  instructionText: {
    fontSize: 12,
    color: '#94A3B8',
    marginVertical: 5,
    lineHeight: 20,
  },
});


