"""Gestor de configuración para el sistema CLI de aforo en tiempo real."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import yaml


class ConfigManager:
    """Clase para cargar y gestionar configuraciones YAML.

    Se encarga de:
    - Cargar `default_config.yaml`.
    - Exponer presets (ultra_fast, fast, balanced, quality).
    - Exponer secciones de visualización, logging, privacidad y guardado.
    """

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or Path(__file__).resolve().parents[1]
        self.config_path = self.base_dir / "config" / "default_config.yaml"
        if not self.config_path.exists():
            raise FileNotFoundError(f"No se encontró archivo de configuración: {self.config_path}")

        self._config = self._load_yaml(self.config_path)

    @staticmethod
    def _load_yaml(path: Path) -> Dict[str, Any]:
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    @property
    def raw(self) -> Dict[str, Any]:
        """Devolver el dict completo de configuración."""

        return self._config

    @lru_cache(maxsize=16)
    def get_preset(self, name: str) -> Dict[str, Any]:
        """Obtener un preset de configuración por nombre.

        Args:
            name: Nombre del preset (ultra_fast, fast, balanced, quality).

        Returns:
            Dict con parámetros del preset.

        Raises:
            ValueError: Si el preset no existe.
        """

        presets = self._config.get("presets", {})
        if name not in presets:
            valid = ", ".join(presets.keys()) or "<ninguno>"
            raise ValueError(f"Preset '{name}' no válido. Opciones: {valid}")
        return presets[name]

    def get_visualization_config(self) -> Dict[str, Any]:
        """Config de visualización (bboxes, paneles, colores)."""

        return self._config.get("visualization", {})

    def get_logging_config(self) -> Dict[str, Any]:
        """Config de logging (formatos, rutas)."""

        return self._config.get("logging", {})

    def get_privacy_config(self) -> Dict[str, Any]:
        """Config de privacidad/anonimización."""

        return self._config.get("privacy", {})

    def get_save_config(self) -> Dict[str, Any]:
        """Config de guardado de videos."""

        return self._config.get("save", {})

    def get_screenshots_config(self) -> Dict[str, Any]:
        """Config de guardado de screenshots."""

        return self._config.get("screenshots", {})

    def get_history_config(self) -> Dict[str, Any]:
        """Config del historial de aforo."""

        return self._config.get("history", {})
