# 🎯 Sistema de Control de Aforo en Tiempo Real

Sistema completo de detección y conteo de personas en tiempo real con interfaz web, optimizado para GPUs NVIDIA GTX 1060 y superiores.

## 🌟 Características

- ✅ **Detección en tiempo real** a 30+ FPS con YOLO11s
- 🎥 **Múltiples fuentes de video**: Webcam, RTSP, DroidCam, IP Cameras
- 🌐 **Interfaz web moderna** con React Native Web
- 📊 **Dashboard en vivo** con métricas y estadísticas
- 🔒 **Opciones de privacidad** (blur facial, fisheye)
- ⚡ **Optimizado para GPU** NVIDIA con CUDA
- 📱 **Compatible con cámaras móviles** (DroidCam, IP Webcam)

## 📋 Requisitos

### Hardware
- **GPU**: NVIDIA GTX 1060 (6GB) o superior
- **RAM**: 8GB mínimo
- **CPU**: Intel i5 o equivalente

### Software
- **Python**: 3.8+
- **Node.js**: 16+
- **CUDA**: 11.8+ (para GPU NVIDIA)
- **Sistema Operativo**: Windows 10/11, Linux

## 🚀 Instalación Rápida

### 1. Clonar el Repositorio
```bash
git clone https://github.com/TU_USUARIO/app_aforo.git
cd app_aforo
```

### 2. Backend (Python)

```powershell
# Ir a carpeta backend
cd backend

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
.\\venv\\Scripts\\activate
# Linux/Mac:
source venv/bin/activate

# Instalar PyTorch con CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Instalar dependencias
pip install -r requirements.txt

# Volver al directorio raíz
cd ..
```

### 3. Frontend (React Native Web)

```bash
# Ir a carpeta frontend
cd frontend

# Instalar dependencias
npm install

# Volver al directorio raíz
cd ..
```

## 🎮 Uso

### Opción 1: Sistema Completo (Backend + Frontend)

```powershell
# Iniciar todo el sistema automáticamente
.\\start_full_system.ps1
```

Esto abrirá:
- Backend en `http://localhost:5000`
- Frontend en `http://localhost:8081`

### Opción 2: Solo Detección CLI

```powershell
# Para webcam local (índice 0)
.\\run_camera.ps1

# Para DroidCam
.\\run_camera.ps1 http://192.168.1.4:4747/video

# Para cámara RTSP
.\\run_camera.ps1 rtsp://192.168.1.100:554/stream
```

## 📱 Configurar DroidCam

1. Instala **DroidCam** en tu celular (Android/iOS)
2. Conecta el celular y la PC a la **misma WiFi**
3. Abre DroidCam y anota la URL (ej: `http://192.168.1.4:4747`)
4. En el frontend, ve a **"Configurar Cámara"**
5. Ingresa la URL: `http://192.168.1.4:4747/video`
6. Selecciona tipo: **MJPEG**
7. Click en **"APLICAR CAMBIOS"**

## ⚙️ Configuración

### Cambiar Modelo YOLO

Edita `backend/app.py` línea ~112:

```python
detector = RealtimeDetector(
    model_path='models/yolo11s.pt',  # Cambiar aquí
    ...
)
```

Modelos soportados:
- `yolo11n.pt` - Nano (más rápido, menos preciso)
- `yolo11s.pt` - **Small (recomendado, 30+ FPS)**
- `yolo11m.pt` - Medium (más preciso, ~20 FPS)
- `yolo11l.pt` - Large (muy preciso, ~10 FPS)

### Ajustar Parámetros de Detección

En `backend/app.py`:

```python
detector = RealtimeDetector(
    imgsz_override=512,      # Resolución (384/512/640)
    conf_override=0.35,      # Confianza (0-1)
    iou_override=0.50,       # IoU threshold (0-1)
    max_det_override=100     # Máx. detecciones
)
```

## 📊 API Endpoints

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/status` | GET | Estado del sistema |
| `/api/config` | GET/POST | Configuración |
| `/api/camera/start` | POST | Iniciar procesamiento |
| `/api/camera/stop` | POST | Detener procesamiento |
| `/api/camera/change` | POST | Cambiar fuente de cámara |
| `/api/camera/test` | POST | Probar conexión a cámara |
| `/viewer` | GET | Visualizador web |

Documentación completa: `http://localhost:5000/apidocs`

## 🛠️ Estructura del Proyecto

```
app_aforo/
├── backend/
│   ├── aforo_realtime/      # Motor de detección optimizado
│   ├── core/                # Detector, cámara, tracker
│   ├── models/              # Modelos YOLO (descargables)
│   ├── app.py              # API Flask principal
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── screens/        # Pantallas React
│   │   ├── services/       # API client
│   │   └── utils/          # Utilidades
│   ├── App.js
│   └── package.json
├── docs/                   # Documentación
├── run_camera.ps1         # Script rápido
└── start_full_system.ps1  # Launcher completo
```

## 🎯 Rendimiento Esperado

| GPU | Modelo | Resolución | FPS |
|-----|--------|------------|-----|
| GTX 1060 6GB | yolo11s | 512px | 30-40 |
| GTX 1660 Ti | yolo11s | 640px | 40-50 |
| RTX 3060 | yolo11m | 640px | 50-60 |

## 🐛 Solución de Problemas

### Backend no inicia
```powershell
# Verificar CUDA
python -c "import torch; print(torch.cuda.is_available())"

# Reinstalar PyTorch
pip install --force-reinstall torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Frontend no conecta
1. Verificar que el backend esté corriendo en puerto 5000
2. Abrir `http://localhost:5000/api/status` en el navegador
3. Revisar configuración de red

### FPS bajo
1. Usar modelo más pequeño (`yolo11n.pt`)
2. Reducir resolución a 384px
3. Desactivar blur/fisheye
4. Cerrar otras aplicaciones que usen GPU

## 📝 Licencia

MIT License - Libre para uso comercial y personal

## 👨‍💻 Autor

Desarrollado con ❤️ para proyectos de visión artificial

## 🙏 Agradecimientos

- [Ultralytics YOLO](https://github.com/ultralytics/ultralytics) - Framework de detección
- [Flask](https://flask.palletsprojects.com/) - Backend API
- [React Native](https://reactnative.dev/) - Frontend

---

⭐ Si te gusta este proyecto, dale una estrella en GitHub!
