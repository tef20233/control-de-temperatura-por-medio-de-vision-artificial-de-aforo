#define IR_SEND_PIN 9

#include <ArduinoJson.h>
#include <IRremote.hpp>
#include <ctype.h>

// -----------------------------------------------------------------------------
// Firmware Arduino HVAC IR
// -----------------------------------------------------------------------------
// Soporta comandos por Serial, una línea JSON por comando:
//
// 1) HVAC compacto:
// {"t":"hvac","id":"cmd-1","b":"challenger","p":1,"m":"cool","temp":22,"f":"auto"}
//
// 2) HVAC verbose:
// {"type":"hvac","command_id":"cmd-1","brand":"challenger","power":true,"mode":"cool","temperature":22,"fan":"auto"}
//
// 3) RAW universal:
// {"t":"raw","id":"cmd-2","b":"challenger","khz":38,"r":2,"pulses":[9000,4500,560,560]}
//
// 4) Preset:
// {"t":"preset","id":"cmd-3","b":"challenger","preset_key":"cool_24_auto"}
//
// Respuesta:
// {"type":"ack","command_id":"...","success":true/false,"reason":"..."}
// -----------------------------------------------------------------------------

// Hardware
static const uint32_t SERIAL_BAUD = 115200;

// Buffers
static const size_t SERIAL_BUFFER_SIZE = 1024;
static const size_t JSON_DOC_SIZE = 1536;
static const size_t MAX_RAW_PULSES = 245;

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
  if (!a || !b) {
    return false;
  }

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
  const char *value = doc[shortKey].as<const char *>();

  if (value && value[0] != '\0') {
    return value;
  }

  value = doc[longKey].as<const char *>();

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

  return equalsIgnoreCase(text, "on") ||
         equalsIgnoreCase(text, "true") ||
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
// Presets programables
// -----------------------------------------------------------------------------

PresetPayload resolveLgPreset(const char *presetKey) {
  /*
    Aquí puedes poner RAW reales capturados del control LG.

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

PresetPayload resolveChallengerPreset(const char *presetKey) {
  /*
    Cuando captures RAW reales del control Challenger, los puedes poner aquí.

    Ejemplo:

    static const uint16_t CHALLENGER_COOL_22_AUTO[] PROGMEM = {
      9000, 4500, 560, 560
    };

    if (equalsIgnoreCase(presetKey, "cool_22_auto")) {
      return {
        CHALLENGER_COOL_22_AUTO,
        sizeof(CHALLENGER_COOL_22_AUTO) / sizeof(CHALLENGER_COOL_22_AUTO[0]),
        38,
        true
      };
    }
  */

  (void)presetKey;
  return {nullptr, 0, DEFAULT_IR_KHZ, false};
}

