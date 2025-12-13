#!/usr/bin/env python3
"""Script para buscar la cámara Tapo por dirección MAC"""

import subprocess
import re
import time
import platform

MAC_BUSCADA = "78-20-51-1E-3B-03"
SUBNET = "192.168.203"  # Tu subred actual

print("=" * 70)
print(f"BUSCANDO CÁMARA CON MAC: {MAC_BUSCADA}")
print("=" * 70)

# Función para hacer ping
def ping_ip(ip):
    """Hace ping a una IP"""
    try:
        # En Windows usamos -n 1, en Linux -c 1
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '1', '-w', '100', ip]
        
        # Ejecutar sin mostrar output
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1)
    except:
        pass

# Escanear rango de IPs
print(f"\nEscaneando subred {SUBNET}.0/24...")
print("Esto puede tomar 30-60 segundos...")
print("\nProgreso: ", end="", flush=True)

for i in range(1, 255):
    ip = f"{SUBNET}.{i}"
    ping_ip(ip)
    
    # Mostrar progreso cada 25 IPs
    if i % 25 == 0:
        print(f"{i}", end="... ", flush=True)

print("\n\nEscaneo completado. Actualizando tabla ARP...")
time.sleep(2)

# Leer tabla ARP
print("\nBuscando en tabla ARP...")
result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
arp_output = result.stdout

# Buscar la MAC (case insensitive)
found = False
mac_lower = MAC_BUSCADA.lower()

for line in arp_output.split('\n'):
    if mac_lower in line.lower():
        print("\n" + "=" * 70)
        print("*** CÁMARA ENCONTRADA ***")
        print("=" * 70)
        print(line)
        
        # Extraer IP usando regex
        ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
        if ip_match:
            ip_found = ip_match.group(1)
            print(f"\nIP de la cámara: {ip_found}")
            
            # Guardar en archivo
            with open("ip_camara_encontrada.txt", "w") as f:
                f.write(ip_found)
            
            print(f"IP guardada en: ip_camara_encontrada.txt")
            
            # Actualizar directamente camara.py
            print("\n¿Quieres actualizar camara.py con esta IP? (s/n): ", end="")
            respuesta = input().strip().lower()
            
            if respuesta == 's':
                import os
                camara_path = os.path.join(os.path.dirname(__file__), "camara.py")
                
                if os.path.exists(camara_path):
                    with open(camara_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Reemplazar IP
                    content = re.sub(
                        r'HOST = "192\.168\.\d{1,3}\.\d{1,3}"',
                        f'HOST = "{ip_found}"',
                        content
                    )
                    
                    # Guardar
                    with open(camara_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    print(f"✓ camara.py actualizado con IP: {ip_found}")
                else:
                    print("! No se encontró camara.py")
        
        found = True
        break

if not found:
    print("\n" + "=" * 70)
    print("CÁMARA NO ENCONTRADA")
    print("=" * 70)
    print(f"\nLa cámara con MAC {MAC_BUSCADA} no está en la subred {SUBNET}.0/24")
    print("\nPosibles razones:")
    print("1. La cámara está en otra subred")
    print("2. La cámara está apagada o sin conexión WiFi")
    print("3. La MAC proporcionada es incorrecta")
    print("\nDispositivos encontrados en la red:")
    print("-" * 70)
    
    # Mostrar primeras 15 entradas dinámicas
    count = 0
    for line in arp_output.split('\n'):
        if 'dinámico' in line.lower() or 'dynamic' in line.lower():
            print(line)
            count += 1
            if count >= 15:
                break
    
    # Sugerencias
    print("\n" + "=" * 70)
    print("SUGERENCIAS:")
    print("=" * 70)
    print("1. Verifica que la cámara esté encendida")
    print("2. Confirma la MAC en la app Tapo")
    print("3. Verifica que tu PC esté en la misma red WiFi")
    print("4. Revisa la IP en: Tapo App > Configuración > Info del dispositivo")

print("\n" + "=" * 70)
