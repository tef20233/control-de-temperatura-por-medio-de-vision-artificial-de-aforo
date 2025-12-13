"""Backend de detección usando Roboflow Inference SDK.

Permite usar un Workflow remoto (por ejemplo `find-people`) como fuente
alternativa de detecciones de personas.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np

from .utils import print_error, print_warning


@dataclass
class RoboflowConfig:
    """Configuración necesaria para ejecutar un Workflow de Roboflow."""

    api_url: str = "https://serverless.roboflow.com"
    api_key: Optional[str] = None
    workspace_name: str = "proyecto-aforo-2"
    workflow_id: str = "find-people"
    use_cache: bool = True


class RoboflowBackend:
    """Cliente ligero para ejecutar un Workflow de Roboflow por frame.

    Se espera que el Workflow devuelva detecciones de personas en formato de
    object detection estándar de Roboflow (predictions con x, y, width, height).
    """

    def __init__(self, config: RoboflowConfig) -> None:
        self.config = config

        api_key = self.config.api_key or os.getenv("ROBOFLOW_API_KEY")
        if not api_key:
            raise RuntimeError(
                "No se encontró API Key de Roboflow. Configura ROBOFLOW_API_KEY "
                "en variables de entorno o pásala explícitamente."
            )

        try:
            from inference_sdk import InferenceHTTPClient  # type: ignore[import]
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                "No se pudo importar inference-sdk. Ejecuta 'pip install inference-sdk' "
                "en tu entorno backend/venv."
            ) from exc

        self._client = InferenceHTTPClient(api_url=self.config.api_url, api_key=api_key)

    # ---------------------------------------------------------------------
    # Inferencia
    # ---------------------------------------------------------------------

    def infer(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Ejecutar el Workflow de Roboflow sobre un frame.

        Args:
            frame: Imagen en formato np.ndarray BGR (como viene de OpenCV).

        Returns:
            Lista de detecciones con claves: bbox, confidence, class, center.
        """

        try:
            result: Dict[str, Any] = self._client.run_workflow(
                workspace_name=self.config.workspace_name,
                workflow_id=self.config.workflow_id,
                images={"image": frame},
                use_cache=self.config.use_cache,
            )
        except Exception as exc:  # noqa: BLE001
            print_error(f"Error al llamar al Workflow de Roboflow: {exc}")
            return []

        preds = self._extract_predictions(result)
        if not preds:
            return []

        h, w = frame.shape[:2]
        detections: List[Dict[str, Any]] = []

        for pred in preds:
            # Formato estándar Roboflow: x,y centro + width,height
            x = float(pred.get("x", 0.0))
            y = float(pred.get("y", 0.0))
            pw = float(pred.get("width", 0.0))
            ph = float(pred.get("height", 0.0))
            conf = float(pred.get("confidence", 0.0))
            cls_name = str(pred.get("class", "person"))

            # Solo clase persona si viene etiquetada
            if cls_name not in {"person", "persona", "people"}:
                continue

            x1 = int(max(0, min(w - 1, x - pw / 2.0)))
            y1 = int(max(0, min(h - 1, y - ph / 2.0)))
            x2 = int(max(0, min(w - 1, x + pw / 2.0)))
            y2 = int(max(0, min(h - 1, y + ph / 2.0)))
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)

            detections.append(
                {
                    "bbox": [x1, y1, x2, y2],
                    "confidence": conf,
                    "class": "person",
                    "center": [cx, cy],
                }
            )

        return detections

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_predictions(result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Intentar extraer la lista de predicciones del resultado del Workflow.

        El formato puede variar según cómo se haya definido el Workflow. Se
        intentan varios patrones comunes:

        - result["predictions"]
        - result["outputs"][<alguna_clave>]["predictions"]
        - result["outputs"]["predictions"]
        """

        if not isinstance(result, dict):
            print_warning("Respuesta de Roboflow no es un diccionario.")
            return []

        # Caso simple: objeto detección directo
        if "predictions" in result and isinstance(result["predictions"], list):
            return result["predictions"]

        outputs = result.get("outputs")
        if isinstance(outputs, dict):
            # Buscar clave con 'predictions'
            if "predictions" in outputs and isinstance(outputs["predictions"], list):
                return outputs["predictions"]

            for value in outputs.values():
                if isinstance(value, dict) and isinstance(value.get("predictions"), list):
                    return value["predictions"]

        print_warning("No se encontraron 'predictions' en la respuesta de Roboflow.")
        return []
