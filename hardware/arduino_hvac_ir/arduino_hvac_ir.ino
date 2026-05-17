#include <ArduinoJson.h>
#include <IRremote.hpp>

// Hardware
static const uint8_t IR_SEND_PIN = 3;
static const uint32_t SERIAL_BAUD = 115200;

// Buffers
static const size_t SERIAL_BUFFER_SIZE = 768;
static const size_t JSON_DOC_SIZE = 1024;
static const size_t MAX_RAW_PULSES = 180;

char serialBuffer[SERIAL_BUFFER_SIZE];
size_t serialLength = 0;
uint16_t rawPulses[MAX_RAW_PULSES];

struct PresetPayload {
  const uint16_t* pulses;
  uint16_t pulseCount;
  uint8_t khz;
  bool programmed;
};

// ---------------------------------------------------------------------------
// Presets programables por marca.
// Reemplaza estas funciones cuando captures los códigos reales de tu control.
// Si aún no tienes códigos, el firmware responderá preset_not_programmed.
// ---------------------------------------------------------------------------

PresetPayload resolveLgPreset(const char* presetKey) {
  (void)presetKey;
  return {nullptr, 0, 38, false};
}

PresetPayload resolveSamsungPreset(const char* presetKey) {
  (void)presetKey;
  return {nullptr, 0, 38, false};
}

PresetPayload resolveHaierPreset(const char* presetKey) {
  (void)presetKey;
  return {nullptr, 0, 38, false};
}

PresetPayload resolveGenericPreset(const char* presetKey) {
  (void)presetKey;
  return {nullptr, 0, 38, false};
}

PresetPayload resolvePreset(const char* brand, const char* presetKey, bool& knownBrand) {
  knownBrand = true;

  if (strcmp(brand, "lg") == 0) {
    return resolveLgPreset(presetKey);
  }
  if (strcmp(brand, "samsung") == 0) {
    return resolveSamsungPreset(presetKey);
  }
  if (strcmp(brand, "haier") == 0) {
    return resolveHaierPreset(presetKey);
  }
  if (strcmp(brand, "generic") == 0) {
    return resolveGenericPreset(presetKey);
  }

  knownBrand = false;
  return {nullptr, 0, 0, false};
}

void sendAck(
  const char* commandId,
  bool success,
  const char* reason,
  const char* brand,
  const char* transportFormat,
  const char* presetKey
) {
  StaticJsonDocument<320> ack;
  ack["type"] = "ack";
  ack["command_id"] = commandId ? commandId : "";
  ack["success"] = success;
  ack["reason"] = reason ? reason : "";
  ack["brand"] = brand ? brand : "";
  ack["transport_format"] = transportFormat ? transportFormat : "";
  if (presetKey && presetKey[0] != '\0') {
    ack["preset_key"] = presetKey;
  }
  serializeJson(ack, Serial);
  Serial.println();
}

bool copyRawPulses(JsonArrayConst pulses, const char*& errorReason) {
  const size_t count = pulses.size();
  if (count == 0 || count > MAX_RAW_PULSES) {
    errorReason = "raw_size_invalid";
    return false;
  }

  for (size_t i = 0; i < count; i++) {
    const long value = pulses[i] | 0;
    if (value <= 0 || value > 65535) {
      errorReason = "raw_size_invalid";
      return false;
    }
    rawPulses[i] = static_cast<uint16_t>(value);
  }

  errorReason = nullptr;
  return true;
}

