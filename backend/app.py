import eventlet
eventlet.monkey_patch()

# SUPRIMIR ERRORES DE CONEXIÓN A NIVEL DE EVENTLET
import sys
import os

# Redirigir stderr de eventlet a null para suprimir ConnectionAbortedError
class SuppressConnectionErrors:
    """Filtro para suprimir errores de conexión abortada"""
    def __init__(self, stream):
        self.stream = stream
        self.suppress = False
    
    def write(self, data):
        # Suprimir si contiene errores de conexión
        if 'ConnectionAbortedError' in data or 'WinError 10053' in data:
            return
        if 'Traceback' in data:
            self.suppress = True
            return
        if self.suppress and ('File ' in data or 'line ' in data or '~' in data or '^' in data):
            return
        # Resetear suppress cuando vemos un log normal
        if data.strip() and not data.strip().startswith(' '):
            self.suppress = False
        self.stream.write(data)
    
    def flush(self):
        self.stream.flush()

sys.stderr = SuppressConnectionErrors(sys.__stderr__)

from flask import Flask, request, jsonify, Response
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from flasgger import Swagger, swag_from
import cv2
import numpy as np
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'aforo_realtime'))
from src.detector import RealtimeDetector
from core.camera import CameraManager
from core.tracker import LineCrossingTracker
from utils.metrics import MetricsCollector
import json
import time
import base64
import logging
import warnings

# Suprimir TODOS los errores de streaming (normales cuando VLC/navegador cierra)
logging.getLogger('eventlet.wsgi.server').setLevel(logging.CRITICAL)
logging.getLogger('eventlet.wsgi').setLevel(logging.CRITICAL)
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', message='.*ConnectionAbortedError.*')

# Configurar logging solo para errores críticos de la app
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
warnings.filterwarnings('ignore', category=DeprecationWarning)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'aforo-secret-key-2025'
CORS(app)

# Configuración de Swagger
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/docs"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Sistema de Control de Aforo - API",
        "description": "API REST para sistema de detección de personas y control de aforo con YOLOv8",
        "version": "1.0.0",
        "contact": {
            "name": "Sistema de Aforo",
            "url": "https://github.com/FlacoAfk/app_aforo"
        }
    },
    "host": "localhost:5000",
    "basePath": "/",
    "schemes": ["http"],
    "tags": [
        {"name": "Sistema", "description": "Endpoints de información general"},
        {"name": "Cámara", "description": "Control de cámara y streaming"},
        {"name": "Configuración", "description": "Gestión de configuración"},
        {"name": "Modelos", "description": "Información de modelos YOLO"},
        {"name": "Métricas", "description": "Historial y estadísticas"}
    ]
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Inicializar componentes - Usar RealtimeDetector (mismo que run_camera.ps1)
detector = RealtimeDetector(
    model_path='models/yolo11s.pt',
    config_preset='fast',
    device='auto',
    half=True, # El detector desactivará esto automáticamente si es 1050 Ti
    anonymize=False,
    fisheye=False,
    imgsz_override=512,
    conf_override=0.35,
    iou_override=0.50,
    max_det_override=100
)
people_tracker = LineCrossingTracker(max_lost=20, iou_threshold=0.2)

# Configuración global ADAPTADA para GTX 1050 Ti (con modelo yolo11s)
config = {
    'max_capacity': 50,
    'ensemble_strategy': 'best',  # Usará yolo11s
    'confidence_threshold': 0.35,
    'enable_privacy': False,
    'enable_fisheye': False,
    'fisheye_strength': 0.0,
    'skip_frames': 0,
    'performance_mode': 'fast',
    'imgsz': 512, # 512px para yolo11s
    'iou_threshold': 0.50,
    'max_detections': 100,
    # Configuración de cámara
    'camera_source': 0,  # 0=webcam del PC
    'camera_type': 'webcam',  # auto, webcam, rtsp, tapo
    # IPs alternativas
    'camera_alternative_ips': [
        'http://localhost:5001',
        'http://192.168.1.4:4747/video' # DroidCam por defecto
    ],
    # Clasificación de ocupación (Editable)
    'occupancy_thresholds': {
        'low': {'max_people': 5, 'max_occupancy_pct': 0.20},
        'medium': {'max_people': 15, 'max_occupancy_pct': 0.60},
        # High es todo lo que supere medium
    }
}

PERFORMANCE_MODES = {
    'ultra_fast': {
        'imgsz': 384,
        'confidence_threshold': 0.5,
        'iou_threshold': 0.6,
        'max_detections': 50,
        'skip_frames': 2,
    },
    'fast': {
        'imgsz': 416,
        'confidence_threshold': 0.45,
        'iou_threshold': 0.6,
        'max_detections': 50,
        'skip_frames': 1,
    },
    'balanced': {
        'imgsz': 512,
        'confidence_threshold': 0.4,
        'iou_threshold': 0.5,
        'max_detections': 100,
        'skip_frames': 0,
    },
    'quality': {
        'imgsz': 640,
        'confidence_threshold': 0.35,
        'iou_threshold': 0.45,
        'max_detections': 300,
        'skip_frames': 0,
    },
}


