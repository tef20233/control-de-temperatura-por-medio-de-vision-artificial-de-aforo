#include <ArduinoJson.h>
#include <IRremote.hpp>
#include <ctype.h>

// -----------------------------------------------------------------------------
// Firmware Arduino HVAC IR
// -----------------------------------------------------------------------------
// Soporta 3 formas de comando por Serial, una por línea:
//
// 1) HVAC compacto:
// {"t":"hvac","id":"cmd-1","b":"lg","p":1,"m":"cool","temp":24,"f":"auto"}
//
// 2) HVAC verbose:
// {"type":"hvac","command_id":"cmd-1","brand":"lg","power":true,"mode":"cool","temperature":24,"fan":"auto"}
//
// 3) RAW universal:
// {"t":"raw","id":"cmd-2","b":"samsung","khz":38,"pulses":[9000,4500,560,560]}
//
// 4) Preset:
// {"t":"preset","id":"cmd-3","b":"lg","preset_key":"cool_24_auto"}
//
// El firmware responde siempre con JSON:
// {"type":"ack","command_id":"...","success":true/false,"reason":"..."}
// -----------------------------------------------------------------------------

// Hardware
static const uint8_t IR_SEND_PIN = 9;
static const uint32_t SERIAL_BAUD = 115200;

// Buffers
static const size_t SERIAL_BUFFER_SIZE = 1024;
static const size_t JSON_DOC_SIZE = 1536;
static const size_t MAX_RAW_PULSES = 220;

// IR
static const uint8_t DEFAULT_IR_KHZ = 38;
static const uint8_t DEFAULT_REPEATS = 1;
static const uint8_t MAX_REPEATS = 5;
static const uint16_t RAW_SEND_GAP_MS = 70;

char serialBuffer[SERIAL_BUFFER_SIZE];
size_t serialLength = 0;
uint16_t rawPulses[MAX_RAW_PULSES];

struct PresetPayload {
  const uint16_t *pulses;
  uint16_t pulseCount;
  uint8_t khz;
  bool programmed;
};

// -----------------------------------------------------------------------------
// Utilidades
// -----------------------------------------------------------------------------

bool equalsIgnoreCase(const char *a, const char *b) {
  if (!a || !b)
    return false;

  while (*a && *b) {
    if (tolower((unsigned char)*a) != tolower((unsigned char)*b)) {
      return false;
    }

    a++;
    b++;
  }

  return *a == '\0' && *b == '\0';
}

const char *getStringOr(JsonDocument &doc, const char *shortKey,
                        const char *longKey, const char *fallback) {
  const char *value = doc[shortKey].as<const char*>();

  if (value && value[0] != '\0') {
    return value;
  }

  value = doc[longKey].as<const char*>();

  if (value && value[0] != '\0') {
    return value;
  }

  return fallback;
}

int getIntOr(JsonDocument &doc, const char *shortKey, const char *longKey,
             int fallback) {
  if (!doc[shortKey].isNull()) {
    return doc[shortKey] | fallback;
  }

  if (!doc[longKey].isNull()) {
    return doc[longKey] | fallback;
  }

  return fallback;
}

bool readPower(JsonDocument &doc, bool fallback) {
  JsonVariant value = !doc["p"].isNull() ? doc["p"] : doc["power"];

  if (value.isNull()) {
    return fallback;
  }

  if (value.is<bool>()) {
    return value.as<bool>();
  }

  if (value.is<int>()) {
    return value.as<int>() == 1;
  }

  const char *text = value.as<const char *>();

  if (!text) {
    return fallback;
  }

  return equalsIgnoreCase(text, "on") || equalsIgnoreCase(text, "true") ||
         equalsIgnoreCase(text, "1");
}

uint8_t readRepeats(JsonDocument &doc) {
  int repeats = getIntOr(doc, "r", "repeats", DEFAULT_REPEATS);
  return (uint8_t)constrain(repeats, 1, MAX_REPEATS);
}

