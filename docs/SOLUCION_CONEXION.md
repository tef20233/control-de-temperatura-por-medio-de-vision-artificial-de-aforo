# 🔧 Guía de Solución de Problemas de Conexión

## ❌ Error: "Network Error" en el Frontend

### 1️⃣ Verificar IP del Backend

```powershell
ipconfig
```

Busca la línea `Dirección IPv4` en tu red WiFi activa.

**Ejemplo**: `192.168.1.6`

### 2️⃣ Actualizar IP Automáticamente

```powershell
.\scripts\batch\actualizar_ip.bat
```

Este script detecta tu IP actual y actualiza automáticamente el frontend.

### 3️⃣ Actualizar IP Manualmente

Edita `frontend/src/utils/constants.js`:

```javascript
export const API_CONFIG = {
  BACKEND_URLS: [
    'http://TU_IP_ACTUAL:5000',  // ← Cambia esto
    'http://localhost:5000',
    // ...
  ],
  BASE_URL: 'http://TU_IP_ACTUAL:5000',  // ← Y esto
  WS_URL: 'ws://TU_IP_ACTUAL:5000',      // ← Y esto
};
```

### 4️⃣ Verificar que el Backend Esté Accesible

```powershell
curl http://TU_IP:5000/api/status
```

Debe responder con JSON del estado del sistema.

### 5️⃣ Verificar Firewall de Windows

Si el `curl` no funciona, el firewall puede estar bloqueando el puerto 5000.

**Solución A - Permitir Python en el Firewall**:

1. Abre "Windows Defender Firewall"
2. Click en "Permitir una aplicación"
3. Busca "Python" y asegúrate de que:
   - ✅ Red privada esté marcada
   - ✅ Red pública esté marcada (opcional)

**Solución B - Crear Regla Específica**:

```powershell
# Ejecutar como Administrador
netsh advfirewall firewall add rule name="Aforo Backend" dir=in action=allow protocol=TCP localport=5000
```

### 6️⃣ Reiniciar el Frontend

Después de actualizar la IP:

```powershell
# En la terminal del frontend, presiona Ctrl+C
# Luego inicia de nuevo
cd frontend
npm start
```

## 🔍 Diagnóstico Completo

### Paso 1: Verificar Backend

```powershell
# ¿Está corriendo el backend?
netstat -ano | Select-String "5000"
```

Debe mostrar:
```
TCP    0.0.0.0:5000    0.0.0.0:0    LISTENING
```

### Paso 2: Probar desde el Mismo PC

```powershell
curl http://localhost:5000/api/status
```

Si esto funciona, el backend está OK.

### Paso 3: Probar desde la Red

```powershell
curl http://192.168.1.6:5000/api/status
```

Si esto **NO** funciona pero localhost sí:
- ❌ Problema de firewall
- ❌ Backend no escuchando en 0.0.0.0

### Paso 4: Verificar que Backend Escucha en 0.0.0.0

En `backend/app.py` al final debe decir:

```python
socketio.run(app, host='0.0.0.0', port=5000, debug=True)
```

✅ `host='0.0.0.0'` = Escucha en TODAS las interfaces (correcto)
❌ `host='127.0.0.1'` = Solo localhost (incorrecto para red)

## 📱 Conexión desde Celular/Tablet

### Requisitos

1. ✅ PC y dispositivo en la **misma red WiFi**
2. ✅ Backend corriendo en `0.0.0.0:5000`
3. ✅ Firewall permitiendo el puerto 5000
4. ✅ IP actualizada en `constants.js`

### Verificar Conexión

En tu celular, abre el navegador y visita:

```
http://192.168.1.6:5000/api/status
```

Debes ver el JSON del estado.

Si no funciona:
- Verifica que ambos estén en la misma WiFi
- Desactiva temporalmente el firewall de Windows para probar
- Asegúrate de que no hay VPN activa

## 🚀 Comandos Útiles

### Obtener IP Actual

```powershell
ipconfig | Select-String "IPv4"
```

### Verificar Puerto 5000

```powershell
netstat -ano | Select-String "5000"
```

### Probar Backend

```powershell
curl http://localhost:5000/api/status
curl http://192.168.1.6:5000/api/status
```

### Ver Logs del Backend

Los logs aparecen en la terminal donde ejecutaste `python app.py`.

### Ver Logs del Frontend

Los logs aparecen en la terminal de Expo y en la consola del dispositivo.

## 🎯 Checklist Rápido

Antes de iniciar el sistema:

- [ ] Obtener IP actual con `ipconfig`
- [ ] Actualizar `constants.js` con la IP actual
- [ ] Verificar que backend escuche en `0.0.0.0`
- [ ] Permitir Python en el firewall
- [ ] Probar con `curl http://TU_IP:5000/api/status`
- [ ] Iniciar backend
- [ ] Iniciar frontend
- [ ] Escanear QR en el celular

## 💡 Tips

### Desarrollo en la Misma PC

Si estás desarrollando en la misma máquina (no usas celular):

```javascript
// constants.js
BASE_URL: 'http://localhost:5000',
WS_URL: 'ws://localhost:5000',
```

Esto es más rápido y no requiere firewall.

### Desarrollo con Dispositivo Móvil

Siempre usa la IP de red (ejemplo: `192.168.1.6`):

```javascript
BASE_URL: 'http://192.168.1.6:5000',
WS_URL: 'ws://192.168.1.6:5000',
```

### Cambio de Red Frecuente

Si cambias de red WiFi frecuentemente:

1. Usa el script `actualizar_ip.bat` antes de iniciar
2. O agrega múltiples IPs en `BACKEND_URLS` para auto-detección

## 🔥 Errores Comunes

### Error: "Network Error"
- ❌ IP incorrecta en `constants.js`
- ❌ Backend no corriendo
- ❌ Firewall bloqueando

**Solución**: Verificar IP y firewall

### Error: "Connection Timeout"
- ❌ Dispositivos en diferentes redes WiFi
- ❌ VPN activa
- ❌ Red de invitados (AP isolation)

**Solución**: Asegurar misma red, desactivar VPN

### Error: "CORS Error"
- ❌ Backend no tiene CORS habilitado

**Solución**: Ya está configurado en `app.py` con `flask-cors`

### Swagger No Carga
- ❌ `flasgger` no instalado
- ❌ Error en docstrings

**Solución**: `pip install flasgger`

## 📞 Ayuda Adicional

Si sigues teniendo problemas:

1. Revisa los logs del backend y frontend
2. Verifica que todos los servicios estén corriendo
3. Prueba con `curl` desde PowerShell
4. Desactiva temporalmente el firewall para diagnosticar
5. Asegúrate de estar en la misma red WiFi

## 🎉 Sistema Funcionando

Cuando todo funciona correctamente verás:

**Backend**:
```
🚀 SISTEMA DE CONTROL DE AFORO - BACKEND
Modelos cargados: ['yolov8m']
Puerto: 5000
(24884) wsgi starting up on http://0.0.0.0:5000
✅ WebSocket conectado
```

**Frontend**:
```
✅ Backend encontrado en: http://192.168.1.6:5000
✅ Conectado a backend: http://192.168.1.6:5000
🔌 Conectando WebSocket a: ws://192.168.1.6:5000
✅ WebSocket conectado
```

**App**:
- Banner verde: "✅ Conectado"
- Video streaming visible
- FPS > 0
- Contador de personas funcionando
