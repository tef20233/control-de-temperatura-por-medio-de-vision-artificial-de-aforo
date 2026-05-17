import json
import threading
import time

try:
    import serial
    from serial.tools import list_ports
except ImportError:  # pragma: no cover - depende del entorno
    serial = None
    list_ports = None


class ArduinoSerialBridge:
    """Puente simple entre el backend y un Arduino conectado por USB serial."""

    def __init__(self, serial_config=None):
        self._lock = threading.Lock()
        self._serial = None
        self.enabled = False
        self.port = ""
        self.baudrate = 115200
        self.timeout_s = 1.0
        self.auto_connect = False
        self.simulation_mode = True
        self.reset_delay_s = 2.0
        self.last_error = None
        self.last_sent_at = None
        self.last_payload = None
        self.configure(serial_config or {})

    def configure(self, serial_config):
        self.enabled = bool(serial_config.get("enabled", False))
        self.port = str(serial_config.get("port", "") or "")
        self.baudrate = int(serial_config.get("baudrate", 115200))
        self.timeout_s = float(serial_config.get("timeout_s", 1.0))
        self.auto_connect = bool(serial_config.get("auto_connect", False))
        self.simulation_mode = bool(serial_config.get("simulation_mode", True))
        self.reset_delay_s = float(serial_config.get("reset_delay_s", 2.0))
        if self.simulation_mode:
            self.last_error = None

    def available_ports(self):
        if list_ports is None:
            return []

        ports = []
        for port in list_ports.comports():
            ports.append(
                {
                    "device": port.device,
                    "description": port.description,
                    "manufacturer": getattr(port, "manufacturer", None),
                    "hwid": port.hwid,
                }
            )
        return ports

    def connect(self):
        with self._lock:
            if self.simulation_mode:
                self.last_error = None
                return {"success": True, "connected": False, "simulated": True}

            if serial is None:
                self.last_error = "pyserial no está instalado"
                return {"success": False, "connected": False, "error": self.last_error}

            if not self.port:
                self.last_error = "No se configuró puerto serial"
                return {"success": False, "connected": False, "error": self.last_error}

            if self._serial and self._serial.is_open:
                return {"success": True, "connected": True, "port": self.port}

            try:
                self._serial = serial.Serial(
                    self.port,
                    self.baudrate,
                    timeout=self.timeout_s,
                    write_timeout=self.timeout_s,
                )
                time.sleep(self.reset_delay_s)
                self.last_error = None
                return {
                    "success": True,
                    "connected": True,
                    "port": self.port,
                    "baudrate": self.baudrate,
                }
            except Exception as exc:  # noqa: BLE001
                self.last_error = str(exc)
                self._serial = None
                return {"success": False, "connected": False, "error": self.last_error}

    def disconnect(self):
        with self._lock:
            if self._serial is not None:
                try:
                    self._serial.close()
                except Exception:  # noqa: BLE001
                    pass
                self._serial = None
            return {"success": True, "connected": False}

    def is_connected(self):
        return bool(self._serial is not None and self._serial.is_open)

    def send_payload(self, payload):
        message = json.dumps(payload, ensure_ascii=True, separators=(",", ":")) + "\n"

        with self._lock:
            self.last_payload = payload
            self.last_sent_at = time.time()

            if self.simulation_mode:
                self.last_error = None
                return {
                    "success": True,
                    "sent": True,
                    "simulated": True,
                    "payload": payload,
                }

            if not self.enabled:
                return {
                    "success": False,
                    "sent": False,
                    "reason": "serial_disabled",
                    "simulated": False,
                }

            if not self.is_connected():
                if self.auto_connect:
                    connect_result = self.connect()
                    if not connect_result.get("success"):
                        return {
                            "success": False,
                            "sent": False,
                            "reason": "connect_failed",
                            "error": self.last_error,
                        }
                else:
                    return {
                        "success": False,
                        "sent": False,
                        "reason": "not_connected",
                        "error": self.last_error,
                    }

            try:
                self._serial.write(message.encode("utf-8"))
                self._serial.flush()
                self.last_error = None
                return {
                    "success": True,
                    "sent": True,
                    "simulated": False,
                    "port": self.port,
                    "payload": payload,
                }
            except Exception as exc:  # noqa: BLE001
                self.last_error = str(exc)
                return {
                    "success": False,
                    "sent": False,
                    "reason": "write_failed",
                    "error": self.last_error,
                }

    def get_status(self):
        return {
            "enabled": self.enabled,
            "simulation_mode": self.simulation_mode,
            "connected": self.is_connected(),
            "port": self.port,
            "baudrate": self.baudrate,
            "auto_connect": self.auto_connect,
            "last_error": self.last_error,
            "last_sent_at": self.last_sent_at,
            "last_payload": self.last_payload,
        }
