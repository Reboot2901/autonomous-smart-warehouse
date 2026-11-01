/* ==========================================================================
 *  config.h  —  Smart Warehouse Monitoring System (ESP32 DevKit V1)
 *  Edit THIS file for your WiFi, server IP, RFID card UIDs and thresholds.
 * ========================================================================== */
#pragma once

// ----------------------------------------------------------------- WiFi
#define WIFI_SSID        "YourHotspotName"        // 2.4 GHz network only!
#define WIFI_PASSWORD    "YourHotspotPassword"

// Laptop running backend/app.py. Use the IPv4 from `ipconfig`, NOT localhost.
#define SERVER_URL       "http://192.168.43.25:5000"
#define DEVICE_ID        "esp32-01"

// NTP time (India Standard Time = UTC+5:30 = 19800 s)
#define NTP_SERVER       "pool.ntp.org"
#define GMT_OFFSET_SEC   19800
#define DST_OFFSET_SEC   0

// ----------------------------------------------------------------- Pins
// HC-SR04 (ECHO through 10k/20k divider: 5V -> 3.33V)
#define PIN_TRIG         32
#define PIN_ECHO         33
// DHT11
#define PIN_DHT          15
#define DHT_TYPE         DHT11
// RC522 RFID (SPI: SCK=18, MOSI=23, MISO=19 are the ESP32 VSPI defaults)
#define PIN_RFID_SS      5
#define PIN_RFID_RST     4
// MQ-2 (AO through 10k/20k divider if module is powered from 5V)
#define PIN_MQ_AO        34
#define PIN_MQ_DO        35     // input-only pin, no internal pull-up
// LDR  (wiring: 3.3V -> LDR -> GPIO36 -> 10k -> GND ; brighter = higher ADC)
#define PIN_LDR          36
// I2C LCD
#define PIN_SDA          21
#define PIN_SCL          22
// Outputs
#define PIN_LED          26     // red LED via 180 ohm
#define PIN_BUZZER       13
// Buttons (wired button -> GND, internal pull-up used)
// NOTE: GPIO12 is a boot strapping pin. It is safe ONLY if nothing pulls it
// HIGH during reset — wire the button to GND and do NOT add an external
// pull-up resistor. If boot problems occur, move the button to GPIO 27.
#define PIN_BTN_ORDER    12
#define PIN_BTN_EMERG    14

// -------------------------------------------------------------- Hardware
#define BUZZER_IS_PASSIVE  true   // true = piezo/passive (needs tone), false = active buzzer
#define LCD_COLS           16
#define LCD_ROWS           2
#define MQ_DO_ACTIVE_LOW   true   // most MQ-2 modules pull DO LOW when gas detected

// ------------------------------------------------------------ Thresholds
// Keep in sync with backend/app.py
#define DISTANCE_ALERT_CM   15     // object closer than this -> bin full / obstruction
#define BIN_DEPTH_CM        60     // distance to empty bin floor -> occupancy %
#define GAS_THRESHOLD_ADC   2000
#define TEMP_HIGH_C         30.0
#define MQ_WARMUP_MS        30000  // ignore gas alerts while the heater warms up
#define LIGHT_BRIGHT_PCT    75
#define LIGHT_DARK_PCT      40

// ---------------------------------------------------------------- Timing
#define SENSOR_INTERVAL_MS     500      // ultrasonic, MQ-2, LDR, alert evaluation
#define DHT_INTERVAL_MS        2000     // DHT11 max sample rate is 1 Hz
#define SERIAL_INTERVAL_MS     2000
#define LCD_REFRESH_MS         1000
#define LCD_ROTATE_MS          3000
#define LCD_OVERLAY_MS         3000     // RFID / order pop-up duration
#define SEND_INTERVAL_MS       5000     // POST /api/log
#define PREDICT_INTERVAL_MS    300000   // each product predicted every 5 min
#define WIFI_RETRY_MS          10000
#define HTTP_BACKOFF_MS        15000    // pause networking after a failed request
#define HTTP_CONNECT_TIMEOUT   1500
#define HTTP_TIMEOUT           2000
#define DEBOUNCE_MS            40

// --------------------------------------------------------------- Products
// Replace the UIDs with YOUR cards: scan each card and copy the UID printed
// on the Serial Monitor ("Unknown card UID: ..."). Stock/reorder values are
// overwritten by the server's inventory after the first successful POST.
struct Product {
  const char* id;
  const char* name;
  const char* uid;
  int stock;
  int reorderPoint;
  int ordersToday;
};

static Product PRODUCTS[] = {
  { "P001", "Rice",  "A1 B2 C3 D4", 40,  8, 0 },
  { "P002", "Milk",  "11 22 33 44", 18, 12, 0 },
  { "P003", "Beans", "DE AD BE EF", 25,  5, 0 },
};
static const int NUM_PRODUCTS = sizeof(PRODUCTS) / sizeof(PRODUCTS[0]);
