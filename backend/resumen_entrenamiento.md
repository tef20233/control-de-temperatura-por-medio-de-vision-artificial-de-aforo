# 📊 Resumen de Entrenamiento (Modelos sin Validar)

Este reporte resume las métricas obtenidas **durante el entrenamiento** (mejor época).

| Modelo | Época (Mejor) | mAP @ 0.5 | mAP @ 0.5-95 | Precisión | Recall |
|--------|---------------|-----------|--------------|-----------|--------|
| **training** | 24 | 0.9750 | 0.7713 | 0.9518 | 0.9375 |
| **training** | 27 | 0.9748 | 0.7692 | 0.9514 | 0.9370 |
| **yolov11s** | 66 | 0.9355 | 0.4941 | 0.9214 | 0.9099 |
| **yolov11n** | 153 | 0.9056 | 0.4823 | 0.9038 | 0.8608 |
| **yolov8s** | 19 | 0.9138 | 0.4709 | 0.8967 | 0.8609 |
| **aforo_v3_gtx1060** | 11 | 0.8547 | 0.4121 | 0.8458 | 0.8254 |

## 📝 Notas
- Estas métricas provienen del archivo `results.csv` generado automáticamente durante el entrenamiento.
- Representan el rendimiento en el set de validación usado durante el entrenamiento.
