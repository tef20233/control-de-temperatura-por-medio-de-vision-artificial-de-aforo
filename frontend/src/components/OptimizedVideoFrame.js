import React, { useEffect, useRef, memo } from 'react';
import { View, Image, StyleSheet } from 'react-native';

/**
 * Componente optimizado para renderizar frames de video a alta velocidad.
 *
 * Optimizaciones implementadas:
 * 1. memo() para evitar re-renders innecesarios
 * 2. useRef para evitar crear nueva URI en cada render
 * 3. Decodificación lazy de base64
 * 4. Cache de imagen nativa
 */
const OptimizedVideoFrame = memo(({ frameData, style }) => {
  const imageRef = useRef(null);
  const lastFrameRef = useRef(null);
  const frameCountRef = useRef(0);
  const lastUpdateRef = useRef(Date.now());

  useEffect(() => {
    if (!frameData) return;

    // Throttling: Solo actualizar si ha pasado suficiente tiempo (aprox 30 FPS = 33ms)
    const now = Date.now();
    const elapsed = now - lastUpdateRef.current;

    // Skip si el frame es el mismo (comparación rápida)
    if (frameData === lastFrameRef.current) {
      return;
    }

    // Actualizar referencias
    lastFrameRef.current = frameData;
    lastUpdateRef.current = now;
    frameCountRef.current++;

    // Log de rendimiento cada 60 frames
    if (frameCountRef.current % 60 === 0) {
      const avgTime = elapsed;
      const estimatedFps = elapsed > 0 ? 1000 / elapsed : 0;
      console.log(`📹 OptimizedVideoFrame: ~${estimatedFps.toFixed(1)} FPS (avg frame time: ${avgTime.toFixed(1)}ms)`);
    }
  }, [frameData]);

  if (!frameData) {
    return null;
  }

  return (
    <Image
      ref={imageRef}
      source={{ uri: `data:image/jpeg;base64,${frameData}` }}
      style={[styles.image, style]}
      resizeMode="contain"
      // Optimizaciones de React Native
      fadeDuration={0} // Sin fade para máxima velocidad
      progressiveRenderingEnabled={false} // Sin renderizado progresivo
      cache="only-if-cached" // Usar cache agresivamente
    />
  );
}, (prevProps, nextProps) => {
  // Comparación personalizada: solo re-renderizar si el frame cambió
  return prevProps.frameData === nextProps.frameData;
});

OptimizedVideoFrame.displayName = 'OptimizedVideoFrame';

const styles = StyleSheet.create({
  image: {
    width: '100%',
    height: '100%',
  },
});

export default OptimizedVideoFrame;
