import os, cv2, time, subprocess, numpy as np
from datetime import datetime

# ==== CONFIG DIRECTA ====
CAMERA_IP   = "192.168.222.224"     # IP actual
USERNAME    = "admin1"           # Usuario RTSP (cuenta de cámara en la app)
PASSWORD    = "987654321Usco.,"           # Clave RTSP
SAVE_FOLDER = os.path.join(os.path.expanduser("~"), "Pictures", "cam_8")
CAPTURE_EVERY_S = 5              # Guardar JPG cada N segundos
CAPTURE_FIRST   = True             # Guardar inmediatamente al conectar

# Intentos de rutas RTSP (primero las que sabemos que te funcionan)
RTSP_BASE_PATHS = [
    "/stream1",
    "/stream2",
]
# Algunas cámaras agradecen ?transportmode=unicast
RTSP_QUERY_SUFFIXES = [
    "",
    "?transportmode=unicast",
]

OUT_W, OUT_H = 1280, 720
WINDOW_TITLE = "Tapo RTSP — 'q' para salir"

# 👉 RUTA A TU ffmpeg.exe (según 'where ffmpeg')
FFMPEG_BIN = "ffmpeg"  # Se asume que ffmpeg está en el PATH de Windows

os.makedirs(SAVE_FOLDER, exist_ok=True)

def build_urls():
    base = f"rtsp://{USERNAME}:{PASSWORD}@{CAMERA_IP}:554"
    urls = []
    for path in RTSP_BASE_PATHS:
        for q in RTSP_QUERY_SUFFIXES:
            urls.append(base + path + q)
    return urls

def start_ffmpeg(url: str):
    """
    Lanza ffmpeg para sacar frames BGR24 por stdout (pipe).
    Igualamos flags a ffplay: solo forzamos TCP y quitamos stimeout/rw_timeout.
    """
    cmd = [
        FFMPEG_BIN,
        "-hide_banner", "-loglevel", "warning",
        "-rtsp_transport", "tcp",
        "-rtsp_flags", "prefer_tcp",
        "-fflags", "nobuffer",         # baja latencia
        "-flags", "low_delay",         # baja latencia
        "-i", url,
        "-an",                         # sin audio
        "-vf", f"scale={OUT_W}:{OUT_H}",
        "-pix_fmt", "bgr24",
        "-f", "rawvideo",
        "pipe:1",
    ]
    print(f"[INFO] Capturando desde: {url}")
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=10**7)

def read_frame(proc: subprocess.Popen):
    frame_size = OUT_W * OUT_H * 3
    raw = proc.stdout.read(frame_size)
    if not raw or len(raw) != frame_size:
        return None
    return np.frombuffer(raw, dtype=np.uint8).reshape((OUT_H, OUT_W, 3))

def try_capture_once(url: str, warmup_frames: int = 5, warmup_timeout_s: float = 8.0):
    """
    Intenta abrir y leer algunos frames de calentamiento.
    Devuelve (proc, first_frame) si logra leer, o (None, None) si falla.
    """
    proc = start_ffmpeg(url)
    start_t = time.time()
    frames_read = 0
    first_frame = None

    while time.time() - start_t < warmup_timeout_s:
        frame = read_frame(proc)
        if frame is None:
            time.sleep(0.1)
            continue
        frames_read += 1
        if first_frame is None:
            first_frame = frame
        if frames_read >= warmup_frames:
            return proc, first_frame

    # Diagnóstico y cierre si no calentó
    try:
        tail = proc.stderr.read().decode(errors="ignore")[-800:]
        if tail:
            print("[WARN] FFmpeg stderr:\n" + tail)
    except Exception:
        pass
    try:
        proc.kill()
    except Exception:
        pass
    return None, None

def capture_loop(proc: subprocess.Popen, first_frame):
    last = -1e9 if CAPTURE_FIRST else time.time()

    while True:
        frame = first_frame if first_frame is not None else read_frame(proc)
        first_frame = None

        if frame is None:
            try:
                tail = proc.stderr.read().decode(errors="ignore")[-800:]
                if tail:
                    print("[WARN] FFmpeg stderr:\n" + tail)
            except Exception:
                pass
            print("[WARN] Se perdió la lectura. Intentaremos otra ruta / reconectar.")
            return False

        cv2.imshow(WINDOW_TITLE, frame)

        now = time.time()
        if now - last >= CAPTURE_EVERY_S:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(SAVE_FOLDER, f"captura_{ts}.jpg")
            cv2.imwrite(path, frame)
            print(f"[INFO] guardado: {path}")
            last = now

        if cv2.waitKey(1) & 0xFF == ord('q'):
            return True

def main():
    urls = build_urls()

    for url in urls:
        print(f"[INFO] Probando {url}")
        proc, first = try_capture_once(url)
        if proc is None:
            print("   → no pudo iniciar con esta ruta. Probando la siguiente…")
            continue

        print("[OK] Video abierto. Iniciando captura…")
        user_quit = capture_loop(proc, first)
        # Limpieza
        try: proc.kill()
        except Exception: pass
        try:
            if proc.stdout: proc.stdout.close()
            if proc.stderr: proc.stderr.close()
        except Exception: pass
        try: cv2.destroyAllWindows()
        except Exception: pass

        if user_quit:
            print("[INFO] Salida por usuario.")
            return
        else:
            print("[INFO] Intentando otra ruta tras pérdida de lectura…")
            # sigue el for para probar siguiente url

    print("❌ No se pudo capturar desde ninguna ruta. Como ffplay abre /stream1, debería funcionar con la primera URL.")

if __name__ == "__main__":
    main()
