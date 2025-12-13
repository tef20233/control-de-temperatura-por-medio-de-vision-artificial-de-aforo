"""
Configuración del sistema de aforo
"""

import os

# Rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, 'models')
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Configuración de cámara
CAMERA_SOURCE = 0  # 0 para webcam, o "rtsp://..." para IP camera
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30

# Configuración de detección
DEFAULT_CONFIDENCE = 0.5
DEFAULT_ENSEMBLE_STRATEGY = 'average'  # average | majority | best | union

# Configuración de aforo
DEFAULT_MAX_CAPACITY = 50

# Configuración de servidor
HOST = '0.0.0.0'
PORT = 5000
DEBUG = True

# Configuración de privacidad
ENABLE_PRIVACY = True
BLUR_KERNEL_SIZE = (15, 15)
