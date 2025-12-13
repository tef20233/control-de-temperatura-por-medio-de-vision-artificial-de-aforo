"""Funciones para visualización de detecciones y métricas."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Tuple

import cv2
import numpy as np


def get_bbox_color(confidence: float) -> Tuple[int, int, int]:
    """Obtener color BGR según nivel de confianza.

    Pensado para configuraciones de alta sensibilidad (conf global ≈ 0.25–0.35):

    - Verde para conf >= 0.5  → detección muy confiable.
    - Amarillo para 0.3 <= conf < 0.5 → detección decente pero no perfecta.
    - Rojo para conf < 0.3 → detección muy baja, potencialmente dudosa.
    """

    if confidence >= 0.5:
        return 0, 255, 0
    if confidence >= 0.3:
        return 0, 255, 255
    return 0, 0, 255


def draw_bounding_boxes(
    frame: np.ndarray,
    detections: List[Dict],
    thickness: int = 2,
    show_confidence: bool = True,
    font_scale: float = 0.6,
) -> np.ndarray:
    """Dibujar bounding boxes coloreados por confianza.

    Args:
        frame: Frame de OpenCV (BGR).
        detections: Lista de detecciones.
        thickness: Grosor de líneas.
        show_confidence: Mostrar score sobre bbox.
        font_scale: Escala de texto.

    Returns:
        Frame anotado.
    """

    annotated = frame.copy()
    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        conf = float(det.get("confidence", 0.0))
        color = get_bbox_color(conf)

        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)

        if show_confidence:
            label = f"{conf:.2f}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1)
            y_label = max(y1 - 5, th + 5)
            cv2.rectangle(annotated, (x1, y_label - th - 4), (x1 + tw + 4, y_label + 2), color, -1)
            cv2.putText(
                annotated,
                label,
                (x1 + 2, y_label - 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                (0, 0, 0),
                1,
                cv2.LINE_AA,
            )

    return annotated


def draw_info_panel(
    frame: np.ndarray,
    people_count: int,
    fps: float,
    config_name: str,
    model_name: str,
    position: str = "top",
) -> np.ndarray:
    """Dibujar panel de información principal.

    Muestra:
    - Conteo de personas.
    - FPS actual.
    - Configuración activa.
    - Modelo en uso.
    - Resolución de procesamiento.
    - Timestamp.
    """

    annotated = frame.copy()
    h, w = annotated.shape[:2]

    lines = [
        f"Personas: {people_count}",
        f"FPS: {fps:.1f}",
        f"Config: {config_name}",
        f"Modelo: {model_name}",
        f"Resolución: {w}x{h}",
        f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    thickness = 2
    line_height = 22

    panel_width = max(cv2.getTextSize(l, font, font_scale, thickness)[0][0] for l in lines) + 20
    panel_height = line_height * len(lines) + 20

    if position == "bottom":
        x1, y1 = 10, h - panel_height - 10
    else:  # "top"
        x1, y1 = 10, 10

    x2, y2 = x1 + panel_width, y1 + panel_height

    cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 0), -1)
    cv2.addWeighted(annotated[y1:y2, x1:x2], 0.6, frame[y1:y2, x1:x2], 0.4, 0, annotated[y1:y2, x1:x2])

    y_text = y1 + 20
    for line in lines:
        cv2.putText(annotated, line, (x1 + 10, y_text), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
        y_text += line_height

    return annotated


def draw_statistics_panel(
    frame: np.ndarray,
    statistics: Dict,
    position: str = "bottom-right",
) -> np.ndarray:
    """Dibujar panel de estadísticas secundario."""

    annotated = frame.copy()
    h, w = annotated.shape[:2]

    stats_lines = [
        f"Frames: {statistics.get('total_frames', 0)}",
        f"Avg aforo: {statistics.get('avg_people_per_frame', 0.0):.1f}",
        f"Max aforo: {statistics.get('max_people', 0)}",
        f"Min aforo: {statistics.get('min_people', 0)}",
        f"FPS prom: {statistics.get('avg_fps', 0.0):.1f}",
        f"Dispositivo: {statistics.get('device', 'cpu')}",
    ]

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    thickness = 1
    line_height = 18

    panel_width = max(cv2.getTextSize(l, font, font_scale, thickness)[0][0] for l in stats_lines) + 16
    panel_height = line_height * len(stats_lines) + 16

    if position == "bottom-right":
        x1, y1 = w - panel_width - 10, h - panel_height - 10
    elif position == "top-right":
        x1, y1 = w - panel_width - 10, 10
    elif position == "top-left":
        x1, y1 = 10, 10
    else:  # bottom-left
        x1, y1 = 10, h - panel_height - 10

    x2, y2 = x1 + panel_width, y1 + panel_height

    cv2.rectangle(annotated, (x1, y1), (x2, y2), (30, 30, 30), -1)

    y_text = y1 + 20
    for line in stats_lines:
        cv2.putText(annotated, line, (x1 + 8, y_text), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
        y_text += line_height

    return annotated


def draw_fps_bar(
    frame: np.ndarray,
    fps: float,
    target_fps: int = 30,
    position: str = "bottom-left",
) -> np.ndarray:
    """Dibujar barra visual de FPS con código de colores."""

    annotated = frame.copy()
    h, w = annotated.shape[:2]

    bar_width = int(w * 0.25)
    bar_height = 20

    if position == "bottom-left":
        x1, y1 = 10, h - bar_height - 10
    elif position == "bottom-right":
        x1, y1 = w - bar_width - 10, h - bar_height - 10
    elif position == "top-right":
        x1, y1 = w - bar_width - 10, 10
    else:  # top-left
        x1, y1 = 10, 10

    x2, y2 = x1 + bar_width, y1 + bar_height

    cv2.rectangle(annotated, (x1, y1), (x2, y2), (50, 50, 50), -1)

    ratio = max(0.0, min(fps / float(target_fps if target_fps > 0 else 30), 1.0))
    fill_width = int(bar_width * ratio)

    if fps >= 30:
        color = (0, 255, 0)
    elif fps >= 20:
        color = (0, 255, 255)
    else:
        color = (0, 0, 255)

    cv2.rectangle(annotated, (x1, y1), (x1 + fill_width, y2), color, -1)

    label = f"FPS: {fps:.1f}"
    cv2.putText(
        annotated,
        label,
        (x1 + 5, y1 - 5),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )

    return annotated


def create_history_graph(
    history: List[int],
    width: int = 400,
    height: int = 100,
    title: str = "Aforo Histórico",
) -> np.ndarray:
    """Crear gráfica simple del historial de aforo."""

    canvas = np.zeros((height, width, 3), dtype=np.uint8)

    if not history:
        cv2.putText(canvas, "Sin datos", (10, height // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        return canvas

    max_val = max(history)
    max_val = max(max_val, 1)

    step_x = max(1, width // max(1, len(history) - 1))

    points = []
    for i, val in enumerate(history[-(width // step_x + 1) :]):
        x = i * step_x
        y = height - int((val / max_val) * (height - 20)) - 10
        points.append((x, y))

    if len(points) > 1:
        for i in range(1, len(points)):
            cv2.line(canvas, points[i - 1], points[i], (0, 255, 0), 2)

    cv2.putText(canvas, title, (10, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    return canvas