def apply_performance_mode(mode):
    profile = PERFORMANCE_MODES.get(mode)
    if not profile:
        return
    config['performance_mode'] = mode
    if 'imgsz' in profile:
        config['imgsz'] = profile['imgsz']
    if 'confidence_threshold' in profile:
        config['confidence_threshold'] = profile['confidence_threshold']
    if 'iou_threshold' in profile:
        config['iou_threshold'] = profile['iou_threshold']
    if 'max_detections' in profile:
        config['max_detections'] = profile['max_detections']
    if 'skip_frames' in profile:
        config['skip_frames'] = profile['skip_frames']


apply_performance_mode(config.get('performance_mode', 'balanced'))

# Inicializar cámara con la configuración
camera = CameraManager(
    source=config['camera_source'],
    camera_type=config['camera_type']
)
metrics = MetricsCollector()

# Estado del sistema
system_state = {
    'running': False,
    'current_count': 0,
    'occupancy_rate': 0.0,
    'fps': 0.0,
    'camera_fps': 30.0,  # FPS reales de la cámara (auto-detectado)
    'models_loaded': ['yolo11s'],  # Solo yolo11s con RealtimeDetector
    'connected_clients': 0,
    'last_frame': None,  # Para HTTP polling
    'frame_buffer': [],  # Buffer de frames para estabilizar FPS
    'target_fps': 30,  # FPS objetivo (se ajusta según cámara)
    'fps_history': [],  # Historial de FPS para promediar
    'last_ws_emit_time': 0,  # Timestamp de último envío WebSocket
    'ws_emit_interval': 1.0 / 30.0,  # Intervalo mínimo entre envíos (auto-ajustado)
    'last_detections': [],
    'last_models_used': [],
    'last_inference_time': 0.0,
    'entries': 0,
    'exits': 0,
    'count_history': [],
    'last_jpeg': None,
}


_fisheye_maps = None


def _get_fisheye_maps(frame_shape, strength):
    """Precalcular y cachear los mapas de distorsión tipo ojo de pez.

    Usa una distorsión radial simple (barrel distortion) centrada en la imagen.
    """
    global _fisheye_maps
    height, width = frame_shape[:2]

    if _fisheye_maps is not None:
        map_x, map_y, cached_w, cached_h, cached_k = _fisheye_maps
        if cached_w == width and cached_h == height and abs(cached_k - strength) < 1e-12:
            return map_x, map_y

    cx, cy = width / 2.0, height / 2.0
    max_radius = (cx ** 2 + cy ** 2) ** 0.5

    # Coordenadas normalizadas
    y_indices, x_indices = np.indices((height, width), dtype=np.float32)
    x = (x_indices - cx) / max_radius
    y = (y_indices - cy) / max_radius
    r2 = x * x + y * y

    # Factor de distorsión radial (barrel)
    k = strength
    factor = 1.0 + k * r2

    src_x = cx + x * factor * max_radius
    src_y = cy + y * factor * max_radius

    map_x = src_x.astype(np.float32)
    map_y = src_y.astype(np.float32)

    _fisheye_maps = (map_x, map_y, width, height, strength)
    return map_x, map_y


def apply_fisheye(frame):
    """Aplicar efecto ojo de pez si está habilitado en la configuración."""
    if not config.get('enable_fisheye', False):
        return frame

    strength = float(config.get('fisheye_strength', 0.0))
    if abs(strength) < 1e-8:
        return frame

    map_x, map_y = _get_fisheye_maps(frame.shape, strength)
    distorted = cv2.remap(
        frame,
        map_x,
        map_y,
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT
    )
    return distorted


# ==================== REST API ENDPOINTS ====================

@app.route('/', methods=['GET'])
def index():
    """
    Información de la API
    ---
    tags:
      - Sistema
    responses:
      200:
        description: Información general del sistema y endpoints disponibles
        schema:
          type: object
          properties:
            message:
              type: string
            version:
              type: string
            status:
              type: string
            endpoints:
              type: object
            websocket:
              type: object
            streaming:
              type: object
            documentation:
              type: string
    """
    return jsonify({
        'message': '🎯 Sistema de Control de Aforo - API REST',
        'version': '1.0.0',
        'status': 'online',
        'endpoints': {
            'status': '/api/status',
            'config': '/api/config',
            'models': '/api/models',
            'camera_start': '/api/camera/start',
            'camera_stop': '/api/camera/stop',
            'camera_test': '/api/camera/test [POST]',
            'camera_scan': '/api/camera/scan [POST]',
            'camera_change': '/api/camera/change [POST]',
            'camera_stats': '/api/camera/stats',
            'history': '/api/history',
            'viewer': '/viewer'
        },
        'websocket': {
            'url': f'ws://{request.host}',
            'event': 'frame_update'
        },
        'streaming': {
            'browser_url': f'http://{request.host}/viewer',
            'instructions': 'Abrir /viewer en un navegador compatible con WebSocket'
        },
        'documentation': 'Swagger UI disponible en /api/docs'
    })


