# Aforo Inteligente – Demo Local

Este **README** describe los pasos necesarios para ejecutar la demo del proyecto **Aforo Inteligente** en tu máquina local y presentarlo a tu profesor. **En esta demo el hardware (Arduino y cámara) es obligatorio**; la aplicación mostrará el control real del HVAC y la transmisión de video.

---

## 📋 Requisitos previos

1. **Sistema operativo**: Windows (se probó en Windows 10/11).
2. **Python** >= 3.9 (recomendado 3.10).
3. **Node.js** >= 18.
4. **Git** para clonar el repositorio.
5. **Arduino UNO/Nano** con el firmware `arduino_hvac_ir.ino` cargado (ver sección *Hardware*).
6. **Cámara**: webcam USB conectada al PC **o** smartphone con app IP Webcam (en la misma red Wi‑Fi).
7. **Puerto serie**: `COM6` (puede cambiarse en `backend/config.py`).

---

## 🛠️ Instalación paso a paso

```bash
# 1. Clonar el repo
git clone https://github.com/tef20233/control-de-temperatura-por-medio-de-vision-artificial-de-aforo.git
cd control-de-temperatura-por-medio-de-vision-artificial-de-aforo

# 2. Backend (Python)
python -m venv venv
venv\Scripts\activate   # en PowerShell: .\venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt

# 3. Frontend (React Native – Expo)
npm install   # dentro de la carpeta frontend
```

---

## 📡 Conexión del hardware

### Arduino (HVAC IR)
1. Abre `hardware/arduino_hvac_ir/arduino_hvac_ir.ino` en el IDE de Arduino.
2. Selecciona la placa **Arduino UNO** (o **Nano**) y el puerto **COM6** (o el que corresponda).
3. Verifica que la librería **ArduinoJson** esté instalada (v6.21 o superior).
4. Carga el firmware.
5. Enciende el Arduino; los LEDs del pin 9 parpadearán indicando que está listo.

### Cámara
- **Opción 1 – Webcam USB**: simplemente conecta la cámara al PC.
- **Opción 2 – Smartphone**: instala una app como **IP Webcam** o **DroidCam**, inicia el stream y copia la URL (ej.: `http://192.168.1.45:8080/video`).

---

## ▶️ Ejecutar la demo

1. **Levantar el backend** (conexión al Arduino y cámara):
```bash
cd backend
venv\Scripts\python.exe app.py   # mantén esta ventana abierta
```
2. **Iniciar el frontend** (Expo):
```bash
cd ../frontend
npm start   # escanea el QR con la app Expo Go o abre el simulador
```
3. La aplicación mostrará:
   - Badge **API OK** (conexión al backend).
   - Badge **LIVE** (WebSocket activo).
   - Video en tiempo real proveniente de la cámara.
   - Estado del Arduino (conexión serie, marca, temperatura, etc.).
4. Desde el *Dashboard* podrás:
   - Cambiar la fuente de video.
   - Ajustar la temperatura, modo y ventilador del HVAC (se enviará el comando IR al Arduino).
   - Ver métricas de FPS y modelo YOLO cargado.

---

## ⏹️ Detener la demo

- En la terminal del backend presiona **Ctrl +C**.
- En la terminal del frontend también presiona **Ctrl +C** o cierra la ventana de Expo.

---

## ✅ Checklist para la presentación

- [ ] Arduino cargado y conectado a `COM6` (o puerto configurado).
- [ ] Cámara detectada y transmitiendo (prueba la URL en el navegador).
- [ ] Backend corriendo sin errores (`python app.py`).
- [ ] Frontend iniciado y mostrando la pantalla de bienvenida.
- [ ] Demonstrar los controles de HVAC y cambiar la cámara.

---

## 🚀 Próximos pasos (opcional)
- Persistencia de configuración en una base SQLite.
- Dockerizar backend y crear CI/CD.
- Añadir autenticación JWT.

¡Listo! Con estos pasos podrás presentar una demo completa que incluye **hardware real**, video en tiempo real y control del climatizador por infrarrojos.


