import os
import time
import torch
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from ultralytics import YOLO
from pathlib import Path

# Configuración
MODELS_DIR = Path("models")
DATA_YAML = "models/test_dataset.yaml"
OUTPUT_DIR = Path("outputs/benchmark_scientific")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Detectar GPU y configurar
DEVICE = 0 if torch.cuda.is_available() else "cpu"
DEVICE_NAME = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
print(f"🔬 Iniciando Benchmark Científico en: {DEVICE_NAME}")

# Configuración específica para GTX 1050 Ti (Pascal)
# Desactivamos FP16 si es Pascal (Compute < 7.0) para evitar degradación de rendimiento
USE_HALF = False
if torch.cuda.is_available():
    cap = torch.cuda.get_device_capability(0)
    if cap[0] >= 7:
        USE_HALF = True
        print("⚡ GPU moderna detectada (Volta+). Usando FP16.")
    else:
        print("⚠️ GPU Pascal/Maxwell detectada. Forzando FP32 para máximo rendimiento.")

def get_models():
    # Solo probar modelos Nano y Small para no demorar horas en la 1050 Ti
    all_models = sorted(list(MODELS_DIR.glob("*.pt")))
    return [m for m in all_models if m.name.endswith(('n.pt', 's.pt'))]

def benchmark_speed(model_path, imgsz=512, num_frames=50):
    print(f"  ⏱️ Midiendo velocidad (Inferencia pura)...")
    try:
        model = YOLO(model_path)
        
        # Dummy input
        dummy_input = np.zeros((imgsz, imgsz, 3), dtype=np.uint8)
        
        # Warmup
        for _ in range(20):
            model(dummy_input, verbose=False, device=DEVICE, half=USE_HALF)
            
        # Benchmark
        torch.cuda.synchronize()
        start_time = time.time()
        
        latencies = []
        for _ in range(num_frames):
            t0 = time.time()
            model(dummy_input, verbose=False, device=DEVICE, half=USE_HALF)
            if torch.cuda.is_available():
                torch.cuda.synchronize()
            latencies.append((time.time() - t0) * 1000) # ms
            
        total_time = time.time() - start_time
        fps = num_frames / total_time
        
        avg_latency = np.mean(latencies)
        std_latency = np.std(latencies)
        p95_latency = np.percentile(latencies, 95)
        
        # Contar parámetros manualmente
        params = sum(p.numel() for p in model.model.parameters())
        
        return {
            "fps": fps,
            "latency_avg_ms": avg_latency,
            "latency_std_ms": std_latency,
            "latency_p95_ms": p95_latency,
            "params_m": params / 1e6
        }
    except Exception as e:
        print(f"  ❌ Error en benchmark de velocidad: {e}")
        return None

def benchmark_accuracy(model_path, imgsz=512):
    print(f"  🎯 Midiendo precisión (Validación en test set)...")
    try:
        model = YOLO(model_path)
        # Validación
        metrics = model.val(
            data=DATA_YAML,
            split='test',
            imgsz=imgsz,
            device=DEVICE,
            half=USE_HALF,
            verbose=False,
            plots=False
        )
        
        return {
            "map50": metrics.box.map50,
            "map50-95": metrics.box.map,
            "precision": metrics.box.mp,
            "recall": metrics.box.mr
        }
    except Exception as e:
        print(f"  ❌ Error en benchmark de precisión: {e}")
        return None

