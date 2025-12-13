# 📱 Aforo App - Frontend React Native

Aplicación móvil para el sistema de control de aforo en tiempo real.

## 🚀 Características

- ✅ Dashboard en tiempo real con streaming de video
- ✅ Visualización de aforo actual con indicador visual
- ✅ Configuración de parámetros del sistema
- ✅ Historial de ocupación con gráficas
- ✅ Información de modelos YOLO cargados
- ✅ Alertas de aforo excedido
- ✅ Conexión WebSocket para datos en tiempo real

## 📦 Requisitos Previos

- Node.js 16+ y npm
- Expo CLI: `npm install -g expo-cli`
- Backend del sistema ejecutándose
- Dispositivo móvil o emulador

## 🔧 Instalación

### 1. Instalar dependencias

```bash
cd frontend
npm install
```

### 2. Configurar URL del backend

Edita `src/utils/constants.js`:

```javascript
export const API_CONFIG = {
  BASE_URL: 'http://TU_IP_BACKEND:5000',  // Cambia esta IP
  WS_URL: 'http://TU_IP_BACKEND:5000',
  TIMEOUT: 5000,
};
```

**Importante**: Usa la IP de tu computadora en la red local, **NO** uses `localhost` si vas a probar en dispositivo físico.

### 3. Iniciar la aplicación

```bash
npm start
```

Esto abrirá Expo DevTools en tu navegador.

## 📱 Ejecutar en Dispositivo

### Opción 1: Expo Go (Recomendado para desarrollo)

1. Instala **Expo Go** desde Play Store (Android) o App Store (iOS)
2. Escanea el código QR que aparece en la terminal
3. La app se cargará en tu dispositivo

### Opción 2: Emulador Android

```bash
npm run android
```

### Opción 3: Simulador iOS (solo Mac)

```bash
npm run ios
```

### Opción 4: Web

```bash
npm run web
```

## 🌐 Configuración de Red

### Encontrar tu IP local

**Windows**:
```bash
ipconfig
# Busca "IPv4 Address" en la conexión activa
```

**Linux/Mac**:
```bash
ifconfig
# Busca "inet" en la interfaz activa (ej: 192.168.1.6)
```

### Asegúrate de que:

1. ✅ Tu dispositivo móvil y computadora están en la **misma red WiFi**
2. ✅ El backend está ejecutándose: `python backend/app.py`
3. ✅ El firewall permite conexiones al puerto 5000
4. ✅ Puedes acceder a `http://TU_IP:5000/api/status` desde el navegador móvil

## 📁 Estructura del Proyecto

```
frontend/
├── App.js                    # Componente raíz con navegación
├── app.json                  # Configuración de Expo
├── package.json              # Dependencias
│
├── src/
│   ├── screens/              # Pantallas principales
│   │   ├── HomeScreen.js     # Dashboard en tiempo real
│   │   ├── ConfigScreen.js   # Configuración del sistema
│   │   ├── HistoryScreen.js  # Historial y gráficas
│   │   └── ModelsScreen.js   # Estado de modelos YOLO
│   │
│   ├── services/             # Servicios de comunicación
│   │   ├── api.js           # Cliente HTTP (axios)
│   │   └── websocket.js     # Cliente WebSocket
│   │
│   └── utils/
│       └── constants.js     # Configuración y constantes
│
└── assets/                   # Imágenes e íconos
```

## 🎨 Pantallas

### 1. HomeScreen (Inicio)
- Stream de video en vivo
- Conteo de personas en tiempo real
- Barra de progreso de ocupación
- Alerta si se excede el aforo
- Gráfica de últimos 60 segundos
- Métricas: FPS, modelos activos

### 2. ConfigScreen (Configuración)
- Aforo máximo
- Estrategia de ensemble
- Umbral de confianza
- Activar/desactivar privacidad
- URL del servidor

### 3. HistoryScreen (Historial)
- Selector de rango (Hoy, Semana, Mes)
- Gráfica de ocupación histórica
- Estadísticas: promedio, pico
- Lista de registros recientes

### 4. ModelsScreen (Modelos)
- Estado de cada modelo YOLO
- Métricas de precisión
- Indicador de modelos cargados
- Información sobre cada variante

## 🔧 Configuración Avanzada

### Cambiar colores del tema

Edita `src/utils/constants.js`:

```javascript
export const COLORS = {
  primary: '#3b82f6',      // Azul principal
  secondary: '#8b5cf6',    // Púrpura secundario
  success: '#10b981',      // Verde éxito
  warning: '#f59e0b',      // Amarillo advertencia
  danger: '#ef4444',       // Rojo peligro
  // ...
};
```

### Ajustar timeout de conexión

```javascript
export const API_CONFIG = {
  // ...
  TIMEOUT: 10000,  // 10 segundos
};
```

## 🐛 Troubleshooting

### Error: "Network request failed"

**Causa**: No puede conectar con el backend.

**Solución**:
1. Verifica que el backend esté ejecutándose
2. Confirma que la IP en `constants.js` es correcta
3. Prueba acceder a `http://TU_IP:5000/api/status` desde el navegador del móvil
4. Desactiva el firewall temporalmente para probar

### Error: "Unable to resolve module socket.io-client"

**Solución**:
```bash
npm install
# o
rm -rf node_modules package-lock.json
npm install
```

### El video no se muestra

**Causa**: WebSocket no está conectado o la cámara no está iniciada.

**Solución**:
1. Presiona "Iniciar Cámara" en la app
2. Verifica el estado de conexión en la parte superior
3. Revisa los logs del backend para errores

### FPS muy bajo en la app

**Solución**:
- Usa solo YOLOv8n (más rápido)
- Cambia estrategia a "Mejor modelo" en configuración
- Reduce la resolución de la cámara en el backend

## 📊 Dependencias Principales

| Librería | Versión | Propósito |
|----------|---------|-----------|
| react-native | 0.73.2 | Framework base |
| expo | ~50.0.0 | Herramientas de desarrollo |
| @react-navigation | ^6.1.9 | Navegación entre pantallas |
| axios | ^1.6.5 | Peticiones HTTP |
| socket.io-client | ^4.6.1 | WebSocket en tiempo real |
| react-native-chart-kit | ^6.12.0 | Gráficas |
| react-native-progress | ^5.0.1 | Barras de progreso |

## 🚀 Compilar para Producción

### Android APK

```bash
expo build:android
```

### iOS IPA (requiere cuenta Apple Developer)

```bash
expo build:ios
```

### Configurar EAS Build (Recomendado)

```bash
npm install -g eas-cli
eas login
eas build:configure
eas build -p android
```

## 📝 Próximas Mejoras

- [ ] Notificaciones push cuando se excede aforo
- [ ] Modo oscuro
- [ ] Exportar historial a CSV
- [ ] Múltiples cámaras
- [ ] Autenticación de usuarios
- [ ] Dashboard para administradores

## 🤝 Contribuir

1. Haz cambios en tu branch
2. Prueba en dispositivo físico
3. Documenta nuevas features
4. Haz commit con mensajes descriptivos

## 📄 Licencia

Proyecto académico

---

## 🆘 Soporte

Si tienes problemas:

1. Lee la sección de Troubleshooting arriba
2. Verifica los logs del backend y la app
3. Confirma la configuración de red
4. Revisa la documentación del backend en `backend/README.md`

---

**¡Listo para usar!** 🎉

Ejecuta `npm start` y escanea el código QR con Expo Go.
