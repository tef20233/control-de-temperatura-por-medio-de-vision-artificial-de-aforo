# 📹 Guía de Configuración de Cámaras

## 🎯 Tipos de Cámaras Soportadas

### 1. 💻 Webcam del PC
**Uso:** Cámara USB conectada directamente al PC

**Configuración:**
- Fuente: `0` (o `1`, `2`, etc. si tienes múltiples cámaras)
- Tipo: `webcam` o `auto`

**Ventajas:**
- Sin configuración adicional
- Fácil de usar
- No requiere red

### 2. 📱 Cámara del Celular (IP Webcam)
**Uso:** Usar la cámara de tu celular como cámara IP

**Pasos:**

1. **Descargar App:**
   - Android: [IP Webcam](https://play.google.com/store/apps/details?id=com.pas.webcam)
   - iOS: [EpocCam](https://apps.apple.com/app/epoccam-webcam-for-computer/id449133483)

2. **Configurar App (IP Webcam):**
   - Abre la app
   - Ajusta la resolución (recomendado: 720p o 1080p)
   - Ajusta la calidad (recomendado: 70-80%)
   - Presiona "Iniciar servidor"

3. **Obtener URL:**
   - La app mostrará una URL como: `http://192.168.1.100:8080`
   - Agrega `/video` al final: `http://192.168.1.100:8080/video`

4. **Configurar en la App de Aforo:**
   - Fuente: `http://192.168.1.100:8080/video`
   - Tipo: `auto` o `mjpeg`

**Ventajas:**
- Usa la cámara del celular (mejor calidad)
- Inalámbrico
- Posicionamiento flexible

**Requisitos:**
- PC y celular en la misma red WiFi
- Batería del celular (o conectar a corriente)

### 3. 🌐 Cámara IP / RTSP
**Uso:** Cámaras IP profesionales con protocolo RTSP

**Configuración:**
- Fuente: `rtsp://usuario:contraseña@192.168.1.X:554/stream`
- Tipo: `rtsp` o `auto`

**Ejemplos comunes:**
- Hikvision: `rtsp://admin:contraseña@192.168.1.X:554/Streaming/Channels/101`
- Dahua: `rtsp://admin:contraseña@192.168.1.X:554/cam/realmonitor?channel=1&subtype=0`
- Tapo (RTSP): `rtsp://admin:contraseña@192.168.1.X:554/stream1`

### 4. 📡 Cámara Tapo (HTTP)
**Uso:** Cámaras TP-Link Tapo con servidor Flask intermediario

**Configuración:**
- Fuente: `http://192.168.1.X:5001/snapshot`
- Tipo: `tapo` o `auto`

**Nota:** Requiere ejecutar el servidor `camara.py` en el PC

### 5. 📹 Otras Cámaras MJPEG
**Uso:** Cualquier cámara que transmita via MJPEG sobre HTTP

**Configuración:**
- Fuente: URL del stream MJPEG
- Tipo: `mjpeg` o `auto`

**Ejemplos:**
- DroidCam: `http://192.168.1.X:4747/video`
- Webcam IP genérica: `http://192.168.1.X:8080/video.mjpg`

---

## 🔧 Cómo Configurar una Cámara

### Desde la App Móvil

1. Abre la app de Control de Aforo
2. Presiona el botón **"⚙️ CONFIGURAR CÁMARA"**
3. Elige una opción rápida o configura manualmente:
   - **Opciones Rápidas:**
     - Webcam del PC
     - Cámara del Celular (muestra instrucciones)
     - Buscar Cámaras en Red (escaneo automático)
   
   - **Configuración Manual:**
     - Ingresa la fuente de la cámara
     - Selecciona el tipo
     - Presiona "🔍 PROBAR CONEXIÓN" (solo para HTTP)
     - Presiona "✅ APLICAR CAMBIOS"

### Desde el Backend (API)

**Cambiar cámara:**
```bash
curl -X POST http://localhost:5000/api/camera/change \
  -H "Content-Type: application/json" \
  -d '{
    "source": "http://192.168.1.100:8080/video",
    "camera_type": "auto"
  }'
```

**Probar conexión:**
```bash
curl -X POST http://localhost:5000/api/camera/test \
  -H "Content-Type: application/json" \
  -d '{
    "camera_url": "http://192.168.1.100:8080/video",
    "timeout": 5
  }'
```

**Escanear red:**
```bash
curl -X POST http://localhost:5000/api/camera/scan \
  -H "Content-Type: application/json" \
  -d '{
    "ips": ["192.168.1.100", "192.168.1.101"],
    "port": 8080,
    "timeout": 3
  }'
```

---

## ❓ Solución de Problemas

### No se puede conectar a la cámara

1. **Verificar red:**
   - PC y cámara deben estar en la misma red WiFi
   - Ejecuta `ipconfig` (Windows) o `ifconfig` (Linux/Mac) para ver tu IP
   - Verifica que puedes hacer ping a la cámara

2. **Verificar URL:**
   - Abre la URL en un navegador web
   - Deberías ver el stream o una imagen

3. **Verificar firewall:**
   - El firewall puede bloquear conexiones
   - Permite el puerto de la cámara (ej: 8080)

4. **Verificar app (IP Webcam):**
   - La app debe estar en primer plano
   - El celular no debe estar en modo de ahorro de energía

### Stream lento o entrecortado

1. **Reducir resolución:**
   - En IP Webcam: configurar a 480p o 720p
   
2. **Reducir calidad:**
   - Ajustar calidad JPEG a 60-70%

3. **Verificar WiFi:**
   - Usar WiFi de 5GHz si está disponible
   - Acercarse al router

4. **Reducir FPS:**
   - En IP Webcam: limitar a 15-20 FPS

### Errores comunes

**Error: "Timeout"**
- La cámara no está accesible en la red
- Verifica la IP y el puerto

**Error: "Connection refused"**
- El servidor/app no está ejecutándose
- Verifica que IP Webcam está activa

**Error: "No se pudo decodificar el frame"**
- Formato de video incompatible
- Prueba con un tipo de cámara diferente

---

## 📊 Comparación de Métodos

| Método | Calidad | Latencia | Configuración | Costo |
|--------|---------|----------|---------------|-------|
| Webcam PC | Media-Alta | Muy baja | Muy fácil | Baja |
| IP Webcam (celular) | Alta | Baja | Fácil | Gratis |
| Cámara IP RTSP | Muy alta | Baja | Media | Alta |
| Cámara Tapo HTTP | Alta | Media | Media | Media |

---

## 💡 Recomendaciones

1. **Para desarrollo/pruebas:**
   - Usa la webcam del PC (más fácil)

2. **Para demostración:**
   - Usa IP Webcam en celular (mejor calidad, móvil)

3. **Para producción:**
   - Usa cámara IP RTSP profesional (confiable, permanente)

4. **Para eventos temporales:**
   - Usa IP Webcam en celular (rápido de configurar)

---

## 🔐 Seguridad

- **No expongas** las URLs de cámaras a internet sin protección
- **Cambia contraseñas** por defecto de cámaras IP
- **Usa HTTPS** cuando sea posible
- **Limita acceso** a la red local

---

## 📚 Recursos Adicionales

- [IP Webcam - Play Store](https://play.google.com/store/apps/details?id=com.pas.webcam)
- [DroidCam](https://www.dev47apps.com/)
- [EpocCam (iOS)](https://www.kinoni.com/)
- [Documentación RTSP](https://en.wikipedia.org/wiki/Real_Time_Streaming_Protocol)
