/* ==========================================================================
 *  Autonomous Smart Warehouse Monitoring System Using AI & IoT
 *  ESP32 DevKit V1 firmware
 *
 *  Sathyabama Institute of Science and Technology — Interdisciplinary Project I
 *  Student: Arya Vamsi Balaji
 *
 *  Architecture: non-blocking, millis()-based cooperative scheduler.
 *    every loop  : buttons, RFID, outputs (LED/buzzer), event queue
 *    500 ms      : HC-SR04, MQ-2, LDR, alert evaluation
 *    2 s         : DHT11, Serial report
 *    1 s / 3 s   : LCD refresh / screen rotation
 *    5 s         : POST /api/log   (sensor data -> Flask backend)
 *    100 s       : POST /api/predict for next product (each product every 5 min)
 *
 *  Required libraries (Arduino Library Manager):
 *    - MFRC522            by GithubCommunity      (RFID)
 *    - DHT sensor library by Adafruit (+ Adafruit Unified Sensor)
 *    - LiquidCrystal I2C  by Frank de Brabander
 *    - ArduinoJson        by Benoit Blanchon  (v7.x)
 *  Board: "ESP32 Dev Module" (esp32 by Espressif Systems, core 2.x or 3.x)
 * ========================================================================== */

#include <WiFi.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <Wire.h>
#include <time.h>
#include <MFRC522.h>
#include <DHT.h>
#include <LiquidCrystal_I2C.h>
#include <ArduinoJson.h>

#include "config.h"

// =========================================================== Global objects
MFRC522 rfid(PIN_RFID_SS, PIN_RFID_RST);
DHT dht(PIN_DHT, DHT_TYPE);
LiquidCrystal_I2C* lcd = nullptr;          // created after I2C address detection
uint8_t lcdAddress = 0;

// ======================================================= Key sensor variables
long  distance      = -1;     // cm, -1 = out of range / no echo
float temperature   = NAN;    // °C
float humidity      = NAN;    // %
float avgTemperature = NAN;   // smoothed temperature for ML feature
int   mqAnalog      = 0;      // 0-4095
bool  mqDigital     = false;  // true = module comparator says gas detected
int   lightAdc      = 0;      // 0-4095
int   lightPercent  = 0;      // 0-100 %
String cardUID      = "";     // last scanned RFID UID ("A1 B2 C3 D4")
int   stockLevel    = 0;      // stock of the currently selected product
int   selectedProduct = 0;    // index into PRODUCTS[]
bool  dhtOk         = false;

// ================================================================ Alerts
struct Alerts {
  bool distance  = false;
  bool gas       = false;
  bool temp      = false;
  bool stock     = false;
  bool emergency = false;
  bool any() const { return distance || gas || temp || stock || emergency; }
  bool critical() const { return gas || emergency; }
} alerts, prevAlerts;

// ============================================================== Prediction
struct Prediction {
  bool valid = false;
  int productIdx = 0;
  int demand = 0;
  int restock = 0;
} lastPrediction;
int nextPredictIdx = 0;

// ============================================================ Event queue
// Events (RFID scan, order, emergency) are sent to the backend immediately.
struct Event { const char* type; int productIdx; };
const int EVENT_QUEUE_SIZE = 8;
Event eventQueue[EVENT_QUEUE_SIZE];
int eqHead = 0, eqTail = 0;

// ============================================================ LCD overlay
char overlayLine1[17] = "";
char overlayLine2[17] = "";
unsigned long overlayUntil = 0;
int lcdScreen = 0;

// ================================================================ Timers
unsigned long tSensor = 0, tDht = 0, tSerial = 0, tLcd = 0, tRotate = 0;
unsigned long tSend = 0, tPredict = 0, tWifi = 0, httpBackoffUntil = 0;
unsigned long bootMillis = 0;

// ============================================================ Net status
int  lastHttpCode = 0;
bool timeSynced = false;
int  lastYday = -1;

