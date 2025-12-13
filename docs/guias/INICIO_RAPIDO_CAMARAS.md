
# 🚀 Inicio Rápido - Sistema con Cámaras

## ✅ Sistema Activo

- ✅ **Backend:** http://localhost:5000
- ✅ **Frontend:** exp://192.168.1.19:8081

## 📱 Conectar desde Celular

1. Instala **Expo Go** en tu celular:
   - [Android - Play Store](https://play.google.com/store/apps/details?id=host.exp.exponent)
   - [iOS - App Store](https://apps.apple.com/app/expo-go/id982107779)

2. Abre Expo Go y escanea el QR de la terminal

3. ¡Listo! La app se abrirá

## 📹 Usar Cámara del Celular

### Opción 1: IP Webcam (Android)

1. **Instalar app:**
   - Busca "IP Webcam" en Play Store
   - O descarga desde: https://play.google.com/store/apps/details?id=com.pas.webcam

2. **Configurar:**
   - Abre IP Webcam
   - Ajusta resolución a 720p
   - Ajusta calidad a 70%
   - Presiona "Iniciar servidor"

3. **Obtener URL:**
   - La app mostrará algo como: `http://192.168.1.100:8080`
   - Agrega `/video` al final: `http://192.168.1.100:8080/video`

4. **Configurar en la app:**
   - En la app de Control de Aforo, presiona "⚙️ CONFIGURAR CÁMARA"
   - Ingresa la URL completa: `http://192.168.1.100:8080/video`
   - Tipo: `auto`
   - Presiona "Probar Conexión"
   - Si funciona, presiona "Aplicar Cambios"

### Opción 2: EpocCam (iOS)

1. **Instalar app:**
   - Busca "EpocCam" en App Store
   - Descarga e instala

2. **Configurar:**
   - Sigue las instrucciones de la app
   - Obtén la URL del stream

3. **Configurar en la app:**
   - Igual que con IP Webcam

## 💻 Usar Webcam del PC

1. En la app, presiona "⚙️ CONFIGURAR CÁMARA"
2. Selecciona "Webcam del PC"
3. Presiona "Aplicar Cambios"
4. ¡Listo!

## 🔧 Solución Rápida de Problemas

### No se conecta la app al backend

1. Verifica que el celular y PC están en la misma WiFi
2. Obtén la IP del PC:
   ```bash
   ipconfig
   ```
3. Actualiza `API_BASE_URL` en `frontend/src/screens/HomeScreenSimple.js`

### No se conecta a la cámara del celular

1. Verifica que IP Webcam está ejecutándose
2. Prueba abrir la URL en el navegador del PC
3. Verifica que ambos están en la misma WiFi
4. Desactiva el firewall temporalmente para probar

### Stream muy lento

1. Reduce la resolución en IP Webcam a 480p
2. Reduce la calidad a 60%
3. Acércate al router WiFi

## 📚 Documentación Completa

- **GUIA_CAMARAS.md** - Guía detallada de todos los tipos de cámaras
- **CAMBIOS_CAMARAS.md** - Resumen técnico de cambios
- **README.md** - Documentación general

## 🎯 Tipos de Cámaras Soportadas

| Tipo | Ejemplo | Configuración |
|------|---------|---------------|
| Webcam PC | Cámara USB | Fuente: `0`, Tipo: `webcam` |
| IP Webcam | Celular Android | Fuente: `http://IP:8080/video`, Tipo: `auto` |
| EpocCam | iPhone/iPad | Fuente: URL de la app, Tipo: `auto` |
| Cámara IP | RTSP | Fuente: `rtsp://IP:554/stream`, Tipo: `rtsp` |
| Tapo | TP-Link Tapo | Fuente: `http://IP:5001/snapshot`, Tipo: `tapo` |

## ⚡ Scripts Útiles

- **INICIAR_TODO.bat** - Inicia backend y frontend automáticamente
- **iniciar_backend.bat** - Solo backend
- **iniciar_frontend.bat** - Solo frontend
- **iniciar_con_webcam.bat** - Prueba webcam antes de iniciar

## 💡 Tips

1. **Mantén el celular enchufado** si lo usas como cámara (consume batería)
2. **Usa WiFi de 5GHz** para mejor rendimiento
3. **Ajusta la calidad** según tu red (más calidad = más ancho de banda)
4. **Posiciona bien la cámara** para mejor detección de personas

## 🎉 ¡Listo!

Ahora tienes un sistema completo de control de aforo con soporte para múltiples tipos de cámaras, incluyendo la cámara de tu celular.

**¿Dudas?** Consulta `GUIA_CAMARAS.md` para información detallada.
