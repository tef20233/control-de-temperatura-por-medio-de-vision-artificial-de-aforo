# 📱 GUÍA RÁPIDA - Frontend React Native

## ⚡ Instalación Rápida (5 minutos)

### 1. Instalar Node.js y Expo CLI

```bash
# Instalar Node.js desde: https://nodejs.org/ (versión LTS)

# Instalar Expo CLI globalmente
npm install -g expo-cli
```

### 2. Instalar dependencias del proyecto

```bash
cd frontend
npm install
```

### 3. Configurar URL del backend

Edita el archivo `frontend/src/utils/constants.js`:

```javascript
export const API_CONFIG = {
  BASE_URL: 'http://192.168.1.6:5000',  // ← Cambia a tu IP
  WS_URL: 'http://192.168.1.6:5000',    // ← Cambia a tu IP
  TIMEOUT: 5000,
};
```

**¿Cómo saber tu IP?**

Windows:
```bash
ipconfig
# Busca "Dirección IPv4" (ej: 192.168.1.6)
```

Linux/Mac:
```bash
ifconfig
# Busca "inet" (ej: 192.168.1.6)
```

### 4. Iniciar la aplicación

```bash
npm start
```

### 5. Ejecutar en tu celular

**Opción A: Usando Expo Go (Recomendado)**

