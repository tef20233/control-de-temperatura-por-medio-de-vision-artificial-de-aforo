# Instalación de FFmpeg para Cámara Tapo

## ¿Por qué necesito FFmpeg?

El servidor de la cámara (`backend/utils/camara.py`) usa **pytapo** que requiere **ffmpeg** para capturar y procesar frames de video de la cámara Tapo.

## 📦 Opción 1: Instalación Rápida con Chocolatey (RECOMENDADO)

Si tienes **Chocolatey** instalado:

```powershell
# Ejecutar PowerShell como Administrador
choco install ffmpeg
```

Si no tienes Chocolatey, primero instálalo:

```powershell
# En PowerShell como Administrador
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

Luego instala ffmpeg:
```powershell
choco install ffmpeg
```

## 📦 Opción 2: Instalación Manual

### Paso 1: Descargar FFmpeg

1. Ve a: https://github.com/BtbN/FFmpeg-Builds/releases
2. Descarga: **ffmpeg-master-latest-win64-gpl.zip** (última versión)

### Paso 2: Extraer archivos

1. Extrae el archivo ZIP a una ubicación permanente, por ejemplo:
   ```
   C:\ffmpeg
   ```

2. Dentro deberías tener algo como:
   ```
   C:\ffmpeg\bin\ffmpeg.exe
   C:\ffmpeg\bin\ffprobe.exe
   C:\ffmpeg\bin\ffplay.exe
   ```

### Paso 3: Agregar al PATH

**Opción A - Por GUI:**

1. Presiona `Win + X` y selecciona "Sistema"
2. Clic en "Configuración avanzada del sistema"
3. Clic en "Variables de entorno"
4. En "Variables del sistema", busca "Path" y haz doble clic
5. Clic en "Nuevo"
6. Agrega: `C:\ffmpeg\bin`
7. Clic en "Aceptar" en todas las ventanas

**Opción B - Por PowerShell (como Administrador):**

```powershell
# Agregar FFmpeg al PATH del sistema
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\ffmpeg\bin", "Machine")
```

### Paso 4: Verificar instalación

Abre una **nueva** ventana de PowerShell o CMD y ejecuta:

```bash
ffmpeg -version
```

Deberías ver algo como:
```
ffmpeg version N-... Copyright (c) 2000-2024 the FFmpeg developers
...
```

## 📦 Opción 3: Usando Conda/Miniconda (Si usas Anaconda)

Si tienes un entorno conda activo:

```bash
conda install -c conda-forge ffmpeg
```

## ✅ Verificar que funciona con Python

Ejecuta este script de prueba:

```python
import subprocess

try:
    result = subprocess.run(['ffmpeg', '-version'], 
                          capture_output=True, 
                          text=True, 
                          timeout=5)
    if result.returncode == 0:
        print("✅ FFmpeg instalado correctamente")
        print(result.stdout.split('\n')[0])
    else:
        print("❌ FFmpeg encontrado pero con errores")
except FileNotFoundError:
    print("❌ FFmpeg NO está instalado o no está en el PATH")
except Exception as e:
    print(f"❌ Error: {e}")
```

## 🚀 Después de Instalar

1. **Cierra y reabre** todas las ventanas de terminal/PowerShell/CMD
2. **Cierra y reabre** tu IDE/editor
3. Verifica que ffmpeg está disponible: `ffmpeg -version`
4. Ahora puedes iniciar el servidor de la cámara:

```bash
cd backend/utils
python camara.py
```

## 🐛 Solución de Problemas

### Problema: "ffmpeg no se reconoce como comando"

**Solución:**
- Verifica que agregaste `C:\ffmpeg\bin` al PATH (no `C:\ffmpeg`)
- Cierra y reabre la terminal
- Reinicia tu PC si es necesario

### Problema: "No module named 'pytapo'"

**Solución:**
```bash
pip install pytapo
```

### Problema: El servidor se inicia pero falla al capturar frames

**Causas posibles:**
1. IP de la cámara incorrecta en `camara.py`
2. Contraseña incorrecta
3. La cámara está apagada o no accesible en la red

**Verificar configuración en camara.py:**
```python
HOST = "192.168.196.100"  # ← Verifica esta IP
USER = "admin"
PASSWORD_CLOUD = "tu_contraseña"  # ← Verifica esta contraseña
```

## 📝 Dependencias Completas

Para que todo funcione, necesitas:

```bash
pip install flask pytapo pillow numpy
```

Y tener instalado:
- Python 3.8+
- FFmpeg (esta guía)

## 🔗 Enlaces Útiles

- FFmpeg oficial: https://ffmpeg.org/
- FFmpeg Windows builds: https://github.com/BtbN/FFmpeg-Builds/releases
- pytapo: https://github.com/JurajNyiri/pytapo
- Chocolatey: https://chocolatey.org/

## ⚡ Instalación Express (Todo en uno)

```powershell
# PowerShell como Administrador

# 1. Instalar Chocolatey (si no lo tienes)
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# 2. Instalar FFmpeg
choco install ffmpeg -y

# 3. Verificar
ffmpeg -version
```

Luego en tu terminal normal:
```bash
# 4. Instalar dependencias Python
pip install flask pytapo pillow numpy

# 5. Iniciar servidor de cámara
cd backend/utils
python camara.py
```

¡Listo! 🎉