@app.route('/api/camera/change', methods=['POST'])
def change_camera():
    """
    Cambiar fuente de cámara dinámicamente
    ---
    tags:
      - Cámara
    parameters:
      - in: body
        name: config
        required: true
        schema:
          type: object
          properties:
            source:
              type: string
              description: URL o índice de cámara (ej. 'http://192.168.1.4:4747/video' o '0')
            type:
              type: string
              enum: [webcam, rtsp, tapo]
              default: webcam
    responses:
      200:
        description: Cámara cambiada correctamente
      400:
        description: Error en parámetros
      500:
        description: Error al conectar nueva cámara
    """
    global camera
    
    data = request.json
    if not data or 'source' not in data:
        return jsonify({'error': 'Missing source parameter'}), 400
    
    new_source = data['source']
    # Convertir a int si es dígito (webcam index)
    if str(new_source).isdigit():
        new_source = int(new_source)
        
    new_type = data.get('type', 'webcam')
    
    print(f"🔄 Cambiando cámara a: {new_source} ({new_type})")
    
    # Detener cámara actual
    was_running = system_state['running']
    if camera.is_connected():
        camera.disconnect()
        system_state['running'] = False
        time.sleep(0.5)
    
    # Actualizar configuración
    config['camera_source'] = new_source
    config['camera_type'] = new_type
    
    # Reinicializar cámara con nueva fuente
    camera = CameraManager(source=new_source, camera_type=new_type)
    
    # Intentar conectar
    if camera.connect():
        print("✅ Nueva cámara conectada")
        if was_running:
            # Reiniciar procesamiento si estaba corriendo
            start_camera()
        return jsonify({'message': 'Camera changed successfully', 'source': new_source})
    else:
        print("❌ Falló conexión a nueva cámara")
        return jsonify({'error': 'Failed to connect to new camera source'}), 500


@app.route('/viewer', methods=['GET'])
def viewer_page():
    """Página simple de visualización en tiempo real usando WebSocket (frame_update)."""
    html = f"""<!DOCTYPE html>
<html lang=\"es\">
<head>
    <meta charset=\"UTF-8\" />
    <title>Sistema de Aforo - Viewer</title>
    <style>
        body {{ margin: 0; font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #e5e7eb; }}
        .header {{ padding: 12px 16px; background: #1d4ed8; display: flex; justify-content: space-between; align-items: center; }}
        .title {{ font-size: 18px; font-weight: 600; }}
        .badge {{ padding: 4px 10px; border-radius: 999px; font-size: 12px; margin-left: 8px; }}
        .badge-ok {{ background: #16a34a; }}
        .badge-bad {{ background: #dc2626; }}
        .content {{ padding: 12px; display: flex; flex-direction: column; gap: 12px; }}
        .video-wrapper {{ position: relative; max-width: 960px; margin: 0 auto; background: #000; border-radius: 8px; overflow: hidden; border: 1px solid #1f2937; }}
        #video {{ width: 100%; display: block; background: #000; }}
        .overlay {{ position: absolute; top: 8px; left: 8px; right: 8px; display: flex; justify-content: space-between; pointer-events: none; }}
        .chip {{ background: rgba(15,23,42,0.9); padding: 4px 8px; border-radius: 999px; font-size: 12px; display: inline-flex; align-items: center; gap: 6px; }}
        .chip span.value {{ font-weight: 600; }}
        .footer {{ font-size: 12px; opacity: 0.7; text-align: center; margin-top: 4px; }}
    </style>
    <script src=\"https://cdn.socket.io/4.7.4/socket.io.min.js\" crossorigin=\"anonymous\"></script>
</head>
<body>
    <div class=\"header\">
        <div class=\"title\">🎥 Sistema de Control de Aforo - Viewer</div>
        <div>
            <span id=\"api-badge\" class=\"badge badge-ok\">API</span>
            <span id=\"ws-badge\" class=\"badge badge-bad\">WS</span>
        </div>
    </div>
    <div class=\"content\">
        <div class=\"video-wrapper\">
            <img id=\"video\" alt=\"Video stream\" />
            <div class=\"overlay\">
                <div class=\"chip\">
                    👤 Personas: <span id=\"count\" class=\"value\">0</span>
                    / <span id=\"max-capacity\" class=\"value\">0</span>
                </div>
                <div class=\"chip\">
                    ⚡ FPS: <span id=\"fps\" class=\"value\">0.0</span>
                    · ⏱️ inf: <span id=\"inf-time\" class=\"value\">0.000</span>s
                </div>
            </div>
        </div>
        <div class=\"footer\">
            Conectando a WebSocket en <code>ws://{request.host}</code> · Evento <code>frame_update</code>
        </div>
    </div>
    <script>
        (function() {{
            const img = document.getElementById('video');
            const countEl = document.getElementById('count');
            const maxCapacityEl = document.getElementById('max-capacity');
            const fpsEl = document.getElementById('fps');
            const infTimeEl = document.getElementById('inf-time');
            const wsBadge = document.getElementById('ws-badge');

            const socket = io(window.location.origin, {{
                transports: ['websocket', 'polling'],
                reconnection: true,
                reconnectionAttempts: 5,
            }});

            socket.on('connect', function() {{
                wsBadge.textContent = 'WS OK';
                wsBadge.classList.remove('badge-bad');
                wsBadge.classList.add('badge-ok');
            }});

            socket.on('disconnect', function() {{
                wsBadge.textContent = 'WS OFF';
                wsBadge.classList.remove('badge-ok');
                wsBadge.classList.add('badge-bad');
            }});

            socket.on('frame_update', function(data) {{
                if (!data || !data.frame) return;

                img.src = 'data:image/jpeg;base64,' + data.frame;
                countEl.textContent = (data.count || 0);
                maxCapacityEl.textContent = (data.max_capacity || 0);
                fpsEl.textContent = (data.fps || 0).toFixed ? data.fps.toFixed(1) : data.fps;
                infTimeEl.textContent = (data.inference_time || 0).toFixed ? data.inference_time.toFixed(3) : data.inference_time;
            }});
        }})();
    </script>
</body>
</html>"""

    return Response(html, mimetype='text/html')


