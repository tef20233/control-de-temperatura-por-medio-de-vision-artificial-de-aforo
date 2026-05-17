# Contrato Serial: Backend <-> Arduino (HVAC IR)

Este documento define el protocolo de comunicación serial (USB) para el sistema de control de aire acondicionado.

## Configuración Serial
- **Baudrate:** 115200
- **Data bits:** 8
- **Parity:** None
- **Stop bits:** 1
- **Terminador de línea:** `\n` (LF)

---

## 1. PC -> Arduino (Comandos)

El PC envía una única línea de texto conteniendo un objeto JSON simplificado.

### Formato General
```json
{
  "t": "hvac",
  "id": "string",
  "b": "string",
  "p": number,
  "m": "string",
  "temp": number,
  "f": "string",
  "s": number
}
```

### Campos
| Campo | Descripción | Valores posibles |
| :--- | :--- | :--- |
| `t` | Tipo de mensaje | Siempre `"hvac"` |
| `id` | ID único de comando | Ej: `"hvac-1715886542"` |
| `b` | Marca (Brand) | `"lg"`, `"samsung"`, `"haier"`, `"generic"` |
| `p` | Power | `0` (Off), `1` (On) |
| `m` | Modo | `"cool"`, `"heat"`, `"fan"`, `"dry"`, `"auto"` |
| `temp` | Temperatura | `16` a `30` |
| `f` | Fan Speed | `"auto"`, `"low"`, `"mid"`, `"high"` |
| `s` | Swing | `0` (Off), `1` (On) |

---

## 2. Arduino -> PC (Respuestas)

El Arduino responde con un JSON para confirmar la recepción y ejecución.

### Mensaje de Inicio (Boot)
Enviado al encender o resetear el Arduino.
```json
{"t":"boot","firmware":"arduino_hvac_ir","version":1,"ready":true}
```

### Confirmación de Comando (Ack)
```json
{
  "t": "ack",
  "id": "string",
  "ok": boolean,
  "msg": "string"
}
```

#### Valores de `msg` comunes:
- `"preset_sent"`: Código IR enviado con éxito.
- `"invalid_json"`: Error de parseo.
- `"unsupported_brand"`: La marca no está implementada.
- `"brand_not_programmed"`: Marca conocida pero sin códigos IR cargados.

---

## 3. Ejemplo de Flujo Completo

1. **PC envía:** `{"t":"hvac","id":"101","b":"lg","p":1,"m":"cool","temp":24,"f":"auto","s":0}`
2. **Arduino procesa:** Identifica que es LG, modo Cool a 24°C.
3. **Arduino emite IR:** Genera la señal IR específica para LG.
4. **Arduino responde:** `{"t":"ack","id":"101","ok":true,"msg":"sent_lg"}`
