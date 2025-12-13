"""Funciones para anonimización facial y preservación de privacidad."""

from __future__ import annotations

from typing import Dict, List, Tuple

import cv2
import numpy as np


def detect_face_region(bbox: List[int], method: str = "thirds") -> Tuple[int, int, int, int]:
    """Estimar región facial dentro de bbox de persona.

    Args:
        bbox: [x1, y1, x2, y2] del bounding box completo.
        method: Método de estimación ('thirds' o 'cascade').

    Returns:
        Tuple (face_x1, face_y1, face_x2, face_y2).
    """

    x1, y1, x2, y2 = bbox
    if method == "thirds" or method not in {"thirds", "cascade"}:
        h = y2 - y1
        face_y2 = y1 + h // 3
        return x1, y1, x2, max(y1, face_y2)

    if method == "cascade":
        # Cargar clasificador Haar Cascade (solo la primera vez si es posible, aquí lo cargamos localmente)
        # Se asume que el archivo xml está en cv2.data.haarcascades
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Extraer ROI de la persona para buscar cara solo ahí
        # Expandir un poco el bbox para asegurar que la cara esté dentro
        h_person = y2 - y1
        w_person = x2 - x1
        
        # Solo buscar en la mitad superior de la persona
        search_y2 = y1 + int(h_person * 0.6)
        
        # Recortar ROI de la imagen original no es posible aquí porque solo tenemos bbox
        # Por diseño de esta función, solo devolvemos coordenadas relativas al frame global.
        # Sin acceso al frame aquí, no podemos ejecutar cascade real.
        # Fallback a 'thirds' mejorado si no se pasa el frame.
        pass

    # Método por defecto: tercio superior
    h = y2 - y1
    face_y2 = y1 + h // 3
    return x1, y1, x2, max(y1, face_y2)


def apply_gaussian_blur(
    region: np.ndarray,
    kernel_size: Tuple[int, int] = (99, 99),
    sigma: float = 30,
) -> np.ndarray:
    """Aplicar desenfoque gaussiano a región."""

    kx, ky = kernel_size
    if kx % 2 == 0:
        kx += 1
    if ky % 2 == 0:
        ky += 1
    kx = max(1, kx)
    ky = max(1, ky)
    return cv2.GaussianBlur(region, (kx, ky), sigma)


def pixelate_region(region: np.ndarray, pixel_size: int = 16) -> np.ndarray:
    """Pixelar región mediante escalado hacia abajo y hacia arriba."""

    h, w = region.shape[:2]
    if h == 0 or w == 0:
        return region

    w_small = max(1, w // pixel_size)
    h_small = max(1, h // pixel_size)

    temp = cv2.resize(region, (w_small, h_small), interpolation=cv2.INTER_LINEAR)
    return cv2.resize(temp, (w, h), interpolation=cv2.INTER_NEAREST)


def black_out_region(region: np.ndarray) -> np.ndarray:
    """Aplicar rectángulo negro a región."""

    return np.zeros_like(region)


def blur_faces(
    frame: np.ndarray,
    detections: List[Dict],
    blur_method: str = "gaussian",
    intensity: int = 99,
) -> np.ndarray:
    """Aplicar desenfoque a rostros de personas detectadas.

    Args:
        frame: Frame original.
        detections: Lista de detecciones con bboxes.
        blur_method: Método ('gaussian', 'median', 'pixelate', 'black').
        intensity: Intensidad del blur.

    Returns:
        Frame con rostros anonimizados.
    """

    anonymized = frame.copy()
    h, w = anonymized.shape[:2]

    for det in detections:
        bbox = det.get("bbox")
        if not bbox or len(bbox) != 4:
            continue

        # Si el método es 'cascade', intentamos detectar cara real
        if blur_method == "cascade":
             # Extraer ROI de la persona
             px1, py1, px2, py2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
             px1, px2 = max(0, px1), min(w, px2)
             py1, py2 = max(0, py1), min(h, py2)
             
             if px2 > px1 and py2 > py1:
                 person_roi = frame[py1:py2, px1:px2]
                 # Convertir a gris para cascade
                 gray_roi = cv2.cvtColor(person_roi, cv2.COLOR_BGR2GRAY)
                 
                 cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                 face_cascade = cv2.CascadeClassifier(cascade_path)
                 
                 # Detectar caras en el ROI de la persona
                 faces = face_cascade.detectMultiScale(gray_roi, scaleFactor=1.1, minNeighbors=5, minSize=(20, 20))
                 
                 if len(faces) > 0:
                     # Tomar la cara más grande encontrada
                     (fx, fy, fw, fh) = max(faces, key=lambda f: f[2] * f[3])
                     # Convertir coordenadas relativas a absolutas
                     fx1 = px1 + fx
                     fy1 = py1 + fy
                     fx2 = fx1 + fw
                     fy2 = fy1 + fh
                 else:
                     # Fallback a tercios si no detecta cara
                     fx1, fy1, fx2, fy2 = detect_face_region(bbox, method="thirds")
             else:
                 fx1, fy1, fx2, fy2 = detect_face_region(bbox, method="thirds")
        else:
            fx1, fy1, fx2, fy2 = detect_face_region(bbox, method="thirds")

        fx1 = max(0, min(w, fx1))
        fx2 = max(0, min(w, fx2))
        fy1 = max(0, min(h, fy1))
        fy2 = max(0, min(h, fy2))

        if fx2 <= fx1 or fy2 <= fy1:
            continue

        roi = anonymized[fy1:fy2, fx1:fx2]
        if roi.size == 0:
            continue

        if blur_method == "gaussian":
            k = intensity if intensity > 0 else 99
            processed = apply_gaussian_blur(roi, (k, k), sigma=30)
        elif blur_method == "median":
            k = intensity if intensity % 2 == 1 else intensity + 1
            k = max(3, k)
            processed = cv2.medianBlur(roi, k)
        elif blur_method == "pixelate":
            processed = pixelate_region(roi, pixel_size=max(4, intensity // 4))
        elif blur_method == "black":
            processed = black_out_region(roi)
        elif blur_method == "fisheye":
            processed = apply_fisheye_effect(roi)
        else:
            processed = apply_gaussian_blur(roi, (99, 99), sigma=30)

        anonymized[fy1:fy2, fx1:fx2] = processed

    return anonymized


def apply_fisheye_effect(region: np.ndarray, strength: float = 0.6) -> np.ndarray:
    """Aplicar efecto ojo de pez a una región de imagen.

    Args:
        region: ROI de imagen (BGR).
        strength: Intensidad del efecto (0.0-1.0 aprox.).

    Returns:
        Región con distorsión de ojo de pez.
    """

    h, w = region.shape[:2]
    if h == 0 or w == 0:
        return region

    # Coordenadas normalizadas centradas en (0, 0)
    y, x = np.indices((h, w), dtype=np.float32)
    cx, cy = w / 2.0, h / 2.0
    x = (x - cx) / cx
    y = (y - cy) / cy

    r = np.sqrt(x * x + y * y)

    # Distorsión radial tipo ojo de pez: r' = r^(1 + k)
    # strength controla cuánto se curva la imagen.
    k = float(max(0.0, strength))
    r_new = np.power(r, 1.0 + k)

    # Evitar divisiones por cero
    scale = np.divide(r_new, r, out=np.ones_like(r), where=r > 1e-6)
    x_new = x * scale
    y_new = y * scale

    map_x = (x_new * cx + cx).astype(np.float32)
    map_y = (y_new * cy + cy).astype(np.float32)

    distorted = cv2.remap(region, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return distorted