@app.route('/api/status', methods=['GET'])
def get_status():
    """
    Estado actual del sistema
    ---
    tags:
      - Sistema
    responses:
      200:
        description: Estado actual del sistema de aforo
        schema:
          type: object
          properties:
            running:
              type: boolean
              description: Si el sistema está procesando video
            camera_active:
              type: boolean
              description: Si la cámara está conectada
            current_count:
              type: integer
              description: Número actual de personas detectadas
            occupancy_rate:
              type: number
              description: Porcentaje de ocupación (0.0-1.0)
            fps:
              type: number
              description: Frames por segundo actuales
            max_capacity:
              type: integer
              description: Capacidad máxima configurada
            models_loaded:
              type: array
              items:
                type: string
              description: Modelos YOLO cargados
            connected_clients:
              type: integer
              description: Número de clientes WebSocket conectados
    """
    return jsonify({
        'running': system_state['running'],
        'camera_active': camera.is_connected(),
        'current_count': system_state['current_count'],
        'occupancy_rate': system_state['occupancy_rate'],
        'fps': system_state['fps'],
        'max_capacity': config['max_capacity'],
        'models_loaded': system_state['models_loaded'],
        'connected_clients': system_state['connected_clients'],
        'entries': system_state.get('entries', 0),
        'exits': system_state.get('exits', 0),
        'occupancy_level': system_state.get('occupancy_level', 'Desconocido')
    })


@app.route('/api/frame', methods=['GET'])
def get_current_frame():
    """Obtener el frame actual procesado (HTTP polling alternativo a WebSocket)"""
    if not system_state['running'] or system_state.get('last_frame') is None:
        return jsonify({'error': 'No frame available', 'running': system_state['running']}), 404
    
    return jsonify(system_state['last_frame'])


@app.route('/video.mjpg')
def mjpeg_stream():
    def generate():
        boundary = b'--frame'
        while True:
            if not system_state.get('running'):
                eventlet.sleep(0.05)
                continue
            jpeg_bytes = system_state.get('last_jpeg', None)
            if jpeg_bytes is None:
                eventlet.sleep(0.01)
                continue
            yield (
                boundary + b"\r\n"
                + b"Content-Type: image/jpeg\r\n"
                + b"Content-Length: " + str(len(jpeg_bytes)).encode('ascii') + b"\r\n\r\n"
                + jpeg_bytes + b"\r\n"
            )
            eventlet.sleep(system_state.get('ws_emit_interval', 1.0 / 20.0))

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/config', methods=['GET', 'POST'])
def manage_config():
    """
    Gestión de configuración
    ---
    tags:
      - Configuración
    parameters:
      - in: body
        name: config
        description: Configuración a actualizar (solo para POST)
        schema:
          type: object
          properties:
            max_capacity:
              type: integer
              example: 50
            ensemble_strategy:
              type: string
              enum: [average, majority, best, union]
              example: best
            confidence_threshold:
              type: number
              example: 0.3
            enable_privacy:
              type: boolean
              example: false
            enable_fisheye:
              type: boolean
              example: true
            fisheye_strength:
              type: number
              example: 0.00001
    responses:
      200:
        description: Configuración actual o actualizada
        schema:
          type: object
          properties:
            max_capacity:
              type: integer
            ensemble_strategy:
              type: string
            confidence_threshold:
              type: number
            enable_privacy:
              type: boolean
            enable_fisheye:
              type: boolean
            fisheye_strength:
              type: number
            camera_source:
              type: string
            camera_type:
              type: string
    """
    if request.method == 'GET':
        return jsonify(config)
    
    elif request.method == 'POST':
        data = request.json
        
        if 'max_capacity' in data:
            config['max_capacity'] = int(data['max_capacity'])
        
        if 'ensemble_strategy' in data:
            if data['ensemble_strategy'] in ['average', 'majority', 'best', 'union']:
                config['ensemble_strategy'] = data['ensemble_strategy']
        
        if 'confidence_threshold' in data:
            config['confidence_threshold'] = float(data['confidence_threshold'])
        
        if 'enable_privacy' in data:
            config['enable_privacy'] = bool(data['enable_privacy'])

        if 'enable_fisheye' in data:
            config['enable_fisheye'] = bool(data['enable_fisheye'])

        if 'fisheye_strength' in data:
            config['fisheye_strength'] = float(data['fisheye_strength'])

        if 'occupancy_thresholds' in data:
            # Validar estructura básica
            new_thresholds = data['occupancy_thresholds']
            if isinstance(new_thresholds, dict) and 'low' in new_thresholds and 'medium' in new_thresholds:
                config['occupancy_thresholds'] = new_thresholds

        if 'performance_mode' in data:
            apply_performance_mode(str(data['performance_mode']))

        if 'skip_frames' in data:
            try:
                config['skip_frames'] = int(data['skip_frames'])
            except (TypeError, ValueError):
                pass

        if 'imgsz' in data:
            try:
                config['imgsz'] = int(data['imgsz'])
            except (TypeError, ValueError):
                pass

        if 'iou_threshold' in data:
            try:
                config['iou_threshold'] = float(data['iou_threshold'])
            except (TypeError, ValueError):
                pass

        if 'max_detections' in data:
            try:
                config['max_detections'] = int(data['max_detections'])
            except (TypeError, ValueError):
                pass
        
        # Configuración de cámara
        camera_changed = False
        if 'camera_source' in data:
            config['camera_source'] = str(data['camera_source'])
            # Si es un número (índice de webcam), convertir a int
            if config['camera_source'].isdigit():
                config['camera_source'] = int(config['camera_source'])
            camera_changed = True
        
        if 'camera_type' in data:
            config['camera_type'] = str(data['camera_type'])
            camera_changed = True
        
        # Reinicializar cámara si cambió la configuración
        if camera_changed:
            global camera
            print(f"🔄 Reinicializando cámara: {config['camera_source']} ({config['camera_type']})")
            # Desconectar cámara actual si está activa
            if camera.is_connected():
                camera.disconnect()
                system_state['running'] = False
            # Crear nueva instancia
            camera = CameraManager(
                source=config['camera_source'],
                camera_type=config['camera_type']
            )
        
        # Guardar config a archivo
        try:
            with open('data/config.json', 'w') as f:
                json.dump(config, f, indent=2)
        except:
            pass
        
        return jsonify({'message': 'Configuration updated', 'config': config})


