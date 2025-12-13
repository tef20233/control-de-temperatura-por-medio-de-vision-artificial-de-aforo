# 🚀 INICIO RÁPIDO - Sistema de Aforo

## ⚡ Empezar en 5 Minutos

### 1️⃣ Preparar Modelos

**Tienes YOLOv8n**: ✅ Ya puedes empezar
```bash
# Copia tu modelo YOLOv8n.pt a:
cp ruta/a/yolov8n.pt backend/models/yolov8n.pt
```

**Necesitas entrenar más modelos**:
```bash
cd scripts

# Windows
train_yolov8m.bat

# Linux/Mac
python train_yolov8m.py
```

### 2️⃣ Instalar Dependencias

```bash
cd backend

# Crear entorno virtual
python -m venv venv

# Activar entorno
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3️⃣ Ejecutar Backend

```bash
python app.py
```

Verás algo como:
```
================================================================================
🚀 SISTEMA DE CONTROL DE AFORO - BACKEND
================================================================================
📦 Buscando modelos YOLO...
✅ yolov8n cargado - models/yolov8n.pt
⚠️ yolov8s no encontrado - models/yolov8s.pt
⚠️ yolov8m no encontrado - models/yolov8m.pt
⚠️ yolov8l no encontrado - models/yolov8l.pt

🎯 1/4 modelos cargados

Modelos cargados: ['yolov8n']
Puerto: 5000
================================================================================
```

### 4️⃣ Probar el Sistema

Abre tu navegador en: `http://localhost:5000/api/status`

Deberías ver:
```json
{
  "status": "stopped",
  "models_loaded": ["yolov8n"],
  "models_missing": ["yolov8s", "yolov8m", "yolov8l"],
  "camera_connected": false,
  "current_count": 0,
  "max_capacity": 50,
  "occupancy_rate": 0.0,
  "fps": 0.0
}
```

### 5️⃣ Iniciar Cámara

```bash
curl -X POST http://localhost:5000/api/camera/start
```

¡Listo! El sistema está detectando personas en tiempo real.

---

## 📊 Verificar Funcionamiento

### Ver estado de modelos

```bash
curl http://localhost:5000/api/models
```

### Configurar aforo máximo

```bash
curl -X POST http://localhost:5000/api/config \
  -H "Content-Type: application/json" \
  -d '{"max_capacity": 100}'
```

### Ver historial

```bash
curl http://localhost:5000/api/history
```

---

## 🎯 Próximos Pasos

### ✅ Ya funcionando con 1 modelo
- **Puntos actuales**: ~260/500 (52%)
- **Nota estimada**: 2.6/5.0

### 🟡 Entrenar YOLOv8m (CRÍTICO)
```bash
cd scripts
python train_yolov8m.py
```
- **Tiempo**: 3 días
- **Puntos después**: ~360/500 (72%)
- **Nota estimada**: 3.6/5.0

### 🟢 Entrenar todos los modelos
```bash
cd scripts
# Windows:
train_all.bat
# Linux/Mac:
bash train_all.sh
```
- **Tiempo**: 7-10 días
- **Puntos después**: ~450/500 (90%)
- **Nota estimada**: 4.5/5.0

---

## 🐛 Problemas Comunes

### Error: "No se encontró ningún modelo YOLO"
**Solución**: Copia al menos 1 archivo `.pt` a `backend/models/`

### Error: "Failed to connect to camera"
**Solución**: 
- Verifica que la webcam esté conectada
- En `backend/app.py`, cambia `source=0` a `source=1`

### FPS muy bajo
**Solución**: 
- Usa solo YOLOv8n (es el más rápido)
- En `backend/app.py`, cambia `ensemble_strategy` a `'best'`

---

## 📚 Documentación Completa

- **LEEME_PRIMERO.md** - Guía general
- **ANALISIS_ESTADO_PROYECTO.md** - Estado vs rúbrica
- **RESUMEN_SISTEMA_AFORO.md** - Arquitectura
- **PROMPT_APLICACION_AFORO.md** - Especificación técnica
- **CODIGO_EJEMPLOS.md** - Ejemplos de código

---

## 🆘 Ayuda Rápida

### Comandos esenciales

```bash
# Backend
cd backend
python app.py                          # Iniciar servidor
curl http://localhost:5000/api/status  # Ver estado
curl -X POST http://localhost:5000/api/camera/start  # Iniciar cámara
curl -X POST http://localhost:5000/api/camera/stop   # Detener cámara

# Entrenamiento
cd scripts
python train_yolov8m.py               # Entrenar YOLOv8m (PRIORIDAD)
python train_yolov8s.py               # Entrenar YOLOv8s
python train_yolov8l.py               # Entrenar YOLOv8l
```

---

**¡Todo listo para comenzar! 🎉**
