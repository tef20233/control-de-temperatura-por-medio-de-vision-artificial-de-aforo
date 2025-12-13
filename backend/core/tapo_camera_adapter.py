#!/usr/bin/env python3
"""
Adaptador para cámara Tapo que obtiene frames via HTTP
desde el servidor Flask (camara.py)
"""

import requests
import base64
import numpy as np
import cv2
import time
from threading import Thread, Lock
import logging

logger = logging.getLogger(__name__)


class TapoCameraAdapter:
    """
    Adaptador para cámara Tapo que obtiene frames via HTTP.
    Compatible con la interfaz de CameraManager.
    """
    
    def __init__(self, camera_url="http://localhost:5000", timeout=10, retry_delay=2):
        """
        Args:
            camera_url: URL base del servidor de la cámara (ej: http://192.168.1.100:5000)
            timeout: Timeout para las peticiones HTTP en segundos
            retry_delay: Tiempo de espera entre reintentos en segundos
        """
        self.camera_url = camera_url.rstrip('/')
        self.snapshot_endpoint = f"{self.camera_url}/snapshot"
        self.timeout = timeout
        self.retry_delay = retry_delay
        
        # Estado
        self.is_opened = False
        self.last_frame = None
        self.last_frame_time = 0
        self.frame_lock = Lock()
        
        # Thread para captura continua
        self.capture_thread = None
        self.running = False
        
        # Estadísticas
        self.total_requests = 0
        self.failed_requests = 0
        self.avg_response_time = 0
        
    def connect(self):
        """Conectar a la cámara y verificar disponibilidad"""
        try:
            logger.info(f"🔌 Conectando a cámara Tapo en {self.camera_url}...")
            
            # Verificar que el servidor está disponible
            response = requests.get(self.snapshot_endpoint, timeout=self.timeout)
            response.raise_for_status()
            
            # Intentar obtener el primer frame
            json_data = response.json()
            if 'image_base64' not in json_data:
                raise Exception("Respuesta no contiene image_base64")
            
            # Decodificar y validar el frame
            frame = self._decode_frame(json_data['image_base64'])
            if frame is None:
                raise Exception("No se pudo decodificar el frame")
            
            # Guardar el frame inicial
            with self.frame_lock:
                self.last_frame = frame
                self.last_frame_time = time.time()
            
            self.is_opened = True
            logger.info(f"✅ Cámara Tapo conectada: {json_data['width']}x{json_data['height']}")
            
            # Iniciar thread de captura continua
            self._start_capture_thread()
            
            return True
            
        except requests.exceptions.Timeout:
            logger.error(f"❌ Timeout conectando a {self.camera_url} (verifique la red)")
            return False
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ No se puede conectar a {self.camera_url} (verifique que camara.py está corriendo)")
            return False
        except Exception as e:
            logger.error(f"❌ Error conectando a cámara Tapo: {e}")
            return False
    
    def _decode_frame(self, image_base64):
        """Decodificar frame desde base64"""
        try:
            img_bytes = base64.b64decode(image_base64)
            nparr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return frame
        except Exception as e:
            logger.error(f"Error decodificando frame: {e}")
            return None
    
    def _start_capture_thread(self):
        """Iniciar thread de captura continua en background"""
        if self.capture_thread is not None and self.capture_thread.is_alive():
            return
        
        self.running = True
        self.capture_thread = Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        logger.info("🎥 Thread de captura continua iniciado")
    
    def _capture_loop(self):
        """Loop de captura continua que obtiene frames del servidor"""
        consecutive_failures = 0
        max_consecutive_failures = 5
        
        while self.running:
            try:
                start_time = time.perf_counter()
                
                # Obtener frame desde el servidor
                response = requests.get(self.snapshot_endpoint, timeout=self.timeout)
                response.raise_for_status()
                
                json_data = response.json()
                frame = self._decode_frame(json_data['image_base64'])
                
                if frame is not None:
                    # Actualizar frame
                    with self.frame_lock:
                        self.last_frame = frame
                        self.last_frame_time = time.time()
                    
                    # Actualizar estadísticas
                    elapsed = time.perf_counter() - start_time
                    self.total_requests += 1
                    self.avg_response_time = (self.avg_response_time * (self.total_requests - 1) + elapsed) / self.total_requests
                    
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    logger.warning(f"⚠️ Frame nulo recibido (fallos consecutivos: {consecutive_failures})")
                
            except requests.exceptions.Timeout:
                consecutive_failures += 1
                self.failed_requests += 1
                logger.warning(f"⚠️ Timeout obteniendo frame (fallos: {consecutive_failures}/{max_consecutive_failures})")
                
            except requests.exceptions.ConnectionError:
                consecutive_failures += 1
                self.failed_requests += 1
                logger.warning(f"⚠️ Error de conexión (fallos: {consecutive_failures}/{max_consecutive_failures})")
                
            except Exception as e:
                consecutive_failures += 1
                self.failed_requests += 1
                logger.error(f"⚠️ Error en captura: {e} (fallos: {consecutive_failures}/{max_consecutive_failures})")
            
            # Si hay muchos fallos consecutivos, marcar como desconectado
            if consecutive_failures >= max_consecutive_failures:
                logger.error(f"❌ Demasiados fallos consecutivos. Cámara desconectada.")
                self.is_opened = False
                break
            
            # Esperar antes del siguiente frame (ajustar según necesidad, ej: 0.1s = 10 FPS)
            time.sleep(0.1)  # 10 FPS aproximadamente
        
        logger.info("🛑 Thread de captura detenido")
    
    def read(self):
        """
        Leer el último frame capturado.
        Compatible con la interfaz de cv2.VideoCapture.
        
        Returns:
            tuple: (ret, frame) donde ret es True si hay frame disponible
        """
        if not self.is_opened:
            return False, None
        
        with self.frame_lock:
            if self.last_frame is None:
                return False, None
            
            # Verificar que el frame no es muy antiguo (> 5 segundos)
            frame_age = time.time() - self.last_frame_time
            if frame_age > 5.0:
                logger.warning(f"⚠️ Frame antiguo ({frame_age:.1f}s)")
                return False, None
            
            # Retornar una copia del frame
            return True, self.last_frame.copy()
    
    def is_connected(self):
        """Verificar si la cámara está conectada"""
        if not self.is_opened:
            return False
        
        # Verificar que el último frame no es muy antiguo
        with self.frame_lock:
            if self.last_frame is None:
                return False
            
            frame_age = time.time() - self.last_frame_time
            return frame_age < 5.0  # Frame debe ser reciente (< 5s)
    
    def disconnect(self):
        """Desconectar cámara y detener thread de captura"""
        logger.info("🔌 Desconectando cámara Tapo...")
        self.running = False
        self.is_opened = False
        
        if self.capture_thread is not None:
            self.capture_thread.join(timeout=2)
        
        with self.frame_lock:
            self.last_frame = None
        
        logger.info("✅ Cámara Tapo desconectada")
    
    def get_stats(self):
        """Obtener estadísticas de la cámara"""
        return {
            'total_requests': self.total_requests,
            'failed_requests': self.failed_requests,
            'success_rate': (self.total_requests - self.failed_requests) / self.total_requests if self.total_requests > 0 else 0,
            'avg_response_time': self.avg_response_time,
            'last_frame_age': time.time() - self.last_frame_time if self.last_frame_time > 0 else None
        }
    
    def test_connection(self):
        """
        Probar la conexión a la cámara sin iniciar captura continua.
        Útil para diagnosticar problemas de red.
        
        Returns:
            dict: Información sobre la prueba de conexión
        """
        result = {
            'success': False,
            'url': self.camera_url,
            'error': None,
            'response_time': None,
            'frame_size': None
        }
        
        try:
            start_time = time.perf_counter()
            response = requests.get(self.snapshot_endpoint, timeout=self.timeout)
            response.raise_for_status()
            elapsed = time.perf_counter() - start_time
            
            json_data = response.json()
            frame = self._decode_frame(json_data['image_base64'])
            
            if frame is not None:
                result['success'] = True
                result['response_time'] = elapsed
                result['frame_size'] = (json_data['width'], json_data['height'])
            else:
                result['error'] = "No se pudo decodificar el frame"
                
        except requests.exceptions.Timeout:
            result['error'] = f"Timeout después de {self.timeout}s (verifique la red)"
        except requests.exceptions.ConnectionError:
            result['error'] = "No se puede conectar al servidor (verifique que camara.py está corriendo)"
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def __del__(self):
        self.disconnect()


# Función de utilidad para probar diferentes IPs/redes
def scan_camera_networks(base_ips, port=5000, timeout=3):
    """
    Escanear múltiples IPs para encontrar la cámara.
    
    Args:
        base_ips: Lista de IPs base a probar (ej: ['192.168.1.100', '192.168.196.100'])
        port: Puerto del servidor
        timeout: Timeout para cada prueba
    
    Returns:
        list: Lista de IPs donde se encontró la cámara
    """
    found_cameras = []
    
    for ip in base_ips:
        url = f"http://{ip}:{port}"
        logger.info(f"🔍 Probando {url}...")
        
        adapter = TapoCameraAdapter(camera_url=url, timeout=timeout)
        test_result = adapter.test_connection()
        
        if test_result['success']:
            logger.info(f"✅ Cámara encontrada en {url} (tiempo: {test_result['response_time']:.3f}s)")
            found_cameras.append({
                'url': url,
                'ip': ip,
                'response_time': test_result['response_time'],
                'frame_size': test_result['frame_size']
            })
        else:
            logger.warning(f"❌ No se encontró cámara en {url}: {test_result['error']}")
    
    return found_cameras
