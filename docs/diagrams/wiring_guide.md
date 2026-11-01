# Hardware Circuit & Wiring Guide

## Autonomous Smart Warehouse Monitoring System Using AI & IoT
**Author:** Arya Vamsi Balaji (balajiaryavamsi@gmail.com)  
**Institution:** Sathyabama Institute of Science and Technology  

---

### Complete Pin Allocation Matrix (ESP32 DevKit V1 - 30 Pin)

| ESP32 Pin | Function / Sensor | Direction | Electrical Interface / Level | Notes / Protection |
|:---|:---|:---:|:---|:---|
| **GPIO 32** | HC-SR04 Trigger | Output | 3.3V Logic | 10µs trigger pulse |
| **GPIO 33** | HC-SR04 Echo | Input | 3.3V (via divider) | **CRITICAL:** 5V Echo → [10kΩ] → GPIO33 → [20kΩ] → GND |
| **GPIO 15** | DHT11 Data | Bi-directional | 3.3V Single-Bus | Sampled every 2 seconds |
| **GPIO 5** | RC522 SDA / SS | Output | 3.3V SPI Slave Select | Active Low select |
| **GPIO 4** | RC522 RST | Output | 3.3V SPI Reset | Module reset line |
| **GPIO 18** | RC522 SCK | Output | 3.3V SPI Clock | Default VSPI clock |
| **GPIO 23** | RC522 MOSI | Output | 3.3V SPI Data Out | Master Out Slave In |
| **GPIO 19** | RC522 MISO | Input | 3.3V SPI Data In | Master In Slave Out |
| **GPIO 34** | MQ-2 Analog (AO) | Input (ADC1_CH6) | 0 – 3.3V Analog | 12-bit ADC, attenuated (ADC1 pin works with Wi-Fi) |
| **GPIO 35** | MQ-2 Digital (DO) | Input | 3.3V Digital (Comparator) | Active LOW when gas exceeds potentiometer threshold |
| **GPIO 36 (VP)** | LDR Analog | Input (ADC1_CH0) | 0 – 3.3V Analog | 3.3V → LDR → GPIO36 → [10kΩ] → GND (brighter = higher ADC) |
| **GPIO 21** | 16×2 LCD SDA | Bi-directional | 3.3V / 5V I2C Data | PCF8574T I2C backpack (Address: 0x27 or 0x3F) |
| **GPIO 22** | 16×2 LCD SCL | Output | 3.3V / 5V I2C Clock | I2C Bus Clock |
| **GPIO 26** | Red Alert LED | Output | 3.3V Logic (Active High) | Through 180Ω current-limiting resistor (~7.2 mA) |
| **GPIO 13** | Piezo Buzzer | Output | 3.3V PWM / Tone | Audible warning chirps and emergency siren |
| **GPIO 12** | Pushbutton 1 (Order) | Input | Active LOW (Pull-up) | **NOTE:** Boot strapping pin. Wire button to GND; no ext. pull-up |
| **GPIO 14** | Pushbutton 2 (Emerg) | Input | Active LOW (Pull-up) | Press latches alarm; press again clears alarm |
| **VIN / 5V** | Power Rail | Power Out / In | 5.0V DC | Powers HC-SR04 VCC, MQ-2 VCC, LCD VCC |
| **3V3** | Power Rail | Power Out | 3.3V Regulated DC | Powers RC522 VCC, DHT11 VCC, LDR divider |
| **GND** | Ground Rail | Ground | 0V Reference | Common Ground for all sensors and power rails |

---

### Detailed Circuit Schematics & Voltage Dividers

```
1. HC-SR04 Ultrasonic Sensor Voltage Divider (5V to 3.3V Level Conversion):
   HC-SR04 ECHO (5V Out) ──[ 10 kΩ Resistor ]──┬──> ESP32 GPIO 33
                                               │
                                         [ 20 kΩ Resistor ]
                                               │
                                              GND
   Formula: V_out = 5.0V * (20k / (10k + 20k)) = 5.0V * (2/3) = 3.33V (Safe for ESP32)

2. Ambient Light Sensor (LDR) Voltage Divider:
   3.3V Rail ──[ LDR (Photoresistor) ]──┬──> ESP32 GPIO 36 (ADC1_CH0)
                                        │
                                  [ 10 kΩ Resistor ]
                                        │
                                       GND
   Operation: Light increases -> LDR resistance drops (e.g. from 1MΩ dark to 10kΩ bright)
              -> Voltage at GPIO 36 increases -> ADC reading increases (0 - 4095).

3. Red LED Indicator:
   ESP32 GPIO 26 ──[ 180 Ω Resistor ]──>|── [Red LED Anode -> Cathode] ──> GND
   Formula: I_led = (3.3V - 2.0V_f) / 180Ω = 1.3V / 180Ω = 7.22 mA

4. Pushbuttons (Order and Emergency):
   ESP32 GPIO 12 ──[ Tactile Switch ]──> GND  (Firmware enables internal pull-up)
   ESP32 GPIO 14 ──[ Tactile Switch ]──> GND  (Firmware enables internal pull-up)

5. RC522 RFID Reader:
   VCC  ──> ESP32 3V3  (DO NOT CONNECT TO 5V)
   RST  ──> ESP32 GPIO 4
   GND  ──> ESP32 GND
   MISO ──> ESP32 GPIO 19
   MOSI ──> ESP32 GPIO 23
   SCK  ──> ESP32 GPIO 18
   SDA  ──> ESP32 GPIO 5

6. I2C LCD Display (with PCF8574 Backpack):
   VCC ──> ESP32 VIN (5V)
   GND ──> ESP32 GND
   SDA ──> ESP32 GPIO 21
   SCL ──> ESP32 GPIO 22
```
