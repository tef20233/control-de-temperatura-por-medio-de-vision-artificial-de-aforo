import requests
import base64
import time
import numpy as np
import cv2
import os
from datetime import datetime

while True:
    t0 = time.perf_counter()  # Medir el tiempo de inicio

    # Hacer la petición GET
    r = requests.get("http://localhost:5001/snapshot", timeout=20)
    r.raise_for_status()  # Lanza una excepción si la respuesta es un error

    # Obtener el JSON de la respuesta
    j = r.json()
    print("Size:", j["width"], "x", j["height"])

    # Decodificar la imagen desde base64
    img_bytes = base64.b64decode(j["image_base64"])  # bytes
    nparr = np.frombuffer(img_bytes, np.uint8)  # 1D uint8 array
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)  # NumPy array (H, W, 3)

    # Generar un nombre de archivo con timestamp
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
    fname = f"{ts}.jpg"

    # Guardar la imagen en un directorio
    os.makedirs("snapshots", exist_ok=True)
    path = os.path.join("snapshots", fname)
    with open(path, "wb") as f:
        f.write(img_bytes)
        print(f"Imagen guardada como: {fname}")

    # Calcular el tiempo total de la petición (incluyendo el procesamiento)
    elapsed = time.perf_counter() - t0
    print(f"HTTP {r.status_code} en {elapsed:.3f}s")

    # Calcular cuánto tiempo esperar para completar los 10 segundos
    #pause = max(10 - elapsed, 1)  # Asegúrate de que nunca sea menor que 1 segundo
    
    pause = 3
    # Dormir el tiempo necesario para que el ciclo se repita cada 10 segundos
    time.sleep(pause)