@app.route('/api/models', methods=['GET'])
def get_models_info():
    """
    Información de modelos YOLO
    ---
    tags:
      - Modelos
    responses:
      200:
        description: Información detallada de los modelos cargados
        schema:
          type: object
          properties:
            models:
              type: array
              items:
                type: object
                properties:
                  name:
                    type: string
                  version:
                    type: string
                  parameters:
                    type: string
    """
    return jsonify(detector.get_models_info())




@app.route('/api/camera/start', methods=['POST'])
def start_camera():
    """
    Iniciar procesamiento de cámara
    ---
    tags:
      - Cámara
    responses:
      200:
        description: Cámara iniciada correctamente
        schema:
          type: object
          properties:
            message:
              type: string
              example: Camera started
      500:
        description: Error al conectar con la cámara
        schema:
          type: object
          properties:
            error:
              type: string
    """
    global system_state
    
    if not camera.is_connected():
        if not camera.connect():
            return jsonify({'error': 'Failed to connect to camera'}), 500
    
    # DETECTAR FPS REALES de la cámara y ajustar sistema
    camera_fps = camera.get_fps()
    system_state['camera_fps'] = camera_fps
    system_state['target_fps'] = min(camera_fps, 20.0)  # Limitar a 20 FPS máx para estabilidad
    system_state['ws_emit_interval'] = 1.0 / system_state['target_fps']
    
    print(f"📹 Cámara FPS: {camera_fps:.1f} → Procesamiento: {system_state['target_fps']:.1f} FPS")
    
    system_state['running'] = True
    
    # Enviar mensaje inmediato para mantener WebSocket vivo
    socketio.emit('camera_starting', {
        'message': 'Iniciando procesamiento...',
        'timestamp': time.time()
    }, namespace='/')
    
    # Iniciar loop de procesamiento en background
    socketio.start_background_task(target=process_video_stream)
    
    return jsonify({
        'message': 'Camera started',
        'camera_fps': camera_fps,
        'target_fps': system_state['target_fps']
    })


@app.route('/api/camera/stop', methods=['POST'])
def stop_camera():
    """
    Detener procesamiento de cámara
    ---
    tags:
      - Cámara
    responses:
      200:
        description: Cámara detenida correctamente
        schema:
          type: object
          properties:
            message:
              type: string
              example: Camera stopped successfully
    """
    global system_state
    
    # Marcar como detenido
    system_state['running'] = False
    system_state['camera_active'] = False
    
    # Dar tiempo para que el loop termine
    time.sleep(0.5)
    
    # Liberar la cámara explícitamente
    try:
        camera.disconnect()
        print("📹 Cámara liberada correctamente")
    except Exception as e:
        print(f"⚠️ Error al liberar cámara: {e}")
    
    # Limpiar último frame
    system_state['last_frame'] = None
    
    return jsonify({'message': 'Camera stopped successfully'})


@app.route('/api/history', methods=['GET'])
def get_history():
    """
    Historial de ocupación
    ---
    tags:
      - Métricas
    parameters:
      - name: start
        in: query
        type: string
        required: false
        description: Timestamp de inicio (opcional)
      - name: end
        in: query
        type: string
        required: false
        description: Timestamp de fin (opcional)
    responses:
      200:
        description: Historial de ocupación y estadísticas
        schema:
          type: object
          properties:
            history:
              type: array
              items:
                type: object
            avg_occupancy:
              type: number
            peak_count:
              type: integer
            peak_time:
              type: string
    """
    start_time = request.args.get('start', None)
    end_time = request.args.get('end', None)
    
    history_data = metrics.get_history(start_time, end_time)
    
    return jsonify({
        'history': history_data,
        'avg_occupancy': metrics.get_avg_occupancy(start_time, end_time),
        'peak_count': metrics.get_peak_count(start_time, end_time),
        'peak_time': metrics.get_peak_time(start_time, end_time)
    })


