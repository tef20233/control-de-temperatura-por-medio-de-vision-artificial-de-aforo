"""Punto de entrada CLI para el sistema de control de aforo en tiempo real."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

from src.detector import RealtimeDetector
from src.utils import resolve_model_path, print_error, print_info, print_warning


def build_parser() -> argparse.ArgumentParser:
    """Construir parser de argumentos CLI."""

    parser = argparse.ArgumentParser(
        description="Sistema de detección y conteo de personas en tiempo real usando YOLO",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("--model", type=str, default="models/yolo11s.pt", help="Ruta al modelo (.pt o .engine)")
    parser.add_argument("--source", type=str, default="0", help="Fuente de video o carpeta de imágenes")
    parser.add_argument(
        "--config",
        type=str,
        default="fast",
        choices=["ultra_fast", "fast", "balanced", "quality"],
        help="Preset de configuración",
    )
    parser.add_argument("--imgsz", type=int, default=None, help="Resolución de procesamiento (override preset)")
    parser.add_argument("--conf", type=float, default=None, help="Threshold de confianza (0.0-1.0)")
    parser.add_argument("--iou", type=float, default=None, help="Threshold IoU para NMS (0.0-1.0)")
    parser.add_argument(
        "--device",
        type=str,
        default="auto",
        help="Dispositivo para inferencia: 0,1,..., cpu, cuda:0, auto",
    )

    half_group = parser.add_mutually_exclusive_group()
    half_group.add_argument("--half", dest="half", action="store_true", help="Forzar FP16 si es posible")
    half_group.add_argument("--no-half", dest="half", action="store_false", help="Desactivar FP16")
    parser.set_defaults(half=None)

    parser.add_argument("--save", action="store_true", help="Guardar video procesado")
    parser.add_argument("--output", type=str, default=None, help="Ruta de salida para video guardado")

    display_group = parser.add_mutually_exclusive_group()
    display_group.add_argument("--no-display", dest="display", action="store_false", help="Modo headless")
    display_group.add_argument("--display", dest="display", action="store_true", help="Forzar display")
    parser.set_defaults(display=True)

    parser.add_argument("--anonymize", action="store_true", help="Activar anonimización facial")
    parser.add_argument("--fisheye", action="store_true", help="Aplicar efecto ojo de pez a todo el frame")

    log_group = parser.add_mutually_exclusive_group()
    log_group.add_argument("--log", dest="log", action="store_true", help="Guardar logs CSV/JSON")
    log_group.add_argument("--no-log", dest="log", action="store_false", help="Desactivar logs")
    parser.set_defaults(log=None)

    parser.add_argument(
        "--log-format",
        type=str,
        default="both",
        choices=["csv", "json", "both"],
        help="Formato de logs",
    )

    parser.add_argument("--max-det", type=int, default=None, help="Máximo de detecciones por frame")
    parser.add_argument("--thickness", type=int, default=2, help="Grosor de bounding boxes")
    parser.add_argument("--font-scale", type=float, default=1.0, help="Escala de texto en pantalla")

    show_conf_group = parser.add_mutually_exclusive_group()
    show_conf_group.add_argument("--show-conf", dest="show_conf", action="store_true", help="Mostrar scores")
    show_conf_group.add_argument("--no-show-conf", dest="show_conf", action="store_false", help="Ocultar scores")
    parser.set_defaults(show_conf=True)

    parser.add_argument(
        "--ensemble",
        type=str,
        default=None,
        help="Modelos adicionales para ensemble, separados por coma (ej: yolov8m.pt,yolov8s.pt)",
    )

    # Roboflow backend
    parser.add_argument("--use-roboflow", action="store_true", help="Usar Workflow de Roboflow como backend de detección")
    parser.add_argument(
        "--roboflow-api-url",
        type=str,
        default="https://serverless.roboflow.com",
        help="URL del API de Roboflow",
    )
    parser.add_argument(
        "--roboflow-workspace",
        type=str,
        default="proyecto-aforo-2",
        help="Nombre de workspace en Roboflow",
    )
    parser.add_argument(
        "--roboflow-workflow",
        type=str,
        default="find-people",
        help="ID del workflow en Roboflow",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Función principal CLI."""

    parser = build_parser()
    args = parser.parse_args(argv)

    # Resolver ruta de modelo
    model_path = resolve_model_path(args.model)
    print_info(f"Usando modelo: {model_path}")

    if not model_path.exists():
        # Si es un modelo estándar (.pt), permitimos que continúe para que Ultralytics lo descargue
        if model_path.suffix == ".pt" and "yolo" in model_path.name.lower():
            print_warning(f"Modelo no encontrado localmente en {model_path}. Se intentará descargar automáticamente.")
        else:
            print_error(f"Modelo no encontrado en {model_path}")
            print_warning("Coloca tus modelos .pt en backend/models o especifica --model")
            return 1

    # Decidir half por defecto según dispositivo y flags
    if args.half is None:
        # half por defecto: True si hay CUDA
        half = torch.cuda.is_available()
    else:
        half = bool(args.half)

    # Parsear rutas de modelos extra para ensemble (si se proporcionan)
    ensemble_paths = None
    if args.ensemble:
        ensemble_paths = [p.strip() for p in args.ensemble.split(",") if p.strip()]

    # Instanciar detector
    detector = RealtimeDetector(
        model_path=str(model_path),
        config_preset=args.config,
        device=args.device,
        half=half,
        anonymize=args.anonymize,
        fisheye=args.fisheye,
        log=args.log,
        log_format=args.log_format,
        imgsz_override=args.imgsz,
        conf_override=args.conf,
        iou_override=args.iou,
        max_det_override=args.max_det,
        thickness=args.thickness,
        font_scale=args.font_scale,
        show_confidence=args.show_conf,
        ensemble_model_paths=ensemble_paths,
        use_roboflow=args.use_roboflow,
        roboflow_api_url=args.roboflow_api_url,
        roboflow_workspace=args.roboflow_workspace,
        roboflow_workflow=args.roboflow_workflow,
    )

    src_path = Path(args.source)

    try:
        if src_path.is_dir():
            print_info(f"Procesando carpeta de imágenes: {src_path}")
            stats = detector.process_image_batch(str(src_path), save_annotated=True)
            print_info(f"Procesamiento batch completado: {stats}")
        else:
            detector.run_video(
                source=args.source,
                save=args.save,
                output_path=args.output,
                display=args.display,
            )
    except KeyboardInterrupt:
        print_warning("Interrupción por teclado (Ctrl+C)")
    except Exception as exc:  # noqa: BLE001
        print_error(f"Error en ejecución: {exc}")
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
