#!/usr/bin/env python3
"""Escaneo completo de red para encontrar la cámara Tapo"""

import subprocess
import re
import time
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

MAC_BUSCADA = "78-20-51-1E-3B-03"
SUBREDES = ["192.168.203", "192.168.1", "192.168.0", "192.168.100", "10.0.0"]
TAPO_PORTS = [443, 80, 554, 2020]  # Puertos comunes de cámaras Tapo

print("=" * 80)
print("ESCANEO COMPLETO PARA ENCONTRAR CÁMARA TAPO")
print("=" * 80)
print(f"MAC Buscada: {MAC_BUSCADA}")
print(f"Subredes a escanear: {', '.join(SUBREDES)}")
print("=" * 80)

def check_port(ip, port, timeout=0.5):
    """Verifica si un puerto está abierto"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def ping_ip(ip):
    """Hace ping rápido a una IP"""
    try:
        subprocess.run(
            ['ping', '-n', '1', '-w', '100', ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=0.5
        )
    except:
        pass

def scan_subnet_fast(subnet):
    """Escanea una subred haciendo ping rápido"""
    print(f"\n[PING] Escaneando {subnet}.0/24...", end=" ", flush=True)
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = []
        for i in range(1, 255):
            ip = f"{subnet}.{i}"
            futures.append(executor.submit(ping_ip, ip))
        
        # Esperar a que terminen
        for future in as_completed(futures):
            pass
    
    print("OK")

def scan_ports_in_subnet(subnet):
    """Busca dispositivos con puertos Tapo abiertos"""
    print(f"\n[PORTS] Buscando puertos Tapo en {subnet}.0/24...")
    devices_found = []
    
    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = {}
        
        for i in range(1, 255):
            ip = f"{subnet}.{i}"
            for port in TAPO_PORTS:
                future = executor.submit(check_port, ip, port, 0.3)
                futures[future] = (ip, port)
        
        for future in as_completed(futures):
            ip, port = futures[future]
            if future.result():
                devices_found.append((ip, port))
                print(f"  ✓ {ip}:{port} ABIERTO")
    
    return devices_found

# Paso 1: Escanear todas las subredes con ping
print("\n" + "=" * 80)
print("PASO 1: PING A TODAS LAS SUBREDES")
print("=" * 80)

for subnet in SUBREDES:
    scan_subnet_fast(subnet)
    time.sleep(0.5)

# Paso 2: Revisar tabla ARP completa
print("\n" + "=" * 80)
print("PASO 2: BUSCAR MAC EN TABLA ARP")
print("=" * 80)

time.sleep(2)
result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
arp_output = result.stdout
mac_lower = MAC_BUSCADA.lower()

camera_found = False
camera_ip = None

for line in arp_output.split('\n'):
    if mac_lower in line.lower():
        print("\n*** CÁMARA ENCONTRADA POR MAC ***")
        print(line)
        
        ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
        if ip_match:
            camera_ip = ip_match.group(1)
            print(f"\n✓ IP de la cámara: {camera_ip}")
            camera_found = True
        break

if not camera_found:
    print("\n✗ Cámara no encontrada por MAC")

# Paso 3: Buscar dispositivos con puertos Tapo abiertos
print("\n" + "=" * 80)
print("PASO 3: BUSCAR DISPOSITIVOS CON PUERTOS TAPO")
print("=" * 80)

all_tapo_devices = []
for subnet in SUBREDES:
    devices = scan_ports_in_subnet(subnet)
    all_tapo_devices.extend(devices)

if all_tapo_devices:
    print(f"\n✓ Se encontraron {len(all_tapo_devices)} dispositivos con puertos Tapo:")
    
    # Agrupar por IP
    devices_by_ip = {}
    for ip, port in all_tapo_devices:
        if ip not in devices_by_ip:
            devices_by_ip[ip] = []
        devices_by_ip[ip].append(port)
    
    print("\nDispositivos encontrados:")
    for ip, ports in devices_by_ip.items():
        ports_str = ", ".join(str(p) for p in sorted(ports))
        print(f"  • {ip} - Puertos: {ports_str}")
        
        # Si no encontramos la cámara por MAC, sugerir estos IPs
        if not camera_found:
            print(f"    → Posible cámara Tapo")

# Paso 4: Intentar conectar con pytapo
if camera_ip or all_tapo_devices:
    print("\n" + "=" * 80)
    print("PASO 4: PROBAR CONEXIÓN PYTAPO")
    print("=" * 80)
    
    # Hacer lista de IPs a probar
    ips_to_test = []
    if camera_ip:
        ips_to_test.append(camera_ip)
    
    # Agregar IPs con puerto 443 abierto
    for ip, port in all_tapo_devices:
        if port == 443 and ip not in ips_to_test:
            ips_to_test.append(ip)
    
    from pytapo import Tapo
    
    for test_ip in ips_to_test:
        print(f"\nProbando {test_ip}...")
        try:
            tapo = Tapo(test_ip, "admin", "soldado1", "soldado1", printDebugInformation=False)
            info = tapo.getBasicInfo()
            
            print(f"✓✓✓ CONEXIÓN EXITOSA ✓✓✓")
            print(f"  IP: {test_ip}")
            print(f"  Modelo: {info.get('device_model', 'N/A')}")
            print(f"  MAC: {info.get('mac', 'N/A')}")
            print(f"  Alias: {info.get('device_alias', 'N/A')}")
            
            # Guardar
            with open("ip_camara_encontrada.txt", "w") as f:
                f.write(test_ip)
            print(f"\n✓ IP guardada en: ip_camara_encontrada.txt")
            
            camera_found = True
            camera_ip = test_ip
            break
            
        except Exception as e:
            print(f"✗ Error: {type(e).__name__}")

# Resumen final
print("\n" + "=" * 80)
print("RESUMEN FINAL")
print("=" * 80)

if camera_found and camera_ip:
    print(f"✓✓✓ CÁMARA ENCONTRADA EN: {camera_ip}")
    print("\nPara actualizar la configuración:")
    print(f"  1. Edita utils/camara.py")
    print(f"  2. Cambia HOST = \"{camera_ip}\"")
    print(f"  3. Reinicia el servidor: python utils/camara.py")
else:
    print("✗✗✗ CÁMARA NO ENCONTRADA")
    print("\nRecomendaciones:")
    print("  1. Verifica que la cámara esté encendida")
    print("  2. Confirma que está conectada al WiFi")
    print("  3. Revisa la IP en la app Tapo")
    print("  4. Asegúrate de estar en la misma red WiFi")

print("=" * 80)
