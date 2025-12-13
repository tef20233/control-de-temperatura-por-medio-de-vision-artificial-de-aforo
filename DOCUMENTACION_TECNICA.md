# 📄 Documentación Técnica del Proyecto de Aforo

## 1. 🛡️ Privacidad y Anonimización
El sistema implementa un módulo dedicado a la privacidad (`backend/aforo_realtime/src/privacy.py`) diseñado para cumplir con normativas de protección de datos (como GDPR) mediante la anonimización de rostros en tiempo real.

### Tecnologías y Métodos:
El sistema utiliza un enfoque híbrido para la detección y ofuscación de rostros:

1.  **Estimación de Región Facial**:
    *   **Método Heurístico ("Thirds")**: Por defecto, estima la ubicación del rostro asumiendo que se encuentra en el tercio superior del bounding box de la persona detectada. Esto es extremadamente rápido y no requiere inferencia adicional.
    *   **Método Cascade (Opcional)**: Puede utilizar `Haar Cascades` de OpenCV para una detección facial precisa dentro del ROI (Region of Interest) de la persona, aunque con un mayor coste computacional.

2.  **Técnicas de Ofuscación**:
    *   **Gaussian Blur (Por defecto)**: Aplica un filtro gaussiano con un kernel dinámico (típicamente 99x99, sigma=30) para difuminar suavemente el área facial.
    *   **Pixelación**: Reduce la resolución de la región facial y la reescala (nearest-neighbor) para crear un efecto de mosaico.
    *   **Máscara Negra**: Oculta totalmente la región con un rectángulo negro sólido.

## 2. 🎯 Tracking y Seguimiento de Personas
El seguimiento se realiza mediante el algoritmo `SimpleTracker` (`backend/aforo_realtime/src/tracker.py`), diseñado para ser ligero y eficiente en escenarios de aforo.

### Algoritmo de Tracking:
Utiliza un enfoque de **Asociación de Datos por IoU (Intersection over Union)** sin necesidad de re-identificación visual profunda (ReID), lo que garantiza alta velocidad (FPS).

1.  **Matriz de Coste**: Calcula la IoU entre todas las detecciones del frame actual y las predicciones de los "tracks" activos del frame anterior.
2.  **Asignación Greedy**: Asocia las detecciones a los tracks existentes maximizando el IoU, siempre que supere un umbral mínimo (`iou_threshold=0.3`).
3.  **Suavizado (Smoothing)**: Aplica un filtro exponencial a las coordenadas de las cajas (`smoothing=0.5`) para reducir el "jitter" o temblor de las detecciones frame a frame.
4.  **Gestión de Vida**:
    *   **Nacimiento**: Crea un nuevo ID si una detección no coincide con ningún track existente.
    *   **Muerte**: Elimina un track si no se actualiza durante `max_age=5` frames consecutivos.

## 3. ⚙️ Configuración del Proyecto
La configuración es modular y se adapta al hardware detectado (específicamente optimizada para NVIDIA GTX 1050 Ti en este despliegue).

### Configuración de Hardware (GTX 1050 Ti):
*   **Modelo**: `yolo11s.pt` (Small) - Balance óptimo entre precisión y velocidad.
*   **Resolución de Entrada**: 512x512 píxeles.
*   **Precisión**: **FP32** (Float32). Se desactiva explícitamente FP16 (Half Precision) ya que la arquitectura Pascal (Compute Capability 6.1) de la GTX 1050 Ti no posee Tensor Cores para acelerar FP16, y su uso podría degradar el rendimiento.
*   **Backend de Inferencia**: CUDA (GPU).

### Parámetros de Detección:
*   **Confianza (Confidence Threshold)**: `0.35` (35%). Filtra detecciones inciertas.
*   **IoU (NMS Threshold)**: `0.50` (50%). Umbral para suprimir cajas duplicadas.
*   **Max Detections**: 100 personas por frame.

## 4. 📊 Métricas de Entrenamiento
A continuación se presentan las métricas obtenidas durante el entrenamiento de los modelos evaluados (basado en la mejor época de validación):

| Modelo | Época (Mejor) | mAP @ 0.5 | mAP @ 0.5-95 | Precisión | Recall |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **training** (yolov8m/l) | 24 | **0.9750** | **0.7713** | 0.9518 | 0.9375 |
| **yolov11s** | 66 | 0.9355 | 0.4941 | 0.9214 | 0.9099 |
| **yolov11n** | 153 | 0.9056 | 0.4823 | 0.9038 | 0.8608 |
| **yolov8s** | 19 | 0.9138 | 0.4709 | 0.8967 | 0.8609 |
| **aforo_v3_gtx1060** | 11 | 0.8547 | 0.4121 | 0.8458 | 0.8254 |

## 5. 💾 Información del Dataset
El modelo fue entrenado utilizando un dataset robusto y diverso para garantizar la generalización en diferentes escenarios de aforo.

### Distribución de Datos:
*   **Total de Imágenes**: 71,148
*   **División (Split)**:
    *   **Entrenamiento (Train)**: 62,004 imágenes (87%)
    *   **Validación (Valid)**: 6,072 imágenes (9%)
    *   **Prueba (Test)**: 3,072 imágenes (4%)

### Preprocesamiento:
*   **Auto-Orient**: Aplicado (corrige orientación EXIF).
*   **Redimensionamiento**: Stretch a 640x640 píxeles.

### Aumentación de Datos (Data Augmentation):
Se aplicaron técnicas de aumentación para triplicar la variabilidad del set de entrenamiento (`Outputs per training example: 3`):
*   **Volteo (Flip)**: Horizontal.
*   **Rotación**: Aleatoria entre -15° y +15°.
*   **Brillo**: Variación aleatoria entre -25% y +25%.
*   **Desenfoque (Blur)**: Gaussiano hasta 1.5px.
*   **Ruido**: Inyección de ruido hasta el 1.15% de los píxeles.
