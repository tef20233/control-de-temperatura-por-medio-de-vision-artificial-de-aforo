# Guía de Instalación para PC con GTX 1060

Esta es la "receta" completa para configurar el proyecto en el PC con la GTX 1060.

## 1. Clonar el proyecto

En PowerShell:

```powershell
cd C:\ruta\donde\quieres\el\proyecto

git clone TU_URL_DEL_REPO.git app_aforo
cd .\app_aforo
```

*(Usa la URL de tu repo, por ejemplo `https://github.com/tu_usuario/app_aforo.git`)*

## 2. Crear entorno virtual e instalar dependencias

```powershell
cd .\backend

python -m venv venv
.\venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

pip install -r .\aforo_realtime\requirements.txt
```

Opcional, si también quieres levantar el backend viejo Flask:

```powershell
pip install -r .\requirements.txt
```

## 3. Comprobar que CUDA ve la 1060 (opcional pero recomendable)

```powershell
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

Debería mostrar `True` y algo tipo `GeForce GTX 1060 6GB`.

## 4. Probar el sistema de aforo realtime

### a) Con webcam del PC

```powershell
.\venv\Scripts\Activate.ps1
cd C:\ruta\a\app_aforo\backend

python .\aforo_realtime\main.py --source 0 --config fast --device auto --half --model yolov11s.pt --imgsz 512 --conf 0.35 --iou 0.55 --max-det 80 --fisheye
```

### b) Con DroidCam en el celular

Asegúrate de la IP que muestra DroidCam (ej. `192.168.1.4`) y usa:

```powershell
.\venv\Scripts\Activate.ps1
cd C:\ruta\a\app_aforo\backend

python .\aforo_realtime\main.py --source "http://192.168.1.4:4747/video" --config fast --device auto --half --model yolov11s.pt --imgsz 512 --conf 0.35 --iou 0.55 --max-det 80 --fisheye
```

Si quieres desenfoque de caras además del ojo de pez:

```powershell
python .\aforo_realtime\main.py --source "http://192.168.1.4:4747/video" --config fast --device auto --half --model yolov11s.pt --imgsz 512 --conf 0.35 --iou 0.55 --max-det 80 --fisheye --anonymize
```

Con esto deberías tener exactamente el mismo sistema corriendo en el PC con la 1060, con más margen para subir resolución (`--imgsz 800` o `960`) si ves que los FPS siguen altos.