1. Descarga **Expo Go** desde:
   - Android: [Play Store](https://play.google.com/store/apps/details?id=host.exp.exponent)
   - iOS: [App Store](https://apps.apple.com/app/expo-go/id982107779)

2. Abre Expo Go en tu celular

3. Escanea el código QR que aparece en la terminal

4. ¡Listo! La app se cargará automáticamente

**Opción B: Usando emulador/simulador**

Android:
```bash
npm run android
```

iOS (solo Mac):
```bash
npm run ios
```

Web (navegador):
```bash
npm run web
```

---

## 🔧 Solución de Problemas Comunes

### ❌ Error: "Network request failed"

**Problema**: La app no puede conectar con el backend.

**Solución**:

1. **Verifica que el backend esté ejecutándose**:
   ```bash
   cd backend
   python app.py
   ```

2. **Confirma que tu celular y PC están en la misma WiFi**

3. **Prueba la conexión desde el navegador de tu celular**:
   - Abre: `http://TU_IP:5000/api/status`
   - Si no carga, hay un problema de red

4. **Desactiva el firewall temporalmente** (Windows):
   - Panel de Control → Firewall de Windows → Desactivar temporalmente
   - Prueba de nuevo
   - Vuelve a activarlo después

5. **Verifica la IP en `constants.js`**:
   - Debe ser tu IP local (ej: 192.168.1.6)
   - **NO** uses `localhost` o `127.0.0.1`

### ❌ Error: "Unable to resolve module"

**Solución**:
```bash
cd frontend
rm -rf node_modules
rm package-lock.json
npm install
```

### ❌ El video no se muestra

**Solución**:

1. Presiona el botón **"Iniciar Cámara"** en la app

2. Verifica que dice **"Conectado"** en la parte superior

3. Revisa que la cámara del backend funcione:
   ```bash
   curl -X POST http://TU_IP:5000/api/camera/start
   ```

### ❌ "Expo Go not found"

**Solución**:

Instala Expo Go en tu celular desde la tienda de aplicaciones.

---

## 📱 Características de la App

### 🏠 Pantalla de Inicio (Home)
- ✅ Video en vivo con detecciones
- ✅ Conteo actual de personas
- ✅ Barra de progreso de ocupación
- ✅ Alerta si se excede el aforo
- ✅ Gráfica de últimos 60 segundos
- ✅ FPS y modelos activos

### ⚙️ Pantalla de Configuración
- ✅ Cambiar aforo máximo
- ✅ Seleccionar estrategia de ensemble
- ✅ Ajustar umbral de confianza
- ✅ Activar/desactivar privacidad

### 📊 Pantalla de Historial
- ✅ Gráfica de ocupación histórica
- ✅ Estadísticas (promedio, pico)
- ✅ Lista de registros recientes
- ✅ Filtros por tiempo

### 🤖 Pantalla de Modelos
- ✅ Estado de cada modelo YOLO
- ✅ Métricas de precisión
- ✅ Indicador de modelos cargados

---

## 📝 Cambiar Configuración

### Cambiar el aforo máximo

1. Ve a la pestaña **"Configuración"**
2. Modifica el campo **"Aforo Máximo"**
3. Presiona **"GUARDAR CAMBIOS"**

### Cambiar estrategia de ensemble

Opciones disponibles:

- **Promedio**: Promedia los conteos de todos los modelos
- **Mayoría**: Usa el conteo más frecuente
- **Mejor Modelo**: Usa solo el modelo con mayor precisión
- **Unión (NMS)**: Une todas las detecciones

### Ajustar umbral de confianza

- Desliza el slider entre 0.0 y 1.0
- Valores más altos = detecciones más seguras pero menos cantidad
- Valores más bajos = más detecciones pero menos precisas
- Recomendado: 0.5

---

## 🎨 Personalización

### Cambiar colores del tema

Edita `frontend/src/utils/constants.js`:

```javascript
export const COLORS = {
  primary: '#3b82f6',      // Azul (cambia este)
  secondary: '#8b5cf6',    // Púrpura
  success: '#10b981',      // Verde
  warning: '#f59e0b',      // Amarillo
  danger: '#ef4444',       // Rojo
  // ...
};
```

### Cambiar URL del servidor

Edita `frontend/src/utils/constants.js`:

```javascript
export const API_CONFIG = {
  BASE_URL: 'http://192.168.1.100:5000',  // Nueva IP
  WS_URL: 'http://192.168.1.100:5000',
  TIMEOUT: 5000,
};
```

---

## 🚀 Compilar para Producción

### Generar APK para Android

```bash
cd frontend
expo build:android
```

Esto generará un APK que puedes instalar en cualquier dispositivo Android.

### Generar IPA para iOS

```bash
expo build:ios
```

(Requiere cuenta de Apple Developer)

---

## 📊 Flujo de Datos

```
┌─────────────────────────────────────────┐
│          CELULAR (App React Native)     │
├─────────────────────────────────────────┤
│                                         │
│  HTTP (axios) ──────→ /api/status       │
│                       /api/config       │
│                       /api/models       │
│                       /api/history      │
│                                         │
│  WebSocket ─────────→ frame_update      │
│  (socket.io)          (video + datos)   │
│                                         │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│      BACKEND (Flask + SocketIO)         │
├─────────────────────────────────────────┤
│                                         │
│  • Procesa video de cámara              │
│  • Ejecuta detección YOLO               │
│  • Envía frames por WebSocket           │
│  • Guarda historial en SQLite           │
│                                         │
└─────────────────────────────────────────┘
```

---

## ✅ Checklist de Verificación

Antes de usar la app, confirma:

- [ ] Backend ejecutándose en `http://TU_IP:5000`
- [ ] Puedes acceder a `/api/status` desde el navegador
- [ ] Celular y PC en la misma WiFi
- [ ] IP correcta en `constants.js`
- [ ] Node.js y Expo CLI instalados
- [ ] Dependencias instaladas (`npm install`)
- [ ] Expo Go instalado en el celular
- [ ] Firewall permite conexiones al puerto 5000

---

## 🎯 Próximos Pasos

1. **Probar todas las pantallas**
   - Home: Iniciar cámara y ver video
   - Config: Cambiar aforo y guardar
   - Historial: Ver gráficas
   - Modelos: Revisar estado

2. **Experimentar con configuraciones**
   - Diferentes estrategias de ensemble
   - Varios umbrales de confianza
   - Aforos máximos diferentes

3. **Revisar métricas**
   - FPS del sistema
   - Precisión de detecciones
   - Ocupación promedio

---

## 📚 Recursos Adicionales

- **Documentación de Expo**: https://docs.expo.dev/
- **React Navigation**: https://reactnavigation.org/
- **Socket.IO**: https://socket.io/docs/v4/
- **Chart Kit**: https://github.com/indiespirit/react-native-chart-kit

---

## 🆘 Soporte

Si algo no funciona:

1. Lee esta guía completa
2. Revisa la sección de troubleshooting
3. Verifica los logs del backend
4. Confirma la configuración de red
5. Prueba en otro dispositivo

---

**¡Tu app está lista! 🎉**

Ejecuta `npm start` en la carpeta `frontend` y escanea el código QR.
