# Protocolo Serial USB HVAC

Este protocolo define la comunicación entre el backend Python y el Arduino que emite IR hacia el aire acondicionado.

## Transporte

- Medio: `USB serial`
- Velocidad por defecto: `115200`
- Formato: `JSON Lines`
- Codificación: `UTF-8`
- Delimitador de mensaje: salto de línea `\n`

Cada comando es un objeto JSON en una sola línea.

Ejemplo:

```json
{"type":"hvac_command","protocol_version":1,"command_id":"hvac-1778960513951","source":"manual","brand":"lg","brand_display":"LG","protocol_hint":"ac_lg","transport_format":"preset","preset_key":"lg_on_cool_24c_auto_off","model":"","power":true,"mode":"cool","target_temperature_c":24.0,"fan_speed":"auto","swing":"off","occupancy_count":0,"occupancy_ratio":0.0,"human_heat_load_w":0.0,"timestamp":1778960513.9512305}
```

## Campos del comando

Campos obligatorios:

- `type`: siempre `hvac_command`
- `protocol_version`: versión del contrato, actualmente `1`
- `command_id`: identificador único del comando
- `brand`: `lg | samsung | haier | generic`
- `transport_format`: `preset | raw`
- `power`: `true | false`
- `mode`: `cool | heat | dry | fan | auto`
- `target_temperature_c`: temperatura objetivo
- `fan_speed`: `auto | low | medium | high | turbo`
- `swing`: `off | auto | vertical | horizontal | both`

Campos opcionales:

- `source`: `auto | manual`
- `brand_display`: nombre legible
- `protocol_hint`: pista para el firmware
- `preset_key`: clave de preset cuando `transport_format = preset`
- `model`: modelo del aire si se conoce
- `occupancy_count`
- `occupancy_ratio`
- `human_heat_load_w`
- `timestamp`
- `raw`: requerido cuando `transport_format = raw`

## Modo `preset`

En este modo el backend envía una clave de preset y el Arduino resuelve el código IR internamente.

Ejemplo:

```json
{
  "type": "hvac_command",
  "protocol_version": 1,
  "command_id": "hvac-1778961000000",
  "brand": "samsung",
  "transport_format": "preset",
  "preset_key": "samsung_on_cool_24c_auto_off",
  "power": true,
  "mode": "cool",
  "target_temperature_c": 24.0,
  "fan_speed": "auto",
  "swing": "off"
}
```

La clave de preset sigue esta forma:

```text
<brand>_<on|off>_<mode>_<temp>c_<fan_speed>_<swing>
```

Ejemplos:

- `lg_on_cool_24c_auto_off`
- `samsung_off_cool_27c_auto_off`
- `haier_on_dry_25c_low_vertical`

## Modo `raw`

En este modo el backend envía pulsos IR ya capturados o aprendidos.

Ejemplo:

```json
{
  "type": "hvac_command",
  "protocol_version": 1,
  "command_id": "hvac-1778961001111",
  "brand": "generic",
  "transport_format": "raw",
  "power": true,
  "mode": "cool",
  "target_temperature_c": 24.0,
  "fan_speed": "auto",
  "swing": "off",
  "raw": {
    "khz": 38,
    "pulses": [9000,4500,560,560,560,1690]
  }
}
```

Campos de `raw`:

- `khz`: frecuencia portadora IR
- `pulses`: arreglo de tiempos en microsegundos para `sendRaw()`

## Respuesta esperada del Arduino

El firmware responde con un `ack` también en JSON Lines.

Éxito:

```json
{"type":"ack","command_id":"hvac-1778960513951","success":true,"reason":"preset_sent","brand":"lg","transport_format":"preset","preset_key":"lg_on_cool_24c_auto_off"}
```

Error:

```json
{"type":"ack","command_id":"hvac-1778960513951","success":false,"reason":"preset_not_programmed","brand":"lg","transport_format":"preset","preset_key":"lg_on_cool_24c_auto_off"}
```

Razones de error previstas:

- `invalid_json`
- `unsupported_type`
- `missing_brand`
- `unsupported_brand`
- `missing_preset_key`
- `preset_not_programmed`
- `missing_raw`
- `raw_size_invalid`
- `raw_frequency_invalid`

## Recomendación operativa

- Usa `preset` cuando ya tengas capturados y programados los códigos del control remoto real.
- Usa `raw` cuando quieras probar rápidamente un código aprendido sin recompilar el firmware.
- Para aires acondicionados, `raw` es útil durante la fase de captura; `preset` es mejor para producción.
