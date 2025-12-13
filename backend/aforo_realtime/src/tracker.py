"""Tracker sencillo basado en IoU para estabilizar bounding boxes entre frames.

Asigna IDs persistentes a cada persona y suaviza el movimiento de los
bounding boxes para reducir parpadeos.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Any

import numpy as np


@dataclass
class Track:
    """Representa una pista (track) activa."""

    track_id: int
    bbox: List[float]  # [x1, y1, x2, y2]
    confidence: float
    hits: int = 1
    time_since_update: int = 0


class SimpleTracker:
    """Tracker multi-objeto muy ligero basado en IoU.

    No usa embeddings, solo proximidad espacial, suficiente para escenas de aforo
    donde las personas se mueven relativamente continuo.
    """

    def __init__(
        self,
        iou_threshold: float = 0.3,
        max_age: int = 5,
        min_hits: int = 1,
        smoothing: float = 0.5,
    ) -> None:
        self.iou_threshold = float(iou_threshold)
        self.max_age = int(max_age)
        self.min_hits = int(min_hits)
        self.smoothing = float(smoothing)

        self.tracks: List[Track] = []
        self._next_id: int = 1

    @staticmethod
    def _iou(b1: List[float], b2: List[float]) -> float:
        x1 = max(b1[0], b2[0])
        y1 = max(b1[1], b2[1])
        x2 = min(b1[2], b2[2])
        y2 = min(b1[3], b2[3])

        inter_w = max(0.0, x2 - x1)
        inter_h = max(0.0, y2 - y1)
        inter = inter_w * inter_h

        area1 = max(0.0, (b1[2] - b1[0]) * (b1[3] - b1[1]))
        area2 = max(0.0, (b2[2] - b2[0]) * (b2[3] - b2[1]))
        union = area1 + area2 - inter
        if union <= 0:
            return 0.0
        return float(inter / union)

    def _build_iou_matrix(self, dets: List[List[float]]) -> np.ndarray:
        if not self.tracks or not dets:
            return np.zeros((len(self.tracks), len(dets)), dtype=float)

        iou_mat = np.zeros((len(self.tracks), len(dets)), dtype=float)
        for i, tr in enumerate(self.tracks):
            for j, db in enumerate(dets):
                iou_mat[i, j] = self._iou(tr.bbox, db)
        return iou_mat

    def update(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Actualizar tracker con nuevas detecciones y devolver detecciones trackeadas.

        Cada detección devuelta incluirá una clave extra 'track_id'.
        Si en un frame no hay detecciones, se mantienen los tracks activos
        (hasta `max_age` frames) para evitar parpadeos bruscos.
        """

        if not detections:
            # Solo envejecer tracks
            for tr in self.tracks:
                tr.time_since_update += 1
            # Filtrar tracks expirados
            self.tracks = [t for t in self.tracks if t.time_since_update <= self.max_age]

            # Devolver cajas basadas en los tracks vivos (sin actualización nueva)
            tracked: List[Dict[str, Any]] = []
            for tr in self.tracks:
                if tr.hits < self.min_hits:
                    continue
                x1, y1, x2, y2 = map(int, tr.bbox)
                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)
                tracked.append(
                    {
                        "bbox": [x1, y1, x2, y2],
                        "confidence": tr.confidence,
                        "class": "person",
                        "center": [cx, cy],
                        "track_id": tr.track_id,
                    }
                )

            return tracked

        det_bboxes = [det["bbox"] for det in detections]
        det_confs = [float(det.get("confidence", 0.0)) for det in detections]

        iou_mat = self._build_iou_matrix(det_bboxes)

        # Asignación greedily por IoU máximo
        assigned_tracks = set()
        assigned_dets = set()

        if self.tracks:
            for _ in range(min(len(self.tracks), len(detections))):
                i, j = divmod(np.argmax(iou_mat), iou_mat.shape[1])
                if iou_mat[i, j] < self.iou_threshold:
                    break
                if i in assigned_tracks or j in assigned_dets:
                    iou_mat[i, j] = -1.0
                    continue

                # Actualizar track con suavizado
                tr = self.tracks[i]
                new_box = det_bboxes[j]
                sm = self.smoothing
                tr.bbox = [
                    float(tr.bbox[k] * (1 - sm) + new_box[k] * sm) for k in range(4)
                ]
                tr.confidence = float(det_confs[j])
                tr.hits += 1
                tr.time_since_update = 0

                assigned_tracks.add(i)
                assigned_dets.add(j)
                iou_mat[i, :] = -1.0
                iou_mat[:, j] = -1.0

        # Crear nuevos tracks para detecciones no asignadas
        for j, (bbox, conf) in enumerate(zip(det_bboxes, det_confs)):
            if j in assigned_dets:
                continue
            self.tracks.append(
                Track(track_id=self._next_id, bbox=list(map(float, bbox)), confidence=float(conf))
            )
            self._next_id += 1

        # Envejecer tracks no actualizados
        for idx, tr in enumerate(self.tracks):
            if idx not in assigned_tracks:
                tr.time_since_update += 1

        # Eliminar tracks muy antiguos
        self.tracks = [t for t in self.tracks if t.time_since_update <= self.max_age]

        # Construir detecciones trackeadas a partir de tracks activos
        tracked: List[Dict[str, Any]] = []
        for tr in self.tracks:
            if tr.hits < self.min_hits:
                continue
            x1, y1, x2, y2 = map(int, tr.bbox)
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            tracked.append(
                {
                    "bbox": [x1, y1, x2, y2],
                    "confidence": tr.confidence,
                    "class": "person",
                    "center": [cx, cy],
                    "track_id": tr.track_id,
                }
            )

        return tracked
