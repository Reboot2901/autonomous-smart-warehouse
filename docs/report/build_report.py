"""
build_report.py
---------------
Compiles the complete 7-chapter Sathyabama Project Report into a styled .docx
document complete with title page, formatted tables, and embedded high-res diagrams.
"""

import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

DOCS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_DIR = os.path.join(DOCS_DIR, "report")
DIAGRAMS_DIR = os.path.join(DOCS_DIR, "diagrams")
OUTPUT_DOCX = os.path.join(REPORT_DIR, "Smart_Warehouse_Report.docx")


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def add_styled_heading(doc, text, level):
    p = doc.add_heading(text, level=level)
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    run = p.runs[0]
    if level == 1:
        run.font.size = Pt(18)
        run.font.bold = True
        run.font.color.rgb = RGBColor(15, 23, 42) # Slate 900
    elif level == 2:
        run.font.size = Pt(14)
        run.font.bold = True
        run.font.color.rgb = RGBColor(30, 41, 59) # Slate 800
    elif level == 3:
        run.font.size = Pt(12)
        run.font.bold = True
        run.font.color.rgb = RGBColor(51, 65, 85)
    return p


def main():
    doc = Document()

    # Page Margins: 1 inch
    for s in doc.sections:
        s.top_margin = Inches(1)
        s.bottom_margin = Inches(1)
        s.left_margin = Inches(1)
        s.right_margin = Inches(1)

    # Base Normal Style
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(12)
    normal_style.font.color.rgb = RGBColor(30, 41, 59)

    # ============================== TITLE PAGE ==============================
    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p_inst.add_run("SATHYABAMA\nINSTITUTE OF SCIENCE AND TECHNOLOGY\n")
    r.font.size = Pt(16)
    r.font.bold = True
    r.font.color.rgb = RGBColor(15, 23, 42)

    r_sub = p_inst.add_run("(DEEMED TO BE UNIVERSITY)\nAccredited with 'A++' Grade by NAAC | Approved by AICTE\nJeppiaar Nagar, Rajiv Gandhi Salai, Chennai – 600 119\n\n")
    r_sub.font.size = Pt(10)
    r_sub.font.color.rgb = RGBColor(100, 116, 139)

    p_proj = doc.add_paragraph()
    p_proj.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_proj.paragraph_format.space_before = Pt(30)
    r_title = p_proj.add_run("AUTONOMOUS SMART WAREHOUSE MONITORING SYSTEM USING AI & IoT\n\n")
    r_title.font.size = Pt(20)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(30, 58, 138) # Deep Blue

    r_desc = p_proj.add_run("AN INTERDISCIPLINARY PROJECT REPORT – I\nSubmitted in partial fulfillment of the requirements for the degree of\nBACHELOR OF TECHNOLOGY / ENGINEERING\n\n\n")
    r_desc.font.size = Pt(11)

    p_auth = doc.add_paragraph()
    p_auth.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_auth.paragraph_format.space_before = Pt(50)
    r_by = p_auth.add_run("Submitted By:\n")
    r_by.font.size = Pt(12)
    r_name = p_auth.add_run("ARYA VAMSI BALAJI\n")
    r_name.font.size = Pt(14)
    r_name.font.bold = True
    r_email = p_auth.add_run("Email: balajiaryavamsi@gmail.com\n\n")
    r_email.font.size = Pt(11)
    r_email.font.italic = True

    r_year = p_auth.add_run("DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING / ECE\nACADEMIC YEAR 2025 – 2026")
    r_year.font.size = Pt(11)
    r_year.font.bold = True

    doc.add_page_break()

    # ========================== TABLE OF CONTENTS ===========================
    add_styled_heading(doc, "TABLE OF CONTENTS", level=1)
    toc_items = [
        ("Chapter 1: Introduction", "1"),
        ("  1.1 Problem Statement", "1"),
        ("  1.2 Objectives", "2"),
        ("  1.3 Scope of the Project", "2"),
        ("Chapter 2: Literature Review", "3"),
        ("  2.1 IoT in Warehouse Management", "3"),
        ("  2.2 Machine Learning for Inventory Demand Forecasting", "4"),
        ("  2.3 RFID Technology Overview", "4"),
        ("  2.4 Smart Sensor Networks & Edge Computing", "5"),
        ("Chapter 3: Requirements & System Design", "6"),
        ("  3.1 Functional Requirements", "6"),
        ("  3.2 Non-Functional Requirements", "7"),
        ("  3.3 System Architecture", "7"),
        ("  3.4 Hardware Interconnect Block Diagram", "9"),
        ("Chapter 4: Implementation", "10"),
        ("  4.1 Hardware Assembly & Interconnects", "10"),
        ("  4.2 Circuit Design & Voltage Divider Formulations", "11"),
        ("  4.3 ESP32 Embedded Firmware Architecture", "12"),
        ("  4.4 Machine Learning Predictive Pipeline", "13"),
        ("  4.5 RESTful Microservice API Design", "14"),
        ("  4.6 Operator Web Dashboard", "15"),
        ("Chapter 5: Results & Performance Analysis", "16"),
        ("  5.1 Machine Learning Model Evaluation", "16"),
        ("  5.2 Verification of Test Cases (TC01 – TC10)", "17"),
        ("  5.3 System Latency & Response Times", "19"),
        ("  5.4 Power Consumption Analysis", "19"),
        ("Chapter 6: Conclusion & Future Scope", "20"),
        ("  6.1 Summary of Achievements", "20"),
        ("  6.2 Limitations Encountered", "20"),
        ("  6.3 Future Work", "21"),
        ("Chapter 7: References & Appendices", "22"),
        ("  7.1 References", "22"),
        ("  7.2 Appendix A: Bill of Materials (BOM)", "23"),
        ("  7.3 Appendix B: Hardware Pin Allocation Matrix", "24"),
    ]

    p_toc = doc.add_paragraph()
    for item, page in toc_items:
        p_t = doc.add_paragraph()
        p_t.paragraph_format.space_after = Pt(3)
        r1 = p_t.add_run(item)
        r1.font.size = Pt(11)
        r2 = p_t.add_run(f"  ................................................  {page}")
        r2.font.color.rgb = RGBColor(148, 163, 184)

    doc.add_page_break()

    # ========================== CHAPTER 1: INTRO ============================
    add_styled_heading(doc, "CHAPTER 1: INTRODUCTION", level=1)
    
    add_styled_heading(doc, "1.1 Problem Statement", level=2)
    p = doc.add_paragraph(
        "Modern inventory and warehouse operations remain hindered by manual audits, delayed stockout detection, "
        "and lack of continuous environmental monitoring. When storing perishable commodities such as grains, dairy products, "
        "and packaged beans, fluctuations in ambient temperature, moisture ingress, or combustible gas buildup can cause rapid, "
        "unnoticed spoilage. Furthermore, traditional ERP reordering policies rely on static threshold assumptions that fail to "
        "account for dynamic real-world variables such as promotion events, weather changes, and day-of-the-week consumption patterns."
    )
    p.paragraph_format.line_spacing = 1.15

    add_styled_heading(doc, "1.2 Objectives", level=2)
    objectives = [
        "Continuous Autonomous Perception: Deploy an ESP32 microcontroller network with 8 sensors/inputs to monitor distance, temperature, humidity, air quality, and ambient light.",
        "Contactless RFID Product Identification: Integrate high-frequency (13.56 MHz) RC522 RFID reader to support automated item lookups and stock cycle counts.",
        "Machine Learning Demand Forecasting: Train a Random Forest regressor on multi-dimensional telemetry and operational features to predict next-day demand with R² > 0.90.",
        "Dynamic Restock Optimization: Calculate intelligent replenishment quantities based on safety thresholds and predicted consumption.",
        "Real-Time Multi-Tier Alerting: Implement <500ms audible and visual edge alerts (piezo buzzer, strobe LED, I2C LCD) alongside a responsive operator Web Dashboard."
    ]
    for obj in objectives:
        doc.add_paragraph(obj, style='List Bullet')

    add_styled_heading(doc, "1.3 Scope of the Project", level=2)
    doc.add_paragraph(
        "The project monitors three targeted warehouse commodity products: P001 (Rice, staple grain), P002 (Milk, temperature-sensitive perishable), "
        "and P003 (Beans, moisture-sensitive legume). The operational scope covers edge data acquisition on bare-metal C++, wireless REST communication "
        "over 2.4 GHz Wi-Fi, a Python Flask microservice with SQLite database, and an operator dashboard."
    )

    doc.add_page_break()

    # ========================== CHAPTER 2: LIT REVIEW =======================
    add_styled_heading(doc, "CHAPTER 2: LITERATURE REVIEW", level=1)
    doc.add_paragraph(
        "2.1 IoT in Warehouse Management:\n"
        "Ubiquitous IoT sensor deployments have radically restructured supply chain logistics (Gubbi et al., 2013). "
        "Edge-based sensor nodes eliminate supervisory blind spots by transforming physical storage environments into digitized, event-driven assets."
    )
    doc.add_paragraph(
        "2.2 Machine Learning for Inventory Demand Forecasting:\n"
        "Carbonneau, Laframboise, and Vahidov (2008) demonstrated that ensemble machine learning models such as Random Forests outperform traditional "
        "linear ARIMA and exponential smoothing methods when non-linear factors (promotions, environmental conditions, seasonality) influence demand."
    )
    doc.add_paragraph(
        "2.3 RFID Technology Overview:\n"
        "Radio Frequency Identification (Want, 2006) provides non-line-of-sight contactless identification, eliminating the manual scanning bottlenecks "
        "and orientation constraints of traditional optical barcodes."
    )
    doc.add_paragraph(
        "2.4 Smart Sensor Networks & Edge Computing:\n"
        "Shi et al. (2016) highlighted the imperative of edge computing in industrial safety loops. Offloading local hazard alerts (such as gas detection) "
        "to the edge microcontroller ensures microsecond responsiveness independent of cloud latency or wide-area network dropouts."
    )

    doc.add_page_break()

    # ========================== CHAPTER 3: REQUIREMENTS ====================
    add_styled_heading(doc, "CHAPTER 3: REQUIREMENTS & SYSTEM DESIGN", level=1)
    
    add_styled_heading(doc, "3.1 Requirements Summary", level=2)
    doc.add_paragraph("Functional Requirements: Continuous sensing, RFID tracking, local LCD rotation (3s), acoustic/visual alerts, ML demand prediction, and web dashboard visualization.")
    doc.add_paragraph("Non-Functional Requirements: Edge alert latency <500 ms, predictive accuracy R² > 0.90, network API response time < 500 ms, and robust non-blocking Wi-Fi auto-recovery.")

    add_styled_heading(doc, "3.2 System Architecture", level=2)
    doc.add_paragraph("The multi-tier system architecture is illustrated below, depicting the flow from Perception Layer to Edge Processing, Transport, Application Backend, and Intelligence Engine:")

    arch_img = os.path.join(DIAGRAMS_DIR, "system_architecture.png")
    if os.path.exists(arch_img):
        doc.add_picture(arch_img, width=Inches(6.2))
        p_cap = doc.add_paragraph("Figure 3.1: End-to-End System Architecture Diagram")
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.runs[0].font.size = Pt(9.5)
        p_cap.runs[0].font.italic = True

    add_styled_heading(doc, "3.3 Hardware Block Diagram", level=2)
    hw_img = os.path.join(DIAGRAMS_DIR, "hardware_block_diagram.png")
    if os.path.exists(hw_img):
        doc.add_picture(hw_img, width=Inches(6.0))
        p_cap2 = doc.add_paragraph("Figure 3.2: ESP32 DevKit V1 Hardware Interconnect Block Diagram")
        p_cap2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap2.runs[0].font.size = Pt(9.5)
        p_cap2.runs[0].font.italic = True

    doc.add_page_break()

    # ========================== CHAPTER 4: IMPLEMENTATION ===================
    add_styled_heading(doc, "CHAPTER 4: IMPLEMENTATION", level=1)
    
    add_styled_heading(doc, "4.1 Circuit Protection & Voltage Dividers", level=2)
    doc.add_paragraph(
        "Because the ESP32 input GPIO pins tolerate a maximum of 3.3V, dedicated voltage divider circuits were engineered:\n"
        "1. HC-SR04 Echo Pin (5V to 3.3V):\n"
        "   V_out = 5.0V * (20k / (10k + 20k)) = 3.33V (Safe for GPIO 33).\n"
        "2. LDR Light Sensor:\n"
        "   3.3V Rail -> LDR (GL5528) -> GPIO 36 (ADC1_CH0) -> 10k Resistor -> GND. Bright light decreases LDR resistance, raising ADC voltage linearly.\n"
        "3. Red LED Current Limiting:\n"
        "   I = (3.3V - 2.0V) / 180 Ohm = 7.22 mA."
    )

    add_styled_heading(doc, "4.2 ESP32 Non-Blocking Firmware", level=2)
    doc.add_paragraph(
        "The firmware is architected using a non-blocking cooperative millis() scheduler. "
        "The main loop debounces buttons and services the RC522 RFID reader at >10 kHz without blocking delay() calls. "
        "Ultrasonic, gas, and LDR readings occur at 500ms intervals; temperature/humidity at 2000ms intervals; "
        "LCD display rotation at 3000ms intervals; and Wi-Fi HTTP POST telemetry at 5000ms intervals."
    )

    add_styled_heading(doc, "4.3 Machine Learning Pipeline", level=2)
    doc.add_paragraph(
        "A Random Forest regressor with 250 trees, max depth of 10, min_samples_split=5, and min_samples_leaf=2 was trained "
        "on 120 days of multi-feature data across all three products (360 samples). "
        "The model predicts next-day demand, enabling the calculation of the optimal dynamic restock order:\n"
        "Restock = max(reorder_point, ceil(pred_demand * 1.25 - stock_on_hand))"
    )

    add_styled_heading(doc, "4.4 Web Dashboard Interface", level=2)
    dash_img = os.path.join(DIAGRAMS_DIR, "dashboard.png")
    if os.path.exists(dash_img):
        doc.add_picture(dash_img, width=Inches(6.2))
        p_cap3 = doc.add_paragraph("Figure 4.1: Real-Time Operator Web Dashboard Interface")
        p_cap3.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap3.runs[0].font.size = Pt(9.5)
        p_cap3.runs[0].font.italic = True

    doc.add_page_break()

    # ========================== CHAPTER 5: RESULTS ==========================
    add_styled_heading(doc, "CHAPTER 5: RESULTS & PERFORMANCE ANALYSIS", level=1)
    
    add_styled_heading(doc, "5.1 Model Evaluation Metrics", level=2)
    doc.add_paragraph(
        "The trained Random Forest model exceeded all target performance specifications on the 25% holdout test set (90 samples):"
    )

    # Metrics Table
    tbl_m = doc.add_table(rows=5, cols=4)
    tbl_m.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Metric", "Target Specification", "Achieved Value", "Status"]
    vals = [
        ("Coefficient of Determination (R²)", "> 0.90 (min 0.93)", "0.9460", "PASSED"),
        ("Mean Absolute Error (MAE)", "< 2.0 units", "0.6852 units", "PASSED"),
        ("Root Mean Squared Error (RMSE)", "< 2.5 units", "0.8653 units", "PASSED"),
        ("Predictions within ±2 Units", "> 90.0%", "97.78%", "PASSED"),
    ]
    for c_idx, h in enumerate(headers):
        cell = tbl_m.cell(0, c_idx)
        cell.text = h
        cell.paragraphs[0].runs[0].font.bold = True
        set_cell_margins(cell)

    for r_idx, row in enumerate(vals, start=1):
        for c_idx, v in enumerate(row):
            cell = tbl_m.cell(r_idx, c_idx)
            cell.text = v
            set_cell_margins(cell)

    fi_img = os.path.join(DIAGRAMS_DIR, "feature_importance.png")
    if os.path.exists(fi_img):
        doc.add_paragraph().paragraph_format.space_before = Pt(10)
        doc.add_picture(fi_img, width=Inches(5.5))
        p_fi = doc.add_paragraph("Figure 5.1: Random Forest Feature Importance Rankings")
        p_fi.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_fi.runs[0].font.size = Pt(9.5)
        p_fi.runs[0].font.italic = True

    add_styled_heading(doc, "5.2 Test Case Verification Matrix (TC01 – TC10)", level=2)
    tbl_tc = doc.add_table(rows=11, cols=4)
    tbl_tc.alignment = WD_TABLE_ALIGNMENT.CENTER
    tc_headers = ["Test ID", "Description", "Pass Criteria", "Status"]
    for c_idx, h in enumerate(tc_headers):
        cell = tbl_tc.cell(0, c_idx)
        cell.text = h
        cell.paragraphs[0].runs[0].font.bold = True
        set_cell_margins(cell)

    tc_data = [
        ("TC01", "DHT11 Temperature Accuracy", "±2°C vs reference", "Verified Procedure"),
        ("TC02", "HC-SR04 Distance Measurement", "±1cm at 5, 15, 25cm", "Verified Procedure"),
        ("TC03", "RFID Card Recognition", "100% UID match rate (<1s)", "PASSED"),
        ("TC04", "LDR Light Level Detection", "Dark/Med/Bright classified", "PASSED"),
        ("TC05", "Gas Sensor Alert", "Alarm triggered at >2000 ADC", "PASSED"),
        ("TC06", "LCD Display Rotation", "4 screens rotate every 3s", "PASSED"),
        ("TC07", "Demand Prediction Accuracy", "Error within ±2 units (R²>0.90)", "PASSED (R²=0.946)"),
        ("TC08", "Stock Alert & Restock Logic", "Alert when stock < RP", "PASSED (100%)"),
        ("TC09", "Wi-Fi REST API Telemetry", "HTTP 200, latency < 500ms", "PASSED (70ms)"),
        ("TC10", "End-to-End Workflow Loop", "Telemetry -> ML -> Alert -> UI", "PASSED"),
    ]
    for r_idx, row in enumerate(tc_data, start=1):
        for c_idx, v in enumerate(row):
            cell = tbl_tc.cell(r_idx, c_idx)
            cell.text = v
            set_cell_margins(cell)

    doc.add_page_break()

    # ========================== CHAPTER 6: CONCLUSION =======================
    add_styled_heading(doc, "CHAPTER 6: CONCLUSION & FUTURE SCOPE", level=1)
    doc.add_paragraph(
        "6.1 Summary of Achievements:\n"
        "The Autonomous Smart Warehouse Monitoring System successfully demonstrates a unified IoT and machine learning solution. "
        "All eight sensors and peripheral components were interfaced without pin conflicts or over-voltage hazards. "
        "The machine learning model achieved an R² score of 0.946 and MAE of 0.69 units, delivering automated dynamic replenishment "
        "recommendations to the web dashboard and LCD display."
    )
    doc.add_paragraph(
        "6.2 Limitations Encountered:\n"
        "The model was evaluated using synthetic training samples structured around realistic supply chain seasonality. "
        "Additionally, ultrasonic distance sensing captures localized bin depth rather than volumetric point-cloud scans."
    )
    doc.add_paragraph(
        "6.3 Future Work:\n"
        "Future enhancements include cloud migration (AWS IoT Core / MQTT), multi-depth LiDAR sensing, "
        "recurrent neural network time-series forecasting (LSTM), and direct integration with automated guided vehicles (AGVs)."
    )

    doc.add_page_break()

    # ========================== CHAPTER 7: REFERENCES =======================
    add_styled_heading(doc, "CHAPTER 7: REFERENCES & APPENDICES", level=1)
    
    add_styled_heading(doc, "7.1 References", level=2)
    refs = [
        "Breiman, L. (2001). 'Random Forests.' Machine Learning, 45(1), 5–32.",
        "Carbonneau, R., Laframboise, K., & Vahidov, R. (2008). 'Application of machine learning techniques for supply chain demand forecasting.' European Journal of Operational Research, 184(3), 1140–1154.",
        "Espressif Systems. (2024). 'ESP32 Series Datasheet, Version 4.3.' Espressif Systems Co., Ltd.",
        "Gubbi, J., Buyya, R., Marusic, S., & Palaniswami, M. (2013). 'Internet of Things (IoT): A vision, architectural elements, and future directions.' Future Generation Computer Systems, 29(7), 1645–1660.",
        "Shi, W., Cao, J., Zhang, Q., Li, Y., & Xu, L. (2016). 'Edge Computing: Vision and Challenges.' IEEE Internet of Things Journal, 3(5), 637–646.",
        "Want, R. (2006). 'An introduction to RFID technology.' IEEE Pervasive Computing, 5(1), 25–33."
    ]
    for r in refs:
        doc.add_paragraph(r, style='List Bullet')

    add_styled_heading(doc, "7.2 Appendix A: Bill of Materials (BOM)", level=2)
    doc.add_paragraph("Total Hardware Budget: ₹1,640. Key parts: ESP32 DevKit V1 (₹450), HC-SR04 (₹85), DHT11 (₹110), RC522 (₹165), MQ-2 (₹140), LDR (₹10), I2C LCD (₹220), Buzzer/LED/Buttons/Passives (₹460).")

    add_styled_heading(doc, "7.3 Appendix B: Hardware Pin Assignment Matrix", level=2)
    doc.add_paragraph(
        "GPIO 32: HC-SR04 TRIG | GPIO 33: HC-SR04 ECHO (10k/20k divider)\n"
        "GPIO 15: DHT11 DATA | GPIO 5: RC522 SS | GPIO 4: RC522 RST | GPIO 18: SCK | GPIO 23: MOSI | GPIO 19: MISO\n"
        "GPIO 34: MQ-2 AO (ADC1) | GPIO 35: MQ-2 DO | GPIO 36: LDR (ADC1)\n"
        "GPIO 21: LCD SDA | GPIO 22: LCD SCL | GPIO 26: Red LED | GPIO 13: Piezo Buzzer\n"
        "GPIO 12: Order Button | GPIO 14: Emergency Button | 5V / 3.3V / GND Rails"
    )

    doc.save(OUTPUT_DOCX)
    print("Report compiled successfully:", OUTPUT_DOCX)


if __name__ == "__main__":
    main()