@app.route('/api/camera/test', methods=['POST'])
def test_camera_connection():
    """
    Probar conexión a cámara
    ---
    tags:
      - Cámara
    parameters:
      - in: body
        name: test_params
        description: Parámetros para probar conexión
        schema:
          type: object
          properties:
            camera_url:
              type: string
              example: http://192.168.1.100:5000
            timeout:
              type: integer
              example: 5
    responses:
      200:
        description: Resultado del test de conexión
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            latency:
              type: number
      400:
        description: Error en parámetros
    """
    data = request.json or {}
    camera_url = data.get('camera_url', '')
    timeout = data.get('timeout', 5)
    
    if not camera_url:
        return jsonify({'error': 'camera_url is required'}), 400
    
    from core.camera import CameraManager
    
    start_time = time.time()
    test_cam = None
    
    try:
        # Convertir a int si es un número (índice de webcam)
        if str(camera_url).isdigit():
            camera_url = int(camera_url)
        
        print(f"🔍 Probando conexión a: {camera_url}")
        
        # Usar CameraManager que maneja automáticamente DroidCam, RTSP, etc.
        test_cam = CameraManager(source=camera_url, camera_type='auto')
        
        # Intentar conectar
        if not test_cam.connect():
            return jsonify({
                'success': False,
                'error': 'No se pudo conectar a la cámara',
                'latency': round(time.time() - start_time, 3)
            })
        
        # Intentar leer algunos frames
        success = False
        last_error = "Sin frames disponibles"
        
        for i in range(10):  # Intentar leer 10 frames
            ret, frame = test_cam.read()
            
            if ret and frame is not None and frame.size > 0:
                success = True
                h, w = frame.shape[:2]
                print(f"✅ Frame leído correctamente: {w}x{h}")
                break
            
            eventlet.sleep(0.2)  # Esperar un poco entre intentos
            
            if not ret:
                last_error = "read() retornó False"
        
        latency = time.time() - start_time
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Conexión exitosa - Resolución: {w}x{h}',
                'latency': round(latency, 3)
            })
        else:
            return jsonify({
                'success': False,
                'error': f'No se pudo leer frames válidos - {last_error}',
                'latency': round(latency, 3)
            })
    
    except Exception as e:
        latency = time.time() - start_time
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'latency': round(latency, 3)
        })
    
    finally:
        if test_cam is not None:
            test_cam.disconnect()
            print(f"🔒 Cámara liberada")


@app.route('/api/camera/scan', methods=['POST'])
def scan_camera_networks():
    """
    Escanear red en busca de cámaras
    ---
    tags:
      - Cámara
    parameters:
      - in: body
        name: scan_params
        description: Parámetros de escaneo
        schema:
          type: object
          properties:
            ips:
              type: array
              items:
                type: string
              example: ["192.168.1.100", "192.168.196.100"]
            port:
              type: integer
              example: 5000
            timeout:
              type: integer
              example: 3
    responses:
      200:
        description: Cámaras encontradas
        schema:
          type: object
          properties:
            found:
              type: integer
            cameras:
              type: array
              items:
                type: object
    """
    from core.tapo_camera_adapter import scan_camera_networks
    
    data = request.json or {}
    
    # Usar IPs de la configuración si no se proporcionan
    if 'ips' in data:
        base_ips = data['ips']
    else:
        # Extraer IPs de las URLs alternativas configuradas
        base_ips = []
        for url in config['camera_alternative_ips']:
            if url.startswith('http://'):
                # Extraer IP de la URL (formato: http://IP:PORT)
                ip_with_port = url.replace('http://', '').replace('https://', '')
                if ':' in ip_with_port:
                    ip = ip_with_port.split(':')[0]
                    base_ips.append(ip)
    
    port = data.get('port', 5000)
    timeout = data.get('timeout', 3)
    
    found_cameras = scan_camera_networks(base_ips, port, timeout)
    
    return jsonify({
        'found': len(found_cameras),
        'cameras': found_cameras
    })


@app.route('/api/camera/change', methods=['POST'])
def change_camera_source():
    """
    Cambiar fuente de cámara
    ---
    tags:
      - Cámara
    parameters:
      - in: body
        name: camera_source
        required: true
        description: Nueva fuente de cámara
        schema:
          type: object
          required:
            - source
          properties:
            source:
              type: string
              example: http://192.168.1.100:5000
            camera_type:
              type: string
              enum: [auto, webcam, rtsp, tapo]
              example: auto
    responses:
      200:
        description: Fuente de cámara cambiada correctamente
        schema:
          type: object
          properties:
            message:
              type: string
            source:
              type: string
            camera_type:
              type: string
            connected:
              type: boolean
      400:
        description: Parámetro source requerido
      500:
        description: Error al conectar con la nueva fuente
    """
    global camera, system_state
    
    data = request.json
    new_source = data.get('source')
    camera_type = data.get('camera_type', 'auto')
    
    if not new_source:
        return jsonify({'error': 'source is required'}), 400
    
    # Detener el sistema si está corriendo
    was_running = system_state['running']
    if was_running:
        system_state['running'] = False
        time.sleep(0.5)  # Dar tiempo para que se detenga el loop
    
    # Desconectar cámara actual
    camera.disconnect()
    
    # Crear nueva cámara
    camera = CameraManager(source=new_source, camera_type=camera_type)
    
    # Intentar conectar
    success = camera.connect()
    
    if success:
        # Actualizar configuración
        config['camera_source'] = new_source
        config['camera_type'] = camera_type
        
        # Reiniciar si estaba corriendo
        if was_running:
            system_state['running'] = True
            socketio.start_background_task(target=process_video_stream)
        
        return jsonify({
            'message': 'Camera source changed successfully',
            'source': new_source,
            'camera_type': camera.camera_type,
            'connected': True
        })
    else:
        return jsonify({
            'error': 'Failed to connect to new camera source',
            'source': new_source
        }), 500