// ======================================================= Buttons (debounced)
struct Button {
  uint8_t pin;
  bool stableState = HIGH;
  bool lastReading = HIGH;
  unsigned long lastChange = 0;
  explicit Button(uint8_t p) : pin(p) {}
};
Button btnOrder(PIN_BTN_ORDER);
Button btnEmerg(PIN_BTN_EMERG);

// ======================================================= Buzzer / LED state
bool buzzerOn = false;
int  chirpsRemaining = 0;
unsigned long chirpToggleAt = 0;
bool chirpPhaseOn = false;

// ===================================================================== Utils
void pushEvent(const char* type, int productIdx) {
  int next = (eqHead + 1) % EVENT_QUEUE_SIZE;
  if (next == eqTail) return;                 // queue full: drop
  eventQueue[eqHead] = {type, productIdx};
  eqHead = next;
}

bool popEvent(Event& e) {
  if (eqTail == eqHead) return false;
  e = eventQueue[eqTail];
  eqTail = (eqTail + 1) % EVENT_QUEUE_SIZE;
  return true;
}

String timestamp() {
  struct tm t;
  if (timeSynced && getLocalTime(&t, 0)) {
    char buf[20];
    strftime(buf, sizeof(buf), "%H:%M:%S", &t);
    return String(buf);
  }
  unsigned long s = (millis() - bootMillis) / 1000;      // fallback: uptime
  char buf[20];
  snprintf(buf, sizeof(buf), "up %02lu:%02lu:%02lu", s / 3600, (s / 60) % 60, s % 60);
  return String(buf);
}

void logEvent(const String& msg) {
  Serial.printf("[%s] %s\n", timestamp().c_str(), msg.c_str());
}

float occupancyPercent() {
  if (distance < 0) return NAN;
  return constrain((1.0f - (float)distance / BIN_DEPTH_CM) * 100.0f, 0.0f, 100.0f);
}

const char* lightLevelName() {
  if (lightPercent > LIGHT_BRIGHT_PCT) return "Bright";
  if (lightPercent >= LIGHT_DARK_PCT)  return "Medium";
  return "Dark";
}

int findProductByUID(const String& uid) {
  for (int i = 0; i < NUM_PRODUCTS; i++)
    if (uid.equalsIgnoreCase(PRODUCTS[i].uid)) return i;
  return -1;
}

int findProductById(const char* id) {
  for (int i = 0; i < NUM_PRODUCTS; i++)
    if (strcmp(id, PRODUCTS[i].id) == 0) return i;
  return -1;
}

// ============================================================ Buzzer helpers
void buzzer(bool on, int freq = 2000) {
#if BUZZER_IS_PASSIVE
  static int currentFreq = 0;
  if (on && (!buzzerOn || freq != currentFreq)) { tone(PIN_BUZZER, freq); currentFreq = freq; }
  if (!on && buzzerOn) noTone(PIN_BUZZER);
#else
  digitalWrite(PIN_BUZZER, on ? HIGH : LOW);
#endif
  buzzerOn = on;
}

void chirp(int count) {             // short non-blocking beeps for warnings
  chirpsRemaining = count;
  chirpPhaseOn = false;
  chirpToggleAt = millis();
}

// ============================================================== LCD helpers
bool i2cDevicePresent(uint8_t addr) {
  Wire.beginTransmission(addr);
  return Wire.endTransmission() == 0;
}

void lcdLine(uint8_t row, const char* text) {
  if (!lcd) return;
  char buf[LCD_COLS + 1];
  snprintf(buf, sizeof(buf), "%-16s", text);   // pad -> no flicker, no clear()
  lcd->setCursor(0, row);
  lcd->print(buf);
}

void showOverlay(const char* l1, const char* l2) {
  strncpy(overlayLine1, l1, 16); overlayLine1[16] = '\0';
  strncpy(overlayLine2, l2, 16); overlayLine2[16] = '\0';
  overlayUntil = millis() + LCD_OVERLAY_MS;
  tLcd = 0;                                      // force immediate redraw
}

