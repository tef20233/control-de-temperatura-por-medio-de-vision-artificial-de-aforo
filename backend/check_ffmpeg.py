#!/usr/bin/env python3
"""
Script para verificar si FFmpeg está instalado y accesible.
"""

import subprocess
import sys
import platform

def check_ffmpeg():
    """Verificar si ffmpeg está instalado"""
    print("=" * 80)
    print("🔍 VERIFICANDO INSTALACIÓN DE FFMPEG")
    print("=" * 80)
    print()
    
    try:
        # Intentar ejecutar ffmpeg -version
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("✅ FFmpeg está INSTALADO correctamente\n")
            
            # Extraer versión
            version_line = result.stdout.split('\n')[0]
            print(f"📦 {version_line}\n")
            
            # Verificar ubicación
            try:
                if platform.system() == 'Windows':
                    where_result = subprocess.run(
                        ['where', 'ffmpeg'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                else:
                    where_result = subprocess.run(
                        ['which', 'ffmpeg'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                
                if where_result.returncode == 0:
                    print(f"📍 Ubicación: {where_result.stdout.strip()}\n")
            except:
                pass
            
            print("=" * 80)
            print("✅ TODO LISTO - Puedes iniciar el servidor de la cámara")
            print("=" * 80)
            print("\nPara iniciar el servidor de la cámara:")
            print("  cd backend/utils")
            print("  python camara.py")
            print()
            
            return True
        else:
            print("❌ FFmpeg encontrado pero retornó un error")
            print(f"   Error: {result.stderr[:200]}")
            return False
            
    except FileNotFoundError:
        print("❌ FFmpeg NO está instalado o no está en el PATH\n")
        print_installation_instructions()
        return False
        
    except subprocess.TimeoutExpired:
        print("⚠️  Timeout al verificar FFmpeg")
        return False
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False


def print_installation_instructions():
    """Mostrar instrucciones de instalación según el sistema operativo"""
    os_name = platform.system()
    
    print("=" * 80)
    print("📝 INSTRUCCIONES DE INSTALACIÓN")
    print("=" * 80)
    print()
    
    if os_name == 'Windows':
        print("🪟 WINDOWS - Opción 1 (Recomendado): Chocolatey")
        print("   1. Abre PowerShell como Administrador")
        print("   2. Si no tienes Chocolatey, instálalo primero:")
        print("      Set-ExecutionPolicy Bypass -Scope Process -Force;")
        print("      [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072;")
        print("      iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))")
        print("   3. Instala FFmpeg:")
        print("      choco install ffmpeg -y")
        print()
        print("🪟 WINDOWS - Opción 2: Manual")
        print("   1. Descarga FFmpeg:")
        print("      https://github.com/BtbN/FFmpeg-Builds/releases")
        print("      (Archivo: ffmpeg-master-latest-win64-gpl.zip)")
        print("   2. Extrae a: C:\\ffmpeg")
        print("   3. Agrega al PATH: C:\\ffmpeg\\bin")
        print("   4. Reinicia la terminal")
        print()
        
    elif os_name == 'Darwin':  # macOS
        print("🍎 macOS - Con Homebrew:")
        print("   brew install ffmpeg")
        print()
        
    elif os_name == 'Linux':
        print("🐧 LINUX - Ubuntu/Debian:")
        print("   sudo apt update")
        print("   sudo apt install ffmpeg")
        print()
        print("🐧 LINUX - Fedora/RHEL:")
        print("   sudo dnf install ffmpeg")
        print()
        print("🐧 LINUX - Arch:")
        print("   sudo pacman -S ffmpeg")
        print()
    
    print("🐍 Con Conda/Miniconda:")
    print("   conda install -c conda-forge ffmpeg")
    print()
    
    print("=" * 80)
    print("📖 Documentación completa: INSTALAR_FFMPEG.md")
    print("=" * 80)
    print()
    print("⚠️  Después de instalar:")
    print("   - Cierra y reabre la terminal")
    print("   - Ejecuta nuevamente: python check_ffmpeg.py")
    print()


def check_python_dependencies():
    """Verificar dependencias de Python necesarias"""
    print("=" * 80)
    print("🐍 VERIFICANDO DEPENDENCIAS DE PYTHON")
    print("=" * 80)
    print()
    
    required_packages = {
        'flask': 'Flask',
        'pytapo': 'pytapo',
        'PIL': 'Pillow',
        'numpy': 'numpy',
        'cv2': 'opencv-python'
    }
    
    missing = []
    
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name} - NO INSTALADO")
            missing.append(package_name)
    
    print()
    
    if missing:
        print("⚠️  FALTAN PAQUETES. Instala con:")
        print(f"   pip install {' '.join(missing)}")
        print()
        return False
    else:
        print("✅ Todas las dependencias de Python están instaladas")
        print()
        return True


def main():
    """Función principal"""
    print()
    
    # Verificar FFmpeg
    ffmpeg_ok = check_ffmpeg()
    
    print()
    
    # Verificar dependencias Python
    python_ok = check_python_dependencies()
    
    # Resumen final
    print("=" * 80)
    print("📊 RESUMEN")
    print("=" * 80)
    print(f"FFmpeg:       {'✅ OK' if ffmpeg_ok else '❌ FALTA'}")
    print(f"Python deps:  {'✅ OK' if python_ok else '❌ FALTAN'}")
    print("=" * 80)
    print()
    
    if ffmpeg_ok and python_ok:
        print("🎉 ¡TODO LISTO! Puedes iniciar el servidor de la cámara.")
        print()
        print("Comandos:")
        print("  cd backend/utils")
        print("  python camara.py")
        print()
        return 0
    else:
        print("⚠️  Completa la instalación de los componentes faltantes.")
        print()
        return 1


if __name__ == '__main__':
    sys.exit(main())
