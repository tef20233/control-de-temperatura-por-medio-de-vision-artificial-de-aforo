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
import { LineChart } from 'react-native-chart-kit';
import { Dimensions } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { apiService } from '../services/api';
import { COLORS, TIME_RANGES } from '../utils/constants';

const screenWidth = Dimensions.get('window').width;

export default function HistoryScreen() {
  const [loading, setLoading] = useState(true);
  const [selectedRange, setSelectedRange] = useState('today');
  const [historyData, setHistoryData] = useState(null);

  useEffect(() => {
    loadHistory();
  }, [selectedRange]);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const data = await apiService.getHistory();
      setHistoryData(data);
    } catch (error) {
      console.error('Error loading history:', error);
      Alert.alert('Error', 'No se pudo cargar el historial');
    } finally {
      setLoading(false);
    }
  };

  const getChartData = () => {
    if (!historyData || !historyData.history || historyData.history.length === 0) {
      return {
        labels: [''],
        datasets: [{ data: [0] }],
      };
    }

    // Tomar máximo 20 puntos para el gráfico
    const points = historyData.history.slice(-20);
    
    return {
      labels: points.map((_, index) => index % 5 === 0 ? index.toString() : ''),
      datasets: [{
        data: points.map(p => p.count),
        color: (opacity = 1) => `rgba(59, 130, 246, ${opacity})`,
        strokeWidth: 2,
      }],
    };
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.loadingText}>Cargando historial...</Text>
      </View>
    );
  }

  const chartData = getChartData();
  const avgOccupancy = historyData?.avg_occupancy || 0;
  const peakCount = historyData?.peak_count || 0;

  return (
    <ScrollView style={styles.container}>
      {/* Selector de rango de tiempo */}
      <View style={styles.rangeSelector}>
        {TIME_RANGES.map((range) => (
          <TouchableOpacity
            key={range.value}
            style={[
              styles.rangeButton,
              selectedRange === range.value && styles.rangeButtonActive,
            ]}
            onPress={() => setSelectedRange(range.value)}
          >
            <Text
              style={[
                styles.rangeButtonText,
                selectedRange === range.value && styles.rangeButtonTextActive,
              ]}
            >
              {range.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Gráfica de historial */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>📊 HISTORIAL DE OCUPACIÓN</Text>
        
        {historyData && historyData.history && historyData.history.length > 0 ? (
          <LineChart
            data={chartData}
            width={screenWidth - 60}
            height={220}
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
                r: '4',
                strokeWidth: '2',
                stroke: COLORS.primary,
              },
            }}
            bezier
            style={styles.chart}
          />
        ) : (
          <View style={styles.noDataContainer}>
            <Ionicons name="analytics-outline" size={60} color={COLORS.textLight} />
            <Text style={styles.noDataText}>No hay datos disponibles</Text>
          </View>
        )}
      </View>

      {/* Estadísticas */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>📈 ESTADÍSTICAS</Text>
        
        <View style={styles.statRow}>
          <View style={styles.statCard}>
            <Ionicons name="trending-up" size={32} color={COLORS.primary} />
            <Text style={styles.statValue}>
              {historyData?.history?.length || 0}
            </Text>
            <Text style={styles.statLabel}>Registros totales</Text>
          </View>

          <View style={styles.statCard}>
            <Ionicons name="bar-chart" size={32} color={COLORS.secondary} />
            <Text style={styles.statValue}>
              {(avgOccupancy * 100).toFixed(0)}%
            </Text>
            <Text style={styles.statLabel}>Ocupación promedio</Text>
          </View>
        </View>

        <View style={styles.statRow}>
          <View style={styles.statCard}>
            <Ionicons name="arrow-up-circle" size={32} color={COLORS.danger} />
            <Text style={styles.statValue}>{peakCount}</Text>
            <Text style={styles.statLabel}>Pico de personas</Text>
          </View>

          <View style={styles.statCard}>
            <Ionicons name="people" size={32} color={COLORS.success} />
            <Text style={styles.statValue}>
              {historyData?.history && historyData.history.length > 0
                ? Math.round(
                    historyData.history.reduce((sum, h) => sum + h.count, 0) /
                      historyData.history.length
                  )
                : 0}
            </Text>
            <Text style={styles.statLabel}>Promedio personas</Text>
          </View>
        </View>
      </View>

      {/* Listado de registros recientes */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>📋 REGISTROS RECIENTES</Text>
        
        {historyData && historyData.history && historyData.history.length > 0 ? (
          <View style={styles.recordsList}>
            {historyData.history.slice(-10).reverse().map((record, index) => (
              <View key={index} style={styles.recordItem}>
                <View style={styles.recordIcon}>
                  <Ionicons name="people" size={20} color={COLORS.primary} />
                </View>
                <View style={styles.recordInfo}>
                  <Text style={styles.recordCount}>
                    {record.count} personas
                  </Text>
                  <Text style={styles.recordTime}>
                    {new Date(record.timestamp).toLocaleString('es-ES', {
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit',
                    })}
                  </Text>
                </View>
                <View style={styles.recordBadge}>
                  <Text style={styles.recordFps}>
                    {record.fps?.toFixed(1) || '0.0'} FPS
                  </Text>
                </View>
              </View>
            ))}
          </View>
        ) : (
          <Text style={styles.noDataText}>No hay registros disponibles</Text>
        )}
      </View>

      {/* Botón de actualizar */}
      <TouchableOpacity style={styles.refreshButton} onPress={loadHistory}>
        <Ionicons name="refresh" size={24} color="#fff" />
        <Text style={styles.refreshButtonText}>ACTUALIZAR DATOS</Text>
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
  rangeSelector: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginHorizontal: 20,
    marginTop: 20,
    marginBottom: 10,
  },
  rangeButton: {
    flex: 1,
    padding: 12,
    marginHorizontal: 5,
    backgroundColor: COLORS.card,
    borderRadius: 8,
    borderWidth: 2,
    borderColor: COLORS.border,
    alignItems: 'center',
  },
  rangeButtonActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  rangeButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
  },
  rangeButtonTextActive: {
    color: '#fff',
  },
  card: {
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
  cardTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: COLORS.textLight,
    marginBottom: 15,
    letterSpacing: 1,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  noDataContainer: {
    padding: 40,
    alignItems: 'center',
  },
  noDataText: {
    marginTop: 10,
    fontSize: 16,
    color: COLORS.textLight,
    textAlign: 'center',
  },
  statRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 15,
  },
  statCard: {
    flex: 1,
    backgroundColor: COLORS.background,
    padding: 15,
    marginHorizontal: 5,
    borderRadius: 8,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: COLORS.text,
    marginVertical: 5,
  },
  statLabel: {
    fontSize: 12,
    color: COLORS.textLight,
    textAlign: 'center',
  },
  recordsList: {
    gap: 10,
  },
  recordItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    backgroundColor: COLORS.background,
    borderRadius: 8,
  },
  recordIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#e0f2fe',
    justifyContent: 'center',
    alignItems: 'center',
  },
  recordInfo: {
    flex: 1,
    marginLeft: 12,
  },
  recordCount: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  recordTime: {
    fontSize: 12,
    color: COLORS.textLight,
    marginTop: 2,
  },
  recordBadge: {
    backgroundColor: '#dbeafe',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 12,
  },
  recordFps: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.primary,
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
