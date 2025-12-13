# Sistema CLI de Control de Aforo en Tiempo Real

Este módulo proporciona una aplicación **standalone por línea de comandos** para detección y conteo de personas en tiempo real usando modelos YOLO ya entrenados en `backend/models`.

- Usa los modelos existentes (por ejemplo `yolov8s.pt`, `yolov11s.pt`).
- Optimizado para GPU NVIDIA (por ejemplo GTX 1050 Ti) con fallback a CPU.
- Soporta webcam, archivos de vídeo, streams RTSP y carpetas de imágenes.
- Incluye presets de velocidad/calidad (`ultra_fast`, `fast`, `balanced`, `quality`).
- Logging a CSV/JSON y resumen de sesión.
- Anonimización facial opcional.

## Instalación (dentro de la carpeta `backend/aforo_realtime`)

```bash
# Crear entorno virtual (opcional)
python -m venv venv
venv\Scripts\activate  # En Windows

# Instalar dependencias mínimas
pip install -r requirements.txt
```

## Uso básico

Desde la carpeta `backend` del proyecto:

```bash
cd backend
python aforo_realtime/main.py               # Webcam 0, preset balanced, modelo por defecto
python aforo_realtime/main.py --source 0    # Webcam explícita
python aforo_realtime/main.py --source video.mp4 --config quality --save
python aforo_realtime/main.py --source rtsp://ip:puerto/stream --no-display --log
python aforo_realtime/main.py --source ruta/a/imagenes/ --config quality
```

Parámetros principales:

- `--model`: ruta al modelo (.pt o .engine). Por defecto busca en `backend/models`.
- `--source`: `0,1,...` (webcam), `archivo.mp4`, `rtsp://...` o carpeta de imágenes.
- `--config`: `ultra_fast | fast | balanced | quality` (default: `balanced`).
- `--imgsz`, `--conf`, `--iou`, `--max-det`: overrides finos sobre el preset.
- `--device`: `auto | cpu | 0 | 1 | cuda:0 ...`.
- `--half` / `--no-half`: activar/desactivar FP16.
- `--save` + `--output`: guardar vídeo procesado.
- `--no-display`: modo sin ventana (headless).
- `--anonymize`: anonimización facial básica.
- `--log` / `--no-log`: activar/desactivar logging CSV/JSON.
- `--log-format`: `csv | json | both`.

El módulo usa por defecto un modelo en `backend/models`, intentando primero `yolov8s_custom.pt` y luego `yolov8s.pt`. Puedes cambiarlo con `--model`.