// =============================================================== Sensors
/** HC-SR04: 10 µs trigger pulse, measure echo width. 25 ms timeout (~4 m)
 *  bounds the only blocking call in the loop. */
void readUltrasonic() {
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);
  unsigned long us = pulseIn(PIN_ECHO, HIGH, 25000UL);
  if (us == 0) { distance = -1; return; }       // no echo / out of range
  long d = (long)(us * 0.0343f / 2.0f);          // speed of sound 343 m/s
  distance = (d < 2 || d > 400) ? -1 : d;        // HC-SR04 valid range 2-400 cm
}

/** DHT11: keep last good value on read failure. */
void readDHT11() {
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  if (isnan(t) || isnan(h)) { dhtOk = false; return; }
  temperature = t;
  humidity = h;
  dhtOk = true;
  avgTemperature = isnan(avgTemperature) ? t : (0.95f * avgTemperature + 0.05f * t);
}

/** MQ-2: average 8 ADC samples (ADC1 pin, works with WiFi on). */
void readMQSensor() {
  long sum = 0;
  for (int i = 0; i < 8; i++) sum += analogRead(PIN_MQ_AO);
  mqAnalog = sum / 8;
  bool raw = digitalRead(PIN_MQ_DO);
  mqDigital = MQ_DO_ACTIVE_LOW ? (raw == LOW) : (raw == HIGH);
}

/** LDR: 3.3V -> LDR -> GPIO36 -> 10k -> GND, so more light = higher ADC. */
void readLDR() {
  long sum = 0;
  for (int i = 0; i < 4; i++) sum += analogRead(PIN_LDR);
  lightAdc = sum / 4;
  lightPercent = map(lightAdc, 0, 4095, 0, 100);
}

/** RC522: non-blocking poll; on a new card, look up the product. */
void scanRFID() {
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) return;

  String uid = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (i) uid += " ";
    if (rfid.uid.uidByte[i] < 0x10) uid += "0";
    uid += String(rfid.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();

  cardUID = uid;
  int idx = findProductByUID(uid);
  if (idx < 0) {
    logEvent("Unknown card UID: " + uid + "  (add it to PRODUCTS[] in config.h)");
    showOverlay("Unknown RFID", uid.c_str());
    chirp(3);
    return;
  }
  selectedProduct = idx;
  stockLevel = PRODUCTS[idx].stock;
  logEvent(String("RFID ") + uid + " -> " + PRODUCTS[idx].id + " " + PRODUCTS[idx].name +
           " | stock " + stockLevel);

  char l1[17], l2[17];
  snprintf(l1, sizeof(l1), "%s %s", PRODUCTS[idx].id, PRODUCTS[idx].name);
  snprintf(l2, sizeof(l2), "Stk:%d RP:%d", PRODUCTS[idx].stock, PRODUCTS[idx].reorderPoint);
  showOverlay(l1, l2);
  chirp(1);
  pushEvent("SCAN", idx);
}

// =============================================================== Buttons
/** Returns true once per debounced press (HIGH -> LOW transition). */
bool buttonPressed(Button& b) {
  bool reading = digitalRead(b.pin);
  if (reading != b.lastReading) { b.lastChange = millis(); b.lastReading = reading; }
  if (millis() - b.lastChange > DEBOUNCE_MS && reading != b.stableState) {
    b.stableState = reading;
    return b.stableState == LOW;
  }
  return false;
}

