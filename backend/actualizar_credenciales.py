#!/usr/bin/env python3
"""
Script para actualizar credenciales de la cámara después de reset de fábrica
"""

import os
import sys

print("="*80)
print("🔧 ACTUALIZAR CREDENCIALES - Cámara Tapo C660")
print("="*80)

print("\n⚠️  IMPORTANTE: Tu cámara fue reseteada de fábrica")
print("   Necesitas configurarla primero en la app Tapo\n")

# Solicitar credenciales al usuario
print("📋 Ingresa las credenciales de tu cámara:\n")

camera_ip = input("1. IP de la cámara (ej: 192.168.1.100): ").strip()
if not camera_ip:
    camera_ip = "192.168.222.224"
    print(f"   Usando IP por defecto: {camera_ip}")

print("\n   Usuario puede ser:")
print("   - 'admin' (por defecto después de reset)")
print("   - Tu email de cuenta Tapo (ej: usuario@email.com)")
username = input("2. Usuario: ").strip()
if not username:
    username = "admin"
    print(f"   Usando usuario por defecto: {username}")

import getpass
password = getpass.getpass("3. Contraseña de cuenta Tapo: ").strip()

if not password:
    print("❌ Error: La contraseña no puede estar vacía")
    sys.exit(1)

# Confirmar
print("\n" + "="*80)
print("📝 Credenciales ingresadas:")
print("="*80)
print(f"IP: {camera_ip}")
print(f"Usuario: {username}")
print(f"Contraseña: {'*' * len(password)}")
print()

confirm = input("¿Son correctas? (s/n): ").strip().lower()
if confirm != 's':
    print("❌ Cancelado por el usuario")
    sys.exit(0)

# Probar primero si las credenciales funcionan
print("\n🔍 Probando conexión con la cámara...")

try:
    from pytapo import Tapo
    
    tapo = Tapo(camera_ip, username, password, password, printDebugInformation=False)
    info = tapo.getBasicInfo()
    
    print(f"✅ ¡Conexión exitosa!")
    print(f"   Modelo: {info.get('device_model', 'N/A')}")
    print(f"   MAC: {info.get('mac', 'N/A')}")
    print(f"   SW Version: {info.get('sw_version', 'N/A')}")
    
except Exception as e:
    print(f"❌ Error conectando a la cámara: {e}")
    print("\n📋 Verifica:")
    print("   1. La cámara está encendida y conectada al WiFi")
    print("   2. La IP es correcta (revisa en la app Tapo)")
    print("   3. Tu PC está en la misma red WiFi")
    print("   4. Las credenciales son correctas")
    print("\n⚠️  No se actualizarán los archivos hasta que la conexión funcione")
    sys.exit(1)

# Si llegamos aquí, las credenciales funcionan. Actualizar archivos
print("\n📝 Actualizando archivos de configuración...")

files_to_update = [
    ("utils/camara.py", [
        (f'HOST = "192.168.222.224"', f'HOST = "{camera_ip}"'),
        (f'USER = "admin1"', f'USER = "{username}"'),
        (f'PASSWORD_CLOUD = "987654321Usco.,"', f'PASSWORD_CLOUD = "{password}"')
    ]),
    ("cam8.py", [
        (f'CAMERA_IP   = "192.168.222.224"', f'CAMERA_IP   = "{camera_ip}"'),
        (f'USERNAME    = "admin1"', f'USERNAME    = "{username}"'),
        (f'PASSWORD    = "987654321Usco.,"', f'PASSWORD    = "{password}"')
    ]),
    ("test_camara_simple.py", [
        (f'CAMERA_IP = "192.168.222.224"', f'CAMERA_IP = "{camera_ip}"'),
        (f'USERNAME = "admin1"', f'USERNAME = "{username}"'),
        (f'PASSWORD = "987654321Usco.,"', f'PASSWORD = "{password}"')
    ])
]

updated_count = 0

for filepath, replacements in files_to_update:
    if not os.path.exists(filepath):
        print(f"⚠️  {filepath} no encontrado, saltando...")
        continue
    
    try:
        # Leer archivo
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Hacer reemplazos
        modified = False
        for old, new in replacements:
            if old in content:
                content = content.replace(old, new)
                modified = True
        
        if modified:
            # Guardar backup
            backup_path = filepath + '.backup'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Guardar archivo actualizado
            # (El contenido ya tiene los cambios)
            print(f"✅ {filepath} actualizado (backup guardado)")
            updated_count += 1
        else:
            print(f"⚠️  {filepath} no tenía los valores antiguos, no modificado")
            
    except Exception as e:
        print(f"❌ Error actualizando {filepath}: {e}")

# Actualizar app.py
app_py_path = "app.py"
if os.path.exists(app_py_path):
    try:
        with open(app_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Actualizar la IP en camera_alternative_ips
        old_ip = "http://192.168.222.224:5001"
        new_ip = f"http://{camera_ip}:5001"
        
        if old_ip in content:
            content = content.replace(old_ip, new_ip)
            with open(app_py_path + '.backup', 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ {app_py_path} actualizado (IP en camera_alternative_ips)")
            updated_count += 1
        
    except Exception as e:
        print(f"❌ Error actualizando {app_py_path}: {e}")

print(f"\n{'='*80}")
print(f"✅ Proceso completado: {updated_count} archivos actualizados")
print("="*80)

# Guardar credenciales en archivo de referencia
with open("credenciales_actuales.txt", "w") as f:
    f.write(f"IP: {camera_ip}\n")
    f.write(f"Usuario: {username}\n")
    f.write(f"Contraseña: {password}\n")
    f.write(f"\nActualizado: {__import__('datetime').datetime.now()}\n")

print("\n💾 Credenciales guardadas en: credenciales_actuales.txt")
print("   (Guarda este archivo en un lugar seguro)")

print("\n📋 PRÓXIMOS PASOS:")
print("\n1. Reinicia el servidor de cámara:")
print("   - Si está corriendo, presiona Ctrl+C para detenerlo")
print("   - Luego ejecuta: python utils/camara.py")
print("\n2. El backend detectará automáticamente la nueva configuración")
print("\n3. Prueba el sistema completo:")
print("   python test_completo.py")
print("\n4. Si todo funciona, inicia el sistema:")
print("   iniciar_sistema_completo.bat")

print("\n✨ ¡Listo! Tu cámara está configurada")
