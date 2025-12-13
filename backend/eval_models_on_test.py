import time
from pathlib import Path

from ultralytics import YOLO


BACKEND_ROOT = Path(__file__).resolve().parent

# Rutas a modelos
MODELS = {
    "yolov11n": BACKEND_ROOT / "models" / "yolov11n.pt",
    "yolov8m": BACKEND_ROOT / "models" / "yolov8m.pt",
    "yolov8n_custom": BACKEND_ROOT / "modelos_entrenados_sin_validar" / "yolov8n" / "training" / "weights" / "best.pt",
    "yolov8n_v3_gtx1060": BACKEND_ROOT / "modelos_entrenados_sin_validar" / "yolov8n" / "aforo_v3_gtx1060" / "weights" / "best.pt",
    "yolov8s_custom": BACKEND_ROOT / "modelos_entrenados_sin_validar" / "yolov8s" / "training" / "weights" / "best.pt",
    "yolov8l_custom": BACKEND_ROOT / "modelos_entrenados_sin_validar" / "yolov8l" / "training" / "weights" / "best.pt",
}

# Dataset de test (imágenes + labels en formato YOLO)
DATA_YAML = BACKEND_ROOT / "modelos_entrenados_sin_validar" / "test_data.yaml"


def format_metrics(model_name: str, metrics) -> None:
    """Imprimir métricas principales de validación de forma legible."""
    # Ultralytics expone métricas agregadas en metrics.results_dict
    d = metrics.results_dict or {}

    mp = d.get("metrics/precision(B)")
    mr = d.get("metrics/recall(B)")
    map50 = d.get("metrics/mAP50(B)")
    map50_95 = d.get("metrics/mAP50-95(B)")

    # Algunos atributos también están en metrics.box
    try:
        box = getattr(metrics, "box", None)
        if box is not None:
            map50_95 = box.map if map50_95 is None else map50_95
            map50 = box.map50 if map50 is None else map50
            mp = box.mp if mp is None else mp
            mr = box.mr if mr is None else mr
    except Exception:
        pass

    print(f"\n=== Resultados para {model_name} ===")
    print(f"Precisión (mp):      {mp:.4f}" if mp is not None else "Precisión (mp):      N/A")
    print(f"Recall (mr):         {mr:.4f}" if mr is not None else "Recall (mr):         N/A")
    print(f"mAP@0.50:           {map50:.4f}" if map50 is not None else "mAP@0.50:           N/A")
    print(f"mAP@0.50:0.95:      {map50_95:.4f}" if map50_95 is not None else "mAP@0.50:0.95:      N/A")

    # Velocidad global (si está disponible)
    try:
        speed = getattr(metrics, "speed", None)
        if speed is not None:
            # speed es un dict con claves como 'inference', 'preprocess', 'postprocess'
            inf = speed.get("inference", None)
            if inf:
                fps = 1000.0 / inf  # ms -> FPS
                print(f"Tiempo inferencia medio: {inf:.2f} ms  (~{fps:.1f} FPS solo modelo)")
    except Exception:
        pass


def main() -> None:
    print("Dataset de test:", DATA_YAML)
    if not DATA_YAML.exists():
        raise SystemExit(f"No se encontró {DATA_YAML}. Asegúrate de que existe y apunta a test/images y test/labels.")

    for name, path in MODELS.items():
        if not path.exists():
            print(f"\n⚠️  Saltando {name}: no se encontró el archivo de modelo en {path}")
            continue

        print(f"\n==============================")
        print(f"Validando modelo: {name}")
        print(f"Pesos: {path}")

        model = YOLO(str(path))

        t0 = time.time()
        metrics = model.val(
            data=str(DATA_YAML),
            split="test",   # usar carpeta test
            imgsz=640,
            verbose=False,
        )
        dt = time.time() - t0

        print(f"Validación terminada en {dt:.1f} s")
        format_metrics(name, metrics)


if __name__ == "__main__":
    main()
