# Script para buscar la camara Tapo por MAC
$macBuscada = "78-20-51-1E-3B-03"
$macBuscadaLower = "78-20-51-1e-3b-03"

Write-Host "Buscando camara con MAC: $macBuscada" -ForegroundColor Cyan
Write-Host "Escaneando red..." -ForegroundColor Yellow

# Hacer ping a un rango de IPs para actualizar la tabla ARP
$subnet = "192.168.203"
Write-Host "Escaneando subred $subnet.0/24..." -ForegroundColor Yellow

1..254 | ForEach-Object -Parallel {
    $ip = "$using:subnet.$_"
    Test-Connection -ComputerName $ip -Count 1 -TimeoutSeconds 1 -Quiet | Out-Null
} -ThrottleLimit 50

Start-Sleep -Seconds 2

# Buscar en la tabla ARP
Write-Host "Buscando en tabla ARP..." -ForegroundColor Yellow
$arpOutput = arp -a

$encontrada = $false
foreach ($line in $arpOutput) {
    if ($line -match $macBuscada -or $line -match $macBuscadaLower) {
        Write-Host ""
        Write-Host "CAMARA ENCONTRADA!" -ForegroundColor Green
        Write-Host $line -ForegroundColor Green
        
        # Extraer IP usando regex
        if ($line -match "(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})") {
            $ipEncontrada = $matches[1]
            Write-Host ""
            Write-Host "IP de la camara: $ipEncontrada" -ForegroundColor Cyan
            
            # Guardar en archivo
            $ipEncontrada | Out-File -FilePath "ip_camara_encontrada.txt" -Encoding utf8
            Write-Host "IP guardada en: ip_camara_encontrada.txt" -ForegroundColor Yellow
        }
        $encontrada = $true
        break
    }
}

if (-not $encontrada) {
    Write-Host ""
    Write-Host "Camara no encontrada en la subred $subnet.0/24" -ForegroundColor Red
    Write-Host "Mostrando todos los dispositivos encontrados:" -ForegroundColor Yellow
    Write-Host ""
    arp -a | Select-String -Pattern "dinamico"
}