void handleButtons() {
  if (buttonPressed(btnOrder)) {
    Product& p = PRODUCTS[selectedProduct];
    if (p.stock > 0) {
      p.stock--;
      p.ordersToday++;
      stockLevel = p.stock;
      logEvent(String("ORDER ") + p.id + " " + p.name + " -1 -> stock " + p.stock);
      char l1[17], l2[17];
      snprintf(l1, sizeof(l1), "ORDER %s -1", p.name);
      snprintf(l2, sizeof(l2), "Stock left: %d", p.stock);
      showOverlay(l1, l2);
      chirp(1);
      pushEvent("ORDER", selectedProduct);
    } else {
      logEvent(String("ORDER rejected: ") + p.name + " out of stock");
      showOverlay("OUT OF STOCK", p.name);
      chirp(3);
    }
  }

  if (buttonPressed(btnEmerg)) {
    alerts.emergency = !alerts.emergency;        // press again to clear
    logEvent(alerts.emergency ? "EMERGENCY ACTIVATED" : "Emergency cleared");
    if (alerts.emergency) pushEvent("EMERGENCY", selectedProduct);
    else pushEvent("EMERGENCY_CLEAR", selectedProduct);
    tLcd = 0;
  }
}

// ================================================================ Alerts
void evaluateAlerts() {
  alerts.distance = (distance > 0 && distance < DISTANCE_ALERT_CM);
  bool warmedUp = millis() - bootMillis > MQ_WARMUP_MS;
  alerts.gas = warmedUp && (mqAnalog > GAS_THRESHOLD_ADC || mqDigital);
  alerts.temp = dhtOk && temperature > TEMP_HIGH_C;
  alerts.stock = false;
  for (int i = 0; i < NUM_PRODUCTS; i++)
    if (PRODUCTS[i].stock < PRODUCTS[i].reorderPoint) alerts.stock = true;

  // Log + chirp on rising edges only
  if (alerts.distance && !prevAlerts.distance) { logEvent("[ALERT] Bin full / obstruction: " + String(distance) + " cm"); chirp(2); }
  if (alerts.gas && !prevAlerts.gas)           { logEvent("[ALERT] GAS level high: ADC " + String(mqAnalog)); }
  if (alerts.temp && !prevAlerts.temp)         { logEvent("[ALERT] High temperature: " + String(temperature, 1) + " C"); chirp(2); }
  if (alerts.stock && !prevAlerts.stock) {
    for (int i = 0; i < NUM_PRODUCTS; i++)
      if (PRODUCTS[i].stock < PRODUCTS[i].reorderPoint)
        logEvent(String("[ALERT] Low stock: ") + PRODUCTS[i].name + " " + PRODUCTS[i].stock +
                 " < reorder point " + PRODUCTS[i].reorderPoint);
    chirp(2);
  }
  if (!alerts.any() && prevAlerts.any()) logEvent("All alerts cleared");
  prevAlerts = alerts;
}

/** LED + buzzer patterns, called every loop (non-blocking). */
void updateOutputs() {
  unsigned long now = millis();

  // LED: fast blink for critical, steady for warnings, off otherwise
  if (alerts.critical())   digitalWrite(PIN_LED, (now / 150) % 2);
  else if (alerts.any())   digitalWrite(PIN_LED, HIGH);
  else                     digitalWrite(PIN_LED, LOW);

  // Buzzer priority: emergency siren > gas beeping > warning chirps
  if (alerts.emergency) {
    buzzer(true, ((now / 300) % 2) ? 1000 : 1800);
  } else if (alerts.gas) {
    buzzer((now / 200) % 2, 2500);
  } else if (chirpsRemaining > 0) {
    if (now >= chirpToggleAt) {
      chirpPhaseOn = !chirpPhaseOn;
      buzzer(chirpPhaseOn, 2200);
      chirpToggleAt = now + (chirpPhaseOn ? 80 : 120);
      if (!chirpPhaseOn) chirpsRemaining--;
    }
  } else {
    buzzer(false);
  }
}

// =================================================================== LCD
/** Rotating screens: Distance, Temp/Hum, Gas, Light (+ ML prediction).
 *  Overlays (RFID/order) and emergency take priority. '!' in the top-right
 *  corner means an alert is active. */
