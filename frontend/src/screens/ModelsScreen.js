import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { apiService } from '../services/api';
import { COLORS } from '../utils/constants';

export default function ModelsScreen() {
  const [loading, setLoading] = useState(true);
  const [modelsData, setModelsData] = useState(null);

  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    setLoading(true);
    try {
      const data = await apiService.getModels();
      setModelsData(data);
    } catch (error) {
      console.error('Error loading models:', error);
      Alert.alert('Error', 'No se pudo cargar información de modelos');
    } finally {
      setLoading(false);
    }
  };

  const getModelColor = (loaded) => {
    return loaded ? COLORS.success : COLORS.textLight;
  };

  const getModelIcon = (loaded) => {
    return loaded ? 'checkmark-circle' : 'close-circle';
  };

  const renderModelCard = (modelName, modelInfo) => {
    const isLoaded = modelInfo.loaded;
    
    return (
      <View key={modelName} style={styles.modelCard}>
        <View style={styles.modelHeader}>
          <Ionicons
            name={getModelIcon(isLoaded)}
            size={32}
            color={getModelColor(isLoaded)}
          />
          <View style={styles.modelTitle}>
            <Text style={styles.modelName}>
              {modelName.toUpperCase()}
            </Text>
            <Text style={styles.modelVariant}>
              {modelName === 'yolov8n' && '(Nano - Más rápido)'}
              {modelName === 'yolov8s' && '(Small - Equilibrado)'}
              {modelName === 'yolov8m' && '(Medium - Preciso)'}
              {modelName === 'yolov8l' && '(Large - Máxima precisión)'}
            </Text>
          </View>
          <View style={[styles.statusBadge, isLoaded && styles.statusBadgeActive]}>
            <Text style={[styles.statusText, isLoaded && styles.statusTextActive]}>
              {isLoaded ? 'ACTIVO' : 'INACTIVO'}
            </Text>
          </View>
        </View>

        {isLoaded ? (
          <View style={styles.modelMetrics}>
            {modelInfo.precision && (
              <View style={styles.metricRow}>
                <Text style={styles.metricLabel}>Precisión:</Text>
                <Text style={styles.metricValue}>
                  {(modelInfo.precision * 100).toFixed(1)}%
                </Text>
              </View>
            )}
            
            {modelInfo.recall && (
              <View style={styles.metricRow}>
                <Text style={styles.metricLabel}>Recall:</Text>
                <Text style={styles.metricValue}>
                  {(modelInfo.recall * 100).toFixed(1)}%
                </Text>
              </View>
            )}
            
            {modelInfo.map50 && (
              <View style={styles.metricRow}>
                <Text style={styles.metricLabel}>mAP50:</Text>
                <Text style={styles.metricValue}>
                  {(modelInfo.map50 * 100).toFixed(1)}%
                </Text>
              </View>
            )}

            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>Archivo:</Text>
              <Text style={styles.metricValueSmall}>{modelInfo.path}</Text>
            </View>

            {modelInfo.parameters && (
              <View style={styles.metricRow}>
                <Text style={styles.metricLabel}>Parámetros:</Text>
                <Text style={styles.metricValue}>
                  {(modelInfo.parameters / 1000000).toFixed(1)}M
                </Text>
              </View>
            )}
          </View>
        ) : (
          <View style={styles.modelUnavailable}>
            <Ionicons name="alert-circle-outline" size={24} color={COLORS.textLight} />
            <Text style={styles.unavailableText}>
              {modelInfo.message || 'Modelo no disponible'}
            </Text>
            <Text style={styles.unavailableHint}>
              Entrena este modelo para mejorar la precisión del sistema
            </Text>
          </View>
        )}
      </View>
    );
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.loadingText}>Cargando modelos...</Text>
      </View>
    );
  }

  const models = modelsData?.models || {};
  const loadedCount = Object.values(models).filter(m => m.loaded).length;
  const totalCount = Object.keys(models).length;

  return (
    <ScrollView style={styles.container}>
      {/* Resumen de modelos */}
      <View style={styles.summaryCard}>
        <Text style={styles.summaryTitle}>ESTADO DE MODELOS YOLO</Text>
        <View style={styles.summaryRow}>
          <View style={styles.summaryItem}>
            <Text style={styles.summaryValue}>{loadedCount}</Text>
            <Text style={styles.summaryLabel}>Cargados</Text>
          </View>
          <View style={styles.summaryDivider} />
          <View style={styles.summaryItem}>
            <Text style={styles.summaryValue}>{totalCount - loadedCount}</Text>
            <Text style={styles.summaryLabel}>Faltantes</Text>
          </View>
          <View style={styles.summaryDivider} />
          <View style={styles.summaryItem}>
            <Text style={styles.summaryValue}>{totalCount}</Text>
            <Text style={styles.summaryLabel}>Total</Text>
          </View>
        </View>

        {/* Barra de progreso */}
        <View style={styles.progressContainer}>
          <View style={styles.progressBar}>
            <View
              style={[
                styles.progressFill,
                { width: `${(loadedCount / totalCount) * 100}%` },
              ]}
            />
          </View>
          <Text style={styles.progressText}>
            {((loadedCount / totalCount) * 100).toFixed(0)}% completo
          </Text>
        </View>
      </View>

      {/* Cards de modelos individuales */}
      {Object.entries(models).map(([modelName, modelInfo]) =>
        renderModelCard(modelName, modelInfo)
      )}

      {/* Información adicional */}
      <View style={styles.infoCard}>
        <Text style={styles.infoTitle}>ℹ️ Sobre los Modelos</Text>
        <Text style={styles.infoText}>
          • <Text style={styles.infoBold}>YOLOv8n</Text>: Más rápido, ideal para dispositivos con recursos limitados
        </Text>
        <Text style={styles.infoText}>
          • <Text style={styles.infoBold}>YOLOv8s</Text>: Balance entre velocidad y precisión
        </Text>
        <Text style={styles.infoText}>
          • <Text style={styles.infoBold}>YOLOv8m</Text>: Mayor precisión, velocidad moderada
        </Text>
        <Text style={styles.infoText}>
          • <Text style={styles.infoBold}>YOLOv8l</Text>: Máxima precisión, requiere más recursos
        </Text>
        <Text style={styles.infoText}>
          {'\n'}El sistema usa <Text style={styles.infoBold}>ensemble</Text> para combinar múltiples modelos y mejorar la precisión general.
        </Text>
      </View>

      {/* Botón de actualizar */}
      <TouchableOpacity style={styles.refreshButton} onPress={loadModels}>
        <Ionicons name="refresh" size={24} color="#fff" />
        <Text style={styles.refreshButtonText}>ACTUALIZAR ESTADO</Text>
      </TouchableOpacity>
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
  summaryCard: {
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
  summaryTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: COLORS.textLight,
    marginBottom: 20,
    letterSpacing: 1,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    marginBottom: 20,
  },
  summaryItem: {
    alignItems: 'center',
  },
  summaryValue: {
    fontSize: 36,
    fontWeight: 'bold',
    color: COLORS.primary,
  },
  summaryLabel: {
    fontSize: 14,
    color: COLORS.textLight,
    marginTop: 5,
  },
  summaryDivider: {
    width: 1,
    height: 50,
    backgroundColor: COLORS.border,
  },
  progressContainer: {
    marginTop: 10,
  },
  progressBar: {
    height: 12,
    backgroundColor: COLORS.border,
    borderRadius: 6,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: COLORS.primary,
    borderRadius: 6,
  },
  progressText: {
    fontSize: 12,
    color: COLORS.textLight,
    textAlign: 'center',
    marginTop: 8,
  },
  modelCard: {
    backgroundColor: COLORS.card,
    marginHorizontal: 20,
    marginTop: 15,
    padding: 20,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  modelHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 15,
  },
  modelTitle: {
    flex: 1,
    marginLeft: 12,
  },
  modelName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  modelVariant: {
    fontSize: 12,
    color: COLORS.textLight,
    marginTop: 2,
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    backgroundColor: COLORS.border,
  },
  statusBadgeActive: {
    backgroundColor: '#d1fae5',
  },
  statusText: {
    fontSize: 11,
    fontWeight: 'bold',
    color: COLORS.textLight,
  },
  statusTextActive: {
    color: COLORS.success,
  },
  modelMetrics: {
    backgroundColor: COLORS.background,
    padding: 15,
    borderRadius: 8,
    gap: 10,
  },
  metricRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 14,
    color: COLORS.textLight,
  },
  metricValue: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  metricValueSmall: {
    fontSize: 12,
    color: COLORS.textLight,
    flex: 1,
    textAlign: 'right',
  },
  modelUnavailable: {
    alignItems: 'center',
    padding: 20,
    backgroundColor: COLORS.background,
    borderRadius: 8,
  },
  unavailableText: {
    fontSize: 14,
    color: COLORS.textLight,
    marginTop: 10,
    textAlign: 'center',
  },
  unavailableHint: {
    fontSize: 12,
    color: COLORS.textLight,
    marginTop: 5,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  infoCard: {
    backgroundColor: '#fef3c7',
    marginHorizontal: 20,
    marginTop: 20,
    marginBottom: 10,
    padding: 20,
    borderRadius: 12,
    borderLeftWidth: 4,
    borderLeftColor: COLORS.warning,
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
    lineHeight: 20,
  },
  infoBold: {
    fontWeight: 'bold',
  },
  refreshButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
    marginHorizontal: 20,
    marginVertical: 30,
    padding: 15,
    borderRadius: 12,
    gap: 10,
  },
  refreshButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
});
