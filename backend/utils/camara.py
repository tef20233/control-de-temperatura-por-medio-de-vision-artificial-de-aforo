#!/usr/bin/env python3
from flask import Flask, jsonify, request
from pytapo import Tapo
from pytapo.media_stream.streamer import Streamer

import asyncio
from io import BytesIO
from PIL import Image
import base64

app = Flask(__name__)

# --- Camera config ---
HOST = "192.168.222.224"
USER = "admin"
PASSWORD_CLOUD = "soldado1"  # adjust as needed

def encode_base64_from_jpeg_bytes(jpeg_bytes: bytes) -> str:
    return base64.b64encode(jpeg_bytes).decode("ascii")

def grab_jpeg_once_sync() -> bytes:
    """
    Synchronous wrapper:
    1) Build Tapo synchronously (so pytapo can safely call asyncio.run() internally).
    2) Use asyncio.run() exactly once to drive our own Streamer workflow.
    """
    tapo = Tapo(HOST, USER, PASSWORD_CLOUD, PASSWORD_CLOUD, printDebugInformation=False)

    async def _worker() -> bytes:
        streamer = Streamer(
            tapo,
            includeAudio=False,
            quality="HD",
            ff_args={
                "-frames:v": "1",       # single frame
                "-f": "image2pipe",
                "-c:v": "mjpeg",
                "-vsync": "0",
            },
        )

        info = await streamer.start()
        proc = info["ffmpegProcess"]
        try:
            # Optional timeout (battery cams may sleep); adjust seconds as needed
            jpeg = await asyncio.wait_for(proc.stdout.read(), timeout=10)
            await proc.wait()
            return jpeg
        finally:
            try:
                await streamer.stop()
            finally:
                if "streamProcess" in info:
                    info["streamProcess"].cancel()

    return asyncio.run(_worker())

@app.post("/move")
def move_camera():
    import json, time
    data = json.loads(request.data)

    horiz = int(data.get("horiz", 0))
    vert = int(data.get("vert", 0))
    steps = int(data.get("steps", 1))  # número de pasos a realizar
    delay = float(data.get("delay", 0.5))  # segundos entre pasos

    tapo = Tapo(HOST, USER, PASSWORD_CLOUD, PASSWORD_CLOUD)

    for i in range(steps):
        tapo.moveMotor(horiz, vert)
        time.sleep(delay)  # pausa entre movimientos

    return jsonify({
        "status": "ok",
        "horiz": horiz,
        "vert": vert,
        "steps": steps,
        "delay": delay
    })



@app.get("/snapshot")
def http_snapshot():
    jpeg = grab_jpeg_once_sync()

    # Get dimensions (no re-encode)
    with Image.open(BytesIO(jpeg)) as img:
        width, height = img.size

    b64 = encode_base64_from_jpeg_bytes(jpeg)
    data_url = f"data:image/jpeg;base64,{b64}"

    return jsonify({
        "format": "jpeg",
        "width": int(width),
        "height": int(height),
        "image_base64": b64,
        "data_url": data_url
    })

@app.get("/live")
def live_stream():
    import cv2
    from flask import Response

    stream_url = f"rtsp://{USER}:{PASSWORD_CLOUD}@{HOST}:554/stream1"
    cap = cv2.VideoCapture(stream_url)

    def generate():
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            ret, jpeg = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    # Make sure ffmpeg is installed and on PATH (or in your conda env).
    # conda:  conda install -c conda-forge ffmpeg
    app.run(host="0.0.0.0", port=5001, debug=True)