void displayOnLCD() {
  if (!lcd) return;
  unsigned long now = millis();
  char l1[17], l2[17];

  if (alerts.emergency) {
    lcdLine(0, "!! EMERGENCY !!");
    lcdLine(1, (now / 1000) % 2 ? "Press BTN2 clear" : "Alarm active");
    return;
  }
  if (now < overlayUntil) {
    lcdLine(0, overlayLine1);
    lcdLine(1, overlayLine2);
    return;
  }

  int screens = lastPrediction.valid ? 5 : 4;
  if (now - tRotate >= LCD_ROTATE_MS) {
    tRotate = now;
    lcdScreen = (lcdScreen + 1) % screens;
  }
  if (lcdScreen >= screens) lcdScreen = 0;

  switch (lcdScreen) {
    case 0:   // Distance / occupancy
      if (distance < 0) snprintf(l1, sizeof(l1), "Dist: -- cm");
      else              snprintf(l1, sizeof(l1), "Dist: %ld cm", distance);
      if (alerts.distance)  snprintf(l2, sizeof(l2), "BIN FULL! <%dcm", DISTANCE_ALERT_CM);
      else if (distance < 0) snprintf(l2, sizeof(l2), "Out of range");
      else                  snprintf(l2, sizeof(l2), "Occupancy: %.0f%%", occupancyPercent());
      break;
    case 1:   // Temperature / humidity
      if (dhtOk) {
        snprintf(l1, sizeof(l1), "Temp: %.1f%cC", temperature, (char)223);
        snprintf(l2, sizeof(l2), "Hum : %.0f %%", humidity);
      } else {
        snprintf(l1, sizeof(l1), "Temp: --");
        snprintf(l2, sizeof(l2), "DHT11 error");
      }
      break;
    case 2:   // Gas
      snprintf(l1, sizeof(l1), "Gas: %d ADC", mqAnalog);
      if (millis() - bootMillis < MQ_WARMUP_MS) snprintf(l2, sizeof(l2), "MQ2 warming up");
      else snprintf(l2, sizeof(l2), alerts.gas ? "GAS ALERT!" : "Air: Clean");
      break;
    case 3:   // Light
      snprintf(l1, sizeof(l1), "Light: %d%%", lightPercent);
      snprintf(l2, sizeof(l2), "Level: %s", lightLevelName());
      break;
    case 4: { // ML prediction
      Product& p = PRODUCTS[lastPrediction.productIdx];
      snprintf(l1, sizeof(l1), "%s next: %du", p.name, lastPrediction.demand);
      snprintf(l2, sizeof(l2), "Restock: %d u", lastPrediction.restock);
      break;
    }
  }

  // reserve column 15 of row 0 for the alert marker
  char row0[17];
  snprintf(row0, sizeof(row0), "%-15.15s%c", l1, alerts.any() ? '!' : ' ');
  lcdLine(0, row0);
  lcdLine(1, l2);
}

// ================================================================ Serial
void printSerialOutput() {
  Product& p = PRODUCTS[selectedProduct];
  Serial.println();
  Serial.printf("------ [%s] Smart Warehouse ------\n", timestamp().c_str());
  if (distance < 0) Serial.println("Distance : out of range");
  else Serial.printf("Distance : %ld cm (occupancy %.0f%%)\n", distance, occupancyPercent());
  if (dhtOk) Serial.printf("Temp/Hum : %.1f C / %.0f %%\n", temperature, humidity);
  else       Serial.println("Temp/Hum : DHT11 read error");
  Serial.printf("Gas MQ-2 : %d ADC, DO=%s%s\n", mqAnalog, mqDigital ? "GAS" : "clear",
                millis() - bootMillis < MQ_WARMUP_MS ? " (warming up)" : "");
  Serial.printf("Light    : %d %% (%s, ADC %d)\n", lightPercent, lightLevelName(), lightAdc);
  Serial.printf("Product  : %s %s | stock %d (reorder %d) | orders today %d\n",
                p.id, p.name, p.stock, p.reorderPoint, p.ordersToday);
  Serial.printf("Last UID : %s\n", cardUID.length() ? cardUID.c_str() : "-");
  if (WiFi.status() == WL_CONNECTED)
    Serial.printf("WiFi     : %s (RSSI %d dBm) | last HTTP %d\n",
                  WiFi.localIP().toString().c_str(), WiFi.RSSI(), lastHttpCode);
  else
    Serial.println("WiFi     : disconnected");
  if (lastPrediction.valid)
    Serial.printf("ML pred  : %s demand %d, restock %d\n",
                  PRODUCTS[lastPrediction.productIdx].name, lastPrediction.demand, lastPrediction.restock);
  Serial.printf("Alerts   : %s%s%s%s%s%s\n",
                alerts.any() ? "" : "none",
                alerts.distance ? "[DISTANCE] " : "", alerts.gas ? "[GAS] " : "",
                alerts.temp ? "[TEMP] " : "", alerts.stock ? "[STOCK] " : "",
                alerts.emergency ? "[EMERGENCY]" : "");
}

