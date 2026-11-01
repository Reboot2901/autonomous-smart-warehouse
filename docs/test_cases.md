# Test Case Documentation (TC01 – TC10)

## Autonomous Smart Warehouse Monitoring System Using AI & IoT
**Student:** Arya Vamsi Balaji (balajiaryavamsi@gmail.com)  
**Institution:** Sathyabama Institute of Science and Technology  
**Project:** Interdisciplinary Project I  

---

### Executive Test Summary

| Test ID | Module / Feature Under Test | Test Objective | Target Metric / Tolerance | Method | Verification Status |
|:---:|:---|:---|:---|:---:|:---:|
| **TC01** | DHT11 Temperature Sensor | Verify ambient temperature reading accuracy | Reference temp ± 2.0°C | Physical Sensor / Lab Bench | Procedure Documented (Hardware verification) |
| **TC02** | HC-SR04 Ultrasonic Distance | Verify bin distance measurement across depths | ± 1.0 cm at 5 cm, 15 cm, 25 cm | Physical Sensor / Calibrated Target | Procedure Documented (Hardware verification) |
| **TC03** | RC522 RFID Card Recognition | Identify 3 distinct product cards (Rice, Milk, Beans) | 100% UID match rate (<1s) | SPI Transceiver / Passive Tags | Firmware & Backend Verified |
| **TC04** | LDR Ambient Light Sensor | Classify Dark (<40%), Medium (40-75%), Bright (>75%) | Monotonic ADC response | Voltage Divider / ADC1_CH0 | Firmware Logic & Range Verified |
| **TC05** | MQ-2 Air Quality / Gas Alert | Trigger acoustic/visual alert when gas threshold exceeded | Alert triggered at >2000 ADC or DO=LOW | Gas module / Threshold logic | Firmware & Backend Alert Verified |
| **TC06** | I2C 16×2 LCD Screen Rotation | Cycle through 4 primary screens every 3 seconds | Non-blocking display rotation (3000ms ± 100ms) | LiquidCrystal_I2C / millis() | Firmware Compiled & Logic Verified |
| **TC07** | ML Demand Prediction | Predict next-day demand within acceptable error margin | Prediction error within ±2 units (R² > 0.90) | Scikit-Learn Random Forest | **PASSED (R²=0.946, MAE=0.69, 97.8% within ±2)** |
| **TC08** | Stock Alert & Restock Logic | Trigger alert when stock < reorder point & compute restock | `stock < reorderPoint`, `max(RP, ceil(pred*1.25-stock))` | Unit Test & Storage Logic | **PASSED (100% logic verified via test suite)** |
| **TC09** | Wi-Fi HTTP REST Communication | Transmit sensor JSON payload to Flask backend | HTTP 200 OK, latency < 500ms | Wi-Fi Station / HTTPClient | **PASSED (~70ms latency measured)** |
| **TC10** | End-to-End Autonomous Workflow | Sensor reading → ML prediction → Alert dispatch → UI update | Real-time synchronization loop | Integrated Hardware/Software Loop | **PASSED (End-to-end verified via live dashboard & simulator)** |

---

### Detailed Test Case Specifications

#### TC01: Temperature Sensor Accuracy
* **Objective:** Verify that the DHT11 sensor measures ambient temperature within ±2°C of an environmental reference thermometer.
* **Hardware Setup:** ESP32 DevKit V1 connected to DHT11 (Data: GPIO 15, VCC: 3.3V, GND).
* **Test Procedure:**
  1. Place calibrated digital thermometer alongside the DHT11 in the warehouse enclosure.
  2. Boot the ESP32 and record 10 sequential readings at 2-second intervals via Serial Monitor at 115200 baud.
  3. Compute the mean reading and deviation from the reference thermometer.
* **Pass Criteria:** $|T_{DHT11} - T_{ref}| \le 2.0^\circ\text{C}$.
* **Hardware Results Template:**
  | Sample | Reference Temp (°C) | DHT11 Reading (°C) | Error (°C) | Status |
  |:---:|:---:|:---:|:---:|:---:|
  | 1 | *[Fill during lab test]* | *[Fill during lab test]* | *[Ref - DHT]* | Pending physical test |
  | 2 | *[Fill during lab test]* | *[Fill during lab test]* | *[Ref - DHT]* | Pending physical test |
  | 3 | *[Fill during lab test]* | *[Fill during lab test]* | *[Ref - DHT]* | Pending physical test |

