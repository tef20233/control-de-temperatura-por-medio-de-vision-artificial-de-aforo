# 📱 Guía Rápida: Usar Cámara del Celular

## 🎯 Objetivo
Convertir tu celular en una cámara IP para el sistema de control de aforo.

---

## 📲 Método 1: IP Webcam (Android) - RECOMENDADO

### Paso 1: Instalar la App
1. Abre **Google Play Store**
2. Busca **"IP Webcam"** (por Pavel Khlebovich)
3. Descarga e instala
4. O usa este link: https://play.google.com/store/apps/details?id=com.pas.webcam

### Paso 2: Configurar IP Webcam
1. Abre la app **IP Webcam**
2. Baja hasta el final y presiona **"Opciones de video"**
3. Configura:
   - **Resolución**: 720p (1280x720) - recomendado
   - **Calidad**: 70-80%
   - **Orientación**: Auto o Landscape
4. Vuelve al menú principal

### Paso 3: Iniciar el Servidor
1. Baja hasta el final del menú principal
2. Presiona **"Iniciar servidor"**
3. La app mostrará una URL como:
   ```
   http://192.168.1.100:8080
   ```
   ⚠️ **IMPORTANTE**: Anota esta IP

### Paso 4: Configurar en la App de Aforo
1. En tu celular, abre la app **Control de Aforo** (Expo Go)
2. Presiona el botón **"⚙️ CONFIGURAR CÁMARA"**
3. En "Fuente de Cámara", ingresa:
   ```
   http://192.168.1.100:8080/video
   ```
   (Reemplaza `192.168.1.100` con tu IP real)
4. Selecciona Tipo: **auto** o **mjpeg**
5. Presiona **"🔍 PROBAR CONEXIÓN"** (opcional pero recomendado)
6. Si funciona, presiona **"✅ APLICAR CAMBIOS"**

### Paso 5: Iniciar Detección
1. Vuelve a la pantalla principal
2. Presiona **"▶️ INICIAR CÁMARA"**
3. En unos segundos verás el video en vivo con las detecciones

---

## 🍎 Método 2: EpocCam (iOS/Android)

### Para iPhone/iPad:
1. Descarga **EpocCam** de App Store
2. Instala también el driver en tu PC (si lo pide)
3. Abre la app y conecta vía WiFi
4. La app mostrará una URL, agrégala en configuración

### Para Android:
1. Descarga **EpocCam** de Play Store
2. Sigue los pasos similares a IP Webcam

---

## 🔧 Método 3: DroidCam (Android/iOS)

1. Descarga **DroidCam** de tu tienda de apps
2. Abre la app
3. Anota la URL que muestra (ej: `http://192.168.1.100:4747`)
4. En la app de aforo, agrega `/video` al final:
   ```
   http://192.168.1.100:4747/video
   ```

---

## ✅ Verificación Rápida

### Probar desde el navegador:
1. En tu PC, abre un navegador
2. Ingresa la URL completa: `http://192.168.1.100:8080/video`
3. Deberías ver el video de tu celular
4. Si no funciona, verifica WiFi y firewall

---

## ⚙️ Configuración Óptima

### Para mejor rendimiento:
| Parámetro | Valor Recomendado | Razón |
|-----------|-------------------|-------|
| Resolución | 720p (1280x720) | Balance calidad/velocidad |
| Calidad | 70-80% | Buena imagen sin saturar red |
| FPS | 20-30 | Suficiente para detección |
| Orientación | Landscape | Mejor campo de visión |

### Si el video va lento:
- ⬇️ Reduce resolución a 480p
- ⬇️ Reduce calidad a 60%
- ⬇️ Reduce FPS a 15-20
- 📶 Usa WiFi 5GHz si está disponible
- 🔌 Conecta el celular a la corriente

---

## 🎥 Posicionamiento de la Cámara

### Para mejor detección:
1. **Altura**: 2-3 metros del suelo
2. **Ángulo**: Ligeramente inclinado hacia abajo (30-45°)
3. **Ubicación**: Entrada principal o área de conteo
4. **Iluminación**: Buena luz, evita contraluz
5. **Estabilidad**: Usa un soporte o trípode

### Ejemplo de montaje:
```
     [Celular con IP Webcam]
           ↓ ↘
      ┌────────────┐
      │            │
      │   ENTRADA  │
      │            │
      └────────────┘
```

