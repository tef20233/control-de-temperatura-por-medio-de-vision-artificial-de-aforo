"""Funciones utilitarias generales para el sistema de aforo."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ProjectPaths:
    """Rutas base útiles dentro del proyecto CLI.

    Se asume que este módulo vive en `backend/aforo_realtime/src/utils.py`.
    """

    base_dir: Path
    backend_dir: Path
    models_dir: Path
    outputs_dir: Path


def get_project_paths() -> ProjectPaths:
    """Calcular rutas base a partir de este archivo.

    Se asume estructura:

    app_aforo/
      backend/
        aforo_realtime/
          src/utils.py (este archivo)
        models/  ← aquí están los modelos YOLO

    Returns:
        ProjectPaths con rutas resueltas.
    """

    src_dir = Path(__file__).resolve().parent  # .../backend/aforo_realtime/src
    base_dir = src_dir.parent  # .../backend/aforo_realtime
    backend_dir = base_dir.parent  # .../backend
    models_dir = backend_dir / "models"  # .../backend/models
    outputs_dir = base_dir / "outputs"   # .../backend/aforo_realtime/outputs
    return ProjectPaths(
        base_dir=base_dir,
        backend_dir=backend_dir,
        models_dir=models_dir,
        outputs_dir=outputs_dir,
    )


def resolve_model_path(model_path: Optional[str]) -> Path:
    """Resolver la ruta al modelo.

    Lógica:
    - Si `model_path` es absoluta o relativa existente → usarla.
    - Si no existe y el nombre es solo archivo, buscar en `backend/models`.

    Args:
        model_path: Ruta proporcionada por CLI (puede ser None).

    Returns:
        Ruta resuelta (puede no existir, se valida más adelante).
    """

    paths = get_project_paths()

    if model_path is None:
        # Por defecto intentamos yolov8s_custom.pt y caemos a yolov8s.pt
        preferred = paths.models_dir / "yolov8s_custom.pt"
        fallback = paths.models_dir / "yolov8s.pt"
        return preferred if preferred.exists() else fallback

    p = Path(model_path)
    if p.is_file():
        return p.resolve()

    # Si no existe aún, intentar dentro de backend/models usando solo el nombre
    name = p.name
    candidate = paths.models_dir / name
    return candidate


def is_camera_source(source: str) -> bool:
    """Indicar si `source` representa un índice de cámara.

    Args:
        source: Cadena pasada por CLI.

    Returns:
        True si es un entero no negativo.
    """

    return source.isdigit()


def print_warning(msg: str) -> None:
    """Imprimir advertencia en stderr (prefijo estándar)."""

    sys.stderr.write(f"[WARNING] {msg}\n")


def print_error(msg: str) -> None:
    """Imprimir error en stderr (prefijo estándar)."""

    sys.stderr.write(f"[ERROR] {msg}\n")


def print_info(msg: str) -> None:
    """Imprimir información en stdout (prefijo estándar)."""

    sys.stdout.write(f"[INFO] {msg}\n")
