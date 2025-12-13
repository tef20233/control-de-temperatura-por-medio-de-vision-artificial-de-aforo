# 🚀 Inicio Rápido con Webcam del PC

## ✅ Estado Actual
El sistema está configurado para usar la **webcam de tu PC** en lugar de la cámara Tapo.

---

## 📦 Método 1: Script Automático (Recomendado)

### Windows
```bash
# Doble clic en el archivo:
iniciar_con_webcam.bat
```

Este script:
1. ✅ Prueba la conexión a la webcam
2. ✅ Inicia el backend automáticamente
3. ✅ Muestra instrucciones para el frontend

---

## 🛠️ Método 2: Manual

### Paso 1: Probar la Webcam
```bash
cd backend
python test_webcam.py
```

### Paso 2: Iniciar Backend
```bash
cd backend
python app.py
```

Verás:
```
============================================================
🚀 SISTEMA DE CONTROL DE AFORO - BACKEND
============================================================
Modelos cargados: [...]
Puerto: 5000
============================================================
```

### Paso 3: Iniciar Frontend

**Opción A: Mismo PC (navegador)**
```bash
cd frontend
npm start
```
Presiona `w` cuando te lo pida para abrir en el navegador.

**Opción B: Dispositivo móvil**
1. Encuentra tu IP local:
   ```bash
   ipconfig
   ```
   Busca la IPv4 (ej: 192.168.1.100)

2. Edita `frontend/src/screens/HomeScreenSimple.js` línea 16:
   ```javascript
   const API_BASE_URL = 'http://192.168.1.100:5000';
   ```

3. Inicia frontend y escanea QR con Expo Go:
   ```bash
   cd frontend
   npm start
   ```

---

## 🎯 Uso del Sistema

### Interfaz Principal

1. **Iniciar Cámara**: Toca el botón "▶️ INICIAR CÁMARA"
2. **Ver Conteo**: El sistema detectará personas automáticamente
3. **Detener**: Toca "⏹️ DETENER CÁMARA" cuando termines

### Panel de Control

- **Aforo Actual**: Muestra personas detectadas vs capacidad máxima
- **FPS**: Velocidad de procesamiento
- **Modelos**: Cantidad de modelos YOLO cargados
- **Estrategia**: Método de ensemble usado

---

## 🔧 Solución de Problemas

### ❌ "No se puede conectar al backend"
```bash
# Verifica que el backend esté corriendo
# Deberías ver: "Running on http://0.0.0.0:5000"
```

### ❌ "Failed to connect to camera"
1. Cierra aplicaciones que usen la webcam (Zoom, Teams, Skype)
2. Verifica permisos de cámara en Windows
3. Prueba con otro índice de cámara:
   ```python
   # En backend/app.py línea 28
   'camera_source': 1,  # En lugar de 0
   ```

### ❌ "Modelos no encontrados"
```bash
cd backend
python download_model.py
```

### ❌ Frontend no se conecta desde el móvil
1. PC y móvil deben estar en la misma WiFi
2. Verifica firewall de Windows:
   - Permite Python en redes privadas
3. Prueba desde navegador del móvil: `http://TU_IP:5000/api/status`

---

## 📊 Endpoints Disponibles

### Verificar Estado
```bash
curl http://localhost:5000/api/status
```

### Iniciar Cámara
```bash
curl -X POST http://localhost:5000/api/camera/start
```

### Detener Cámara
```bash
curl -X POST http://localhost:5000/api/camera/stop
```

---

## ⚙️ Configuración Avanzada

### Cambiar Capacidad Máxima
```python
# backend/app.py línea 23
'max_capacity': 100,  # Cambia según necesites
```

### Cambiar Estrategia de Detección
```python
# backend/app.py línea 24
'ensemble_strategy': 'union',  # average | majority | best | union
```

### Ajustar Confianza de Detección
```python
# backend/app.py línea 25
'confidence_threshold': 0.35,  # Más bajo = más detecciones (más falsos positivos)
```

---

## 📝 Arquitectura

```
┌─────────────┐     HTTP/WS      ┌─────────────┐
│  Frontend   │ ◄──────────────► │   Backend   │
│ (React App) │                  │  (Flask)    │
└─────────────┘                  └──────┬──────┘
                                        │
                                        ▼
                                 ┌──────────────┐
                                 │   Webcam PC  │
                                 │   (OpenCV)   │
                                 └──────────────┘
                                        │
                                        ▼
                                 ┌──────────────┐
                                 │  YOLOv8 x4   │
                                 │  (Ensemble)  │
                                 └──────────────┘
```

---

## 🎓 Próximos Pasos

✅ Sistema funcionando con webcam
⏳ Configuración cámara Tapo (pendiente para más adelante)

---

## 📚 Documentación Adicional

- `CONFIGURACION_WEBCAM.md` - Detalles técnicos de configuración
- `README.md` - Documentación completa del proyecto
- `LEEME_PRIMERO.md` - Guía general del sistema