// --- LG AC Protocol (28 bits) ---
// Estructura: 0x88 (Header) | Op (4 bits) | Mode (3 bits) | Temp (4 bits) | Fan (3 bits) | Checksum (4 bits)
void sendLgAc(bool power, const char* mode, int temp, const char* fan) {
  uint32_t code = 0x8800000;
  
  if (!power) {
    // Código de apagado estándar LG: 0x88C0051
    IrSender.sendLG(0x88, 0xC0051, 0);
    return;
  }

  uint8_t op = 0x0; // 0 = Control de temperatura / modo
  uint8_t m = 0;    // 0:Cool, 1:Dry, 2:Fan, 4:Heat
  if (strcmp(mode, "dry") == 0) m = 1;
  else if (strcmp(mode, "fan") == 0) m = 2;
  else if (strcmp(mode, "heat") == 0) m = 4;
  else m = 0; // cool por defecto

  uint8_t t = (uint8_t)(constrain(temp, 18, 30) - 15);
  
  uint8_t f = 0; // 0:Low, 2:Mid, 4:High, 5:Natural
  if (strcmp(fan, "low") == 0) f = 0;
  else if (strcmp(fan, "mid") == 0) f = 2;
  else if (strcmp(fan, "high") == 0) f = 4;
  else f = 5; // auto/natural

  // Construir payload (bits 8-23)
  // [Op:4][Mode:3][0:1][Temp:4][0:1][Fan:3]
  uint32_t payload = 0;
  payload |= ((uint32_t)op << 12);
  payload |= ((uint32_t)m << 9);
  payload |= ((uint32_t)t << 4);
  payload |= (uint32_t)f;

  // Checksum: Suma de los nibbles del payload
  uint8_t checksum = (op + m + t + f) & 0x0F;
  
  uint32_t finalCode = 0x8800000 | (payload << 4) | checksum;
  
  // Enviar usando el protocolo LG (28 bits)
  IrSender.sendLG(0x88, (finalCode & 0xFFFFF), 0); 
}

void handleHvacCommand(JsonDocument& doc) {
  const char* commandId = doc["id"] | "";
  const char* brand = doc["b"] | "";
  bool power = (doc["p"] | 0) == 1;
  const char* mode = doc["m"] | "cool";
  int temp = doc["temp"] | 24;
  const char* fan = doc["f"] | "auto";
  int swing = doc["s"] | 0;

  if (brand[0] == '\0') {
    sendAck(commandId, false, "missing_brand", brand, "hvac", "");
    return;
  }

  bool success = false;
  const char* msg = "unknown_error";

  // Lógica por marca
  if (strcmp(brand, "lg") == 0) {
    sendLgAc(power, mode, temp, fan);
    success = true;
    msg = "lg_sent";
  } 
  else if (strcmp(brand, "samsung") == 0) {
    // Samsung usa un protocolo de 15 bytes muy complejo. 
    // Requiere capturar el código completo o usar librerías específicas de AC.
    success = false;
    msg = "samsung_requires_raw_or_ac_library";
  }
  else if (strcmp(brand, "haier") == 0) {
    success = false;
    msg = "haier_requires_raw_or_ac_library";
  }
  else if (strcmp(brand, "generic") == 0) {
    success = false;
    msg = "generic_not_implemented";
  } else {
    msg = "unsupported_brand";
  }

  sendAck(commandId, success, msg, brand, "hvac", "");
}

void processLine(const char* line) {
  StaticJsonDocument<JSON_DOC_SIZE> doc;
  DeserializationError error = deserializeJson(doc, line);

  if (error) {
    sendAck("", false, "invalid_json", "", "", "");
    return;
  }

  const char* type = doc["t"] | "";
  if (strcmp(type, "hvac") == 0) {
    handleHvacCommand(doc);
    return;
  }

  sendAck(doc["id"] | "", false, "unsupported_type", doc["b"] | "", "", "");
}

void readSerialLines() {
  while (Serial.available() > 0) {
    char c = static_cast<char>(Serial.read());

    if (c == '\r') {
      continue;
    }

    if (c == '\n') {
      serialBuffer[serialLength] = '\0';
      if (serialLength > 0) {
        processLine(serialBuffer);
      }
      serialLength = 0;
      continue;
    }

    if (serialLength < (SERIAL_BUFFER_SIZE - 1)) {
      serialBuffer[serialLength++] = c;
    } else {
      serialLength = 0;
      sendAck("", false, "invalid_json", "", "", "");
    }
  }
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  Serial.setTimeout(50);
  IrSender.begin(IR_SEND_PIN, ENABLE_LED_FEEDBACK);

  while (!Serial) {
    ;  // Solo relevante en placas con USB nativo.
  }

  StaticJsonDocument<192> boot;
  boot["type"] = "boot";
  boot["firmware"] = "arduino_hvac_ir";
  boot["protocol_version"] = 1;
  boot["ready"] = true;
  serializeJson(boot, Serial);
  Serial.println();
}

void loop() {
  readSerialLines();
}