PresetPayload resolveMideaPreset(const char *presetKey) {
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

  if (equalsIgnoreCase(brand, "challenger")) {
    return resolveChallengerPreset(presetKey);
  }

  if (equalsIgnoreCase(brand, "midea")) {
    return resolveMideaPreset(presetKey);
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
// LG AC básico
// -----------------------------------------------------------------------------

void sendLgAc(bool power, const char *mode, int temp, const char *fan) {
  if (!power) {
    IrSender.sendLG(0x88, 0xC0051, 0);
  
    return;
  }

  uint8_t op = 0x0;
  uint8_t m = 0;

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

  if (equalsIgnoreCase(fan, "low")) {
    f = 0;
  } else if (equalsIgnoreCase(fan, "mid") ||
             equalsIgnoreCase(fan, "medium")) {
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
// Challenger AC - Códigos RAW capturados del control original
// Modo: Cool, Fan: Auto. Temperaturas: 18, 22, 24, 26, 30°C + OFF
// -----------------------------------------------------------------------------

static const uint16_t CHALLENGER_OFF[] PROGMEM = {
  8850,4450,550,1700,500,1700,500,550,550,550,550,550,500,600,500,1700,500,1700,
  550,1700,500,1700,500,1700,500,600,500,600,500,550,550,550,500,1700,
  550,550,500,600,500,600,500,600,500,600,500,1700,500,1700,500,1700,
  500,600,500,550,550,600,500,550,550,550,500,600,500,600,500,600,
  500,600,500,550,550,550,500,600,500,600,500,1700,500,600,500,1700,
  500,600,500,600,500,600,500,550,550,550,500,600,500,600,500,600,
  500,600,500,550,550,550,500,600,500,600,500,1700,500,600,500,600,
  500,600,500,550,550,550,500,600,500,600,500,600,500,550,550,550,
  550,550,550,550,550,550,500,600,500,550,550,550,500,600,500,600,
  500,600,500,600,500,550,500,600,500,600,500,600,500,600,500,550,
  550,550,500,600,500,600,500,600,500,600,500,550,550,550,500,600,
  500,1700,500,600,500,1700,500,600,500,600,500,600,500,600,500,550,
  550,1700,500,1700,500,1700,500,1700,500,600,500,1700,500,1700,500,1750,500
};
static const uint16_t CHALLENGER_OFF_LEN = sizeof(CHALLENGER_OFF) / sizeof(CHALLENGER_OFF[0]);

static const uint16_t CHALLENGER_COOL_18[] PROGMEM = {
  8850,4450,500,1700,500,1700,500,600,500,600,500,600,500,550,500,1750,500,1700,
  500,1700,500,1700,500,1700,500,600,500,1700,500,600,500,1700,500,600,
  500,600,500,600,500,600,500,550,500,600,500,1700,550,1700,500,1700,
  500,600,500,550,550,550,500,600,500,600,500,600,500,550,550,550,
  500,600,500,600,500,600,500,600,500,550,550,1700,500,550,550,1700,
  500,550,550,550,500,600,500,600,500,600,500,600,500,550,500,600,
  500,600,500,600,500,600,500,550,550,550,500,1700,550,550,500,600,
  500,600,500,600,500,600,500,550,550,550,500,600,500,600,500,600,
  500,600,500,550,500,600,500,600,500,600,500,600,500,550,500,600,
  500,600,500,600,500,600,500,600,500,550,550,1700,500,550,550,550,
  500,600,500,600,500,600,500,550,550,550,500,600,500,600,500,600,
  500,1700,500,600,500,600,500,550,500,600,500,600,500,600,500,600,
  500,1700,500,1700,500,600,500,1700,500,1700,500,600,500,1700,500,1700,550
};
static const uint16_t CHALLENGER_COOL_18_LEN = sizeof(CHALLENGER_COOL_18) / sizeof(CHALLENGER_COOL_18[0]);

static const uint16_t CHALLENGER_COOL_22[] PROGMEM = {
  8850,4400,550,1700,500,1700,500,600,500,600,500,600,500,550,550,1700,500,1700,
  500,1700,500,1700,500,1700,500,600,500,1700,550,1700,500,1700,500,600,
  500,550,550,550,500,600,500,600,500,600,500,1700,500,1700,500,1700,
  500,600,500,600,500,600,500,600,500,550,500,600,500,600,500,600,
  500,600,500,550,550,550,500,600,500,600,500,1700,500,600,500,1700,
  500,600,500,600,500,600,500,550,550,550,500,600,500,600,500,600,
  500,600,500,550,550,550,500,600,500,600,500,1700,500,600,500,600,
  500,550,550,550,500,600,500,600,500,600,500,600,500,550,550,550,
  500,600,500,600,500,600,500,600,500,550,550,550,500,600,500,600,
  500,600,500,550,550,550,500,600,500,600,500,1700,500,600,500,600,
  500,600,500,550,550,550,500,600,500,600,500,600,500,600,500,550,
  550,1700,500,550,550,550,500,600,500,600,500,600,500,550,550,550,
  500,1700,550,1650,550,550,550,1650,550,1650,550,1700,500,1700,500,1700,550
};
static const uint16_t CHALLENGER_COOL_22_LEN = sizeof(CHALLENGER_COOL_22) / sizeof(CHALLENGER_COOL_22[0]);

static const uint16_t CHALLENGER_COOL_24[] PROGMEM = {
  8800,4450,550,1700,500,1700,500,600,500,550,550,550,500,600,500,1700,500,1700,
  550,1700,500,1700,500,1700,500,1700,500,600,500,600,500,600,500,1700,
  500,600,500,600,500,550,500,600,500,600,500,1700,500,1700,550,1700,
  500,550,550,550,500,600,500,600,500,600,500,550,550,550,500,600,
  500,600,500,600,500,600,500,550,550,550,500,1700,550,550,500,1700,
  550,550,500,600,500,600,500,600,500,600,500,550,550,550,500,600,
  500,600,500,600,500,600,500,550,500,600,500,1700,500,600,500,600,
  500,600,500,600,500,550,550,550,500,600,500,600,500,600,500,600,
  500,550,550,550,500,600,500,600,500,600,450,650,500,550,550,550,
  500,600,500,600,500,600,500,550,550,550,500,1700,550,550,500,600,
  500,600,500,600,500,600,500,550,500,600,500,600,500,600,500,600,
  500,1700,500,600,500,1700,500,600,500,600,500,550,500,600,500,600,
  500,1700,500,1700,550,1700,500,550,550,1700,500,550,550,550,500,600,500
};
static const uint16_t CHALLENGER_COOL_24_LEN = sizeof(CHALLENGER_COOL_24) / sizeof(CHALLENGER_COOL_24[0]);

static const uint16_t CHALLENGER_COOL_26[] PROGMEM = {
  8800,4500,500,1700,500,1700,500,600,500,600,500,550,550,550,500,1700,550,1700,
  500,1700,500,1700,500,1700,500,600,500,1700,500,600,500,600,500,1700,
  500,600,500,600,500,600,500,550,500,600,500,1700,500,1750,500,1700,
  500,600,500,550,550,550,500,600,500,600,500,600,500,600,500,550,
  500,600,500,600,500,600,500,600,500,550,550,1700,500,550,550,1700,
  500,550,550,550,500,600,500,600,500,600,500,600,500,550,550,550,
  500,600,500,600,500,600,500,600,500,550,550,1700,500,550,550,550,
  500,600,500,600,500,600,500,550,550,550,500,600,500,600,500,600,
  500,600,500,550,550,550,500,600,500,600,500,600,500,600,500,550,
  550,550,500,600,500,600,500,600,500,600,500,1700,500,600,500,550,
  500,600,500,600,500,600,500,600,500,600,500,550,500,600,500,600,
  500,1700,500,600,500,600,450,650,450,600,550,550,550,550,500,600,
  500,1700,500,1700,500,600,500,1700,500,1700,500,600,500,600,500,600,500
};
static const uint16_t CHALLENGER_COOL_26_LEN = sizeof(CHALLENGER_COOL_26) / sizeof(CHALLENGER_COOL_26[0]);

static const uint16_t CHALLENGER_COOL_30[] PROGMEM = {
  8850,4450,500,1750,500,1700,500,600,500,550,500,600,500,600,500,1700,500,1700,
  550,1700,500,1700,500,1700,500,600,500,1700,500,1700,500,600,500,1700,
  500,600,500,600,500,600,500,600,500,550,500,1750,500,1700,500,1700,
  500,600,500,600,500,550,500,600,500,600,500,600,500,600,500,600,
  500,550,500,600,500,600,500,600,500,600,500,1700,500,600,500,1700,
  500,600,500,550,550,550,500,600,500,600,500,600,500,600,500,550,
  550,550,500,600,500,600,500,600,500,600,500,1700,500,600,500,550,
  550,550,500,600,500,600,500,600,500,600,500,550,500,600,500,600,
  500,600,500,600,500,550,550,550,500,600,500,600,500,600,500,600,
  500,550,550,550,500,600,500,600,500,600,500,1700,500,600,500,600,
  500,550,550,550,500,600,500,600,500,600,500,600,500,550,500,600,
  500,1700,500,600,500,600,500,600,500,600,500,600,500,550,500,600,
  500,1700,500,1750,500,550,500,1750,500,1700,500,1700,500,600,500,600,500
};
static const uint16_t CHALLENGER_COOL_30_LEN = sizeof(CHALLENGER_COOL_30) / sizeof(CHALLENGER_COOL_30[0]);

// Envía un array PROGMEM de pulsos RAW con doble transmisión
void sendChallengerRaw(const uint16_t *progmemData, uint16_t len) {
  // Copiar de PROGMEM a RAM
  for (uint16_t i = 0; i < len && i < MAX_RAW_PULSES; i++) {
    rawPulses[i] = pgm_read_word(&progmemData[i]);
  }
  // Doble envío (igual que tu código que funciona)
  IrSender.sendRaw(rawPulses, len, 38);
  delay(120);
  IrSender.sendRaw(rawPulses, len, 38);
}

void sendChallengerAc(bool power, const char *mode, int temp, const char *fan) {
  (void)mode; // Los códigos capturados son todos Cool Auto
  (void)fan;

  if (!power) {
    sendChallengerRaw(CHALLENGER_OFF, CHALLENGER_OFF_LEN);
    return;
  }

  // Mapear temperatura al código capturado más cercano
  // 16-19 → 18°C, 20-22 → 22°C, 23-25 → 24°C, 26-28 → 26°C, 29-30 → 30°C
  int t = constrain(temp, 16, 30);

  if (t <= 19) {
    sendChallengerRaw(CHALLENGER_COOL_18, CHALLENGER_COOL_18_LEN);
  } else if (t <= 22) {
    sendChallengerRaw(CHALLENGER_COOL_22, CHALLENGER_COOL_22_LEN);
  } else if (t <= 25) {
    sendChallengerRaw(CHALLENGER_COOL_24, CHALLENGER_COOL_24_LEN);
  } else if (t <= 28) {
    sendChallengerRaw(CHALLENGER_COOL_26, CHALLENGER_COOL_26_LEN);
  } else {
    sendChallengerRaw(CHALLENGER_COOL_30, CHALLENGER_COOL_30_LEN);
  }
}

// -----------------------------------------------------------------------------
// Midea AC - Códigos RAW capturados del control original
// -----------------------------------------------------------------------------

static const uint16_t MIDEA_ON[] PROGMEM = {
  4300,4300,550,1550,550,500,550,1550,550,1600,500,550,500,550,500,1600,500,550,
  500,550,500,1600,550,500,550,500,550,1550,550,1550,550,500,550,1550,
  550,500,550,1600,500,550,500,1600,500,1600,500,1600,500,1600,550,1550,
  550,1550,550,500,550,1550,550,500,550,500,550,500,550,500,550,550,
  500,500,550,1600,500,550,500,1600,500,500,550,500,600,500,550,500,
  550,1550,550,500,550,1550,550,500,550,1550,550,1600,500,1600,500,1600,
  500,5100,
  4300,4300,550,1550,550,500,550,1550,550,1600,500,500,550,500,550,1600,500,500,
  550,500,550,1600,500,500,550,500,600,1550,550,1550,550,500,550,1550,
  550,500,550,1550,550,500,550,1600,500,1600,500,1600,500,1600,500,1600,
  500,1600,500,550,550,1550,550,500,550,500,550,500,550,500,550,500,
  550,500,550,1550,550,500,550,1550,550,500,550,500,550,500,550,500,
  550,1550,550,500,550,1550,550,500,550,1550,550,1550,550,1550,550,1550,550
};
static const uint16_t MIDEA_ON_LEN = sizeof(MIDEA_ON) / sizeof(MIDEA_ON[0]);

static const uint16_t MIDEA_OFF[] PROGMEM = {
  4350,4250,550,1600,500,500,550,1600,500,1600,500,500,550,500,550,1600,500,550,
  500,550,550,1550,500,550,500,550,550,1550,550,1550,500,550,500,1600,
  550,500,550,1600,500,1600,500,1600,500,1600,500,500,550,1600,500,1600,
  550,1550,550,500,550,500,550,500,550,500,550,1550,550,500,550,500,
  550,1600,500,1600,500,1600,500,500,550,500,600,500,550,500,550,500,
  550,500,550,500,550,500,550,1550,550,1550,550,1550,550,1600,500,1600,
  500,5050,
  4350,4250,550,1600,500,500,550,1600,550,1550,550,500,550,500,550,1550,550,500,
  550,500,550,1550,550,500,550,500,550,1550,550,1550,500,550,500,1600,
  500,550,500,1600,550,1550,550,1550,550,1550,550,500,550,1550,550,1550,
  550,1550,550,500,550,500,550,500,550,500,550,1600,500,550,500,550,
  500,1600,500,1600,500,1600,500,550,500,550,500,550,500,550,500,550,
  500,550,500,550,500,550,500,1600,500,1600,500,1600,500,1600,500,1600,500
};
static const uint16_t MIDEA_OFF_LEN = sizeof(MIDEA_OFF) / sizeof(MIDEA_OFF[0]);

static const uint16_t MIDEA_COOL_18[] PROGMEM = {
  4300,4300,550,1550,550,500,550,1550,550,1550,550,500,550,500,550,1550,550,500,
  550,550,500,1600,500,550,500,550,500,1600,500,1600,500,550,500,1600,
  500,550,500,1600,500,550,500,1600,500,1600,500,1600,550,1550,550,1550,
  550,1550,550,500,550,1550,550,500,550,500,550,500,550,500,550,500,
  550,500,550,500,550,500,550,1550,550,500,550,500,550,500,550,500,
  550,1550,550,1550,550,1600,500,500,550,1600,500,1600,500,1600,500,1600,
  500,5050,
  4350,4250,550,1600,500,550,500,1600,500,1600,500,500,550,500,550,1600,500,500,
  550,550,550,1550,550,500,550,500,550,1550,550,1550,550,500,550,1550,
  550,500,550,1550,550,500,550,1550,550,1550,550,1550,550,1550,550,1550,
  550,1550,550,500,550,1550,550,500,550,500,550,500,550,500,550,500,
  550,500,550,500,550,500,550,1550,550,500,550,500,550,500,550,500,
  550,1550,550,1550,550,1550,550,500,550,1550,550,1600,500,1600,500,1600,500
};
static const uint16_t MIDEA_COOL_18_LEN = sizeof(MIDEA_COOL_18) / sizeof(MIDEA_COOL_18[0]);

static const uint16_t MIDEA_COOL_22[] PROGMEM = {
  4350,4250,550,1600,500,550,500,1600,500,1600,500,550,500,550,500,1600,500,550,
  550,500,550,1550,550,500,550,500,550,1550,550,1550,550,500,550,1550,
  550,500,550,1550,550,500,550,1550,550,1550,550,1550,550,1550,550,1600,
  500,1600,500,500,550,1600,500,500,550,500,550,500,550,500,550,500,
  550,500,550,1550,550,1600,500,1600,500,500,550,500,550,500,550,550,
  500,1600,550,500,550,500,550,500,550,1550,550,1550,550,1550,550,1550,
  550,5050,
  4300,4300,550,1550,550,500,550,1550,550,1550,550,500,550,500,550,1550,550,550,
  500,550,500,1600,500,500,550,500,550,1600,500,1550,550,500,550,1550,
  550,500,550,1550,550,500,550,1550,550,1550,550,1550,550,1550,600,1500,
  600,1550,550,500,550,1550,550,500,550,500,550,500,550,500,500,550,
  500,550,500,1600,550,1550,500,1600,500,550,500,550,500,550,500,550,
  500,1600,500,550,500,550,500,550,500,1600,550,1550,550,1550,550,1550,550
};
static const uint16_t MIDEA_COOL_22_LEN = sizeof(MIDEA_COOL_22) / sizeof(MIDEA_COOL_22[0]);

static const uint16_t MIDEA_COOL_26[] PROGMEM = {
  4300,4300,550,1550,550,500,550,1550,550,1550,550,550,500,550,500,1600,500,500,
  550,500,550,1600,500,550,500,500,550,1600,500,1600,500,550,500,1600,
  500,500,550,1600,500,550,500,1600,500,1600,550,1550,550,1550,550,1550,
  550,1550,550,500,550,1550,550,500,550,500,550,500,550,500,550,500,
  550,1550,550,1550,550,500,550,1600,500,500,550,500,550,500,550,500,
  550,500,550,500,550,1600,500,500,550,1600,500,1600,500,1600,500,1600,
  500,5100,
  4300,4250,550,1600,500,500,550,1600,550,1550,550,500,550,500,550,1550,550,500,
  550,500,550,1550,550,500,550,500,550,1550,550,1550,550,500,550,1550,
  550,500,550,1550,550,500,550,1600,500,1600,500,1600,500,1600,500,1600,
  500,1600,500,500,550,1550,550,500,550,500,550,500,550,500,550,500,
  550,1550,550,1550,600,450,600,1500,600,500,550,500,550,500,550,500,
  550,500,550,500,550,1550,550,500,500,1600,500,1600,500,1600,500,1600,500
};
static const uint16_t MIDEA_COOL_26_LEN = sizeof(MIDEA_COOL_26) / sizeof(MIDEA_COOL_26[0]);

static const uint16_t MIDEA_COOL_30[] PROGMEM = {
  4300,4250,550,1600,500,550,500,1600,500,1600,550,500,550,500,550,1550,550,500,
  550,500,550,1550,550,500,550,500,550,1550,550,1550,550,500,550,1550,
  550,500,550,1550,550,500,550,1600,500,1600,500,1600,500,1600,500,1600,
  500,1600,500,550,500,1600,500,550,500,500,550,550,500,550,500,550,
  500,1600,500,500,550,1600,550,1550,550,500,550,500,550,500,550,500,
  550,500,550,1550,550,500,550,500,550,1550,550,1550,550,1550,550,1550,
  550,5050,
  4350,4250,550,1550,550,500,550,1600,500,1550,550,500,550,550,500,1600,500,500,
  550,500,550,1600,500,500,550,500,550,1600,500,1600,500,500,550,1600,
  500,500,550,1600,550,450,600,1550,550,1550,550,1550,550,1550,550,1550,
  550,1550,550,500,550,1550,550,500,550,500,550,500,550,500,550,500,
  550,1550,550,500,550,1600,500,1600,500,500,550,500,550,500,550,550,
  500,550,500,1600,500,550,500,550,500,1600,500,1600,500,1600,500,1600,500
};
static const uint16_t MIDEA_COOL_30_LEN = sizeof(MIDEA_COOL_30) / sizeof(MIDEA_COOL_30[0]);

void sendMideaRaw(const uint16_t *progmemData, uint16_t len) {
  for (uint16_t i = 0; i < len && i < MAX_RAW_PULSES; i++) {
    rawPulses[i] = pgm_read_word(&progmemData[i]);
  }
  IrSender.sendRaw(rawPulses, len, 38);
  delay(120);
  IrSender.sendRaw(rawPulses, len, 38);
}

void sendMideaAc(bool power, const char *mode, int temp, const char *fan) {
  (void)mode;
  (void)fan;

  if (!power) {
    sendMideaRaw(MIDEA_OFF, MIDEA_OFF_LEN);
    return;
  }

  int t = constrain(temp, 16, 30);
  if (t <= 19) {
    sendMideaRaw(MIDEA_COOL_18, MIDEA_COOL_18_LEN);
  } else if (t <= 23) {
    sendMideaRaw(MIDEA_COOL_22, MIDEA_COOL_22_LEN);
  } else if (t <= 27) {
    sendMideaRaw(MIDEA_COOL_26, MIDEA_COOL_26_LEN);
  } else {
    sendMideaRaw(MIDEA_COOL_30, MIDEA_COOL_30_LEN);
  }
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

  if (equalsIgnoreCase(transportFormat, "raw") ||
      !doc["pulses"].isNull() ||
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

  if (equalsIgnoreCase(brand, "challenger")) {
    sendChallengerAc(power, mode, temp, fan);
    sendAck(commandId, true, "challenger_sent", brand, "hvac");
    return;
  }

  if (equalsIgnoreCase(brand, "midea")) {
    sendMideaAc(power, mode, temp, fan);
    sendAck(commandId, true, "midea_sent", brand, "hvac");
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

// -----------------------------------------------------------------------------
// Serial
// -----------------------------------------------------------------------------

void processLine(const char *line) {
  StaticJsonDocument<JSON_DOC_SIZE> doc;
  DeserializationError error = deserializeJson(doc, line);

  if (error) {
    sendAck("", false, "invalid_json", "", "");
    return;
  }

  const char *type = getStringOr(doc, "t", "type", "");

  if (!type || type[0] == '\0') {
    type = doc["command"].as<const char *>();
  }

  if ((!type || type[0] == '\0') &&
      (!doc["pulses"].isNull() || !doc["raw"].isNull())) {
    handleRawCommand(doc);
    return;
  }

  if ((!type || type[0] == '\0') &&
      (!doc["brand"].isNull() || !doc["b"].isNull())) {
    handleHvacCommand(doc);
    return;
  }

  if (equalsIgnoreCase(type, "hvac") ||
      equalsIgnoreCase(type, "ac") ||
      equalsIgnoreCase(type, "air_conditioner")) {
    handleHvacCommand(doc);
    return;
  }

  if (equalsIgnoreCase(type, "raw") ||
      equalsIgnoreCase(type, "ir_raw")) {
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

// -----------------------------------------------------------------------------
// Arduino setup/loop
// -----------------------------------------------------------------------------

void setup() {
  Serial.begin(SERIAL_BAUD);
  Serial.setTimeout(50);

  IrSender.begin(ENABLE_LED_FEEDBACK);

  delay(300);

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

void loop() {
  readSerialLines();
}