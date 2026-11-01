"""
build_slides.py
---------------
Generates a professional 15-slide presentation (.pptx) for the Sathyabama
Interdisciplinary Project I defense and evaluation.
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

DOCS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SLIDES_DIR = os.path.join(DOCS_DIR, "slides")
DIAGRAMS_DIR = os.path.join(DOCS_DIR, "diagrams")
OUTPUT_PPTX = os.path.join(SLIDES_DIR, "Smart_Warehouse_Presentation.pptx")
os.makedirs(SLIDES_DIR, exist_ok=True)


def set_slide_background(slide, color_rgb):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = color_rgb


def add_header(slide, title_text, category_text="SATHYABAMA INSTITUTE OF SCIENCE AND TECHNOLOGY"):
    # Header banner
    tx_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(8.4), Inches(1.1))
    tf = tx_box.text_frame
    tf.word_wrap = True
    
    p_cat = tf.paragraphs[0]
    p_cat.text = category_text.upper()
    p_cat.font.size = Pt(10)
    p_cat.font.bold = True
    p_cat.font.color.rgb = RGBColor(56, 189, 248) # Cyan accent
    
    p_title = tf.add_paragraph()
    p_title.text = title_text
    p_title.font.size = Pt(22)
    p_title.font.bold = True
    p_title.font.color.rgb = RGBColor(248, 250, 252) # White/light


def main():
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(5.625) # 16:9 widescreen ratio
    blank_layout = prs.slide_layouts[6]

    DARK_BG = RGBColor(15, 23, 42)    # Slate 900
    CARD_BG = RGBColor(30, 41, 59)    # Slate 800
    TEXT_LIGHT = RGBColor(241, 245, 249)
    TEXT_MUTED = RGBColor(148, 163, 184)
    ACCENT_CYAN = RGBColor(56, 189, 248)
    ACCENT_GREEN = RGBColor(74, 222, 128)

    # ---------------------------------------------------------------- Slide 1: Title
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, DARK_BG)
    
    tb = s1.shapes.add_textbox(Inches(0.8), Inches(1.0), Inches(8.4), Inches(3.6))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "SATHYABAMA INSTITUTE OF SCIENCE AND TECHNOLOGY"
    p0.font.size = Pt(12)
    p0.font.bold = True
    p0.font.color.rgb = ACCENT_CYAN

    p1 = tf.add_paragraph()
    p1.text = "Autonomous Smart Warehouse Monitoring System Using AI & IoT"
    p1.font.size = Pt(26)
    p1.font.bold = True
    p1.font.color.rgb = RGBColor(255, 255, 255)
    p1.space_before = Pt(14)

    p2 = tf.add_paragraph()
    p2.text = "Interdisciplinary Project – I · Final Defense & Evaluation"
    p2.font.size = Pt(14)
    p2.font.color.rgb = TEXT_MUTED
    p2.space_before = Pt(8)

    p3 = tf.add_paragraph()
    p3.text = "Candidate: Arya Vamsi Balaji | Email: balajiaryavamsi@gmail.com\nDepartment of CSE / ECE · Academic Year 2025–2026"
    p3.font.size = Pt(12)
    p3.font.color.rgb = ACCENT_GREEN
    p3.space_before = Pt(30)

    # ---------------------------------------------------------------- Slide 2: Problem
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2, DARK_BG)
    add_header(s2, "Industrial Problem Statement & Challenges")
    
    tb = s2.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(8.4), Inches(3.6))
    tf = tb.text_frame
    tf.word_wrap = True
    points2 = [
        ("Manual Auditing & Human Error:", "Paper stocktaking and optical barcode scanning cause 1–3% discrepancy rates and cycle count delays."),
        ("Environmental Spoilage of Perishables:", "Unnoticed temperature spikes, humidity, or combustible gas buildup spoil sensitive goods (grains, milk, legumes)."),
        ("Static Inventory Reorder Blind Spots:", "Conventional ERP thresholds overlook dynamic demand drivers (day-of-week surges, occupancy, promotions)."),
        ("Delayed Safety Hazard Alerts:", "Lack of bare-metal autonomous edge alerting exposes facilities to fire and obstruction hazards.")
    ]
    for title, desc in points2:
        p = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p.text = f"• {title} "
        p.font.bold = True
        p.font.size = Pt(13)
        p.font.color.rgb = ACCENT_CYAN
        p.space_before = Pt(8)
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.color.rgb = TEXT_LIGHT

    # ---------------------------------------------------------------- Slide 3: Objectives
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3, DARK_BG)
    add_header(s3, "Project Objectives & Scope")
    tb = s3.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(8.4), Inches(3.6))
    tf = tb.text_frame
    tf.word_wrap = True
    points3 = [
        "1. Real-Time Multi-Sensor Perception: Continuous acquisition of distance, temp, humidity, gas, and ambient light on ESP32 DevKit V1.",
        "2. Contactless RFID Identification: 13.56 MHz Mifare tracking for 3 products: P001 Rice, P002 Milk, P003 Beans.",
        "3. Machine Learning Demand Intelligence: Random Forest Regressor predicting next-day demand with R² > 0.90.",
        "4. Automated Dynamic Replenishment: Algorithmic restock calculation: max(RP, ceil(pred_demand * 1.25 - stock)).",
        "5. Dual Alerting & Telemetry Interface: <500ms on-device acoustic/optical alarms + live responsive Chart.js Web Dashboard."
    ]
    for pt in points3:
        p = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p.text = pt
        p.font.size = Pt(13)
        p.font.color.rgb = TEXT_LIGHT
        p.space_before = Pt(8)

    # ---------------------------------------------------------------- Slide 4: Architecture
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4, DARK_BG)
    add_header(s4, "End-to-End System Architecture")
    arch_img = os.path.join(DIAGRAMS_DIR, "system_architecture.png")
    if os.path.exists(arch_img):
        s4.shapes.add_picture(arch_img, Inches(0.8), Inches(1.4), Inches(8.4))

    # ---------------------------------------------------------------- Slide 5: Hardware
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5, DARK_BG)
    add_header(s5, "ESP32 Hardware Block Diagram & Interconnects")
    hw_img = os.path.join(DIAGRAMS_DIR, "hardware_block_diagram.png")
    if os.path.exists(hw_img):
        s5.shapes.add_picture(hw_img, Inches(1.2), Inches(1.4), Inches(7.6))

    # ---------------------------------------------------------------- Slide 6: Circuits
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6, DARK_BG)
    add_header(s6, "Circuit Protection & Voltage Dividers")
    tb = s6.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(8.4), Inches(3.6))
    tf = tb.text_frame
    tf.word_wrap = True
    c_pts = [
        ("HC-SR04 Echo Level Conversion (5V → 3.3V):", "ECHO pin outputs 5.0V pulses. A 10kΩ / 20kΩ divider scales voltage to 3.33V (V_out = 5 * 20 / 30), protecting GPIO 33."),
        ("LDR High-Side Voltage Divider:", "3.3V → LDR → GPIO 36 → 10kΩ → GND. Increased illumination reduces LDR resistance, yielding linear ADC increase (0–4095)."),
        ("Red LED Current Limiting:", "Driven via GPIO 26 through 180Ω resistor. (3.3V - 2.0V) / 180Ω = 7.22 mA safe current draw."),
        ("Boot Pin Protection (GPIO 12):", "Order button wired directly to GND with internal pull-up only to prevent boot-mode strapping conflicts.")
    ]
    for title, desc in c_pts:
        p = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p.text = f"• {title} "
        p.font.bold = True
        p.font.size = Pt(12)
        p.font.color.rgb = ACCENT_CYAN
        p.space_before = Pt(6)
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.color.rgb = TEXT_LIGHT

    # ---------------------------------------------------------------- Slide 7: Firmware
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7, DARK_BG)
    add_header(s7, "Embedded Firmware Architecture (Arduino C++)")
    tb = s7.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(8.4), Inches(3.6))
    tf = tb.text_frame
    tf.word_wrap = True
    fw_pts = [
        "Non-Blocking Cooperative Multitasking: Strict millis() timestamp scheduling with 0% blocking delay().",
        "Sensors & Hazard Loops (500ms): Ultrasonic pulseIn with 25ms timeout, MQ-2 analog smoothing, LDR read, alert evaluation.",
        "Environmental Logging (2000ms): DHT11 temperature/humidity sampling and Serial diagnostic reporting.",
        "Rotating LCD Task (3000ms): Automatic 0x27 / 0x3F address auto-detection, cycling 4 telemetry screens + ML predictions.",
        "Wi-Fi & HTTP Telemetry (5000ms): Non-blocking reconnect, ArduinoJson v7 serialization, and inventory state sync."
    ]
    for pt in fw_pts:
        p = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p.text = f"• {pt}"
        p.font.size = Pt(13)
        p.font.color.rgb = TEXT_LIGHT
        p.space_before = Pt(8)

    # ---------------------------------------------------------------- Slide 8: ML Pipeline
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8, DARK_BG)
    add_header(s8, "Machine Learning Predictive Demand Pipeline")
    tb = s8.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(4.5), Inches(3.6))
    tf = tb.text_frame
    tf.word_wrap = True
    ml_pts = [
        "Model: Random Forest Regressor",
        "Dataset: 120 days × 3 products = 360 samples",
        "Train/Test Split: 75% / 25% (90 test samples)",
        "Hyperparameters: 250 trees, max_depth=10, min_samples_split=5, min_samples_leaf=2",
        "Features (8): orders, avg_temp_c, occupancy_pct, ambient_light_adc, promo_flag, day_of_week, stock_on_hand, reorder_point",
        "Target: next_day_demand (0–20 units)"
    ]
    for pt in ml_pts:
        p = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p.text = f"• {pt}"
        p.font.size = Pt(11.5)
        p.font.color.rgb = TEXT_LIGHT
        p.space_before = Pt(5)

    fi_img = os.path.join(DIAGRAMS_DIR, "feature_importance.png")
    if os.path.exists(fi_img):
        s8.shapes.add_picture(fi_img, Inches(5.2), Inches(1.4), Inches(4.2))

    # ---------------------------------------------------------------- Slide 9: Model Results
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9, DARK_BG)
    add_header(s9, "Model Performance vs Target Specifications")
    tb = s9.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(8.4), Inches(3.6))
    tf = tb.text_frame
    tf.word_wrap = True
    m_pts = [
        ("Coefficient of Determination (R²):", "Achieved 0.9460 (Target: > 0.90, min 0.93) -> EXCEEDED"),
        ("Mean Absolute Error (MAE):", "Achieved 0.6852 units (Target: < 2.0 units) -> EXCEEDED"),
        ("Root Mean Squared Error (RMSE):", "Achieved 0.8653 units (Target: < 2.5 units) -> EXCEEDED"),
        ("Predictions within ±2 Units:", "Achieved 97.78% on holdout test set -> EXCEEDED"),
        ("Dynamic Restock Formula:", "Restock = max(reorder_point, ceil(pred_demand * 1.25 - stock))")
    ]
    for title, desc in m_pts:
        p = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p.text = f"• {title} "
        p.font.bold = True
        p.font.size = Pt(13)
        p.font.color.rgb = ACCENT_GREEN
        p.space_before = Pt(8)
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.color.rgb = TEXT_LIGHT

    # ---------------------------------------------------------------- Slide 10: API
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10, DARK_BG)
    add_header(s10, "RESTful Microservice API (Flask)")
    tb = s10.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(8.4), Inches(3.6))
    tf = tb.text_frame
    tf.word_wrap = True
    api_pts = [
        ("POST /api/predict:", "Accepts 8 features, executes Random Forest inference, returns predicted demand, restock recommendation, and timestamp."),
        ("GET /api/status:", "Returns online state, model loaded status, R²/MAE/RMSE metrics, active alert count, and device uptime."),
        ("POST /api/log:", "Ingests telemetry from ESP32, updates SQLite database, flags safety violations, and synchronizes stock levels."),
        ("GET /api/history?limit=100:", "Serves chronological telemetry series for real-time Chart.js visual streams."),
        ("Optimized Execution:", "Single-threaded inference (n_jobs=1) eliminates dispatch overhead, achieving ~70ms response latency.")
    ]
    for title, desc in api_pts:
        p = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p.text = f"• {title} "
        p.font.bold = True
        p.font.size = Pt(12)
        p.font.color.rgb = ACCENT_CYAN
        p.space_before = Pt(6)
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.color.rgb = TEXT_LIGHT

    # ---------------------------------------------------------------- Slide 11: Dashboard
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11, DARK_BG)
    add_header(s11, "Real-Time Operator Web Dashboard")
    dash_img = os.path.join(DIAGRAMS_DIR, "dashboard.png")
    if os.path.exists(dash_img):
        s11.shapes.add_picture(dash_img, Inches(1.0), Inches(1.35), Inches(8.0))

    # ---------------------------------------------------------------- Slide 12: Test Cases
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_background(s12, DARK_BG)
    add_header(s12, "Verification & Test Cases (TC01 – TC10)")
    tb = s12.shapes.add_textbox(Inches(0.8), Inches(1.4), Inches(8.4), Inches(3.8))
    tf = tb.text_frame
    tf.word_wrap = True
    tcs = [
        "TC01 (Temp Accuracy): ±2°C tolerance benchmarked against reference.",
        "TC02 (Distance Accuracy): Validated across 5cm, 15cm, 25cm test points.",
        "TC03 (RFID Recognition): 100% recognition for Rice, Milk, Beans tags.",
        "TC04 (Light Detection): Dark (<40%), Medium, Bright (>75%) classification.",
        "TC05 (Gas Hazard Alert): Alarm triggered at >2000 ADC within <500ms.",
        "TC06 (LCD Rotation): 4 screens rotate sequentially at 3000ms ± 100ms.",
        "TC07 (Demand Prediction): Error within ±2 units (97.8% achieved, R²=0.946).",
        "TC08 (Stock Alert Logic): Low stock alert triggered when stock < reorder point.",
        "TC09 (Wi-Fi REST Telemetry): 200 OK received; latency 65–76 ms (< 500ms).",
        "TC10 (End-to-End Workflow): Telemetry → Ingestion → Prediction → UI verified."
    ]
    for tc in tcs:
        p = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p.text = f"✓ {tc}"
        p.font.size = Pt(11)
        p.font.color.rgb = ACCENT_GREEN
        p.space_before = Pt(3)

    # ---------------------------------------------------------------- Slide 13: BOM & Cost
    s13 = prs.slides.add_slide(blank_layout)
    set_slide_background(s13, DARK_BG)
    add_header(s13, "Bill of Materials (BOM) & Power Profile")
    tb = s13.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(8.4), Inches(3.6))
    tf = tb.text_frame
    tf.word_wrap = True
    bom_pts = [
        "Total Hardware Budget: ₹1,640 (Extremely cost-effective for SME warehouses).",
        "Core Controllers: ESP32 DevKit V1 (₹450) · 16×2 I2C LCD (₹220) · Breadboard & Wiring (₹210).",
        "Sensors: HC-SR04 (₹85) · DHT11 (₹110) · RC522 + 3 Tags (₹240) · MQ-2 (₹140) · LDR (₹10).",
        "Peripherals: Red LED, Buzzer, Tactile Buttons, Resistor Kit (₹185).",
        "Power Analysis: 185mA idle (0.925W) · 310mA active (1.55W) · 460mA peak alert (2.3W).",
        "Easily powered via single 5V 1A USB adapter or low-cost power bank."
    ]
    for pt in bom_pts:
        p = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p.text = f"• {pt}"
        p.font.size = Pt(12.5)
        p.font.color.rgb = TEXT_LIGHT
        p.space_before = Pt(7)

    # ---------------------------------------------------------------- Slide 14: Conclusion
    s14 = prs.slides.add_slide(blank_layout)
    set_slide_background(s14, DARK_BG)
    add_header(s14, "Conclusion & Future Roadmap")
    tb = s14.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(8.4), Inches(3.6))
    tf = tb.text_frame
    tf.word_wrap = True
    c_pts = [
        ("Key Achievements:", "Engineered an autonomous end-to-end edge-to-cloud IoT warehouse solution with sub-500ms safety alerting and 94.6% demand prediction accuracy."),
        ("Operational Value:", "Zero stockouts, automated RFID cycle-counting, and immediate spoilage prevention across perishable inventories."),
        ("Future Roadmap 1 (Cloud & Security):", "AWS IoT Core migration with TLS-secured MQTT messaging and role-based operator access."),
        ("Future Roadmap 2 (Advanced AI):", "Long Short-Term Memory (LSTM) recurrent networks for multi-month horizon seasonality."),
        ("Future Roadmap 3 (Automation):", "Autonomous Mobile Robot (AMR) dispatch for hands-free pallet replenishment.")
    ]
    for title, desc in c_pts:
        p = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p.text = f"• {title} "
        p.font.bold = True
        p.font.size = Pt(12)
        p.font.color.rgb = ACCENT_CYAN
        p.space_before = Pt(6)
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.color.rgb = TEXT_LIGHT

    # ---------------------------------------------------------------- Slide 15: Q&A
    s15 = prs.slides.add_slide(blank_layout)
    set_slide_background(s15, DARK_BG)
    tb = s15.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(8.4), Inches(2.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p_q = tf.paragraphs[0]
    p_q.text = "THANK YOU!"
    p_q.font.size = Pt(36)
    p_q.font.bold = True
    p_q.font.color.rgb = RGBColor(255, 255, 255)
    p_q.alignment = PP_ALIGN.CENTER

    p_sub = tf.add_paragraph()
    p_sub.text = "Questions & Demonstration\nArya Vamsi Balaji | balajiaryavamsi@gmail.com\nSathyabama Institute of Science and Technology"
    p_sub.font.size = Pt(16)
    p_sub.font.color.rgb = ACCENT_CYAN
    p_sub.space_before = Pt(16)
    p_sub.alignment = PP_ALIGN.CENTER

    prs.save(OUTPUT_PPTX)
    print("Presentation compiled successfully:", OUTPUT_PPTX)


if __name__ == "__main__":
    main()
