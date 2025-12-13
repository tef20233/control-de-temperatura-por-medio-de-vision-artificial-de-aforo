# 🚀 Guía de Inicio del Sistema de Aforo

## 📋 Información de Configuración

### Cámara Tapo
- **IP:** 192.168.222.224
- **Usuario:** admin
- **Password:** 987654321Usco.,

### Arquitectura del Sistema
```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  Cámara Tapo    │ ──────> │  Servicio Cámara │ ──────> │  Backend YOLO   │
│  192.168.222.224│         │  Puerto 5001     │         │  Puerto 5000    │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                                                    │
                                                                    v
                                                          ┌─────────────────┐
                                                          │    Frontend     │
                                                          │  React Native   │
                                                          └─────────────────┘
```

## 🔧 Pasos para Iniciar el Sistema

### 1. Instalar Dependencias (Solo la primera vez)

#### Backend:
```bash
cd backend
pip install -r requirements.txt
```

#### Frontend:
```bash
cd frontend
npm install
```

### 2. Iniciar los Servicios (En este orden)

#### Terminal 1 - Servicio de Cámara:
```bash
cd backend
python utils/camara.py
```
✅ Debe mostrar: `Running on http://0.0.0.0:5001`

#### Terminal 2 - Backend Principal:
```bash
cd backend
python app.py
```
✅ Debe mostrar:
- Modelos YOLO cargados
- `Running on http://0.0.0.0:5000`

#### Terminal 3 - Frontend:
```bash
cd frontend
npm start
```
✅ Debe abrir el navegador en `http://localhost:3000` o `http://localhost:19006`

### 3. Verificar Conexión

#### Opción A - Script de Diagnóstico:
```bash
cd backend
python test_conexion_completa.py
```

#### Opción B - Manual:
1. **Servicio de Cámara:** http://localhost:5001/snapshot
2. **Backend API:** http://localhost:5000/api/status
3. **Frontend:** http://localhost:3000 (o el puerto que muestre)

## 🔍 Resolución de Problemas

### ❌ Error: "No se puede conectar al servicio de cámara"
**Solución:**
1. Verificar que `python utils/camara.py` está corriendo
2. Verificar IP de la cámara en `backend/utils/camara.py` línea 14:
   ```python
   HOST = "192.168.222.224"
   ```
3. Hacer ping a la cámara: `ping 192.168.222.224`

### ❌ Error: "Failed to connect to camera"
**Solución:**
1. Verificar que la cámara Tapo está encendida y conectada a la red
2. Verificar credenciales en `backend/utils/camara.py`:
   - USER = "admin"
   - PASSWORD_CLOUD = "987654321Usco.,"
3. Intentar acceder manualmente: http://192.168.222.224:5001/snapshot

### ❌ Error: "Timeout" en el frontend
**Solución:**
1. El timeout está configurado en 10 segundos en `frontend/src/utils/constants.js`
2. Si sigue fallando, aumentar a 15000:
   ```javascript
   TIMEOUT: 15000,
   ```

### ❌ Error: "No models loaded"
**Solución:**
1. Descargar modelos YOLOv8:
   ```bash
   cd backend
   python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
   ```
2. Los modelos se guardan automáticamente en `backend/models/`

### ❌ Error: "ModuleNotFoundError: No module named 'pytapo'"
**Solución:**
```bash
pip install pytapo
```

### ❌ Error: CORS en el navegador
**Solución:**
1. Verificar que `flask-cors` está instalado:
   ```bash
   pip install flask-cors
   ```
2. Ya está configurado en `backend/app.py` línea 15:
   ```python
   CORS(app)
   ```

## 📊 Monitoreo del Sistema

### Ver logs del sistema:
- **Servicio de Cámara:** Ver terminal 1
- **Backend:** Ver terminal 2
- **Frontend:** Ver consola del navegador (F12)

### Endpoints útiles:
- **Estado del sistema:** http://localhost:5000/api/status
- **Configuración:** http://localhost:5000/api/config
- **Información de modelos:** http://localhost:5000/api/models
- **Test de cámara:** POST http://localhost:5000/api/camera/test
- **Escanear cámaras:** POST http://localhost:5000/api/camera/scan

## 🎯 Iniciar Detección

1. En el frontend, hacer clic en **"Iniciar Cámara"**
2. El sistema comenzará a:
   - Capturar frames de la cámara Tapo
   - Procesar con YOLOv8 (detección de personas)
   - Mostrar conteo en tiempo real
   - Enviar alertas si se supera el aforo

## 📝 Configuración Avanzada

### Cambiar estrategia de ensemble:
En el frontend o mediante POST a `/api/config`:
```json
{
  "ensemble_strategy": "union",
  "confidence_threshold": 0.35,
  "max_capacity": 50
}
```

Estrategias disponibles:
- **average:** Promedia conteos de todos los modelos
- **majority:** Usa el conteo más frecuente
- **best:** Usa solo el modelo con mayor mAP
- **union:** Une todas las detecciones (RECOMENDADO)

### Cambiar fuente de cámara:
POST a `/api/camera/change`:
```json
{
  "source": "http://192.168.222.224:5001",
  "camera_type": "tapo"
}
```

## 🛠️ Scripts Útiles

### Iniciar todos los servicios:
```bash
# Windows
iniciar_backend.bat

# Linux/Mac
./scripts/start_all.sh
```

### Detener todos los servicios:
- Presionar `Ctrl+C` en cada terminal

### Diagnóstico completo:
```bash
cd backend
python test_conexion_completa.py
```

## 📚 Documentación Adicional

- **README.md:** Información general del proyecto
- **CONFIGURACION_CAMARA_TAPO.md:** Configuración detallada de la cámara
- **INTEGRACION_COMPLETA.md:** Detalles de la integración
- **RESUMEN_SISTEMA_AFORO.md:** Resumen del sistema completo

## 💡 Tips

1. **Siempre iniciar en orden:** Cámara → Backend → Frontend
2. **Mantener las terminales abiertas** para ver logs en tiempo real
3. **Si algo falla:** Ejecutar `test_conexion_completa.py` para diagnosticar
4. **Primera vez:** Los modelos YOLO se descargan automáticamente (puede tardar)
5. **Red lenta:** Aumentar timeout en `constants.js`

## 🎉 ¡Listo!

Si todos los servicios están corriendo correctamente, deberías ver:
- ✅ Cámara conectada
- ✅ Backend procesando frames
- ✅ Frontend mostrando video en tiempo real
- ✅ Conteo de personas funcionando

¿Problemas? Ejecuta el script de diagnóstico: `python backend/test_conexion_completa.py`
