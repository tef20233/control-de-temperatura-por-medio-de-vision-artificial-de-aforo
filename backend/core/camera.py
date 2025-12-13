import cv2
import logging
from .tapo_camera_adapter import TapoCameraAdapter
from .mjpeg_stream_adapter import MJPEGStreamAdapter

logger = logging.getLogger(__name__)


class CameraManager:
    """
    Maneja conexión y lectura de cámara (USB, RTSP, Tapo HTTP, o MJPEG Stream).
    Soporta múltiples tipos de fuentes de video.
    """
    
    def __init__(self, source=0, camera_type='auto'):
        """
        Args:
            source: 
                - 0 para webcam
                - "rtsp://..." para IP camera
                - "http://...:<puerto>/snapshot" para cámara Tapo via HTTP
                - "http://...:<puerto>/video" para stream MJPEG (IP Webcam, DroidCam)
            camera_type: 
                - 'auto': Detectar automáticamente según source
                - 'webcam': Cámara USB/webcam
                - 'rtsp': Cámara RTSP
                - 'tapo': Cámara Tapo via HTTP
                - 'mjpeg': Stream MJPEG (IP Webcam, DroidCam, etc.)
        """
        self.source = source
        self.camera_type = self._detect_camera_type(source, camera_type)
        self.cap = None
        self.is_opened = False
        
        logger.info(f"🎥 CameraManager inicializado: tipo={self.camera_type}, source={self.source}")
    
    def _detect_camera_type(self, source, camera_type):
        """Detectar el tipo de cámara según la fuente"""
        if camera_type != 'auto':
            return camera_type
        
        if isinstance(source, int):
            return 'webcam'
        elif isinstance(source, str):
            if source.startswith('rtsp://'):
                return 'rtsp'
            elif source.startswith('http://') or source.startswith('https://'):
                # Detectar entre Tapo y MJPEG según la URL
                if '/video' in source.lower() or '/mjpeg' in source.lower():
                    return 'mjpeg'
                elif '/snapshot' in source.lower():
                    return 'tapo'
                else:
                    # Por defecto, asumir MJPEG para streams genéricos
                    return 'mjpeg'
        
        return 'webcam'
    
    def connect(self):
        """Conectar a la cámara según el tipo"""
        try:
            if self.camera_type == 'tapo':
                # Usar TapoCameraAdapter para cámaras Tapo
                logger.info(f"Conectando a cámara Tapo en {self.source}")
                self.cap = TapoCameraAdapter(camera_url=self.source, timeout=10)
                self.is_opened = self.cap.connect()
            elif self.camera_type == 'mjpeg':
                # Usar MJPEGStreamAdapter para streams MJPEG (IP Webcam, DroidCam, etc.)
                logger.info(f"Conectando a stream MJPEG en {self.source}")
                self.cap = MJPEGStreamAdapter(stream_url=self.source, timeout=10)
                self.is_opened = self.cap.connect()
            else:
                # Usar cv2.VideoCapture para webcam y RTSP
                logger.info(f"Conectando a cámara {self.camera_type} en {self.source}")
                self.cap = cv2.VideoCapture(self.source)
                
                if self.camera_type == 'webcam':
                    # MÁXIMA VELOCIDAD: Resolución ultra-baja = stream fluido
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
                    self.cap.set(cv2.CAP_PROP_FPS, 30)
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
                    self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
                    self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
                    
                    # DETECTAR FPS REAL de la cámara
                    actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
                    actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    logger.info(f"📹 Cámara: {actual_width}x{actual_height} @ {actual_fps:.1f} FPS")
                
                self.is_opened = self.cap.isOpened()
            
            if self.is_opened:
                logger.info(f"✅ Cámara conectada: tipo={self.camera_type}, source={self.source}")
            else:
                logger.error(f"❌ No se pudo conectar a cámara: {self.source}")
            
            return self.is_opened
        
        except Exception as e:
            logger.error(f"❌ Error conectando cámara: {e}")
            return False
    
    def read(self):
        """Leer frame de la cámara"""
        if not self.is_opened:
            return False, None
        
        ret, frame = self.cap.read()
        return ret, frame
    
    def get_fps(self):
        """Obtener FPS reales de la cámara"""
        if not self.is_opened or self.cap is None:
            return 0
        
        if self.camera_type in ['tapo', 'mjpeg']:
            # Para adapters custom, retornar 30 por defecto
            return 30.0
        else:
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            return fps if fps > 0 else 30.0
    
    def is_connected(self):
        """Verificar si la cámara está conectada"""
        if not self.is_opened or self.cap is None:
            return False
        
        if self.camera_type in ['tapo', 'mjpeg']:
            return self.cap.is_connected()
        else:
            return self.cap.isOpened()
    
    def disconnect(self):
        """Desconectar cámara"""
        if self.cap is not None:
            if self.camera_type in ['tapo', 'mjpeg']:
                self.cap.disconnect()
            else:
                self.cap.release()
            self.is_opened = False
            logger.info("🔌 Cámara desconectada")
    
    def __del__(self):
        self.disconnect()
