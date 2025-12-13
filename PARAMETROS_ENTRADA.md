# ⚙️ Parámetros de Entrada del Sistema

## 1. Parámetros de Entrada del Modelo (YOLO)
El modelo de detección de objetos (`yolo11s.pt`) recibe los frames de video procesados con las siguientes características:

*   **Resolución de Entrada (Input Size)**: `512x512` píxeles.
    *   *Nota*: Las imágenes originales se redimensionan (resize) y se rellenan (pad) automáticamente para mantener la relación de aspecto (aspect ratio) antes de entrar a la red neuronal.
*   **Canales de Color**: `3` (RGB - Red, Green, Blue).
    *   *Nota*: OpenCV captura en BGR, pero la librería `ultralytics` convierte internamente a RGB.
*   **Normalización**: Los valores de píxel `[0, 255]` se normalizan a `[0.0, 1.0]` dividiendo por 255.0.
*   **Batch Size**: `1` (Inferencia en tiempo real frame a frame).
*   **Precisión de Tensores**: `FP32` (Float32) para la GTX 1050 Ti (FP16 desactivado).

## 2. Parámetros de Configuración del Algoritmo
Estos parámetros controlan cómo se interpretan las predicciones del modelo:

*   **Umbral de Confianza (Confidence Threshold)**: `0.35` (35%).
    *   *Descripción*: Solo se aceptan detecciones donde el modelo tiene más del 35% de certeza de que es una "persona".
*   **Umbral de IoU (NMS Threshold)**: `0.50` (50%).
    *   *Descripción*: Utilizado en la Supresión de No Máximos (NMS). Si dos cajas se superponen más del 50%, se elimina la de menor confianza para evitar duplicados.
*   **Clases Filtradas**: `[0]` (Person).
    *   *Descripción*: El modelo ignora cualquier otra clase (coches, perros, etc.) y solo devuelve detecciones de personas.

## 3. Parámetros de Entrada de la Fuente de Video
*   **Fuente**: Webcam (USB) o Stream IP (MJPEG/RTSP).
*   **Formato de Captura**: BGR (Blue-Green-Red) estándar de OpenCV.
*   **Resolución Nativa**: Depende de la cámara (típicamente 640x480 o 1280x720), redimensionada posteriormente a 512x512 para el modelo.