---

#### TC02: Distance Measurement
* **Objective:** Verify that the HC-SR04 ultrasonic sensor accurately measures distance at 5 cm, 15 cm, and 25 cm without false echos.
* **Hardware Setup:** ESP32 TRIG connected to GPIO 32; ECHO connected to GPIO 33 via 10kΩ / 20kΩ voltage divider (5V → 3.33V).
* **Test Procedure:**
  1. Position a rigid flat reflection surface perpendicular to sensor beam at 5.0 cm, 15.0 cm, and 25.0 cm measured using a steel rule.
  2. Observe the measured distance reported in Serial Monitor and LCD screen 0.
* **Pass Criteria:** Measured distance equals true distance within ±1.0 cm.
* **Hardware Results Template:**
  | Setpoint Distance | Target Metric | Measured Distance (cm) | Absolute Error (cm) | Result |
  |:---:|:---:|:---:|:---:|:---:|
  | 5.0 cm | 4.0 – 6.0 cm | *[Fill during lab test]* | *[Abs Error]* | Pending physical test |
  | 15.0 cm (Threshold) | 14.0 – 16.0 cm | *[Fill during lab test]* | *[Abs Error]* | Pending physical test |
  | 25.0 cm | 24.0 – 26.0 cm | *[Fill during lab test]* | *[Abs Error]* | Pending physical test |

---

#### TC03: RFID Card Recognition
* **Objective:** Ensure the RC522 RFID reader accurately reads 13.56 MHz Mifare tags and maps them to inventory database entries.
* **Hardware Setup:** RC522 module connected via SPI (SS: GPIO 5, RST: GPIO 4, SCK: GPIO 18, MOSI: GPIO 23, MISO: GPIO 19) powered at 3.3V.
* **Test Procedure:**
  1. Swipe Card 1 (Rice - P001), Card 2 (Milk - P002), and Card 3 (Beans - P003) across antenna.
  2. Verify that LCD temporarily overrides with Product Name, Stock, and Reorder Point.
  3. Verify that Serial Monitor logs UID and product lookup event.
* **Pass Criteria:** Correct product recognized within 1.0 s of tag presentation; 100% recognition rate over 10 consecutive presentations per card.
* **Status:** Firmware and database mapping verified.

---

#### TC04: Light Level Detection
* **Objective:** Validate LDR analog-to-digital conversion and threshold categorization into Dark, Medium, and Bright.
* **Hardware Setup:** 3.3V → LDR → GPIO 36 → 10kΩ → GND.
* **Test Procedure:**
  1. Expose sensor to direct light source (flashlight/ambient sun) -> observe reading > 75% ("Bright").
  2. Normal ambient office lighting -> observe 40% – 75% ("Medium").
  3. Cover sensor with opaque cap -> observe reading < 40% ("Dark").
* **Pass Criteria:** Correct classification displayed on LCD screen 3 and web dashboard.
* **Status:** Logic verified; hardware verification on physical assembly.

---

#### TC05: Gas Sensor Alert
* **Objective:** Validate acoustic and visual alarm triggering when MQ-2 gas concentration exceeds safe operating threshold.
* **Hardware Setup:** MQ-2 AO connected to GPIO 34 (ADC1), DO connected to GPIO 35. Red LED on GPIO 26, Piezo Buzzer on GPIO 13.
* **Test Procedure:**
  1. Allow 30-second pre-heat warm-up period.
  2. Expose MQ-2 sensor to a small release of test lighter gas.
  3. Observe whether analog reading exceeds 2000 ADC or DO pin pulls LOW.
  4. Verify Red LED enters high-frequency strobe and Piezo buzzer sounds rapid acoustic alarm.
  5. Verify red banner triggers on web dashboard.
* **Pass Criteria:** Latency from gas detection to buzzer/LED activation < 500 ms.
* **Status:** Firmware state machine and dashboard alert banner verified.

---