// =================================================================== WiFi
void maintainWiFi() {
  if (WiFi.status() == WL_CONNECTED) {
    if (!timeSynced) {
      struct tm t;
      if (getLocalTime(&t, 0)) { timeSynced = true; logEvent("NTP time synced"); }
    }
    return;
  }
  if (millis() - tWifi < WIFI_RETRY_MS) return;
  tWifi = millis();
  logEvent("WiFi not connected, retrying...");
  WiFi.disconnect();
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
}

void onWiFiEvent(WiFiEvent_t event) {
  if (event == ARDUINO_EVENT_WIFI_STA_GOT_IP) {
    Serial.printf("[WiFi] Connected, IP %s\n", WiFi.localIP().toString().c_str());
    configTime(GMT_OFFSET_SEC, DST_OFFSET_SEC, NTP_SERVER);
  } else if (event == ARDUINO_EVENT_WIFI_STA_DISCONNECTED) {
    Serial.println("[WiFi] Disconnected");
  }
}

bool networkReady() {
  return WiFi.status() == WL_CONNECTED && millis() >= httpBackoffUntil;
}

/** Sync stock + reorder points from the server's inventory list. */
void applyInventory(JsonArrayConst inv) {
  for (JsonObjectConst item : inv) {
    const char* id = item["id"] | "";
    int idx = findProductById(id);
    if (idx < 0) continue;
    PRODUCTS[idx].stock = item["stock"] | PRODUCTS[idx].stock;
    PRODUCTS[idx].reorderPoint = item["reorder_point"] | PRODUCTS[idx].reorderPoint;
  }
  stockLevel = PRODUCTS[selectedProduct].stock;
}

/** POST /api/log  — periodic sensor data, or an event (SCAN/ORDER/EMERGENCY). */
bool sendToBackend(const char* eventType = nullptr, int productIdx = -1) {
  if (!networkReady()) return false;

  JsonDocument doc;
  doc["device_id"] = DEVICE_ID;
  if (distance >= 0) doc["distance"] = distance; else doc["distance"] = nullptr;
  if (dhtOk) { doc["temperature"] = temperature; doc["humidity"] = humidity; }
  doc["mqAnalog"]     = mqAnalog;
  doc["gasAlert"]     = alerts.gas ? 1 : 0;
  doc["lightAdc"]     = lightAdc;
  doc["lightPercent"] = lightPercent;
  doc["uptime_s"]     = (millis() - bootMillis) / 1000;
  if (eventType) {
    doc["event"] = eventType;
    if (productIdx >= 0) {
      doc["productId"]  = PRODUCTS[productIdx].id;
      if (strcmp(eventType, "ORDER") == 0) doc["stockLevel"] = PRODUCTS[productIdx].stock;
      if (cardUID.length()) doc["cardUID"] = cardUID;
    }
  }
  String body;
  serializeJson(doc, body);

  HTTPClient http;
  http.setConnectTimeout(HTTP_CONNECT_TIMEOUT);
  http.setTimeout(HTTP_TIMEOUT);
  http.begin(String(SERVER_URL) + "/api/log");
  http.addHeader("Content-Type", "application/json");
  unsigned long t0 = millis();
  lastHttpCode = http.POST(body);

  bool ok = lastHttpCode == 200;
  if (ok) {
    JsonDocument res;
    if (!deserializeJson(res, http.getString()) && res["inventory"].is<JsonArrayConst>())
      applyInventory(res["inventory"].as<JsonArrayConst>());
    if (eventType) logEvent(String("POST /api/log [") + eventType + "] OK in " + (millis() - t0) + " ms");
  } else {
    logEvent("POST /api/log failed: " + String(lastHttpCode) + " " + http.errorToString(lastHttpCode));
    httpBackoffUntil = millis() + HTTP_BACKOFF_MS;
  }
  http.end();
  return ok;
}

