import time
from copy import deepcopy


SUPPORTED_HVAC_BRANDS = {
    "lg": {
        "display_name": "LG",
        "protocol_hint": "ac_lg",
        "model_required": False,
    },
    "samsung": {
        "display_name": "Samsung",
        "protocol_hint": "ac_samsung",
        "model_required": False,
    },
    "haier": {
        "display_name": "Haier",
        "protocol_hint": "ac_haier",
        "model_required": False,
    },
    "challenger": {
        "display_name": "Challenger",
        "protocol_hint": "ac_challenger",
        "model_required": False,
    },
    "generic": {
        "display_name": "Genérico",
        "protocol_hint": "ac_generic",
        "model_required": False,
    },
}


class OccupancyBasedHVACController:
    """Lógica de control HVAC basada en aforo para backend."""

    def __init__(self, hvac_config=None):
        self.hvac_config = {}
        self.last_decision = None
        self.last_command = None
        self.last_command_at = 0.0
        self.smoothed_temperature = None
        self.configure(hvac_config or {})

    def configure(self, hvac_config):
        self.hvac_config = deepcopy(hvac_config or {})

    def get_supported_brands(self):
        return SUPPORTED_HVAC_BRANDS

    def _brand_info(self, brand):
        return SUPPORTED_HVAC_BRANDS.get(str(brand or "").lower(), SUPPORTED_HVAC_BRANDS["generic"])

    def evaluate(self, occupancy_count, max_capacity, occupancy_level=None):
        now = time.time()
        count = max(0, int(occupancy_count or 0))
        capacity = max(1, int(max_capacity or 1))
        occupancy_ratio = min(1.0, count / float(capacity))

        people_heat_gain_w = float(self.hvac_config.get("people_heat_gain_w", 75.0))
        human_heat_load_w = round(count * people_heat_gain_w, 2)
        design_heat_load_w = max(people_heat_gain_w, capacity * people_heat_gain_w)
        thermal_load_ratio = min(1.0, human_heat_load_w / design_heat_load_w)

        temp_cfg = self.hvac_config.get("temperature", {})
        min_temp = float(temp_cfg.get("minimum_c", 20.0))
        max_temp = float(temp_cfg.get("maximum_c", 27.0))
        vacant_temp = float(temp_cfg.get("vacant_c", max_temp))
        occupied_min_temp = float(temp_cfg.get("occupied_min_c", 23.0))
        smoothing = float(temp_cfg.get("smoothing_factor", 0.35))
        deadband_c = float(temp_cfg.get("deadband_c", 0.5))
        step_c = float(temp_cfg.get("step_c", 1.0))
        min_command_interval_s = float(temp_cfg.get("min_command_interval_s", 15.0))
        curve_exponent = float(temp_cfg.get("curve_exponent", 0.5)) # Exponente para curva no lineal (sensibilidad)

        auto_power_off_when_empty = bool(self.hvac_config.get("auto_power_off_when_empty", True))
        enabled = bool(self.hvac_config.get("enabled", False))
        control_mode = str(self.hvac_config.get("control_mode", "auto")).lower()

        occupancy_weight = float(self.hvac_config.get("occupancy_weight", 0.65))
        thermal_weight = float(self.hvac_config.get("thermal_weight", 0.35))
        demand_ratio = max(
            0.0,
            min(1.0, occupancy_ratio * occupancy_weight + thermal_load_ratio * thermal_weight),
        )

        # Aplicar curva no lineal para mayor sensibilidad/confort con aforos bajos
        demand_ratio = demand_ratio ** curve_exponent

        if count <= 0:
            raw_target_temp = vacant_temp
        else:
            cooling_span = max(0.0, vacant_temp - occupied_min_temp)
            raw_target_temp = vacant_temp - demand_ratio * cooling_span

        raw_target_temp = min(max_temp, max(min_temp, raw_target_temp))

        if self.smoothed_temperature is None:
            self.smoothed_temperature = raw_target_temp
        else:
            self.smoothed_temperature = (
                (1.0 - smoothing) * self.smoothed_temperature + smoothing * raw_target_temp
            )

        if step_c > 0:
            rounded_target_temp = round(self.smoothed_temperature / step_c) * step_c
        else:
            rounded_target_temp = self.smoothed_temperature

        rounded_target_temp = min(max_temp, max(min_temp, rounded_target_temp))
        power_on = count > 0 or not auto_power_off_when_empty

        decision = {
            "timestamp": now,
            "enabled": enabled,
            "control_mode": control_mode,
            "occupancy_count": count,
            "max_capacity": capacity,
            "occupancy_ratio": round(occupancy_ratio, 4),
            "occupancy_level": occupancy_level or "Desconocido",
            "human_heat_load_w": human_heat_load_w,
            "thermal_load_ratio": round(thermal_load_ratio, 4),
            "raw_target_temperature_c": round(raw_target_temp, 2),
            "target_temperature_c": round(rounded_target_temp, 2),
            "recommended_power": power_on,
            "mode": str(self.hvac_config.get("mode", "cool")).lower(),
            "fan_speed": str(self.hvac_config.get("fan_speed", "auto")).lower(),
            "swing": str(self.hvac_config.get("swing", "off")).lower(),
            "brand": str(self.hvac_config.get("brand", "generic")).lower(),
            "model": str(self.hvac_config.get("model", "") or ""),
            "should_dispatch": False,
            "reason": "hvac_disabled",
        }

        if not enabled:
            decision["reason"] = "hvac_disabled"
        elif control_mode != "auto":
            decision["reason"] = "manual_mode"
        else:
            if self._requires_dispatch(decision, deadband_c, min_command_interval_s):
                decision["should_dispatch"] = True
                decision["reason"] = "dispatch_required"
            else:
                decision["reason"] = "stable"

        self.last_decision = decision
        return decision

    def _requires_dispatch(self, decision, deadband_c, min_command_interval_s):
        if self.last_command is None:
            return True

        if decision["recommended_power"] != self.last_command.get("power"):
            return self._cooldown_ok(min_command_interval_s)

        last_temp = float(self.last_command.get("target_temperature_c", decision["target_temperature_c"]))
        if abs(decision["target_temperature_c"] - last_temp) >= deadband_c:
            return self._cooldown_ok(min_command_interval_s)

        if decision["fan_speed"] != self.last_command.get("fan_speed"):
            return self._cooldown_ok(min_command_interval_s)

        if decision["mode"] != self.last_command.get("mode"):
            return self._cooldown_ok(min_command_interval_s)

        return False

    def _cooldown_ok(self, min_command_interval_s):
        return (time.time() - self.last_command_at) >= min_command_interval_s

    def _build_preset_key(self, brand, power, mode, target_temperature_c, fan_speed, swing):
        power_token = "on" if power else "off"
        temp_token = f"{int(round(float(target_temperature_c))):02d}c"
        return f"{brand}_{power_token}_{mode}_{temp_token}_{fan_speed}_{swing}"

    def build_command(self, decision, source="auto", overrides=None):
        overrides = overrides or {}
        brand = str(overrides.get("brand", decision.get("brand", self.hvac_config.get("brand", "generic")))).lower()
        brand_info = self._brand_info(brand)
        power = bool(overrides.get("power", decision.get("recommended_power", True)))
        mode = str(overrides.get("mode", decision.get("mode", "cool"))).lower()
        target_temperature_c = float(overrides.get("target_temperature_c", decision.get("target_temperature_c", 24.0)))
        fan_speed = str(overrides.get("fan_speed", decision.get("fan_speed", self.hvac_config.get("fan_speed", "auto")))).lower()
        swing = str(overrides.get("swing", decision.get("swing", self.hvac_config.get("swing", "off")))).lower()
        preset_key = str(
            overrides.get(
                "preset_key",
                self._build_preset_key(brand, power, mode, target_temperature_c, fan_speed, swing),
            )
        )
        command_id = str(overrides.get("command_id", f"hvac-{int(time.time() * 1000)}"))
        raw_payload = overrides.get("raw")

        command = {
            "type": "hvac_command",
            "protocol_version": 1,
            "command_id": command_id,
            "source": source,
            "brand": brand,
            "brand_display": brand_info["display_name"],
            "protocol_hint": brand_info["protocol_hint"],
            "transport_format": "raw" if raw_payload else "preset",
            "preset_key": preset_key,
            "model": str(overrides.get("model", decision.get("model", self.hvac_config.get("model", ""))) or ""),
            "power": power,
            "mode": mode,
            "target_temperature_c": target_temperature_c,
            "fan_speed": fan_speed,
            "swing": swing,
            "occupancy_count": int(decision.get("occupancy_count", 0)),
            "occupancy_ratio": float(decision.get("occupancy_ratio", 0.0)),
            "human_heat_load_w": float(decision.get("human_heat_load_w", 0.0)),
            "timestamp": time.time(),
        }
        if raw_payload:
            command["raw"] = raw_payload
        return command

    def build_serial_payload(self, command):
        """Genera el JSON simplificado para el Arduino para ahorrar RAM."""
        return {
            "t": "hvac",
            "id": command.get("command_id", ""),
            "b": command.get("brand", "generic"),
            "p": 1 if command.get("power") else 0,
            "m": command.get("mode", "cool"),
            "temp": int(command.get("target_temperature_c", 24)),
            "f": command.get("fan_speed", "auto"),
            "s": 1 if command.get("swing") == "on" else 0
        }

    def register_dispatch(self, command, transport_result=None):
        self.last_command = deepcopy(command)
        self.last_command_at = time.time()
        status = {
            "last_command": self.last_command,
            "last_command_at": self.last_command_at,
            "transport": transport_result or {},
        }
        return status

    def get_status(self):
        return {
            "config": deepcopy(self.hvac_config),
            "last_decision": deepcopy(self.last_decision),
            "last_command": deepcopy(self.last_command),
            "last_command_at": self.last_command_at,
            "supported_brands": self.get_supported_brands(),
        }
