# Firmware Arduino HVAC IR

Firmware base para recibir comandos HVAC por `USB serial` en formato JSON y emitirlos por un LED infrarrojo.

## Librerías requeridas

- `ArduinoJson`
- `IRremote`

Instálalas desde el Library Manager del IDE de Arduino.

## Hardware mínimo

- Arduino con conexión USB serial
- LED IR + resistencia
- Transistor recomendado para mejorar alcance

Pin por defecto del emisor IR:

- `D3`

Si cambias el pin, modifica `IR_SEND_PIN` en [arduino_hvac_ir.ino](</c:/Users/stefh/Desktop/app_aforo/hardware/arduino_hvac_ir/arduino_hvac_ir.ino:5>).

## Qué hace hoy

- Recibe comandos `hvac_command` por serial
- Soporta `transport_format = preset`
- Soporta `transport_format = raw`
- Responde con `ack` por serial

## Limitación actual

Los presets por marca todavía están vacíos a propósito.  
Eso significa:

- `lg`, `samsung`, `haier` y `generic` ya tienen estructura de resolución
- pero aún debes cargar los pulsos IR reales de tu control remoto

## Dónde agregar códigos reales

Edita estas funciones:

- `resolveLgPreset(...)`
- `resolveSamsungPreset(...)`
- `resolveHaierPreset(...)`
- `resolveGenericPreset(...)`

Están en [arduino_hvac_ir.ino](</c:/Users/stefh/Desktop/app_aforo/hardware/arduino_hvac_ir/arduino_hvac_ir.ino:24>).

## Estrategia recomendada

1. Empezar con `raw`
2. Capturar los códigos reales del control remoto
3. Validar que el aire responde
4. Convertir esos códigos capturados a presets por marca/modelo

## Protocolo

La definición completa del contrato está en:

[docs/PROTOCOLO_SERIAL_ARDUINO_HVAC.md](</c:/Users/stefh/Desktop/app_aforo/docs/PROTOCOLO_SERIAL_ARDUINO_HVAC.md:1>)
