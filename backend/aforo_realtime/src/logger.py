"""Sistema de logging para exportar métricas y estadísticas."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from statistics import mean, pstdev
from typing import Dict, List, Optional, Any


@dataclass
class FrameLog:
    """Estructura de datos para un frame logueado."""

    timestamp: datetime
    frame_id: int
    people_count: int
    fps: float
    avg_confidence: float
    detections: List[Dict[str, Any]] = field(default_factory=list)


class SessionLogger:
    """Logger para guardar métricas de sesión en CSV/JSON."""

    def __init__(
        self,
        output_dir: str = "outputs/logs",
        format: str = "both",
        session_name: Optional[str] = None,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.format = format
        now = datetime.now()
        timestamp_str = now.strftime("%Y%m%d_%H%M%S")
        self.session_name = session_name or f"aforo_session_{timestamp_str}"

        self.start_time: datetime = now
        self.end_time: Optional[datetime] = None

        self._frames: List[FrameLog] = []

    def log_frame(
        self,
        frame_id: int,
        people_count: int,
        fps: float,
        detections: List[Dict[str, Any]],
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Registrar información de un frame."""

        ts = timestamp or datetime.now()
        confidences = [float(d.get("confidence", 0.0)) for d in detections] or [0.0]
        avg_conf = float(mean(confidences))

        self._frames.append(
            FrameLog(
                timestamp=ts,
                frame_id=frame_id,
                people_count=people_count,
                fps=fps,
                avg_confidence=avg_conf,
                detections=detections,
            )
        )

    # ----------------- Guardado de archivos -----------------

    def _base_path(self) -> Path:
        return self.output_dir / self.session_name

    def save_csv(self) -> str:
        """Guardar logs en formato CSV sencillo (un registro por frame)."""

        path = self._base_path().with_suffix(".csv")
        fieldnames = [
            "timestamp",
            "frame_id",
            "people_count",
            "fps",
            "avg_confidence",
        ]

        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for fl in self._frames:
                writer.writerow(
                    {
                        "timestamp": fl.timestamp.isoformat(),
                        "frame_id": fl.frame_id,
                        "people_count": fl.people_count,
                        "fps": f"{fl.fps:.4f}",
                        "avg_confidence": f"{fl.avg_confidence:.4f}",
                    }
                )

        return str(path)

    def save_json(self) -> str:
        """Guardar logs en formato JSON detallado."""

        self.end_time = self.end_time or datetime.now()
        stats = self.get_statistics()

        path = self._base_path().with_suffix(".json")
        data = {
            "session_info": {
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "total_frames": stats.get("total_frames", 0),
                "total_duration": f"{stats.get('total_duration', 0.0):.3f}s",
                "avg_fps": stats.get("avg_fps", 0.0),
            },
            "statistics": {
                "avg_people_count": stats.get("avg_people_per_frame", 0.0),
                "max_people_count": stats.get("max_people", 0),
                "min_people_count": stats.get("min_people", 0),
                "std_deviation": stats.get("std_people", 0.0),
            },
            "frames": [
                {
                    "frame_id": fl.frame_id,
                    "timestamp": fl.timestamp.isoformat(),
                    "people_count": fl.people_count,
                    "fps": fl.fps,
                    "detections": fl.detections,
                }
                for fl in self._frames
            ],
        }

        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return str(path)

    def save_summary(self) -> str:
        """Guardar resumen de sesión en texto plano con estadísticas básicas."""

        self.end_time = self.end_time or datetime.now()
        stats = self.get_statistics()

        path = self._base_path().with_name(f"session_summary_{self._base_path().stem}").with_suffix(".txt")

        lines = [
            "# Resumen de sesión de aforo",
            f"Inicio: {self.start_time.isoformat()}",
            f"Fin: {self.end_time.isoformat() if self.end_time else 'N/A'}",
            f"Duración total (s): {stats.get('total_duration', 0.0):.3f}",
            f"Frames procesados: {stats.get('total_frames', 0)}",
            f"FPS promedio: {stats.get('avg_fps', 0.0):.2f}",
            f"Aforo promedio: {stats.get('avg_people_per_frame', 0.0):.2f}",
            f"Aforo máximo: {stats.get('max_people', 0)}",
            f"Aforo mínimo: {stats.get('min_people', 0)}",
            f"Desviación estándar de aforo: {stats.get('std_people', 0.0):.2f}",
            "",
            "Histograma ASCII aproximado (10 bins):",
        ]

        # Histograma ASCII simple
        counts = [fl.people_count for fl in self._frames]
        if counts:
            min_c, max_c = min(counts), max(counts)
            span = max(1, max_c - min_c)
            bins = 10
            bin_size = span / bins
            hist = [0] * bins
            for c in counts:
                idx = min(bins - 1, int((c - min_c) / bin_size))
                hist[idx] += 1

            for i, val in enumerate(hist):
                low = min_c + i * bin_size
                high = low + bin_size
                bar = "#" * max(1, int(40 * (val / max(1, len(counts)))))
                lines.append(f"[{low:5.1f} - {high:5.1f}]: {bar} ({val})")
        else:
            lines.append("Sin datos suficientes para histograma.")

        with path.open("w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return str(path)

    # ----------------- Estadísticas en memoria -----------------

    def get_statistics(self) -> Dict[str, Any]:
        """Calcular estadísticas agregadas de la sesión."""

        if not self._frames:
            return {
                "total_frames": 0,
                "total_duration": 0.0,
                "avg_fps": 0.0,
                "avg_people_per_frame": 0.0,
                "max_people": 0,
                "min_people": 0,
                "std_people": 0.0,
            }

        total_frames = len(self._frames)
        # Duración aproximada basada en timestamps
        t0 = self._frames[0].timestamp
        t1 = self._frames[-1].timestamp
        total_duration = max(0.0, (t1 - t0).total_seconds())

        fps_values = [fl.fps for fl in self._frames]
        people_values = [fl.people_count for fl in self._frames]

        return {
            "total_frames": total_frames,
            "total_duration": total_duration,
            "avg_fps": float(mean(fps_values)) if fps_values else 0.0,
            "avg_people_per_frame": float(mean(people_values)) if people_values else 0.0,
            "max_people": max(people_values) if people_values else 0,
            "min_people": min(people_values) if people_values else 0,
            "std_people": float(pstdev(people_values)) if len(people_values) > 1 else 0.0,
        }

    def close(self) -> None:
        """Cerrar logger y guardar archivos finales según formato configurado."""

        self.end_time = self.end_time or datetime.now()
        fmt = self.format.lower()
        if fmt in {"csv", "both"}:
            self.save_csv()
        if fmt in {"json", "both"}:
            self.save_json()
        # Resumen de texto siempre
        self.save_summary()