Este **README** describe los pasos necesarios para ejecutar la demo del proyecto **Aforo Inteligente** en tu máquina local y presentarlo a tu profesor.

---

## 📋 Requisitos previos

1. **Sistema operativo**: Windows (se probó en Windows 10/11).   
2. **Python 3.10+** (para el backend).   
3. **Node.js 18+** y **npm** (para el frontend).   
4. **Git** (para clonar el repositorio).   
5. **Opcional – Arduino**: Si deseas conectar el hardware real, necesitarás un Arduino UNO/Nano y el firmware `arduino_hvac_ir.ino`.

---

## 🛠️ Instalación del proyecto

```bash
# 1️⃣ Clonar el repositorio
git clone https://github.com/tef20233/control-de-temperatura-por-medio-de-vision-artificial-de-aforo.git
cd control-de-temperatura-por-medio-de-vision-artificial-de-aforo
```

### Backend (Flask)
```bash
# 2️⃣ Crear entorno virtual
python -m venv venv
# Activar (cmd)    : venv\Scripts\activate
# Activar (PowerShell) : .\venv\Scripts\Activate.ps1
# Activar (Git Bash)    : source venv/Scripts/activate

# 3️⃣ Instalar dependencias
pip install -r backend/requirements.txt

# 4️⃣ (Opcional) Simular hardware si no tienes Arduino
#    Edita backend/config.py y cambia:
#    SIMULATION = False  -> SIMULATION = True
```

### Frontend (React‑Native con Expo)
```bash
# 5️⃣ Instalar dependencias del frontend
cd frontend
npm install
```

---

## ▶️ Ejecutar la demo en local

### 1️⃣ Iniciar el backend
```bash
cd ..               # volver al root del proyecto
venv\Scripts\python.exe backend/app.py   # o: python backend/app.py
```
> **Salida esperada**: el servidor se levanta en `http://127.0.0.1:5000` y muestra “*Servidor iniciado*”.  Mantén esta ventana abierta para que la app pueda conectar.

### 2️⃣ Iniciar el frontend (Expo)
```bash
cd frontend
npm start               # abre el Metro Bundler y muestra un QR
```
Escanea el QR con la cámara de tu teléfono (Android o iOS) o elige **Run on Android device / emulator**.

### 3️⃣ Ver la demo
1. **Pantalla de bienvenida** – barra de carga y radar animado.
2. **Dashboard** – badges *API OK* y *LIVE*, contador de personas, barra de ocupación y métricas.
3. **Configurar cámara** – pulsa el botón ⚙ CONFIGURAR y prueba: 
   - *Webcam de PC* (fuente `0`).
   - *Cámara del celular* (muestra instrucciones para usar una app de streaming).
   - *Escanear red* (busca cámaras IP en la LAN).
4. **Configurar HVAC** – pulsa ❄ CLIMATIZACIÓN (IR) y cambia temperatura, modo, ventilador o cambia de marca.
5. Si no tienes Arduino, la app mostrará “Arduino Simulado” y seguirá funcionando.

---

## 🛑 Detener la demo
```bash
# En la ventana del backend
Ctrl + C
# En la ventana de Expo (Metro Bundler)
Ctrl + C
```

---

## ✅ Qué está listo para la presentación
- Interfaz premium (modo oscuro, colores neón, animaciones).  
- Video en tiempo real vía WebSocket (o placeholder radar cuando está inactivo).  
- Configuración de cámara y HVAC totalmente operativa.  
- Simulación automática si el hardware no está conectado.  
- Todo funciona en *localhost* sin necesidad de despliegue en la nube.

---

## 📦 Próximos pasos (para continuar el proyecto)
- Persistencia de configuración (SQLite/TinyDB).  
- Dockerizar el backend y crear CI/CD.  
- Autenticación JWT y HTTPS.  
- Soporte para más marcas y protocolos de cámara.

---

## 🎉 ¡Listo!
Con estos pasos podrás lanzar la demo localmente y demostrar a tu profesor que el proyecto está completamente funcional y visualmente atractivo.
