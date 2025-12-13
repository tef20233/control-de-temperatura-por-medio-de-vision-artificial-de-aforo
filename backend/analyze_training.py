import os
import pandas as pd
from pathlib import Path

# Directorio base
BASE_DIR = Path("modelos_entrenados_sin_validar")
OUTPUT_FILE = "resumen_entrenamiento.md"

def analyze_training_results():
    print(f"🔍 Analizando resultados de entrenamiento en: {BASE_DIR}")
    
    summaries = []
    
    # Buscar recursivamente archivos results.csv
    for result_file in BASE_DIR.rglob("results.csv"):
        model_dir = result_file.parent
        model_name = model_dir.name
        
        # Si el nombre es genérico (ej. "weights" o "train"), intentar subir un nivel
        if model_name in ["weights", "train", "detect"]:
            model_name = model_dir.parent.name
            
        try:
            # Leer CSV (Ultralytics suele tener espacios en los nombres de columnas)
            df = pd.read_csv(result_file)
            df.columns = [c.strip() for c in df.columns]
            
            # Obtener la mejor época (basada en mAP50-95)
            if 'metrics/mAP50-95(B)' in df.columns:
                best_epoch = df.loc[df['metrics/mAP50-95(B)'].idxmax()]
                map50 = best_epoch['metrics/mAP50(B)']
                map50_95 = best_epoch['metrics/mAP50-95(B)']
                precision = best_epoch['metrics/precision(B)']
                recall = best_epoch['metrics/recall(B)']
                epoch = int(best_epoch['epoch'])
            else:
                # Fallback para formatos antiguos o diferentes
                print(f"⚠️ Formato de columnas no reconocido en {model_name}")
                continue

            summaries.append({
                "Modelo": model_name,
                "Ruta": str(model_dir),
                "Época": epoch,
                "mAP50": map50,
                "mAP50-95": map50_95,
                "Precision": precision,
                "Recall": recall
            })
            
        except Exception as e:
            print(f"❌ Error leyendo {result_file}: {e}")

    # Generar reporte Markdown
    if not summaries:
        print("❌ No se encontraron resultados válidos.")
        return

    df_summary = pd.DataFrame(summaries)
    df_summary = df_summary.sort_values(by="mAP50-95", ascending=False)
    
    md_content = "# 📊 Resumen de Entrenamiento (Modelos sin Validar)\n\n"
    md_content += "Este reporte resume las métricas obtenidas **durante el entrenamiento** (mejor época).\n\n"
    
    md_content += "| Modelo | Época (Mejor) | mAP @ 0.5 | mAP @ 0.5-95 | Precisión | Recall |\n"
    md_content += "|--------|---------------|-----------|--------------|-----------|--------|\n"
    
    for _, row in df_summary.iterrows():
        md_content += f"| **{row['Modelo']}** | {row['Época']} | {row['mAP50']:.4f} | {row['mAP50-95']:.4f} | {row['Precision']:.4f} | {row['Recall']:.4f} |\n"
    
    md_content += "\n## 📝 Notas\n"
    md_content += "- Estas métricas provienen del archivo `results.csv` generado automáticamente durante el entrenamiento.\n"
    md_content += "- Representan el rendimiento en el set de validación usado durante el entrenamiento.\n"
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    print(f"✅ Reporte generado: {OUTPUT_FILE}")
    print(df_summary)

if __name__ == "__main__":
    analyze_training_results()
