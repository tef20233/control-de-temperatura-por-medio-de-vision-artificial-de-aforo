import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Alert,
  Switch,
  ActivityIndicator,
} from 'react-native';
import { Picker } from '@react-native-picker/picker';
import Slider from '@react-native-community/slider';
import { Ionicons } from '@expo/vector-icons';

import { apiService } from '../services/api';
import { COLORS, ENSEMBLE_STRATEGIES, API_CONFIG } from '../utils/constants';

export default function ConfigScreen() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [config, setConfig] = useState({
    max_capacity: 50,
    ensemble_strategy: 'average',
    confidence_threshold: 0.5,
    enable_privacy: true,
  });
  const [serverUrl, setServerUrl] = useState(API_CONFIG.BASE_URL);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const data = await apiService.getConfig();
      setConfig(data);
      setLoading(false);
    } catch (error) {
      console.error('Error loading config:', error);
      Alert.alert('Error', 'No se pudo cargar la configuración');
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await apiService.updateConfig(config);
      Alert.alert('Éxito', 'Configuración guardada correctamente');
    } catch (error) {
      Alert.alert('Error', 'No se pudo guardar la configuración');
    } finally {
      setSaving(false);
    }
  };

  const getStrategyDescription = (value) => {
    const strategy = ENSEMBLE_STRATEGIES.find(s => s.value === value);
    return strategy ? strategy.description : '';
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>AFORO MÁXIMO</Text>
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            value={config.max_capacity.toString()}
            onChangeText={(text) => {
              const value = parseInt(text) || 0;
              setConfig({ ...config, max_capacity: value });
            }}
            keyboardType="number-pad"
            placeholder="Ej: 50"
          />
          <Text style={styles.inputLabel}>personas</Text>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>ESTRATEGIA DE ENSEMBLE</Text>
        <View style={styles.pickerContainer}>
          <Picker
            selectedValue={config.ensemble_strategy}
            onValueChange={(value) => setConfig({ ...config, ensemble_strategy: value })}
            style={styles.picker}
          >
            {ENSEMBLE_STRATEGIES.map((strategy) => (
              <Picker.Item
                key={strategy.value}
                label={strategy.label}
                value={strategy.value}
              />
            ))}
          </Picker>
        </View>
        <Text style={styles.description}>
          {getStrategyDescription(config.ensemble_strategy)}
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>UMBRAL DE CONFIANZA</Text>
        <View style={styles.sliderContainer}>
          <Slider
            style={styles.slider}
            minimumValue={0}
            maximumValue={1}
            step={0.05}
            value={config.confidence_threshold}
            onValueChange={(value) => setConfig({ ...config, confidence_threshold: value })}
            minimumTrackTintColor={COLORS.primary}
            maximumTrackTintColor={COLORS.border}
            thumbTintColor={COLORS.primary}
          />
          <Text style={styles.sliderValue}>
            {config.confidence_threshold.toFixed(2)}
          </Text>
        </View>
        <Text style={styles.description}>
          Detecciones con confianza menor a este valor serán ignoradas
        </Text>
      </View>

      <View style={styles.section}>
        <View style={styles.switchRow}>
          <View style={styles.switchLabel}>
            <Ionicons name="eye-off" size={24} color={COLORS.text} />
            <Text style={styles.sectionTitle}>PRIVACIDAD</Text>
          </View>
          <Switch
            value={config.enable_privacy}
            onValueChange={(value) => setConfig({ ...config, enable_privacy: value })}
            trackColor={{ false: COLORS.border, true: COLORS.primary }}
            thumbColor={config.enable_privacy ? COLORS.primary : COLORS.textLight}
          />
        </View>
        <Text style={styles.description}>
          Difumina rostros en el video en tiempo real
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>URL DEL SERVIDOR</Text>
        <TextInput
          style={styles.input}
          value={serverUrl}
          onChangeText={setServerUrl}
          placeholder="http://192.168.1.6:5000"
          autoCapitalize="none"
          autoCorrect={false}
        />
        <Text style={styles.description}>
          Cambia esta URL si el backend está en otra dirección
        </Text>
      </View>

      <TouchableOpacity
        style={[styles.saveButton, saving && styles.saveButtonDisabled]}
        onPress={handleSave}
        disabled={saving}
      >
        {saving ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <>
            <Ionicons name="save" size={24} color="#fff" />
            <Text style={styles.saveButtonText}>GUARDAR CAMBIOS</Text>
          </>
        )}
      </TouchableOpacity>

      {/* Información del sistema */}
      <View style={styles.infoCard}>
        <Text style={styles.infoTitle}>ℹ️ Información</Text>
        <Text style={styles.infoText}>• Los cambios se aplican inmediatamente</Text>
        <Text style={styles.infoText}>• El aforo máximo debe ser mayor a 0</Text>
        <Text style={styles.infoText}>• La privacidad requiere recursos adicionales</Text>
        <Text style={styles.infoText}>• Reinicia la cámara después de cambios importantes</Text>
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
  section: {
    backgroundColor: COLORS.card,
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
  sectionTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: COLORS.textLight,
    marginBottom: 15,
    letterSpacing: 1,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  input: {
    flex: 1,
    fontSize: 18,
    padding: 15,
    backgroundColor: COLORS.background,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  inputLabel: {
    fontSize: 16,
    color: COLORS.textLight,
  },
  pickerContainer: {
    backgroundColor: COLORS.background,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.border,
    overflow: 'hidden',
  },
  picker: {
    height: 50,
  },
  description: {
    fontSize: 14,
    color: COLORS.textLight,
    marginTop: 10,
    fontStyle: 'italic',
  },
  sliderContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 15,
  },
  slider: {
    flex: 1,
    height: 40,
  },
  sliderValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: COLORS.text,
    minWidth: 50,
    textAlign: 'center',
  },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  switchLabel: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  saveButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
    marginHorizontal: 20,
    marginVertical: 30,
    padding: 18,
    borderRadius: 12,
    gap: 10,
  },
  saveButtonDisabled: {
    backgroundColor: COLORS.textLight,
  },
  saveButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  infoCard: {
    backgroundColor: '#e0f2fe',
    marginHorizontal: 20,
    marginBottom: 30,
    padding: 20,
    borderRadius: 12,
    borderLeftWidth: 4,
    borderLeftColor: COLORS.primary,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: COLORS.text,
    marginBottom: 10,
  },
  infoText: {
    fontSize: 14,
    color: COLORS.text,
    marginVertical: 3,
  },
});
