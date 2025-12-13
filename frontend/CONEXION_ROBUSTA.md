# 🔄 Sistema de Conexión Robusta - Frontend

## 🎯 Mejoras Implementadas

### 1. **Auto-Detección de Backend**

El frontend ahora detecta automáticamente el backend disponible en múltiples URLs:

```javascript
BACKEND_URLS: [
  'http://localhost:5000',           // Localhost (misma máquina)
  'http://127.0.0.1:5000',          // IPv4 loopback
  'http://192.168.218.31:5000',     // IP actual de tu PC
  'http://192.168.1.19:5000',       // IP alternativa
  'http://192.168.196.100:5000',    // Otra red posible
]
```

### 2. **Reconexión Automática**

- **API REST**: Reintenta automáticamente hasta 10 veces antes de cambiar de URL
- **WebSocket**: Reconecta automáticamente con heartbeat cada 5 segundos
- **Detección de cambio de red**: Si la conexión se pierde, busca el backend en todas las URLs configuradas

### 3. **Indicadores Visuales**

- **Banner superior**: Muestra el estado de conexión en tiempo real
- **Botón de reconexión manual**: Permite forzar la reconexión si es necesario
- **Colores intuitivos**:
  - 🟢 Verde = Conectado
  - 🟡 Amarillo = Reconectando
  - 🔴 Rojo = Desconectado

## 🔧 Configuración

### Agregar Nuevas URLs de Backend

Edita `frontend/src/utils/constants.js`:

```javascript
export const API_CONFIG = {
  BACKEND_URLS: [
    'http://localhost:5000',
    'http://TU_NUEVA_IP:5000',  // Agregar aquí
    // ... más URLs
  ],
};
```

### Ajustar Timeouts

```javascript
export const API_CONFIG = {
  TIMEOUT: 5000,        // Timeout de peticiones HTTP (ms)
  RETRY_INTERVAL: 3000, // Intervalo entre reintentos (ms)
  MAX_RETRIES: 10,      // Máximo de reintentos
};
```

## 🚀 Uso

### Inicialización Automática

El frontend automáticamente:
1. Detecta el backend disponible al iniciar
2. Conecta al WebSocket
3. Muestra el estado de conexión

### Reconexión Manual

Si pierdes la conexión, puedes:
1. Esperar la reconexión automática (ocurre cada 3-5 segundos)
2. Presionar el botón "🔄 Reconectar" en el banner rojo

## 📱 Componentes

### `ConnectionStatus.js`

Componente visual que muestra el estado de conexión:

```javascript
import ConnectionStatus from '../components/ConnectionStatus';

// En tu screen:
<ConnectionStatus />
```

### `api.js`

Servicio mejorado con interceptores de Axios:
- Detecta errores de red
- Reintenta automáticamente
- Cambia de URL si es necesario

```javascript
import { initializeConnection } from '../services/api';

// Inicializar conexión
const connected = await initializeConnection();
```

### `websocket.js`

WebSocket mejorado con:
- Heartbeat para detectar desconexiones
- Reconexión inteligente
- Detección de cambio de red

```javascript
import wsService from '../services/websocket';

// Conectar
await wsService.connect();

// Forzar reconexión
wsService.forceReconnect();
```

## 🔍 Troubleshooting

### El frontend no conecta

1. **Verifica que el backend esté corriendo**:
   ```bash
   cd backend
   python app.py
   ```

2. **Verifica tu IP actual**:
   ```bash
   ipconfig
   ```
   Busca "IPv4 Address" en la red activa

3. **Agrega tu IP a las URLs**:
   Edita `frontend/src/utils/constants.js` y agrega tu IP

### La conexión se pierde al cambiar de red WiFi

Esto es **normal y esperado**. El sistema automáticamente:
1. Detecta la pérdida de conexión
2. Busca el backend en todas las URLs configuradas
3. Reconecta cuando encuentra el backend

**Recomendación**: Agrega múltiples IPs de tus redes habituales (casa, trabajo, etc.)

### WebSocket se desconecta constantemente

1. **Verifica firewall**: Asegúrate de que el puerto 5000 esté abierto
2. **Aumenta el timeout**:
   ```javascript
   // En websocket.js
   timeout: 15000, // Aumentar a 15 segundos
   ```

## 📊 Logs de Debug

El sistema registra información útil en la consola:

```
🔍 Detectando backend disponible...
✅ Backend encontrado en: http://192.168.1.19:5000
✅ Conectado a backend: http://192.168.1.19:5000
🔌 Conectando WebSocket a: ws://192.168.1.19:5000
✅ WebSocket conectado
```

Si hay problemas:
```
⚠️ No se pudo conectar a http://localhost:5000
⚠️ No se pudo conectar a http://192.168.218.31:5000
❌ No se encontró ningún backend disponible
```

## 🎯 Ventajas del Nuevo Sistema

1. **Funciona en múltiples redes**: Casa, trabajo, hotspot móvil
2. **Sin configuración manual**: Detecta automáticamente el backend
3. **Robusto ante fallos**: Reconexión automática e inteligente
4. **Feedback visual**: Siempre sabes el estado de la conexión
5. **Cambio de red sin problemas**: Se adapta automáticamente

## 🔄 Flujo de Reconexión

```
┌─────────────────┐
│  App inicia     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ Detectar backend        │
│ (prueba todas las URLs) │
└────────┬────────────────┘
         │
    ┌────▼────┐
    │ ¿Éxito? │
    └────┬────┘
         │
    ┌────▼────┐           ┌──────────────┐
    │   SÍ    ├──────────►│ Conectar WS  │
    └─────────┘           └──────┬───────┘
                                 │
    ┌─────────┐                  ▼
    │   NO    ├──────►  ┌────────────────┐
    └─────────┘         │ Mostrar error  │
                        └────────┬───────┘
                                 │
                                 ▼
                        ┌────────────────┐
                        │ Reintentar en  │
                        │   3 segundos   │
                        └────────────────┘
```

## 💡 Tips

- **Desarrollo local**: Usa `localhost:5000` (más rápido)
- **Dispositivo físico**: Usa la IP de tu PC en la red WiFi
- **Producción**: Configura una URL fija o usa DNS dinámico
- **Múltiples redes**: Agrega todas las IPs posibles a `BACKEND_URLS`

## 📚 Archivos Modificados

- ✅ `frontend/src/utils/constants.js` - URLs y configuración
- ✅ `frontend/src/services/api.js` - Auto-reconexión API
- ✅ `frontend/src/services/websocket.js` - WebSocket robusto
- ✅ `frontend/src/components/ConnectionStatus.js` - Indicador visual
- ✅ `frontend/src/screens/HomeScreen.js` - Integración

## 🎉 Resultado

Ahora el frontend **mantiene la conexión automáticamente** incluso cuando:
- Cambias de red WiFi
- El backend se reinicia
- Hay interrupciones temporales de red
- Cambias entre redes (casa ↔ trabajo)