/** POST /api/predict for one product, show result on LCD. */
void requestPrediction(int idx) {
  if (!networkReady()) return;
  Product& p = PRODUCTS[idx];

  struct tm t;
  int dow = 0;                                   // spec: 0 = Monday
  if (timeSynced && getLocalTime(&t, 0)) dow = (t.tm_wday + 6) % 7;

  float occ = occupancyPercent();
  JsonDocument doc;
  doc["product_id"]        = p.id;
  doc["orders"]            = min(p.ordersToday, 5);
  doc["avg_temp_c"]        = isnan(avgTemperature) ? 25.0f : avgTemperature;
  doc["occupancy_pct"]     = isnan(occ) ? 40.0f : occ;
  doc["ambient_light_adc"] = lightAdc;
  doc["promo_flag"]        = 0;
  doc["day_of_week"]       = dow;
  doc["stock_on_hand"]     = p.stock;
  doc["reorder_point"]     = p.reorderPoint;
  String body;
  serializeJson(doc, body);

  HTTPClient http;
  http.setConnectTimeout(HTTP_CONNECT_TIMEOUT);
  http.setTimeout(HTTP_TIMEOUT);
  http.begin(String(SERVER_URL) + "/api/predict");
  http.addHeader("Content-Type", "application/json");
  unsigned long t0 = millis();
  lastHttpCode = http.POST(body);

  if (lastHttpCode == 200) {
    JsonDocument res;
    if (!deserializeJson(res, http.getString())) {
      lastPrediction.valid      = true;
      lastPrediction.productIdx = idx;
      lastPrediction.demand     = res["predicted_demand"] | 0;
      lastPrediction.restock    = res["restock_recommendation"] | 0;
      logEvent(String("Prediction ") + p.name + ": demand " + lastPrediction.demand +
               ", restock " + lastPrediction.restock + " (" + (millis() - t0) + " ms)");
    }
  } else {
    logEvent("POST /api/predict failed: " + String(lastHttpCode));
    httpBackoffUntil = millis() + HTTP_BACKOFF_MS;
  }
  http.end();
}

/** Reset per-product order counters at midnight (needs NTP). */
void dailyReset() {
  struct tm t;
  if (!timeSynced || !getLocalTime(&t, 0)) return;
  if (lastYday >= 0 && t.tm_yday != lastYday) {
    for (int i = 0; i < NUM_PRODUCTS; i++) PRODUCTS[i].ordersToday = 0;
    logEvent("New day: order counters reset");
  }
  lastYday = t.tm_yday;
}