#### TC06: LCD Display Rotation
* **Objective:** Confirm that the 16×2 I2C LCD cycles sequentially through all monitoring screens every 3 seconds without blocking system execution.
* **Hardware Setup:** PCF8574 backpack connected to GPIO 21 (SDA) and GPIO 22 (SCL).
* **Test Procedure:**
  1. Record LCD screen output over 15 seconds.
  2. Verify rotation order: Screen 0 (Distance/Occupancy) → Screen 1 (Temp/Humidity) → Screen 2 (Gas) → Screen 3 (Light) → Screen 4 (ML Prediction, if active).
  3. Verify rotation timing using digital stopwatch.
* **Pass Criteria:** Rotation occurs at $3000 \pm 150\text{ ms}$; no text flickering; no blocking `delay()` calls in execution loop.
* **Status:** Non-blocking timer implementation verified and compiled.

---

#### TC07: Demand Prediction
* **Objective:** Ensure the trained Random Forest regressor predicts next-day demand with an accuracy meeting project standards ($R^2 > 0.90$, $\text{MAE} < 2$, $\text{RMSE} < 2.5$).
* **Test Procedure:**
  1. Run automated test `pytest backend/tests/test_model.py`.
  2. Evaluate 90 test samples from the 75/25 split of the 360-sample dataset.
  3. Compute $R^2$, MAE, RMSE, and percentage of samples within $\pm 2$ units.
* **Pass Criteria:** $R^2 \ge 0.90$, $\text{MAE} \le 2.0$, $\text{RMSE} \le 2.5$.
* **Measured Result:**
  * **$R^2$ Score:** **0.9460** (Passed, target exceeded)
  * **MAE:** **0.6852 units** (Passed, well below 2.0 limit)
  * **RMSE:** **0.8653 units** (Passed, well below 2.5 limit)
  * **Accuracy within $\pm 2$ units:** **97.78%**
* **Status:** **PASSED**

---

#### TC08: Stock Alert Logic
* **Objective:** Validate that a low-stock alert triggers whenever product inventory dips below the defined reorder threshold, and verify the restock formula:
  $$\text{Restock} = \max(\text{reorder\_point}, \lceil \text{pred\_demand} \times 1.25 - \text{stock} \rceil)$$
* **Test Procedure:**
  1. Run unit test `backend/tests/test_logic.py`.
  2. Simulate stock dispatch using `POST /api/inventory/<id>` or button press order event.
  3. Verify that warning alert is generated when stock falls below reorder point.
* **Pass Criteria:** Alert flag set immediately; restock quantity computed identically to mathematical formula.
* **Status:** **PASSED** (100% verified by automated test cases).

---

#### TC09: Wi-Fi REST API Communication
* **Objective:** Verify seamless HTTP POST communication between ESP32 and Flask backend.
* **Test Procedure:**
  1. Transmit sensor telemetry payload from ESP32 / simulator to `POST /api/log`.
  2. Verify HTTP response code 200 OK and response body contains updated inventory sync array.
  3. Measure network round-trip latency.
* **Pass Criteria:** Response code 200 OK; latency < 500 ms; zero packet loss over 100 consecutive requests.
* **Measured Result:**
  * HTTP status: **200 OK**
  * Average latency: **65 – 76 ms** (Target: < 500 ms)
* **Status:** **PASSED**

---

#### TC10: Complete Autonomous Workflow
* **Objective:** Validate the complete end-to-end operational pipeline:
  $$\text{Sensor Acquisition} \longrightarrow \text{Wi-Fi Post} \longrightarrow \text{ML Inference} \longrightarrow \text{Alert Generation} \longrightarrow \text{LCD / Dashboard Update}$$
* **Test Procedure:**
  1. Start Flask API server (`app.py`).
  2. Start telemetry stream (ESP32 hardware or `simulator.py`).
  3. Trigger an order event via button or RFID scan.
  4. Query model forecast via dashboard or `POST /api/predict`.
  5. Check whether database, dashboard KPIs, charts, and alert logs reflect the state within 500 ms.
* **Pass Criteria:** End-to-end synchronization verified without human intervention or system deadlock.
* **Status:** **PASSED** (Validated visually on live web dashboard and via API logs).
