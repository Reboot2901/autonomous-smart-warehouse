# Bill of Materials (BOM)

## Autonomous Smart Warehouse Monitoring System Using AI & IoT
**Student:** Arya Vamsi Balaji (balajiaryavamsi@gmail.com)  
**Institution:** Sathyabama Institute of Science and Technology  
**Project:** Interdisciplinary Project I  

---

### Hardware Components Specification & Cost Breakdown

| S.No | Component | Description / Part No. | Operating Voltage | Interface / GPIO Pins | Qty | Unit Price (INR ₹) | Total Price (INR ₹) | Sourcing / Remarks |
|:---:|:---|:---|:---:|:---:|:---:|---:|---:|:---|
| 1 | **ESP32 DevKit V1** | 30-pin Dual-Core Xtensa LX6, 2.4 GHz Wi-Fi + BLE, 520 KB SRAM | 5V (USB) / 3.3V Logic | Main Microcontroller | 1 | ₹450 | ₹450 | Robu.in / Amazon |
| 2 | **HC-SR04** | Ultrasonic Distance Sensor (2 cm – 400 cm range, 15° beam) | 5V VCC | TRIG: GPIO 32<br>ECHO: GPIO 33 (via divider) | 1 | ₹85 | ₹85 | Requires 10k/20k voltage divider on ECHO |
| 3 | **DHT11** | Digital Temperature & Humidity Sensor (0–50°C ±2°C, 20–90% RH ±5%) | 3.3V – 5V | DATA: GPIO 15 | 1 | ₹110 | ₹110 | Single-bus communication |
| 4 | **RC522 Module** | 13.56 MHz RFID Reader/Writer (ISO/IEC 14443A Mifare) | 3.3V VCC | SPI: SS=5, RST=4, SCK=18, MOSI=23, MISO=19 | 1 | ₹165 | ₹165 | Power from 3.3V rail ONLY |
| 5 | **RFID Tags / Cards** | 13.56 MHz Mifare Classic 1K Cards/Keyfobs (P001, P002, P003) | Passive | Wireless RF | 3 | ₹25 | ₹75 | Assigned to Rice, Milk, Beans |
| 6 | **MQ-2 Gas Sensor** | Smoke, LPG, Butane, Methane, Combustible Gas Sensor | 5V VCC (Heater ~800 mW) | AO: GPIO 34 (via divider)<br>DO: GPIO 35 | 1 | ₹140 | ₹140 | Needs ~30s heater pre-heat period |
| 7 | **LDR (Photoresistor)** | 5mm Light Dependent Resistor (GL5528, 10k–20k light, 1M dark) | 3.3V | Analog: GPIO 36 (ADC1_CH0) | 1 | ₹10 | ₹10 | In voltage divider with 10kΩ resistor |
| 8 | **I2C 16×2 LCD Display** | HD44780 with PCF8574T I2C Backpack (Address 0x27 or 0x3F) | 5V VCC | I2C: SDA=21, SCL=22 | 1 | ₹220 | ₹220 | Blue backlight with trimpot contrast |
| 9 | **Red 5mm LED** | High-brightness diffuse Red LED (Stock alert indicator) | 2.0V Vf | GPIO 26 (via 180Ω resistor) | 1 | ₹5 | ₹5 | Current: ~(3.3 - 2.0) / 180 = ~7.2 mA |
| 10 | **Piezo Buzzer** | 5V/3.3V Passive Buzzer (Audible alarms & tones) | 3.3V | GPIO 13 | 1 | ₹25 | ₹25 | Tone generated for frequency modulation |
| 11 | **Pushbuttons** | 6×6×5mm Tactile switches (Order & Emergency) | 3.3V | BTN1 (Order): GPIO 12<br>BTN2 (Emerg): GPIO 14 | 2 | ₹10 | ₹20 | Internal pull-up enabled in firmware |
| 12 | **Resistor Kit** | 180Ω (LED), 10kΩ & 20kΩ (voltage dividers & pull-downs) | 1/4W Metal Film | Passive circuits | 1 set | ₹30 | ₹30 | 180Ω (1x), 10kΩ (3x), 20kΩ (2x) |
| 13 | **Solderless Breadboard** | 830-point MB-102 Breadboard with power distribution rails | - | Prototyping | 1 | ₹130 | ₹130 | Dual power rails |
| 14 | **Jumper Wires** | Male-to-Male, Male-to-Female, Female-to-Female assortment | - | Interconnects | 1 pack | ₹80 | ₹80 | 40-pin ribbon |
| 15 | **Micro-USB Cable** | High-quality USB-A to Micro-USB data cable (1m) | 5V, 2A | Power & Serial Programming | 1 | ₹90 | ₹90 | UART flashing & debugging |
| **Total** | | | | | | | **₹1,640** | **Total Estimated Hardware Budget** |

---

### Component Power Consumption Estimates

| Component | Supply Voltage | Active Current | Idle Current | Notes |
|:---|:---:|:---:|:---:|:---|
| ESP32 DevKit V1 | 5.0 V | 160 – 240 mA | 80 mA | Wi-Fi TX bursts reach ~240 mA peak |
| MQ-2 Sensor | 5.0 V | ~160 mA | ~160 mA | Internal heater coil draws continuous current |
| I2C 16×2 LCD | 5.0 V | ~25 mA | ~5 mA | Includes LED backlight |
| HC-SR04 | 5.0 V | 15 mA | 2 mA | Trigger pulse periodic draw |
| RC522 RFID | 3.3 V | 26 mA | 10 mA | Transceiver active during scan |
| DHT11 | 3.3 V | 1.5 mA | 0.1 mA | Sample reading every 2 seconds |
| LDR Circuit | 3.3 V | ~0.3 mA | ~0.1 mA | Divider with 10kΩ resistor |
| Red LED | 3.3 V | 7.2 mA | 0 mA | Only drawn when alert LED is ON |
| Piezo Buzzer | 3.3 V | 15 mA | 0 mA | Only drawn during acoustic alerts |
| **Total System Draw** | **5.0 V / 3.3 V** | **~460 mA (peak)** | **~260 mA** | **Easily powered by a standard 5V 1A or 2A USB port/charger** |
