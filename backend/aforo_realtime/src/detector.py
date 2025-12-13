"""Detector de personas en tiempo real usando modelos YOLO."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple, List, Optional, Any

import cv2
import numpy as np
import torch
from ultralytics import YOLO

from .config_manager import ConfigManager
from .logger import SessionLogger
from .privacy import blur_faces
from . import visualizer
from .utils import (
    get_project_paths,
    resolve_model_path,
    is_camera_source,
    print_error,
    print_info,
    print_warning,
)
from .tracker import SimpleTracker
from .roboflow_backend import RoboflowBackend, RoboflowConfig


@dataclass
class DetectorStats:
    """Estructura para estadísticas de sesión."""

    total_frames: int = 0
    total_detections: int = 0
    avg_people_per_frame: float = 0.0
    avg_fps: float = 0.0
    avg_inference_time: float = 0.0
    max_people: int = 0
    min_people: int = 0


class RealtimeDetector:
    """Detector de personas en tiempo real usando YOLO.

    Características:
    - Carga modelos YOLO (.pt, .engine).
    - Procesa frames individuales o streams de video.
    - Configurable con presets de velocidad/calidad.
    - Logging automático de métricas.
    - Anonimización facial opcional.
    """

    def __init__(
        self,
        model_path: str = "models/yolov8s.pt",
        config_preset: str = "balanced",
        device: str = "auto",
        half: bool = True,
        anonymize: bool = False,
        fisheye: bool = False,
        log: bool = True,
        log_format: str = "both",
        imgsz_override: Optional[int] = None,
        conf_override: Optional[float] = None,
        iou_override: Optional[float] = None,
        max_det_override: Optional[int] = None,
        thickness: int = 2,
        font_scale: float = 1.0,
        show_confidence: bool = True,
        ensemble_model_paths: Optional[List[str]] = None,
        use_roboflow: bool = False,
        roboflow_api_url: Optional[str] = None,
        roboflow_workspace: Optional[str] = None,
        roboflow_workflow: Optional[str] = None,
    ) -> None:
        self.paths = get_project_paths()
        self.config_manager = ConfigManager(base_dir=self.paths.base_dir)

        self.config_preset = config_preset
        self._cfg = self.load_config(config_preset)

        # Overrides desde CLI
        if imgsz_override is not None:
            self._cfg["imgsz"] = int(imgsz_override)
        if conf_override is not None:
            self._cfg["conf_threshold"] = float(conf_override)
        if iou_override is not None:
            self._cfg["iou_threshold"] = float(iou_override)
        if max_det_override is not None:
            self._cfg["max_det"] = int(max_det_override)

        self.imgsz: int = int(self._cfg["imgsz"])
        self.conf_threshold: float = float(self._cfg["conf_threshold"])
        self.iou_threshold: float = float(self._cfg["iou_threshold"])
        self.max_det: int = int(self._cfg["max_det"])
        self.target_fps: int = int(self._cfg.get("target_fps", 30))

        # Visualización
        self.thickness = thickness
        self.font_scale = font_scale
        self.show_confidence = show_confidence

        # Estado de dispositivo
        self.device_str = device
        self.device = self._select_device(device)
        
        # Verificar soporte de FP16 (Half Precision)
        # GTX 1050 Ti (Compute 6.1) y anteriores no tienen Tensor Cores para FP16 eficiente
        if half and self.device.type == "cuda":
            try:
                cap = torch.cuda.get_device_capability(self.device)
                if cap[0] < 7:
                    print_warning(f"GPU con Compute Capability {cap[0]}.{cap[1]} detectada (GTX 10xx). Desactivando FP16 para mejor rendimiento.")
                    self.half = False
                else:
                    self.half = True
            except Exception:
                self.half = True
        else:
            self.half = False

        self.anonymize = anonymize
        self.fisheye = fisheye
        
        # Cargar configuración de privacidad
        privacy_cfg = self.config_manager.get_privacy_config()
        self.blur_method = privacy_cfg.get("blur_method", "gaussian")

        # Logging
        logging_cfg = self.config_manager.get_logging_config()
        if log is None:
            log = bool(logging_cfg.get("enabled", True))
        self.log_enabled = log
        self.log_format = log_format or logging_cfg.get("format", "both")

        logs_dir = logging_cfg.get("output_dir", "outputs/logs")
        logs_path = (self.paths.base_dir / logs_dir).resolve()
        self.logger: Optional[SessionLogger] = SessionLogger(
            output_dir=str(logs_path), format=self.log_format
        ) if self.log_enabled else None

        # Estadísticas
        history_cfg = self.config_manager.get_history_config()
        self.history_max_len = int(history_cfg.get("max_length", 100))
        self.people_history: deque[int] = deque(maxlen=self.history_max_len)
        self.fps_history: deque[float] = deque(maxlen=self.history_max_len)
        self.inference_times: deque[float] = deque(maxlen=self.history_max_len)

        self.total_frames: int = 0
        self.total_detections: int = 0
        self.max_people: int = 0
        self.min_people: int = 0

        self._last_frame_time: Optional[float] = None

        # Tracker sencillo para estabilizar bounding boxes entre frames
        # Parametrización ajustada para mayor estabilidad visual:
        # - max_age más alto: mantiene tracks varios frames aunque se pierda detección puntual.
        # - smoothing alto: el bbox se mueve suavizado, no "baila" frame a frame.
        self.tracker: Optional[SimpleTracker] = SimpleTracker(
            iou_threshold=0.35,
            max_age=10,
            min_hits=3,
            smoothing=0.8,
        )

        # Backend Roboflow opcional
        self.use_roboflow = use_roboflow
        self.roboflow_backend: Optional[RoboflowBackend] = None
        if self.use_roboflow:
            rf_cfg = RoboflowConfig(
                api_url=roboflow_api_url or "https://serverless.roboflow.com",
                workspace_name=roboflow_workspace or "proyecto-aforo-2",
                workflow_id=roboflow_workflow or "find-people",
                use_cache=True,
            )
            try:
                self.roboflow_backend = RoboflowBackend(rf_cfg)
            except RuntimeError as exc:
                print_error(str(exc))
                print_warning("Desactivando backend Roboflow, continuando con modelos locales YOLO")
                self.use_roboflow = False

        # Modelos (ensemble opcional)
        self.models: List[YOLO] = []
        self.model: Optional[YOLO] = None  # alias al primer modelo para compatibilidad
        self.model_path = str(resolve_model_path(model_path))
        self.model_name = Path(self.model_path).name
        self.load_model(self.model_path)

        # Cargar modelos adicionales para ensemble (si se proporcionan)
        self.ensemble_model_paths = ensemble_model_paths or []
        for extra_path in self.ensemble_model_paths:
            extra_resolved = str(resolve_model_path(extra_path))
            if extra_resolved == self.model_path:
                continue
            self.load_model(extra_resolved)

    # ----------------- Carga de modelo y config -----------------

    def _select_device(self, device: str) -> torch.device:
        """Seleccionar dispositivo según string de usuario."""

        if device == "auto":
            if torch.cuda.is_available():
                print_info("CUDA disponible, usando GPU 0")
                return torch.device("cuda:0")
            print_warning("CUDA no disponible, usando CPU")
            return torch.device("cpu")

        if device == "cpu":
            return torch.device("cpu")

        if device.isdigit():
            idx = int(device)
            if torch.cuda.is_available() and idx < torch.cuda.device_count():
                return torch.device(f"cuda:{idx}")
            print_warning("Índice de GPU no válido o CUDA no disponible, usando CPU")
            return torch.device("cpu")

        # Intentar usar string avanzado (ej. "cuda:1")
        try:
            dev = torch.device(device)
            if dev.type == "cuda" and not torch.cuda.is_available():
                print_warning("Se pidió CUDA pero no está disponible, usando CPU")
                return torch.device("cpu")
            return dev
        except Exception:
            print_warning(f"Dispositivo '{device}' no reconocido, usando CPU")
            return torch.device("cpu")

    def load_model(self, model_path: str) -> None:
        """Cargar modelo YOLO desde archivo.

        Args:
            model_path: Ruta al archivo .pt o .engine.
        """

        p = Path(model_path)
        
        # Si no existe, verificamos si es descargable
        model_to_load = str(p)
        if not p.exists():
            if p.suffix.lower() == ".pt" and "yolo" in p.name.lower():
                # Pasamos solo el nombre (ej. yolov11l.pt) para que Ultralytics lo busque/descargue
                model_to_load = p.name
                print_info(f"Modelo no encontrado en disco, intentando descarga automática: {model_to_load}")
            else:
                print_error(f"Modelo no encontrado en {p}")
                available = list(self.paths.models_dir.glob("*.pt"))
                if available:
                    print_info("Modelos disponibles en backend/models:")
                    for m in available:
                        print_info(f"  - {m.name}")
                raise FileNotFoundError(f"Modelo no encontrado: {p}")

        if p.suffix.lower() not in {".pt", ".engine"} and not (model_to_load.endswith(".pt") or model_to_load.endswith(".engine")):
             raise ValueError(f"Formato de modelo no soportado: {p.suffix}. Use .pt o .engine")

        print_info(f"Cargando modelo YOLO: {model_to_load} en dispositivo {self.device} (half={self.half})...")

        try:
            model = YOLO(model_to_load)
        except Exception as exc:  # noqa: BLE001
            print_error(f"Error al cargar el modelo: {exc}")
            raise

        # Registrar modelo en la lista de modelos del detector (para ensemble).
        self.models.append(model)
        if self.model is None:
            # Alias al primer modelo cargado para compatibilidad con código existente.
            self.model = model

        # Ultralytics maneja half en tiempo de inferencia; no forzamos .half() aquí.
        print_info(f"Modelo cargado correctamente: {p.name}")

    def load_config(self, preset: str) -> Dict[str, Any]:
        """Cargar configuración desde preset."""

        cfg = self.config_manager.get_preset(preset)
        return dict(cfg)

    def get_models_info(self) -> Dict[str, Any]:
        """Obtener información de los modelos cargados."""
        models_list = []
        for i, model in enumerate(self.models):
            # Obtener nombre del modelo si es posible
            name = getattr(model, 'pt_path', f"model_{i}")
            if hasattr(model, 'ckpt_path'):
                name = Path(model.ckpt_path).name
            
            # Obtener parametros aproximados
            params = "Unknown"
            if hasattr(model, 'info'):
                 # Intentar obtener info si está disponible
                 pass
            
            models_list.append({
                "name": str(name),
                "version": "v11" if "11" in str(name) else "v8",
                "parameters": params,
                "device": str(self.device)
            })
            
        return {"models": models_list}

    # ----------------- Operaciones sobre frames -----------------

    def detect_frame(
        self,
        frame: np.ndarray,
        return_annotated: bool = True,
    ) -> Tuple[np.ndarray, List[Dict[str, Any]], float]:
        """Detectar personas en un frame individual."""

        orig_h, orig_w = frame.shape[:2]
        t0 = time.time()
        # Si está habilitado el backend Roboflow, usarlo como fuente de detecciones
        if self.use_roboflow and self.roboflow_backend is not None:
            detections = self.roboflow_backend.infer(frame)
            inference_time = time.time() - t0
            self.inference_times.append(inference_time)
        else:
            if not self.models:
                raise RuntimeError("Modelos no cargados")

            # Ejecutar todos los modelos del ensemble y combinar sus salidas
            all_boxes: List[List[float]] = []  # [x1, y1, x2, y2]
            all_confs: List[float] = []

            for model in self.models:
                try:
                    results = model(
                        frame,
                        imgsz=self.imgsz,
                        conf=self.conf_threshold,
                        iou=self.iou_threshold,
                        device=str(self.device),
                        half=self.half,
                        max_det=self.max_det,
                        classes=[0],  # solo persona
                        verbose=False,
                    )
                except torch.cuda.OutOfMemoryError:  # type: ignore[attr-defined]
                    print_warning("CUDA Out Of Memory, cambiando a CPU")
                    torch.cuda.empty_cache()
                    self.device = torch.device("cpu")
                    self.half = False
                    results = model(
                        frame,
                        imgsz=self.imgsz,
                        conf=self.conf_threshold,
                        iou=self.iou_threshold,
                        device="cpu",
                        half=False,
                        max_det=self.max_det,
                        classes=[0],
                        verbose=False,
                    )

                res = results[0]
                if res.boxes is not None and len(res.boxes) > 0:  # type: ignore[truthy-function]
                    xyxy = res.boxes.xyxy.cpu().numpy()
                    confs = res.boxes.conf.cpu().numpy()

                    for (x1, y1, x2, y2), conf in zip(xyxy, confs):
                        all_boxes.append([float(x1), float(y1), float(x2), float(y2)])
                        all_confs.append(float(conf))

            inference_time = time.time() - t0
            self.inference_times.append(inference_time)

            # NMS global con consenso entre modelos para evitar duplicados y reducir falsos positivos
            detections = []
            if all_boxes:
                boxes_np = np.array(all_boxes, dtype=float)
                confs_np = np.array(all_confs, dtype=float)

                num_boxes = boxes_np.shape[0]
                used = np.zeros(num_boxes, dtype=bool)

                # En ensemble, exigir al menos 2 "votos" (modelos de acuerdo) por detección.
                # Si solo hay un modelo, min_votes = 1 (comportamiento normal).
                min_votes = 2 if len(self.models) > 1 else 1

                # IOU para agrupar cajas del ensemble (más estricto que el NMS interno del modelo)
                ensemble_iou = max(0.4, float(self.iou_threshold))

                # Ordenar por confianza descendente
                order = confs_np.argsort()[::-1]

                for idx in order:
                    if used[idx]:
                        continue

                    # Crear un grupo (cluster) de cajas que se solapan con esta
                    base_box = boxes_np[idx]
                    cluster_idxs: List[int] = [idx]
                    used[idx] = True

                    for j in range(num_boxes):
                        if used[j] or j == idx:
                            continue
                        if SimpleTracker._iou(base_box.tolist(), boxes_np[j].tolist()) >= ensemble_iou:
                            used[j] = True
                            cluster_idxs.append(j)

                    # Solo aceptar grupos donde al menos `min_votes` cajas coinciden
                    if len(cluster_idxs) < min_votes:
                        continue

                    # Dentro del grupo, quedarse con la caja de mayor confianza
                    best_idx = max(cluster_idxs, key=lambda k: confs_np[k])
                    x1, y1, x2, y2 = boxes_np[best_idx]
                    conf = float(confs_np[best_idx])

                    x1_i = int(max(0, min(orig_w - 1, x1)))
                    y1_i = int(max(0, min(orig_h - 1, y1)))
                    x2_i = int(max(0, min(orig_w - 1, x2)))
                    y2_i = int(max(0, min(orig_h - 1, y2)))
                    cx = int((x1_i + x2_i) / 2)
                    cy = int((y1_i + y2_i) / 2)

                    detections.append(
                        {
                            "bbox": [x1_i, y1_i, x2_i, y2_i],
                            "confidence": conf,
                            "class": "person",
                            "center": [cx, cy],
                        }
                    )

        # Actualizar tracker para estabilizar y asignar IDs persistentes
        if self.tracker is not None:
            detections = self.tracker.update(detections)

        people_count = self.count_people(detections)

        # Actualizar estadísticas
        self.total_frames += 1
        self.total_detections += len(detections)
        self.people_history.append(people_count)
        if self.total_frames == 1:
            self.max_people = people_count
            self.min_people = people_count
        else:
            self.max_people = max(self.max_people, people_count)
            self.min_people = min(self.min_people, people_count)

        now = time.time()
        if self._last_frame_time is None:
            fps_inst = 0.0
        else:
            fps_inst = 1.0 / max(1e-6, now - self._last_frame_time)
        self._last_frame_time = now
        self.fps_history.append(fps_inst)

        if self.log_enabled and self.logger is not None:
            self.logger.log_frame(
                frame_id=self.total_frames,
                people_count=people_count,
                fps=fps_inst,
                detections=detections,
            )

        # Liberar cache periódicamente
        if self.device.type == "cuda" and self.total_frames % 100 == 0:
            torch.cuda.empty_cache()

        annotated = frame
        if return_annotated:
            annotated = self._annotate_frame(frame, detections, fps_inst)

        return annotated, detections, inference_time

    def _annotate_frame(
        self,
        frame: np.ndarray,
        detections: List[Dict[str, Any]],
        fps: float,
    ) -> np.ndarray:
        """Aplicar anotaciones completas (bboxes, paneles, barra FPS, etc.)."""

        annotated = visualizer.draw_bounding_boxes(
            frame,
            detections,
            thickness=self.thickness,
            show_confidence=self.show_confidence,
            font_scale=self.font_scale,
        )
        
        if self.fisheye:
             # Aplicar efecto fisheye al frame completo
             from src.privacy import apply_fisheye_effect
             annotated = apply_fisheye_effect(annotated, strength=0.3)

        if self.anonymize:
            annotated = blur_faces(annotated, detections, blur_method=self.blur_method)

        stats = self.get_statistics()

        annotated = visualizer.draw_info_panel(
            annotated,
            people_count=self.count_people(detections),
            fps=fps,
            config_name=self.config_preset,
            model_name=self.model_name,
            position="top",
        )

        annotated = visualizer.draw_statistics_panel(
            annotated,
            statistics={
                **stats,
                "device": str(self.device),
            },
            position="bottom-right",
        )

        annotated = visualizer.draw_fps_bar(
            annotated,
            fps=fps,
            target_fps=self.target_fps,
            position="bottom-left",
        )

        # Historial de aforo como pequeña gráfica en la esquina superior derecha
        history_img = visualizer.create_history_graph(list(self.people_history))
        h_hist, w_hist = history_img.shape[:2]
        h, w = annotated.shape[:2]

        x1 = w - w_hist - 10
        y1 = 10
        x2 = x1 + w_hist
        y2 = y1 + h_hist

        if x1 >= 0 and y2 <= h:
            roi = annotated[y1:y2, x1:x2]
            blended = cv2.addWeighted(roi, 0.3, history_img, 0.7, 0)
            annotated[y1:y2, x1:x2] = blended

        return annotated

    def count_people(self, detections: List[Dict[str, Any]]) -> int:
        """Contar personas a partir de detecciones."""

        return len(detections)

    # ----------------- Video en tiempo real -----------------

    def run_video(
        self,
        source: str = "0",
        save: bool = False,
        output_path: Optional[str] = None,
        display: bool = True,
    ) -> None:
        """Ejecutar detección en loop de video."""

        # Detectar tipo de fuente
        if is_camera_source(source):
            src = int(source)
            print_info(f"Usando webcam índice {src}")
        else:
            src = source
            print_info(f"Usando fuente de video: {src}")

        cap = cv2.VideoCapture(src)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not cap.isOpened():
            print_error(f"No se pudo abrir la fuente: {source}")
            
            # Fallback automático a webcam 0 si falla una fuente remota (IP/Archivo)
            if not is_camera_source(source) and str(source) != "0":
                print_warning("⚠️ Falló la conexión a la cámara IP/Archivo.")
                print_info("🔄 Intentando conectar a la webcam integrada (índice 0)...")
                
                cap = cv2.VideoCapture(0)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                if cap.isOpened():
                    print_info("✅ Conectado exitosamente a la webcam integrada")
                else:
                    print_error("❌ También falló la conexión a la webcam integrada")
                    cap.release()
                    return
            else:
                if is_camera_source(source):
                    print_warning("Verifica que la webcam esté conectada y no usada por otra app")
                else:
                    print_warning("Verifica que el archivo/stream exista y sea accesible")
                cap.release()
                return

        writer: Optional[cv2.VideoWriter] = None
        save_cfg = self.config_manager.get_save_config()

        fourcc = cv2.VideoWriter_fourcc(*save_cfg.get("codec", "mp4v"))

        paused = False
        print_info("Controles: Q/ESC = salir, ESPACIO = pausar/reanudar, S = guardar captura")

        try:
            while True:
                if not paused:
                    ret, frame = cap.read()
                    if not ret or frame is None:
                        print_warning("Fin de stream o error al leer frame")
                        break

                    annotated, detections, _ = self.detect_frame(frame, return_annotated=True)

                    # Inicializar writer cuando sepamos tamaño
                    if save and writer is None:
                        h, w = annotated.shape[:2]
                        if output_path is None:
                            ts = time.strftime("%Y%m%d_%H%M%S")
                            out_dir = (self.paths.base_dir / save_cfg.get("output_dir", "outputs/videos")).resolve()
                            out_dir.mkdir(parents=True, exist_ok=True)
                            output_path = str(out_dir / f"video_processed_{ts}.mp4")
                        writer = cv2.VideoWriter(output_path, fourcc, float(self.target_fps), (w, h))

                    if writer is not None:
                        writer.write(annotated)

                else:
                    annotated = frame if "frame" in locals() else None

                if display and annotated is not None:
                    cv2.imshow("Aforo Realtime", annotated)
                    key = cv2.waitKey(1) & 0xFF
                elif display:
                    key = cv2.waitKey(1) & 0xFF
                else:
                    key = 0

                if key in (ord("q"), 27):  # q o ESC
                    print_info("Saliendo por comando del usuario")
                    break
                if key == 32:  # SPACE
                    paused = not paused
                    print_info("Pausa activada" if paused else "Pausa desactivada")
                if key in (ord("s"), ord("S")) and annotated is not None:
                    screenshots_cfg = self.config_manager.get_screenshots_config()
                    out_dir = (self.paths.base_dir / screenshots_cfg.get("output_dir", "outputs/screenshots")).resolve()
                    out_dir.mkdir(parents=True, exist_ok=True)
                    ts = time.strftime("%Y%m%d_%H%M%S")
                    out_path = out_dir / f"screenshot_{ts}.png"
                    cv2.imwrite(str(out_path), annotated)
                    print_info(f"Captura guardada en {out_path}")

        finally:
            cap.release()
            if writer is not None:
                writer.release()
            if display:
                try:
                    cv2.destroyAllWindows()
                except Exception:  # noqa: BLE001
                    pass

            self.save_logs(self.log_format)

    # ----------------- Procesamiento batch de imágenes -----------------

    def process_image_batch(
        self,
        images_path: str,
        save_annotated: bool = True,
    ) -> Dict[str, Any]:
        """Procesar lote de imágenes en una carpeta."""

        img_dir = Path(images_path)
        if not img_dir.is_dir():
            raise FileNotFoundError(f"Carpeta de imágenes no encontrada: {img_dir}")

        output_dir = self.paths.base_dir / "outputs" / "screenshots"
        output_dir.mkdir(parents=True, exist_ok=True)

        exts = {".jpg", ".jpeg", ".png", ".bmp"}
        files = [p for p in sorted(img_dir.iterdir()) if p.suffix.lower() in exts]

        for img_path in files:
            img = cv2.imread(str(img_path))
            if img is None:
                continue

            annotated, detections, _ = self.detect_frame(img, return_annotated=True)

            if save_annotated:
                out_path = output_dir / f"annotated_{img_path.name}"
                cv2.imwrite(str(out_path), annotated)

        stats = self.get_statistics()
        self.save_logs(self.log_format)
        return stats

    # ----------------- Estadísticas -----------------

    def get_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas de la sesión actual."""

        if self.total_frames == 0:
            return {
                "total_frames": 0,
                "total_detections": 0,
                "avg_people_per_frame": 0.0,
                "avg_fps": 0.0,
                "avg_inference_time": 0.0,
                "max_people": 0,
                "min_people": 0,
            }

        avg_people = float(sum(self.people_history) / max(1, len(self.people_history)))
        avg_fps = float(sum(self.fps_history) / max(1, len(self.fps_history)))
        avg_inf = float(sum(self.inference_times) / max(1, len(self.inference_times)))

        return {
            "total_frames": self.total_frames,
            "total_detections": self.total_detections,
            "avg_people_per_frame": avg_people,
            "avg_fps": avg_fps,
            "avg_inference_time": avg_inf,
            "max_people": self.max_people,
            "min_people": self.min_people,
        }

    def reset_statistics(self) -> None:
        """Resetear contadores y estadísticas."""

        self.people_history.clear()
        self.fps_history.clear()
        self.inference_times.clear()
        self.total_frames = 0
        self.total_detections = 0
        self.max_people = 0
        self.min_people = 0

    # ----------------- Logging -----------------

    def save_logs(self, format: str = "both") -> None:
        """Guardar logs de sesión (CSV/JSON/resumen)."""

        if not self.log_enabled or self.logger is None:
            return

        self.logger.format = format
        self.logger.close()

    def __del__(self) -> None:  # pragma: no cover - mejor esfuerzo
        try:
            self.save_logs(self.log_format)
        except Exception:  # noqa: BLE001
            pass