---

## 🔍 Solución de Problemas

### ❌ "No se puede conectar"

**Problema**: El backend no encuentra la cámara

**Soluciones**:
1. ✅ Verifica que celular y PC estén en la **misma WiFi**
2. ✅ Abre la URL en el navegador del PC para probar
3. ✅ Verifica que IP Webcam esté ejecutándose
4. ✅ Desactiva temporalmente el firewall
5. ✅ Prueba hacer ping a la IP del celular:
   ```bash
   ping 192.168.1.100
   ```

### ⏱️ "Timeout"

**Problema**: La conexión es muy lenta

**Soluciones**:
1. ⬇️ Reduce la resolución y calidad
2. 📶 Acércate al router WiFi
3. 🔄 Reinicia el router
4. 📵 Desconecta otros dispositivos de la WiFi

### 📹 "No se ve el video"

**Problema**: URL incorrecta

**Soluciones**:
1. ✅ Asegúrate de agregar `/video` al final
2. ✅ Verifica que la IP sea correcta
3. ✅ Prueba con tipo `mjpeg` en lugar de `auto`
4. ✅ Reinicia IP Webcam

### 🐌 "Video muy lento o entrecortado"

**Problema**: Red saturada o mala señal

**Soluciones**:
1. ⬇️ Reduce a 480p y calidad 60%
2. ⬇️ Limita FPS a 15
3. 📶 Usa WiFi 5GHz
4. 📱 Cierra otras apps en el celular
5. 💻 Cierra otras apps en el PC

---

## 💡 Tips y Trucos

### 🔋 Ahorro de Batería:
- Conecta el celular a la corriente
- Reduce brillo de pantalla en IP Webcam
- Desactiva otras apps en segundo plano

### 🌐 Encontrar tu IP:
**En IP Webcam:**
- Se muestra automáticamente al iniciar servidor

**Manualmente en Android:**
1. Configuración → WiFi
2. Presiona tu red conectada
3. Busca "Dirección IP"

### 🔐 Seguridad:
- No expongas la cámara a internet público
- Usa solo en tu red local
- Desactiva cuando no uses

### 📊 Verificar Rendimiento:
```bash
# Desde PC, verifica conectividad
ping 192.168.1.100

# Abre en navegador para ver latencia
http://192.168.1.100:8080/video
```

---

## 🎯 Checklist Rápido

Antes de empezar, verifica:

- [ ] ✅ Celular y PC en la misma WiFi
- [ ] ✅ IP Webcam instalada y ejecutándose
- [ ] ✅ Backend ejecutándose (`http://localhost:5000`)
- [ ] ✅ Frontend ejecutándose (Expo Go)
- [ ] ✅ URL probada en navegador
- [ ] ✅ Celular con buena carga o conectado
- [ ] ✅ Cámara bien posicionada

---

## 📞 Ayuda Adicional

### URLs de ejemplo válidas:
```bash
# IP Webcam
http://192.168.1.100:8080/video

# DroidCam
http://192.168.1.100:4747/video

# EpocCam
http://192.168.1.100:9000/video
```

### Verificar backend:
```bash
# En navegador o Postman
GET http://localhost:5000/api/status

# Cambiar cámara manualmente
POST http://localhost:5000/api/camera/change
{
  "source": "http://192.168.1.100:8080/video",
  "camera_type": "auto"
}
```

---

## ✨ Resultado Esperado

Cuando todo funcione correctamente verás:

1. ✅ Video en vivo en la app
2. ✅ Cuadros verdes alrededor de personas detectadas
3. ✅ Contador de personas actualizado en tiempo real
4. ✅ FPS mostrado en pantalla
5. ✅ Alertas cuando se excede aforo

---

## 🎉 ¡Éxito!

Si llegaste hasta aquí y todo funciona:

1. 👍 Tu celular ahora es una cámara IP
2. 🎯 El sistema está contando personas
3. 📊 Puedes ver estadísticas en tiempo real
4. 🚀 ¡Sistema completamente operativo!

---

**¿Necesitas más ayuda?**
- Consulta `GUIA_CAMARAS.md` para opciones avanzadas
- Revisa `CAMBIOS_CAMARAS.md` para detalles técnicos
- Verifica logs del backend en la terminal
