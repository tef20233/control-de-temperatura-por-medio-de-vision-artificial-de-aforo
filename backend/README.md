# 🚀 Backend - Sistema de Control de Aforo

Backend Flask con detección YOLO y WebSocket para streaming en tiempo real.

## 📋 Requisitos

- Python 3.8+
- Webcam o cámara IP
- GPU recomendada (opcional)
- Modelos YOLO entrenados (al menos 1)

## 🔧 Instalación

### 1. Crear entorno virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Preparar modelos

Coloca tus modelos YOLO entrenados en la carpeta `models/`:

```
backend/
├── models/
│   ├── yolov8n.pt    # ✅ Obligatorio (al menos 1 modelo)
│   ├── yolov8s.pt    # ⚠️ Opcional
│   ├── yolov8m.pt    # ⚠️ Opcional
│   └── yolov8l.pt    # ⚠️ Opcional
```

**Nota**: El sistema funciona con 1-4 modelos. Usa los que tengas disponibles.

### 4. Crear carpetas necesarias

```bash
mkdir data
mkdir models
```

## 🚀 Ejecución

### Modo desarrollo

```bash
python app.py
```

El servidor estará disponible en: `http://localhost:5000`

### Modo producción

```bash
gunicorn --worker-class gevent --workers 1 --bind 0.0.0.0:5000 --timeout 300 app:app
```

## 📡 API Endpoints

### REST API

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/status` | GET | Estado del sistema |
| `/api/config` | GET/POST | Configuración |
| `/api/models` | GET | Info de modelos |
| `/api/camera/start` | POST | Iniciar cámara |
| `/api/camera/stop` | POST | Detener cámara |
| `/api/history` | GET | Historial de ocupación |

### WebSocket

**URL**: `ws://localhost:5000/`

**Evento**: `frame_update`

```json
{
  "type": "frame",
  "timestamp": 1730877600.0,
  "frame": "base64_encoded_image",
  "count": 12,
  "max_capacity": 50,
  "occupancy_rate": 0.24,
  "alert": false,
  "models_used": ["yolov8n", "yolov8m"],
  "fps": 18.5,
  "inference_time": 0.053
}
```

## ⚙️ Configuración

Edita `config.py` para ajustar:

- Fuente de cámara (USB o IP)
- Estrategia de ensemble
- Aforo máximo
- Umbral de confianza
- Privacidad

### Ejemplo: Configurar aforo máximo

```bash
curl -X POST http://localhost:5000/api/config \
  -H "Content-Type: application/json" \
  -d '{"max_capacity": 100}'
```

### Ejemplo: Cambiar estrategia de ensemble

```bash
curl -X POST http://localhost:5000/api/config \
  -H "Content-Type: application/json" \
  -d '{"ensemble_strategy": "best"}'
```

Estrategias disponibles:
- `average`: Promedio de conteos
- `majority`: Moda (más frecuente)
- `best`: Modelo con mayor mAP
- `union`: Unión de detecciones + NMS

## 🧪 Testing

### Verificar estado del sistema

```bash
curl http://localhost:5000/api/status
```

### Ver modelos cargados

```bash
curl http://localhost:5000/api/models
```

### Iniciar cámara

```bash
curl -X POST http://localhost:5000/api/camera/start
```

## 📊 Estructura del Proyecto

```
backend/
├── app.py                  # Punto de entrada principal
├── config.py               # Configuración
├── requirements.txt        # Dependencias
├── README.md              # Esta documentación
├── core/
│   ├── __init__.py
│   ├── detector.py        # Detector YOLO con ensemble
│   ├── camera.py          # Manejo de cámara
│   └── privacy.py         # Anonimización (futuro)
├── utils/
│   ├── __init__.py
│   └── metrics.py         # Recolector de métricas
├── models/
│   └── [archivos .pt]     # Modelos YOLO
└── data/
    ├── history.db         # Base de datos SQLite
    └── config.json        # Configuración guardada
```

## 🔍 Troubleshooting

### Error: "No se encontró ningún modelo YOLO"

**Solución**: Coloca al menos 1 archivo `.pt` en la carpeta `models/`

### Error: "Failed to connect to camera"

**Solución**: 
- Verifica que la cámara esté conectada
- Prueba con `source=0` o `source=1` en `config.py`
- Si usas IP camera, verifica la URL RTSP

### FPS muy bajo (<5)

**Solución**:
- Usa menos modelos (ej: solo YOLOv8n)
- Reduce resolución de cámara
- Usa GPU si está disponible
- Cambia estrategia a `best` (usa solo 1 modelo)

## 📚 Más Información

Ver documentación completa en la carpeta raíz del proyecto:
- `PROMPT_APLICACION_AFORO.md`
- `RESUMEN_SISTEMA_AFORO.md`
- `ANALISIS_ESTADO_PROYECTO.md`