@app.route('/api/camera/stats', methods=['GET'])
def get_camera_stats():
    """
    Estadísticas de cámara
    ---
    tags:
      - Cámara
    responses:
      200:
        description: Estadísticas de la cámara (disponible solo para cámaras Tapo)
        schema:
          type: object
          properties:
            camera_type:
              type: string
            source:
              type: string
            stats:
              type: object
            message:
              type: string
    """
    if camera.camera_type == 'tapo' and hasattr(camera.cap, 'get_stats'):
        stats = camera.cap.get_stats()
        return jsonify({
            'camera_type': 'tapo',
            'source': config['camera_source'],
            'stats': stats
        })
    else:
        return jsonify({
            'camera_type': camera.camera_type,
            'source': config['camera_source'],
            'message': 'Stats only available for Tapo cameras'
        })


# ==================== WEBSOCKET ====================

def process_video_stream():
    """
    Loop principal que procesa video y envía por WebSocket
    Se ejecuta en background mientras system_state['running'] == True
    """
    print("🎬 Iniciando loop de procesamiento de video...")
    
    frame_count = 0
    
    # OPTIMIZACIÓN: Pre-alocar variables para reducir overhead
    import gc
    gc.disable()  # Desactivar GC durante procesamiento para FPS estables
    
    while system_state['running']:
        frame_count += 1
        
        try:
            # Verificar si todavía estamos corriendo antes de leer
            if not system_state['running']:
                break
            
            # Capturar frame con verificación de conexión
            if not camera.is_connected():
                print("⚠️ Cámara desconectada, saliendo del loop")
                break
            
            ret, frame = camera.read()
            
            if not ret:
                print("⚠️ No se pudo leer frame de la cámara")
                time.sleep(0.1)
                continue
            
            # Aplicar efecto ojo de pez si está habilitado
            frame = apply_fisheye(frame)

            # OPTIMIZACIÓN: Timestamp antes de detección
            start_time = time.time()

            skip_cfg = config.get('skip_frames', 0)
            try:
                skip_frames_value = int(skip_cfg) if skip_cfg is not None else 0
            except (TypeError, ValueError):
                skip_frames_value = 0
            if skip_frames_value < 0:
                skip_frames_value = 0

            do_detection = (
                skip_frames_value == 0
                or frame_count == 1
                or (frame_count % (skip_frames_value + 1) == 0)
            )

            if do_detection:
                # RealtimeDetector.detect_frame() retorna (annotated, detections, inference_time)
                _, detections, inference_time = detector.detect_frame(frame, return_annotated=False)
                
                count = len(detections)
                models_used = ['yolo11s']  # Solo usamos yolo11s

                system_state['last_detections'] = detections
                system_state['last_models_used'] = models_used
                system_state['last_inference_time'] = inference_time
            else:
                detections = system_state.get('last_detections', [])
                models_used = system_state.get('last_models_used', system_state['models_loaded'])
                inference_time = system_state.get('last_inference_time', 0.0)
                count = len(detections)

            # Tracking ligero para conteo bidireccional
            tracked_count = count
            tracked_detections = None
            try:
                entry_delta, exit_delta = people_tracker.update(detections, frame.shape)
                system_state['entries'] = system_state.get('entries', 0) + entry_delta
                system_state['exits'] = system_state.get('exits', 0) + exit_delta
                tracked_count = len(people_tracker.tracks)

                tracked_detections = []
                for track in people_tracker.tracks.values():
                    tracked_detections.append({
                        'bbox': track['bbox'],
                        'confidence': float(track.get('confidence', 1.0)),
                        'class': 'person',
                        'model': 'track'
                    })
            except Exception:
                tracked_count = count

            history = system_state.get('count_history', [])
            history.append(tracked_count)
            if len(history) > 10:
                history.pop(0)
            system_state['count_history'] = history
            stable_count = int(round(sum(history) / len(history))) if history else tracked_count

            # Calcular FPS real del ciclo completo
            elapsed_total = time.time() - start_time
            fps = 1.0 / elapsed_total if elapsed_total > 0 else 0
            
            # Actualizar estado
            system_state['current_count'] = stable_count
            occupancy_rate = stable_count / config['max_capacity'] if config['max_capacity'] > 0 else 0
            system_state['occupancy_rate'] = occupancy_rate
            system_state['fps'] = fps

            # Calcular Nivel de Ocupación
            thresholds = config.get('occupancy_thresholds', {})
            low_cfg = thresholds.get('low', {'max_people': 5, 'max_occupancy_pct': 0.20})
            med_cfg = thresholds.get('medium', {'max_people': 15, 'max_occupancy_pct': 0.60})

            if stable_count <= low_cfg['max_people'] and occupancy_rate < low_cfg['max_occupancy_pct']:
                occupancy_level = 'Baja'
            elif stable_count <= med_cfg['max_people'] and occupancy_rate < med_cfg['max_occupancy_pct']:
                occupancy_level = 'Media'
            else:
                occupancy_level = 'Alta'
            
            system_state['occupancy_level'] = occupancy_level
            
            # OPTIMIZACIÓN: Usar detecciones directas sin tracking complejo
            display_detections = detections
            
            # Dibujar bounding boxes (sin copiar frame para ahorrar memoria)
            annotated_frame = draw_detections(frame, display_detections)
            
            # OPTIMIZACIÓN: Aplicar privacidad SOLO cada N frames para ahorrar CPU
            if config['enable_privacy'] and frame_count % 3 == 0:  # Solo cada 3 frames
                annotated_frame = blur_faces(annotated_frame)

            # OPTIMIZACIÓN: No redimensionar el frame - enviar resolución original
            # Esto ahorra CPU significativo
            stream_frame = annotated_frame
            
            # OPTIMIZACIÓN MÁXIMA: JPEG calidad 50 para encoding ultra-rápido
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, 50]
            success, buffer = cv2.imencode('.jpg', stream_frame, encode_params)
            if not success:
                continue
            jpeg_bytes = buffer.tobytes()
            frame_base64 = base64.b64encode(jpeg_bytes).decode('utf-8')
            
            # Verificar alertas
            alert = stable_count > config['max_capacity']
            
            # Crear objeto con datos del frame
            frame_data = {
                'type': 'frame',
                'timestamp': time.time(),
                'frame': frame_base64,
                'count': stable_count,
                'tracked_count': tracked_count,
                'raw_count': count,
                'max_capacity': config['max_capacity'],
                'occupancy_rate': system_state['occupancy_rate'],
                'alert': alert,
                'models_used': models_used,
                'entries': system_state.get('entries', 0),
                'exits': system_state.get('exits', 0),
                'fps': round(fps, 1),
                'camera_fps': round(system_state.get('camera_fps', 30), 1),
                'inference_time': round(inference_time, 3),
                'frame_number': frame_count,
                'occupancy_level': system_state.get('occupancy_level', 'Desconocido')
            }
            
            # Guardar frame actual en estado (para HTTP polling y streams)
            system_state['last_frame'] = frame_data
            system_state['last_jpeg'] = jpeg_bytes

            # Enviar por WebSocket SIN THROTTLING (máxima velocidad)
            if system_state['connected_clients'] > 0:
                socketio.emit('frame_update', frame_data, namespace='/')
            
            # Log cada 90 frames (~3 seg) para mínimo overhead
            if frame_count % 90 == 0:
                avg_fps = sum(system_state['fps_history']) / len(system_state['fps_history']) if system_state['fps_history'] else fps
                print(f"✅ Frame #{frame_count}: {count} personas, {avg_fps:.1f} FPS (avg)")
            
            # Guardar en historial cada 15 segundos para reducir I/O
            if frame_count % 450 == 0:  # ~15 seg a 30 FPS
                metrics.log_inference(count, models_used, inference_time, fps, config['max_capacity'])
            
            # Actualizar historial de FPS para estabilización
            system_state['fps_history'].append(fps)
            if len(system_state['fps_history']) > 30:  # Promediar últimos 30 frames
                system_state['fps_history'].pop(0)
            
            # LIMITADOR DE FPS: Forzar 30 FPS constantes para stream fluido
            target_fps = system_state.get('target_fps', 30.0)
            elapsed = time.time() - start_time
            target_frame_time = 1.0 / target_fps
            
            if elapsed < target_frame_time:
                eventlet.sleep(target_frame_time - elapsed)
            
            # OPTIMIZACIÓN: Garbage collection cada 100 frames
            if frame_count % 100 == 0:
                import gc
                gc.collect()
            
        except Exception as e:
            print(f"❌ Error in video processing loop: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(0.1)  # Esperar un poco antes de reintentar
    
    # Limpiar al salir del loop
    print("🛑 Video processing loop stopped")
    
    # Re-activar garbage collector
    import gc
    gc.enable()
    
    # Actualizar estado
    system_state['camera_active'] = False
    system_state['current_count'] = 0
    system_state['fps'] = 0
    
    # Asegurar que la cámara se libere
    try:
        camera.disconnect()
        print("📹 Cámara desconectada desde el loop")
    except Exception as e:
        print(f"⚠️ Error al desconectar cámara desde loop: {e}")


def draw_detections(frame, detections):
    """Dibujar bounding boxes en el frame con mejor visualización"""
    for det in detections:
        x1, y1, x2, y2 = det['bbox']
        conf = det['confidence']
        color = (0, 255, 0) if conf > 0.5 else (0, 255, 255)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
    return frame


def blur_faces(frame):
    """Aplicar blur a rostros detectados (privacidad)"""
    # TODO: Implementar con MediaPipe o MTCNN
    # Por ahora, aplicar blur general ligero
    return cv2.GaussianBlur(frame, (15, 15), 0)


@socketio.on('connect')
def handle_connect():
    global system_state
    system_state['connected_clients'] += 1
    print(f'✅ Client connected (total: {system_state["connected_clients"]})')
    print(f'🔗 WebSocket connection established')
    emit('connection_response', {'status': 'connected', 'message': 'Backend ready'})


@socketio.on('disconnect')
def handle_disconnect():
    global system_state
    system_state['connected_clients'] = max(0, system_state['connected_clients'] - 1)
    print(f'❌ Client disconnected (remaining: {system_state["connected_clients"]})')
    print(f'⚠️ WebSocket connection closed')


# ==================== MAIN ====================

if __name__ == '__main__':
    print("="*80)
    print("🚀 SISTEMA DE CONTROL DE AFORO - BACKEND")
    print("="*80)
    print(f"Modelos cargados: {system_state['models_loaded']}")
    print(f"Puerto: 5000")
    print("="*80)
    
    # Ejecutar con SocketIO (soporta WebSockets)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
