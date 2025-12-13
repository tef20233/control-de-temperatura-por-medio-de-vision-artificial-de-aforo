#!/usr/bin/env python3
"""
Script para encontrar la cámara Tapo probando en múltiples redes
"""
import socket
import requests
from pytapo import Tapo

# Credenciales de la cámara
USER = "admin"
PASSWORD = "987654321Usco.,"

def get_local_ip():
    """Obtener la IP local de la PC"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def check_tapo_camera(ip):
    """Probar si hay una cámara Tapo en una IP"""
    try:
        print(f"  Probando {ip}...", end=" ", flush=True)
        
        # Intentar conectar al puerto 443 (HTTPS que usa Tapo)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((ip, 443))
        sock.close()
        
        if result == 0:
            # Puerto abierto, intentar autenticar con pytapo
            try:
                tapo = Tapo(ip, USER, PASSWORD)
                info = tapo.getBasicInfo()
                print(f"✅ ¡CÁMARA ENCONTRADA!")
                return True, info
            except Exception as e:
                print(f"⚠️ Puerto 443 abierto pero no es Tapo o credenciales incorrectas")
                return False, None
        else:
            print("❌")
            return False, None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, None

if __name__ == "__main__":
    local_ip = get_local_ip()
    current_network = '.'.join(local_ip.split('.')[:-1])
    
    print("="*70)
    print("🔍 BUSCANDO CÁMARA TAPO")
    print("="*70)
    print(f"📍 Tu PC está en: {local_ip}")
    print(f"🌐 Red actual: {current_network}.x")
    print("="*70)
    print()
    
    # Lista de IPs comunes para cámaras Tapo
    common_ips = [100, 101, 102, 103, 104, 105, 110, 150, 200, 201, 250]
    
    # Redes que hemos visto en el proyecto
    networks_to_check = [
        current_network,      # Red actual de la PC
        "192.168.196",        # Red donde estaba la cámara antes
        "192.168.203",        # Red donde estaba el backend
        "192.168.217",        # Otra red vista en los logs
        "192.168.1",          # Red común de routers
    ]
    
    # Eliminar duplicados
    networks_to_check = list(dict.fromkeys(networks_to_check))
    
    print(f"🔎 Buscando en {len(networks_to_check)} redes...")
    print()
    
    found = False
    for network in networks_to_check:
        print(f"📡 Red {network}.x:")
        for ip_end in common_ips:
            ip = f"{network}.{ip_end}"
            success, info = check_tapo_camera(ip)
            if success:
                print()
                print("="*70)
                print("✅ ¡CÁMARA TAPO ENCONTRADA!")
                print("="*70)
                print(f"📍 IP: {ip}")
                print(f"🏷️  Modelo: {info.get('device_model', 'N/A')}")
                print(f"📛 Nombre: {info.get('device_alias', 'N/A')}")
                print(f"🔧 Firmware: {info.get('sw_version', 'N/A')}")
                print()
                print("📝 Actualiza utils/camara.py con:")
                print(f"   HOST = \"{ip}\"")
                print("="*70)
                found = True
                break
        
        if found:
            break
        print()
    
    if not found:
        print("="*70)
        print("❌ No se encontró la cámara Tapo")
        print("="*70)
        print()
        print("💡 Soluciones:")
        print("   1. Verifica que la cámara esté encendida")
        print("   2. Asegúrate de que PC y cámara estén en la misma WiFi")
        print("   3. Busca la IP manualmente:")
        print("      - App Tapo → Configuración → Info del dispositivo")
        print("      - Router → Dispositivos conectados")
        print("   4. Verifica las credenciales:")
        print(f"      Usuario: {USER}")
        print(f"      Password: {PASSWORD}")
        print("="*70)