void sendAck(const char *commandId, bool success, const char *reason,
             const char *brand, const char *transportFormat,
             const char *presetKey = "") {
  StaticJsonDocument<384> ack;

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

bool copyRawPulses(JsonArrayConst pulses, uint16_t &pulseCount,
                   const char *&errorReason) {
  const size_t count = pulses.size();

  if (count == 0) {
    errorReason = "raw_empty";
    return false;
  }

  if (count > MAX_RAW_PULSES) {
    errorReason = "raw_too_long";
    return false;
  }

  for (size_t i = 0; i < count; i++) {
    const long value = pulses[i] | 0;

    if (value <= 0 || value > 65535) {
      errorReason = "raw_pulse_invalid";
      return false;
    }

    rawPulses[i] = static_cast<uint16_t>(value);
  }

  pulseCount = static_cast<uint16_t>(count);
  errorReason = nullptr;
  return true;
}

void sendRawPulses(uint16_t pulseCount, uint8_t khz, uint8_t repeats) {
  khz = constrain(khz, 30, 60);

  for (uint8_t i = 0; i < repeats; i++) {
    IrSender.sendRaw(rawPulses, pulseCount, khz);

    if (i + 1 < repeats) {
      delay(RAW_SEND_GAP_MS);
    }
  }
}

// -----------------------------------------------------------------------------
// Presets programables por marca.
// Reemplaza estas funciones con códigos RAW reales capturados de cada control.
// -----------------------------------------------------------------------------

PresetPayload resolveLgPreset(const char *presetKey) {
  /*
    Ejemplo futuro:

    static const uint16_t LG_COOL_24_AUTO[] PROGMEM = {
      9000, 4500, 560, 560
    };

    if (equalsIgnoreCase(presetKey, "cool_24_auto")) {
      return {
        LG_COOL_24_AUTO,
        sizeof(LG_COOL_24_AUTO) / sizeof(LG_COOL_24_AUTO[0]),
        38,
        true
      };
    }
  */

  (void)presetKey;
  return {nullptr, 0, DEFAULT_IR_KHZ, false};
}

PresetPayload resolveSamsungPreset(const char *presetKey) {
  (void)presetKey;
  return {nullptr, 0, DEFAULT_IR_KHZ, false};
}

PresetPayload resolveHaierPreset(const char *presetKey) {
  (void)presetKey;
  return {nullptr, 0, DEFAULT_IR_KHZ, false};
}

PresetPayload resolveGenericPreset(const char *presetKey) {
  (void)presetKey;
  return {nullptr, 0, DEFAULT_IR_KHZ, false};
}

PresetPayload resolvePreset(const char *brand, const char *presetKey,
                            bool &knownBrand) {
  knownBrand = true;

  if (equalsIgnoreCase(brand, "lg")) {
    return resolveLgPreset(presetKey);
  }

  if (equalsIgnoreCase(brand, "samsung")) {
    return resolveSamsungPreset(presetKey);
  }

  if (equalsIgnoreCase(brand, "haier")) {
    return resolveHaierPreset(presetKey);
  }

  if (equalsIgnoreCase(brand, "generic")) {
    return resolveGenericPreset(presetKey);
  }

  knownBrand = false;
  return {nullptr, 0, 0, false};
}

bool copyPresetToRawBuffer(const PresetPayload &preset,
                           const char *&errorReason) {
  if (!preset.programmed || !preset.pulses || preset.pulseCount == 0) {
    errorReason = "preset_not_programmed";
    return false;
  }

  if (preset.pulseCount > MAX_RAW_PULSES) {
    errorReason = "preset_too_long";
    return false;
  }

  for (uint16_t i = 0; i < preset.pulseCount; i++) {
    rawPulses[i] = pgm_read_word(&(preset.pulses[i]));
  }

  errorReason = nullptr;
  return true;
}

// -----------------------------------------------------------------------------
// LG AC Protocol básico
// -----------------------------------------------------------------------------
// Nota: puede no funcionar en todos los modelos LG.
// Para producción es más confiable usar RAW capturado o una librería AC
// dedicada.
// -----------------------------------------------------------------------------

void sendLgAc(bool power, const char *mode, int temp, const char *fan) {
  if (!power) {
    // Código de apagado estándar LG.
    IrSender.sendLG(0x88, 0xC0051, 0);
    return;
  }

  uint8_t op = 0x0;
  uint8_t m = 0;

  // 0: cool, 1: dry, 2: fan, 4: heat
  if (equalsIgnoreCase(mode, "dry")) {
    m = 1;
  } else if (equalsIgnoreCase(mode, "fan")) {
    m = 2;
  } else if (equalsIgnoreCase(mode, "heat")) {
    m = 4;
  } else {
    m = 0;
  }

  uint8_t t = (uint8_t)(constrain(temp, 18, 30) - 15);

  uint8_t f = 5;

  // 0: low, 2: mid, 4: high, 5: auto/natural
  if (equalsIgnoreCase(fan, "low")) {
    f = 0;
  } else if (equalsIgnoreCase(fan, "mid") || equalsIgnoreCase(fan, "medium")) {
    f = 2;
  } else if (equalsIgnoreCase(fan, "high")) {
    f = 4;
  }

  uint32_t payload = 0;
  payload |= ((uint32_t)op << 12);
  payload |= ((uint32_t)m << 9);
  payload |= ((uint32_t)t << 4);
  payload |= (uint32_t)f;

  uint8_t checksum = (op + m + t + f) & 0x0F;
  uint32_t finalCode = 0x8800000 | (payload << 4) | checksum;

  IrSender.sendLG(0x88, (finalCode & 0xFFFFF), 0);
}

// -----------------------------------------------------------------------------
// Handlers
// -----------------------------------------------------------------------------

void handleRawCommand(JsonDocument &doc) {
  const char *commandId = getStringOr(doc, "id", "command_id", "");
  const char *brand = getStringOr(doc, "b", "brand", "");

  uint8_t khz = (uint8_t)getIntOr(doc, "khz", "frequency_khz", DEFAULT_IR_KHZ);

  uint8_t repeats = readRepeats(doc);

  JsonArrayConst pulses = doc["pulses"].as<JsonArrayConst>();

  if (pulses.isNull()) {
    pulses = doc["raw"].as<JsonArrayConst>();
  }

  uint16_t pulseCount = 0;
  const char *errorReason = nullptr;

  if (pulses.isNull()) {
    sendAck(commandId, false, "missing_raw_pulses", brand, "raw");
    return;
  }

  if (!copyRawPulses(pulses, pulseCount, errorReason)) {
    sendAck(commandId, false, errorReason, brand, "raw");
    return;
  }

  sendRawPulses(pulseCount, khz, repeats);
  sendAck(commandId, true, "raw_sent", brand, "raw");
}

void handlePresetCommand(JsonDocument &doc) {
  const char *commandId = getStringOr(doc, "id", "command_id", "");
  const char *brand = getStringOr(doc, "b", "brand", "");
  const char *presetKey = getStringOr(doc, "k", "preset_key", "");

  uint8_t repeats = readRepeats(doc);

  if (brand[0] == '\0') {
    sendAck(commandId, false, "missing_brand", brand, "preset", presetKey);
    return;
  }

  if (presetKey[0] == '\0') {
    sendAck(commandId, false, "missing_preset_key", brand, "preset", presetKey);
    return;
  }

  bool knownBrand = false;
  PresetPayload preset = resolvePreset(brand, presetKey, knownBrand);

  if (!knownBrand) {
    sendAck(commandId, false, "unsupported_brand", brand, "preset", presetKey);
    return;
  }

  const char *errorReason = nullptr;

  if (!copyPresetToRawBuffer(preset, errorReason)) {
    sendAck(commandId, false, errorReason, brand, "preset", presetKey);
    return;
  }

  sendRawPulses(preset.pulseCount, preset.khz, repeats);
  sendAck(commandId, true, "preset_sent", brand, "preset", presetKey);
}

void handleHvacCommand(JsonDocument &doc) {
  const char *commandId = getStringOr(doc, "id", "command_id", "");
  const char *brand = getStringOr(doc, "b", "brand", "");

  const char *transportFormat =
      getStringOr(doc, "fmt", "transport_format", "hvac");

  // Permite que el backend mande type=hvac + transport_format=raw.
  if (equalsIgnoreCase(transportFormat, "raw") || !doc["pulses"].isNull() ||
      !doc["raw"].isNull()) {
    handleRawCommand(doc);
    return;
  }

  const char *presetKey = getStringOr(doc, "k", "preset_key", "");

  if (presetKey[0] != '\0') {
    handlePresetCommand(doc);
    return;
  }

  bool power = readPower(doc, true);
  const char *mode = getStringOr(doc, "m", "mode", "cool");
  int temp = getIntOr(doc, "temp", "temperature", 24);
  const char *fan = getStringOr(doc, "f", "fan", "auto");

  if (brand[0] == '\0') {
    sendAck(commandId, false, "missing_brand", brand, "hvac");
    return;
  }

  if (temp < 16 || temp > 32) {
    sendAck(commandId, false, "temperature_out_of_range", brand, "hvac");
    return;
  }

  if (equalsIgnoreCase(brand, "lg")) {
    sendLgAc(power, mode, temp, fan);
    sendAck(commandId, true, "lg_sent", brand, "hvac");
    return;
  }

  if (equalsIgnoreCase(brand, "samsung")) {
    sendAck(commandId, false, "samsung_requires_raw_or_preset", brand, "hvac");
    return;
  }

  if (equalsIgnoreCase(brand, "haier")) {
    sendAck(commandId, false, "haier_requires_raw_or_preset", brand, "hvac");
    return;
  }

  if (equalsIgnoreCase(brand, "generic")) {
    sendAck(commandId, false, "generic_requires_raw_or_preset", brand, "hvac");
    return;
  }

  sendAck(commandId, false, "unsupported_brand", brand, "hvac");
}

void processLine(const char *line) {
  StaticJsonDocument<JSON_DOC_SIZE> doc;
  DeserializationError error = deserializeJson(doc, line);

  if (error) {
    sendAck("", false, "invalid_json", "", "");
    return;
  }

  const char *type = getStringOr(doc, "t", "type", "");

  if (equalsIgnoreCase(type, "hvac")) {
    handleHvacCommand(doc);
    return;
  }

  if (equalsIgnoreCase(type, "raw")) {
    handleRawCommand(doc);
    return;
  }

  if (equalsIgnoreCase(type, "preset")) {
    handlePresetCommand(doc);
    return;
  }

  sendAck(getStringOr(doc, "id", "command_id", ""), false, "unsupported_type",
          getStringOr(doc, "b", "brand", ""), "");
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
      sendAck("", false, "serial_buffer_overflow", "", "");
    }
  }
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  Serial.setTimeout(50);

  IrSender.begin(IR_SEND_PIN, ENABLE_LED_FEEDBACK);

  while (!Serial) {
    ; // Solo relevante en placas con USB nativo.
  }

  StaticJsonDocument<224> boot;

  boot["type"] = "boot";
  boot["firmware"] = "arduino_hvac_ir";
  boot["protocol_version"] = 2;
  boot["ready"] = true;
  boot["ir_send_pin"] = IR_SEND_PIN;
  boot["baud"] = SERIAL_BAUD;

  serializeJson(boot, Serial);
  Serial.println();
}

void loop() { readSerialLines(); }