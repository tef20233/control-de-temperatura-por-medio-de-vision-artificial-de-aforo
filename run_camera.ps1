$ErrorActionPreference = "Stop"

# URL de DroidCam por defecto
$DefaultSource = "http://192.168.214.137:4747/video"

$Source = if ($args.Count -gt 0) { $args[0] } else { $DefaultSource }

Write-Host "Iniciando sistema de aforo (ADAPTADO GTX 1050 Ti + YOLO11s)..." -ForegroundColor Cyan
Write-Host "Usando fuente: $Source" -ForegroundColor Gray
Write-Host "Modelo: YOLO11 Small (yolo11s.pt) - Resolución: 512px" -ForegroundColor Gray

Set-Location "$PSScriptRoot\backend"

if (-not (Test-Path "venv")) {
    Write-Error "El entorno virtual no existe. Ejecuta la instalación primero."
    exit 1
}

# Verificar que existe el modelo seleccionado
if (-not (Test-Path "models\yolo11s.pt")) {
    Write-Host "Descargando modelo yolo11s.pt..." -ForegroundColor Yellow
    & .\venv\Scripts\python.exe -c "from ultralytics import YOLO; YOLO('yolo11s.pt').export(format='torchscript')" 2>$null
    Move-Item "yolo11s.pt" "models\yolo11s.pt" -Force -ErrorAction SilentlyContinue
}

# CONFIGURACIÓN ADAPTADA
# --model yolo11s.pt : Modelo Small solicitado por usuario.
# --imgsz 512        : Resolución estándar para Small.
# --conf 0.35        : Confianza estándar.

$cmd = ".\venv\Scripts\python.exe aforo_realtime\main.py --source `"$Source`" --config fast --device auto --half --model models\yolo11s.pt --imgsz 512 --conf 0.35 --iou 0.50 --max-det 100"

Invoke-Expression $cmd

if ($LASTEXITCODE -ne 0) {
    Write-Host "El programa terminó con errores." -ForegroundColor Red
    Read-Host "Presiona Enter para salir..."
}
