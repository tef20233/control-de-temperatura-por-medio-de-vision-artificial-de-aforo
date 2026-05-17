import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
  StatusBar,
  Dimensions,
} from 'react-native';

const { width } = Dimensions.get('window');

export default function WelcomeScreen({ onEnter }) {
  const [loadingComplete, setLoadingComplete] = useState(false);
  
  // Animation values
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const pulseAnim = useRef(new Animated.Value(0.9)).current;
  const progressAnim = useRef(new Animated.Value(0)).current;
  const buttonFadeAnim = useRef(new Animated.Value(0)).current;
  const progressPercent = useRef(new Animated.Value(0)).current;
  const [percentText, setPercentText] = useState('0%');

  useEffect(() => {
    // 1. Fade in whole screen contents
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 1000,
      useNativeDriver: true,
    }).start();

    // 2. Pulse loop for radar glow
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.15,
          duration: 1500,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 0.9,
          duration: 1500,
          useNativeDriver: true,
        }),
      ])
    ).start();

    // 3. Fake system initialization loading bar
    Animated.timing(progressAnim, {
      toValue: 1,
      duration: 3500,
      useNativeDriver: false, // Requerido para animar ancho
    }).start(({ finished }) => {
      if (finished) {
        setLoadingComplete(true);
        // Fade in button once loaded
        Animated.timing(buttonFadeAnim, {
          toValue: 1,
          duration: 800,
          useNativeDriver: true,
        }).start();
      }
    });

    // Animate loading text percentage
    const listenerId = progressAnim.addListener(({ value }) => {
      setPercentText(`${Math.round(value * 100)}%`);
    });

    return () => {
      progressAnim.removeListener(listenerId);
    };
  }, []);

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#080C14" />
      
      <Animated.View style={[styles.content, { opacity: fadeAnim }]}>
        
        {/* Subtitle */}
        <Text style={styles.tagline}>CENTRO DE INTELIGENCIA DE SEGURIDAD</Text>
        
        {/* Title */}
        <Text style={styles.title}>AFORO IA</Text>
        <Text style={styles.titleGradient}>& HVAC SYSTEM</Text>

        {/* Pulse Radar Decoration */}
        <View style={styles.radarContainer}>
          <Animated.View 
            style={[
              styles.radarRing, 
              styles.radarRingOuter, 
              { transform: [{ scale: pulseAnim }] }
            ]} 
          />
          <Animated.View 
            style={[
              styles.radarRing, 
              styles.radarRingMiddle, 
              { transform: [{ scale: pulseAnim }] }
            ]} 
          />
          <View style={styles.radarCenter}>
            <Text style={styles.radarIcon}>👁‍🗨</Text>
          </View>
        </View>

        {/* Status System Initializing */}
        <View style={styles.statusBox}>
          <Text style={styles.statusTitle}>
            {loadingComplete ? '🛰️ ENLACE SEGURO CON LA NUBE' : '🔧 CARGANDO MÓDULOS DE VISIÓN...'}
          </Text>
          
          {/* Progress Bar Container */}
          <View style={styles.progressContainer}>
            <Animated.View 
              style={[
                styles.progressFill, 
                {
                  width: progressAnim.interpolate({
                    inputRange: [0, 1],
                    outputRange: ['0%', '100%'],
                  })
                }
              ]} 
            />
          </View>
          <Text style={styles.percentText}>{percentText}</Text>
        </View>

        {/* Action Button Container */}
        <View style={styles.buttonContainer}>
          {loadingComplete ? (
            <Animated.View style={{ opacity: buttonFadeAnim, width: '100%' }}>
              <TouchableOpacity style={styles.enterButton} onPress={onEnter}>
                <Text style={styles.enterButtonText}>INICIAR MONITOREO</Text>
              </TouchableOpacity>
            </Animated.View>
          ) : (
            <Text style={styles.initializingText}>INICIALIZANDO CONEXIÓN SERIAL COM6...</Text>
          )}
        </View>

        {/* Graduate Project Metadata Footer */}
        <View style={styles.metaFooter}>
          <Text style={styles.metaText}>PROYECTO DE GRADO INTEGRADO</Text>
          <Text style={styles.metaSubtext}>VISIÓN ARTIFICIAL & INTERNET DE LAS COSAS</Text>
        </View>

      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#080C14',
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    width: '100%',
    height: '100%',
    padding: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  tagline: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#7C4DFF',
    letterSpacing: 3,
    marginBottom: 10,
    textAlign: 'center',
  },
  title: {
    fontSize: 48,
    fontWeight: '900',
    color: '#FFFFFF',
    letterSpacing: 1,
    textAlign: 'center',
  },
  titleGradient: {
    fontSize: 34,
    fontWeight: '900',
    color: '#00E5FF',
    letterSpacing: 2,
    marginBottom: 40,
    textAlign: 'center',
    textShadowColor: 'rgba(0, 229, 255, 0.4)',
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 15,
  },
  radarContainer: {
    width: 180,
    height: 180,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 50,
  },
  radarRing: {
    position: 'absolute',
    borderRadius: 180,
    borderWidth: 2,
  },
  radarRingOuter: {
    width: 170,
    height: 170,
    borderColor: 'rgba(0, 229, 255, 0.15)',
  },
  radarRingMiddle: {
    width: 130,
    height: 130,
    borderColor: 'rgba(124, 77, 255, 0.25)',
  },
  radarCenter: {
    width: 80,
    height: 80,
    borderRadius: 80,
    backgroundColor: '#101726',
    borderWidth: 2,
    borderColor: '#00E5FF',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#00E5FF',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.4,
    shadowRadius: 15,
    elevation: 6,
  },
  radarIcon: {
    fontSize: 28,
  },
  statusBox: {
    width: '100%',
    alignItems: 'center',
    marginBottom: 40,
  },
  statusTitle: {
    fontSize: 11,
    fontWeight: 'bold',
    color: '#94A3B8',
    letterSpacing: 1,
    marginBottom: 12,
    textAlign: 'center',
  },
  progressContainer: {
    width: width * 0.75,
    height: 8,
    backgroundColor: '#1F2942',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 8,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#00E5FF',
    borderRadius: 4,
  },
  percentText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#00E5FF',
  },
  buttonContainer: {
    width: '100%',
    height: 60,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 60,
  },
  enterButton: {
    backgroundColor: '#00E676',
    paddingVertical: 16,
    paddingHorizontal: 40,
    borderRadius: 14,
    width: width * 0.75,
    alignSelf: 'center',
    alignItems: 'center',
    shadowColor: '#00E676',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.35,
    shadowRadius: 10,
    elevation: 4,
  },
  enterButtonText: {
    color: '#080C14',
    fontSize: 14,
    fontWeight: 'bold',
    letterSpacing: 2,
  },
  initializingText: {
    fontSize: 11,
    fontWeight: 'bold',
    color: '#64748B',
    letterSpacing: 1,
    textAlign: 'center',
  },
  metaFooter: {
    position: 'absolute',
    bottom: 30,
    alignItems: 'center',
  },
  metaText: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#94A3B8',
    letterSpacing: 2,
    marginBottom: 3,
  },
  metaSubtext: {
    fontSize: 8,
    fontWeight: '500',
    color: '#64748B',
    letterSpacing: 1.5,
  },
});
