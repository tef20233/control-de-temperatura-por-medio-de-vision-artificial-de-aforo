#!/usr/bin/env python3
"""
Adaptador para streams MJPEG (IP Webcam, DroidCam, etc.)
Soporta streams HTTP de cámaras de celular y otras fuentes MJPEG
"""

import cv2
import requests
import numpy as np
import logging
from threading import Thread, Lock
import time

logger = logging.getLogger(__name__)


class MJPEGStreamAdapter:
    """
    Adaptador para streams MJPEG via HTTP.
    Soporta apps como IP Webcam, DroidCam, etc.
    Compatible con la interfaz de cv2.VideoCapture.
    """
    
    def __init__(self, stream_url, timeout=10):
        """
        Args:
            stream_url: URL del stream MJPEG (ej: http://192.168.1.100:8080/video)
            timeout: Timeout para conexión inicial
        """
        self.stream_url = stream_url
        self.timeout = timeout
        
        # Estado
        self.is_opened = False
        self.stream = None
        self.last_frame = None
        self.last_frame_time = 0
        self.frame_lock = Lock()
        
        # Thread para captura
        self.capture_thread = None
        self.running = False
        
    def connect(self):
        """Conectar al stream MJPEG"""
        try:
            logger.info(f"🔌 Conectando a stream MJPEG: {self.stream_url}")
            
            # Verificar conexión inicial
            response = requests.get(self.stream_url, timeout=self.timeout, stream=True)
            response.raise_for_status()
            
            # Intentar leer el primer frame
            bytes_data = b''
            for chunk in response.iter_content(chunk_size=1024):
                bytes_data += chunk
                a = bytes_data.find(b'\xff\xd8')  # Inicio JPEG
                b = bytes_data.find(b'\xff\xd9')  # Fin JPEG
                
                if a != -1 and b != -1:
                    jpg = bytes_data[a:b+2]
                    bytes_data = bytes_data[b+2:]
                    
                    # Decodificar frame
                    frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if frame is not None:
                        with self.frame_lock:
                            self.last_frame = frame
                            self.last_frame_time = time.time()
                        
                        self.is_opened = True
                        logger.info(f"✅ Stream MJPEG conectado: {frame.shape[1]}x{frame.shape[0]}")
                        
                        # Cerrar esta conexión y empezar thread continuo
                        response.close()
                        self._start_capture_thread()
                        return True
                
                # Solo intentar con los primeros chunks
                if len(bytes_data) > 100000:
                    break
            
            logger.error("❌ No se pudo obtener frame del stream MJPEG")
            return False
            
        except requests.exceptions.Timeout:
            logger.error(f"❌ Timeout conectando a {self.stream_url}")
            return False
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Error de conexión a {self.stream_url}")
            return False
        except Exception as e:
            logger.error(f"❌ Error conectando: {e}")
            return False
    
    def _start_capture_thread(self):
        """Iniciar thread de captura continua"""
        if self.capture_thread is not None and self.capture_thread.is_alive():
            return
        
        self.running = True
        self.capture_thread = Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        logger.info("🎥 Thread de captura MJPEG iniciado")
    
    def _capture_loop(self):
        """Loop de captura continua del stream MJPEG"""
        consecutive_failures = 0
        max_consecutive_failures = 5
        
        while self.running:
            try:
                # Abrir conexión al stream
                response = requests.get(self.stream_url, timeout=self.timeout, stream=True)
                response.raise_for_status()
                
                bytes_data = b''
                
                for chunk in response.iter_content(chunk_size=1024):
                    if not self.running:
                        break
                    
                    bytes_data += chunk
                    a = bytes_data.find(b'\xff\xd8')  # Inicio JPEG
                    b = bytes_data.find(b'\xff\xd9')  # Fin JPEG
                    
                    if a != -1 and b != -1:
                        jpg = bytes_data[a:b+2]
                        bytes_data = bytes_data[b+2:]
                        
                        # Decodificar frame
                        frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                        
                        if frame is not None:
                            with self.frame_lock:
                                self.last_frame = frame
                                self.last_frame_time = time.time()
                            consecutive_failures = 0
                
                response.close()
                
            except requests.exceptions.Timeout:
                consecutive_failures += 1
                logger.warning(f"⚠️ Timeout en stream (fallos: {consecutive_failures}/{max_consecutive_failures})")
                
            except requests.exceptions.ConnectionError:
                consecutive_failures += 1
                logger.warning(f"⚠️ Error de conexión (fallos: {consecutive_failures}/{max_consecutive_failures})")
                
            except Exception as e:
                consecutive_failures += 1
                logger.error(f"⚠️ Error en captura: {e} (fallos: {consecutive_failures}/{max_consecutive_failures})")
            
            # Si hay muchos fallos, marcar como desconectado
            if consecutive_failures >= max_consecutive_failures:
                logger.error(f"❌ Demasiados fallos. Stream desconectado.")
                self.is_opened = False
                break
            
            # Esperar un poco antes de reintentar
            if consecutive_failures > 0:
                time.sleep(1)
        
        logger.info("🛑 Thread de captura MJPEG detenido")
    
    def read(self):
        """
        Leer el último frame capturado.
        Compatible con cv2.VideoCapture.
        
        Returns:
            tuple: (ret, frame)
        """
        if not self.is_opened:
            return False, None
        
        with self.frame_lock:
            if self.last_frame is None:
                return False, None
            
            # Verificar que el frame no es muy antiguo
            frame_age = time.time() - self.last_frame_time
            if frame_age > 5.0:
                logger.warning(f"⚠️ Frame antiguo ({frame_age:.1f}s)")
                return False, None
            
            return True, self.last_frame.copy()
    
    def is_connected(self):
        """Verificar si el stream está conectado"""
        if not self.is_opened:
            return False
        
        with self.frame_lock:
            if self.last_frame is None:
                return False
            
            frame_age = time.time() - self.last_frame_time
            return frame_age < 5.0
    
    def disconnect(self):
        """Desconectar stream"""
        logger.info("🔌 Desconectando stream MJPEG...")
        self.running = False
        self.is_opened = False
        
        if self.capture_thread is not None:
            self.capture_thread.join(timeout=2)
        
        with self.frame_lock:
            self.last_frame = None
        
        logger.info("✅ Stream MJPEG desconectado")
    
    def __del__(self):
        self.disconnect()