def generate_plots(results_df):
    print("📊 Generando gráficas científicas...")
    sns.set_theme(style="whitegrid")
    
    # 1. FPS vs mAP50 (Trade-off)
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=results_df, x="fps", y="map50", hue="model", s=200, style="model")
    for i, row in results_df.iterrows():
        plt.text(row.fps+1, row.map50, row.model, fontsize=9)
    plt.title(f"Trade-off Velocidad vs Precisión ({DEVICE_NAME})")
    plt.xlabel("Velocidad (FPS)")
    plt.ylabel("Precisión (mAP @ 0.5)")
    plt.savefig(OUTPUT_DIR / "tradeoff_fps_map.png")
    plt.close()
    
    # 2. Latency Comparison
    plt.figure(figsize=(10, 6))
    sns.barplot(data=results_df, x="model", y="latency_avg_ms", hue="model")
    plt.title("Latencia Promedio de Inferencia (ms)")
    plt.ylabel("Latencia (ms) - Menor es mejor")
    plt.xticks(rotation=45)
    plt.savefig(OUTPUT_DIR / "latency_comparison.png")
    plt.close()
    
    # 3. Model Size vs Accuracy
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=results_df, x="params_m", y="map50-95", hue="model", s=200)
    plt.title("Eficiencia de Parámetros")
    plt.xlabel("Parámetros (Millones)")
    plt.ylabel("mAP 50-95")
    plt.savefig(OUTPUT_DIR / "params_efficiency.png")
    plt.close()

def get_models():
    # Habilitar TODOS los modelos disponibles
    return sorted(list(MODELS_DIR.glob("*.pt")))

def main():
    models = get_models()
    results = []
    
    print(f"📋 Modelos encontrados: {[m.name for m in models]}")
    
    for model_path in models:
        model_name = model_path.stem
        print(f"\n🧪 Evaluando: {model_name}")
        
        try:
            # 1. Velocidad
            speed_metrics = benchmark_speed(model_path)
            if not speed_metrics: 
                print("⚠️ Saltando por error en velocidad")
                continue
            
            # 2. Precisión
            acc_metrics = benchmark_accuracy(model_path)
            if not acc_metrics: 
                print("⚠️ Saltando por error en precisión")
                continue
            
            # Combinar
            result = {
                "model": model_name,
                **speed_metrics,
                **acc_metrics
            }
            results.append(result)
            print(f"  ✅ FPS: {result['fps']:.1f} | mAP50: {result['map50']:.3f} | Latencia: {result['latency_avg_ms']:.1f}ms")
            
        except Exception as e:
            print(f"❌ Error fatal en modelo {model_name}: {e}")

    if not results:
        print("❌ No se obtuvieron resultados.")
        return

    # Guardar resultados
    df = pd.DataFrame(results)
    print("Resultados DataFrame:")
    print(df)
    df.to_csv(OUTPUT_DIR / "benchmark_results.csv", index=False)
    df.to_json(OUTPUT_DIR / "benchmark_results.json", orient="records", indent=2)
    
    # Generar reporte Markdown
    md_report = f"""# 🧪 Reporte Científico de Modelos YOLO
**Hardware**: {DEVICE_NAME}
**Fecha**: {time.strftime('%Y-%m-%d %H:%M:%S')}
**Configuración**: FP16={'Activado' if USE_HALF else 'Desactivado (Optimización Pascal)'}

## 📊 Resumen de Métricas

| Modelo | FPS | Latencia (ms) | mAP @ 0.5 | mAP @ 0.5-95 | Parámetros (M) |
|--------|-----|---------------|-----------|--------------|----------------|
"""
    for _, row in df.iterrows():
        md_report += f"| {row['model']} | {row['fps']:.1f} | {row['latency_avg_ms']:.2f} | {row['map50']:.3f} | {row['map50-95']:.3f} | {row['params_m']:.2f} |\n"
    
    md_report += "\n## 📈 Análisis\n"
    best_fps = df.loc[df['fps'].idxmax()]
    best_map = df.loc[df['map50'].idxmax()]
    
    md_report += f"- **Modelo más rápido**: {best_fps['model']} ({best_fps['fps']:.1f} FPS)\n"
    md_report += f"- **Modelo más preciso**: {best_map['model']} (mAP50: {best_map['map50']:.3f})\n"
    
    with open(OUTPUT_DIR / "reporte_cientifico.md", "w", encoding="utf-8") as f:
        f.write(md_report)
        
    # Generar gráficas
    try:
        generate_plots(df)
    except Exception as e:
        print(f"⚠️ No se pudieron generar gráficas (posiblemente falta seaborn/matplotlib): {e}")

    print(f"\n✅ Benchmark completado. Resultados en: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
