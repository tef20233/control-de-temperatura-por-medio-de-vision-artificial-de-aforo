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

  const testCamera = async (url) => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE_URL}/api/camera/test`, {
        camera_url: url,
        timeout: 5,
      });

      if (response.data.success) {
        Alert.alert('✅ Conexión Exitosa', 'La cámara está accesible');
        return true;
      } else {
        Alert.alert('❌ Conexión Fallida', response.data.error || 'No se pudo conectar');
        return false;
      }
    } catch (error) {
      let errorMsg = 'No se pudo probar la conexión';
      if (error.response) {
        errorMsg = error.response.data.error || errorMsg;
      } else if (error.message.includes('Network Error')) {
        errorMsg = 'Error de red. Verifica que el backend esté ejecutándose.';
      }
      Alert.alert('❌ Error', errorMsg);
      return false;
    } finally {
      setLoading(false);
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
        window.alert('✅ Éxito\nCámara cambiada correctamente');
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
      window.alert(`❌ Error al Cambiar Cámara\n${errorMsg}`);
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
      window.alert('⚠️ Campo Requerido\nPor favor ingresa una fuente de cámara');
      return;
    }

    const confirmed = window.confirm(`Confirmar Cambio\n¿Cambiar a: ${cameraSource}?`);
    if (confirmed) {
      changeCamera(cameraSource, cameraType);
    }
  };

  const usePhoneCamera = () => {
    Alert.alert(
      '📱 Usar Cámara del Celular',
      'Para usar la cámara de este celular:\n\n1. Instala una app de streaming (ej: IP Webcam)\n2. Inicia el stream en la app\n3. Ingresa la URL que proporciona la app\n\nEjemplo: http://192.168.1.X:8080',
      [{ text: 'Entendido' }]
    );
  };

  return (
    <ScrollView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={onBack} style={styles.backButton}>
          <Text style={styles.backButtonText}>← Volver</Text>
        </TouchableOpacity>
        <Text style={styles.title}>⚙️ Configurar Cámara</Text>
      </View>

      {/* Current Configuration */}
      {currentConfig && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>CONFIGURACIÓN ACTUAL</Text>
          <Text style={styles.configText}>
            Fuente: {currentConfig.camera_source}
          </Text>
          <Text style={styles.configText}>
            Tipo: {currentConfig.camera_type}
          </Text>
          <Text style={styles.configText}>
            Aforo máximo:{' '}
            {currentConfig.max_capacity !== undefined ? currentConfig.max_capacity : 'No definido'}
          </Text>
        </View>
      )}

      {/* Quick Options */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>OPCIONES RÁPIDAS</Text>

        <TouchableOpacity
          style={styles.optionButton}
          onPress={() => {
            setCameraSource('0');
            setCameraType('webcam');
          }}
        >
          <Text style={styles.optionIcon}>💻</Text>
          <View style={styles.optionTextContainer}>
            <Text style={styles.optionTitle}>Webcam del PC</Text>
            <Text style={styles.optionSubtitle}>Usar cámara conectada al PC</Text>
          </View>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.optionButton}
          onPress={usePhoneCamera}
        >
          <Text style={styles.optionIcon}>📱</Text>
          <View style={styles.optionTextContainer}>
            <Text style={styles.optionTitle}>Cámara de este Celular</Text>
            <Text style={styles.optionSubtitle}>Instrucciones para usar esta cámara</Text>
          </View>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.optionButton}
          onPress={scanNetwork}
          disabled={scanning}
        >
          <Text style={styles.optionIcon}>🔍</Text>
          <View style={styles.optionTextContainer}>
            <Text style={styles.optionTitle}>
              {scanning ? 'Escaneando...' : 'Buscar Cámaras en Red'}
            </Text>
            <Text style={styles.optionSubtitle}>
              Detectar automáticamente cámaras IP
            </Text>
          </View>
          {scanning && <ActivityIndicator color="#3b82f6" />}
        </TouchableOpacity>
      </View>

      {/* Scan Results */}
      {scanResults.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>CÁMARAS ENCONTRADAS</Text>
          {scanResults.map((camera, index) => (
            <TouchableOpacity
              key={index}
              style={styles.resultItem}
              onPress={() => {
                setCameraSource(camera.url);
                setCameraType('tapo');
              }}
            >
              <Text style={styles.resultIcon}>📹</Text>
              <View style={styles.resultTextContainer}>
                <Text style={styles.resultTitle}>{camera.url}</Text>
                <Text style={styles.resultSubtitle}>
                  Tiempo: {camera.response_time}ms
                </Text>
              </View>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {/* Manual Configuration */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>CONFIGURACIÓN MANUAL</Text>

        <Text style={styles.label}>Fuente de Cámara</Text>
        <TextInput
          style={styles.input}
          value={cameraSource}
          onChangeText={setCameraSource}
          placeholder="0 (webcam) | rtsp://... | http://..."
          placeholderTextColor="#9ca3af"
        />

        <Text style={styles.label}>Tipo de Cámara</Text>
        <View style={styles.typeSelector}>
          {['auto', 'webcam', 'rtsp', 'tapo', 'mjpeg'].map((type) => (
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

        <Text style={styles.label}>Aforo máximo (personas)</Text>
        <TextInput
          style={styles.input}
          value={maxCapacity}
          onChangeText={setMaxCapacity}
          placeholder="Ej: 100"
          placeholderTextColor="#9ca3af"
          keyboardType="numeric"
        />

        <TouchableOpacity
          style={styles.testButton}
          onPress={() => testCamera(cameraSource)}
          disabled={loading || !cameraSource.startsWith('http')}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>🔍 PROBAR CONEXIÓN</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.applyButton}
          onPress={saveMaxCapacity}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>💾 GUARDAR AFORO MÁXIMO</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.applyButton}
          onPress={applyCameraConfig}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>✅ APLICAR CAMBIOS</Text>
          )}
        </TouchableOpacity>
      </View>

      {/* Examples */}
      <View style={styles.infoCard}>
        <Text style={styles.infoTitle}>💡 Ejemplos de URL</Text>
        <Text style={styles.exampleText}>• Webcam PC: 0</Text>
        <Text style={styles.exampleText}>
          • IP Webcam (celular): http://192.168.1.X:8080
        </Text>
        <Text style={styles.exampleText}>
          • Cámara RTSP: rtsp://192.168.1.X:554/stream
        </Text>
        <Text style={styles.exampleText}>
          • Cámara Tapo: http://192.168.1.X:5001
        </Text>
        <Text style={styles.exampleText}>
          • DroidCam: http://192.168.1.X:4747/video
        </Text>
      </View>

      {/* Instructions for Phone Camera */}
      <View style={styles.infoCard}>
        <Text style={styles.infoTitle}>📱 Usar Cámara del Celular</Text>
        <Text style={styles.instructionText}>
          1. Descarga "IP Webcam" desde Play Store o App Store
        </Text>
        <Text style={styles.instructionText}>
          2. Abre la app y presiona "Iniciar servidor"
        </Text>
        <Text style={styles.instructionText}>
          3. La app mostrará una URL (ej: http://192.168.1.100:8080)
        </Text>
        <Text style={styles.instructionText}>
          4. Agrega "/video" al final de la URL
        </Text>
        <Text style={styles.instructionText}>
          5. Ingresa la URL completa aquí y selecciona tipo "auto"
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
  header: {
    backgroundColor: '#3b82f6',
    padding: 20,
    paddingTop: 40,
  },
  backButton: {
    marginBottom: 10,
  },
  backButtonText: {
    color: '#fff',
    fontSize: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  card: {
    backgroundColor: '#fff',
    marginHorizontal: 20,
    marginTop: 20,
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
  configText: {
    fontSize: 14,
    color: '#1f2937',
    marginVertical: 5,
  },
  optionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 15,
    backgroundColor: '#f9fafb',
    borderRadius: 8,
    marginBottom: 10,
  },
  optionIcon: {
    fontSize: 32,
    marginRight: 15,
  },
  optionTextContainer: {
    flex: 1,
  },
  optionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1f2937',
  },
  optionSubtitle: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 2,
  },
  resultItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#dbeafe',
    borderRadius: 8,
    marginBottom: 8,
  },
  resultIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  resultTextContainer: {
    flex: 1,
  },
  resultTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#1f2937',
  },
  resultSubtitle: {
    fontSize: 12,
    color: '#6b7280',
  },
  label: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#1f2937',
    marginTop: 15,
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#f9fafb',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    fontSize: 14,
  },
  typeSelector: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 15,
  },
  typeButton: {
    backgroundColor: '#f3f4f6',
    paddingVertical: 8,
    paddingHorizontal: 15,
    borderRadius: 8,
    marginRight: 8,
    marginTop: 8,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  typeButtonActive: {
    backgroundColor: '#3b82f6',
    borderColor: '#3b82f6',
  },
  typeButtonText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#6b7280',
  },
  typeButtonTextActive: {
    color: '#fff',
  },
  testButton: {
    backgroundColor: '#f59e0b',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 15,
  },
  applyButton: {
    backgroundColor: '#10b981',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 10,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  infoCard: {
    backgroundColor: '#fef3c7',
    marginHorizontal: 20,
    marginTop: 20,
    marginBottom: 20,
    padding: 20,
    borderRadius: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#f59e0b',
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  exampleText: {
    fontSize: 13,
    marginVertical: 4,
    lineHeight: 20,
  },
  instructionText: {
    fontSize: 13,
    marginVertical: 5,
    lineHeight: 22,
  },
});
