#!/usr/bin/env python3
"""Script de diagnóstico para verificar la conectividad con la cámara Tapo"""

import socket
import requests
from pytapo import Tapo

# Configuración desde camara.py
HOST = "192.168.222.224"
USER = "admin"
PASSWORD_CLOUD = "soldado1"

print("=" * 60)
print("DIAGNÓSTICO DE CÁMARA TAPO")
print("=" * 60)

# 1. Verificar conectividad de red (TCP)
print(f"\n1. Verificando conectividad TCP a {HOST}:443...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex((HOST, 443))
    sock.close()
    
    if result == 0:
        print(f"   ✅ Puerto 443 ABIERTO en {HOST}")
    else:
        print(f"   ❌ Puerto 443 CERRADO en {HOST}")
        print(f"   Error code: {result}")
except socket.gaierror:
    print(f"   ❌ No se pudo resolver el host {HOST}")
except socket.timeout:
    print(f"   ❌ Timeout al conectar a {HOST}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 2. Verificar conexión HTTP/HTTPS
print(f"\n2. Verificando acceso HTTP/HTTPS a la cámara...")
for protocol in ["http", "https"]:
    try:
        url = f"{protocol}://{HOST}"
        print(f"   Intentando {url}...")
        resp = requests.get(url, timeout=5, verify=False)
        print(f"   ✅ {protocol.upper()} respondió con código {resp.status_code}")
    except requests.exceptions.Timeout:
        print(f"   ❌ Timeout en {protocol.upper()}")
    except requests.exceptions.ConnectionError:
        print(f"   ❌ No se pudo conectar via {protocol.upper()}")
    except Exception as e:
        print(f"   ❌ Error en {protocol.upper()}: {type(e).__name__}")

# 3. Verificar credenciales con pytapo
print(f"\n3. Verificando credenciales con pytapo...")
print(f"   Usuario: {USER}")
print(f"   Password: {'*' * len(PASSWORD_CLOUD)}")

try:
    print("   Intentando autenticar con Tapo...")
    tapo = Tapo(HOST, USER, PASSWORD_CLOUD, PASSWORD_CLOUD, printDebugInformation=True)
    
    # Intentar obtener info básica
    print("   Obteniendo información de la cámara...")
    info = tapo.getBasicInfo()
    
    print(f"   ✅ AUTENTICACIÓN EXITOSA")
    print(f"   Modelo: {info.get('device_model', 'N/A')}")
    print(f"   Alias: {info.get('device_alias', 'N/A')}")
    print(f"   Firmware: {info.get('sw_version', 'N/A')}")
    
except Exception as e:
    print(f"   ❌ ERROR DE AUTENTICACIÓN")
    print(f"   Tipo de error: {type(e).__name__}")
    print(f"   Mensaje: {str(e)}")

# 4. Verificar ffmpeg
print(f"\n4. Verificando ffmpeg...")
import subprocess
try:
    result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        version_line = result.stdout.split('\n')[0]
        print(f"   ✅ {version_line}")
    else:
        print(f"   ❌ ffmpeg retornó código {result.returncode}")
except FileNotFoundError:
    print(f"   ❌ ffmpeg NO encontrado en PATH")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("FIN DEL DIAGNÓSTICO")
print("=" * 60)
