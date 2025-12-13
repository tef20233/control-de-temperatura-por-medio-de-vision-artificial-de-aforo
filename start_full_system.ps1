$ErrorActionPreference = "Stop"

Write-Host "Iniciando SISTEMA COMPLETO (Backend + Frontend)..." -ForegroundColor Cyan

# 1. Iniciar Backend (Flask API)
Write-Host "Iniciando Backend (API)..." -ForegroundColor Yellow
$BackendScript = "$PSScriptRoot\backend\app.py"
$VenvPython = "$PSScriptRoot\backend\venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Error "Entorno virtual no encontrado en backend/venv"
    exit 1
}

# Iniciar backend en nueva ventana
Start-Process -FilePath $VenvPython -ArgumentList $BackendScript -WorkingDirectory "$PSScriptRoot\backend" -WindowStyle Normal

# 2. Iniciar Frontend (Expo Web)
Write-Host "Iniciando Frontend (Web)..." -ForegroundColor Yellow
$FrontendDir = "$PSScriptRoot\frontend"

# Verificar node_modules
if (-not (Test-Path "$FrontendDir\node_modules")) {
    Write-Host "Instalando dependencias del frontend..." -ForegroundColor Gray
    Start-Process -FilePath "npm" -ArgumentList "install" -WorkingDirectory $FrontendDir -Wait
}

# Iniciar frontend en nueva ventana
Start-Process -FilePath "npm" -ArgumentList "run web" -WorkingDirectory $FrontendDir -WindowStyle Normal

Write-Host "Sistema iniciado." -ForegroundColor Green
Write-Host "Backend: http://localhost:5000" -ForegroundColor Gray
Write-Host "Frontend: http://localhost:8081 (se abrirá automáticamente)" -ForegroundColor Gray
