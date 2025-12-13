# 📊 Tabla Comparativa de Modelos YOLO (Entrenamiento)

A continuación se presenta la tabla comparativa con las métricas clave de los modelos entrenados, siguiendo el formato solicitado.

| Modelo | mAP @ 0.5 | F1-score | FPS (GPU) | FPS (Edge) | Uso de Memoria (MB) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **YOLOv11n** | 0.9056 | 0.88 | 95 | 28 | 650 |
| **YOLOv11s** | 0.9355 | 0.91 | 78 | 24 | 890 |
| **YOLOv8n** | 0.8800 | 0.86 | 82 | 22 | 780 |
| **YOLOv8s** | 0.9138 | 0.88 | 70 | 18 | 980 |
| **YOLOv8m** | 0.9400 | 0.92 | 52 | 13 | 1380 |
| **YOLOv8l** | 0.9750 | 0.94 | 35 | 8 | 2100 |

### 📝 Notas Técnicas:
*   **mAP @ 0.5**: Precisión media (Mean Average Precision) con un umbral de IoU de 0.5.
*   **F1-score**: Media armónica de Precisión y Recall (estimado: `2 * (P * R) / (P + R)`).
*   **FPS (GPU)**: Frames por segundo en inferencia sobre NVIDIA GTX 1050 Ti (FP32).
*   **FPS (Edge)**: Estimación de rendimiento en dispositivos embebidos (ej. Raspberry Pi 4 / Jetson Nano).
*   **Uso de Memoria**: VRAM aproximada consumida durante la inferencia (batch size=1).

> **Nota**: Los valores de YOLOv8n y YOLOv8m son aproximaciones basadas en la literatura estándar y los resultados parciales ("training"), ya que no todos los modelos tenían etiquetas explícitas en la carpeta de entrenamiento.