// ================================================================== Setup
void setup() {
  Serial.begin(115200);
  bootMillis = millis();
  Serial.println("\n=== Autonomous Smart Warehouse Monitoring System ===");

  // GPIO
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);
  pinMode(PIN_MQ_DO, INPUT);                     // GPIO35: input-only, no pull-up
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_BTN_ORDER, INPUT_PULLUP);
  pinMode(PIN_BTN_EMERG, INPUT_PULLUP);
  digitalWrite(PIN_LED, LOW);

  // ADC: 12-bit, full 0-3.3 V range on the analog pins
  analogReadResolution(12);
  analogSetPinAttenuation(PIN_MQ_AO, ADC_11db);
  analogSetPinAttenuation(PIN_LDR, ADC_11db);

  // I2C LCD with automatic 0x27 / 0x3F detection
  Wire.begin(PIN_SDA, PIN_SCL);
  if (i2cDevicePresent(0x27)) lcdAddress = 0x27;
  else if (i2cDevicePresent(0x3F)) lcdAddress = 0x3F;
  if (lcdAddress) {
    lcd = new LiquidCrystal_I2C(lcdAddress, LCD_COLS, LCD_ROWS);
    lcd->init();
    lcd->backlight();
    lcdLine(0, "Smart Warehouse");
    lcdLine(1, "Starting...");
    Serial.printf("[LCD] Found at 0x%02X\n", lcdAddress);
  } else {
    Serial.println("[LCD] Not found at 0x27/0x3F - check SDA/SCL wiring");
  }

  // SPI RFID
  SPI.begin();                                   // SCK=18, MISO=19, MOSI=23
  rfid.PCD_Init();
  byte ver = rfid.PCD_ReadRegister(MFRC522::VersionReg);
  if (ver == 0x00 || ver == 0xFF) Serial.println("[RFID] RC522 not detected - check wiring / 3.3V");
  else Serial.printf("[RFID] RC522 firmware 0x%02X\n", ver);

  // DHT11
  dht.begin();

  // WiFi (non-blocking: loop continues while connecting)
  WiFi.mode(WIFI_STA);
  WiFi.onEvent(onWiFiEvent);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  tWifi = millis();
  Serial.printf("[WiFi] Connecting to %s ...\n", WIFI_SSID);
  Serial.printf("[API ] Backend %s\n", SERVER_URL);

  stockLevel = PRODUCTS[selectedProduct].stock;
  // first prediction ~20 s after boot (after WiFi + some sensor history)
  tPredict = millis() - PREDICT_INTERVAL_MS / NUM_PRODUCTS + 20000;
  chirp(1);
}

// =================================================================== Loop
void loop() {
  unsigned long now = millis();

  // ---- every loop: fast, non-blocking tasks
  handleButtons();
  scanRFID();
  updateOutputs();

  // ---- 500 ms: sensors + alerts (alert latency <= 500 ms)
  if (now - tSensor >= SENSOR_INTERVAL_MS) {
    tSensor = now;
    readUltrasonic();
    readMQSensor();
    readLDR();
    evaluateAlerts();
  }

  // ---- 2 s: DHT11
  if (now - tDht >= DHT_INTERVAL_MS) {
    tDht = now;
    readDHT11();
    dailyReset();
  }

  // ---- 1 s: LCD refresh (rotation every 3 s handled inside)
  if (now - tLcd >= LCD_REFRESH_MS) {
    tLcd = now;
    displayOnLCD();
  }

  // ---- 2 s: Serial report
  if (now - tSerial >= SERIAL_INTERVAL_MS) {
    tSerial = now;
    printSerialOutput();
  }

  // ---- networking (at most one HTTP request per loop pass)
  maintainWiFi();
  Event e;
  if (eqHead != eqTail && networkReady()) {
    popEvent(e);
    if (sendToBackend(e.type, e.productIdx)) tSend = now;
    else pushEvent(e.type, e.productIdx);         // retry after backoff
  } else if (now - tSend >= SEND_INTERVAL_MS) {
    tSend = now;
    sendToBackend();
  } else if (now - tPredict >= PREDICT_INTERVAL_MS / NUM_PRODUCTS) {
    tPredict = now;
    requestPrediction(nextPredictIdx);
    nextPredictIdx = (nextPredictIdx + 1) % NUM_PRODUCTS;
  }
}
