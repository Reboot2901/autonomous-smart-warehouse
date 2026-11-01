"""
generate_diagrams.py
---------------------
Generates high-resolution architecture diagrams, hardware block diagrams,
and model performance evaluation charts for the project report and slides.
"""

import os
import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUTPUT_DIR, exist_ok=True)


def plot_system_architecture():
    fig, ax = plt.subplots(figsize=(12, 6.5), dpi=300)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6.5)
    ax.axis("off")
    fig.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#0f172a")

    # Titles
    ax.text(6, 6.1, "Autonomous Smart Warehouse Monitoring System Architecture",
            ha="center", va="center", color="#f8fafc", fontsize=15, fontweight="bold")
    ax.text(6, 5.7, "Edge IoT Telemetry · RESTful Microservice · Scikit-Learn Predictive Intelligence",
            ha="center", va="center", color="#94a3b8", fontsize=10)

    # Box styling helper
    def draw_box(x, y, w, h, title, subtitle, color, border_color):
        box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                                     facecolor=color, edgecolor=border_color, linewidth=1.5)
        ax.add_patch(box)
        ax.text(x + w/2, y + h*0.65, title, ha="center", va="center",
                color="#ffffff", fontsize=11, fontweight="bold")
        ax.text(x + w/2, y + h*0.35, subtitle, ha="center", va="center",
                color="#cbd5e1", fontsize=8.5, multialignment="center")

    # Layer 1: Hardware Layer
    draw_box(0.5, 3.2, 2.8, 1.8, "Perception Layer\n(Sensors & Inputs)",
             "HC-SR04 · DHT11 · MQ-2\nRC522 RFID · LDR\nButtons (Order/Emerg)", "#1e293b", "#38bdf8")

    # Layer 2: Edge Controller
    draw_box(4.0, 3.2, 2.5, 1.8, "Edge Processing\n(ESP32 DevKit V1)",
             "Dual-Core Xtensa LX6\nFreeRTOS / Non-blocking Loop\nI2C LCD & Acoustic/LED Alert", "#1e293b", "#818cf8")

    # Arrow 1 -> 2
    ax.annotate("", xy=(4.0, 4.1), xytext=(3.3, 4.1),
                arrowprops=dict(arrowstyle="->", color="#38bdf8", lw=2))
    ax.text(3.65, 4.3, "GPIO / SPI / I2C", ha="center", va="bottom", color="#94a3b8", fontsize=7.5)

    # Layer 3: Cloud / Backend Server
    draw_box(7.2, 3.2, 2.6, 1.8, "Application Backend\n(Flask REST API)",
             "Endpoints: /predict, /log\nSQLite Persistence Layer\nState & Inventory Sync", "#1e293b", "#4ade80")

    # Arrow 2 -> 3 (Wi-Fi)
    ax.annotate("", xy=(7.2, 4.1), xytext=(6.5, 4.1),
                arrowprops=dict(arrowstyle="->", color="#818cf8", lw=2))
    ax.text(6.85, 4.3, "Wi-Fi (HTTP/JSON)\n5s interval", ha="center", va="bottom", color="#94a3b8", fontsize=7.5)

    # Layer 4: Intelligence Engine
    draw_box(7.2, 0.7, 2.6, 1.7, "Predictive Engine\n(Random Forest)",
             "250 Trees · Depth 10\nNext-Day Demand & Restock\nR² = 0.946 · MAE = 0.69", "#1e293b", "#fbbf24")

    # Arrow 3 <-> 4
    ax.annotate("", xy=(8.5, 2.4), xytext=(8.5, 3.2),
                arrowprops=dict(arrowstyle="<->", color="#fbbf24", lw=2))
    ax.text(8.7, 2.8, "Joblib\nInference", ha="left", va="center", color="#fbbf24", fontsize=7.5)

    # Layer 5: Presentation Dashboard
    draw_box(10.3, 3.2, 1.5, 1.8, "Web Dashboard\n(Chart.js UI)",
             "Live Tile KPIs\nAlert Log\nForecast Trends", "#1e293b", "#f43f5e")

    # Arrow 3 -> 5
    ax.annotate("", xy=(10.3, 4.1), xytext=(9.8, 4.1),
                arrowprops=dict(arrowstyle="->", color="#4ade80", lw=2))
    ax.text(10.05, 4.3, "HTTP", ha="center", va="bottom", color="#94a3b8", fontsize=7.5)

    # Feedback loop: Model -> Prediction -> ESP32 LCD
    ax.annotate("", xy=(5.25, 3.2), xytext=(7.2, 1.55),
                arrowprops=dict(arrowstyle="->", color="#a78bfa", lw=1.5, connectionstyle="arc3,rad=0.2", ls="--"))
    ax.text(5.7, 1.8, "Predictions returned to ESP32 for LCD display", ha="center", color="#a78bfa", fontsize=8)

    plt.tight_layout()
    out_file = os.path.join(OUTPUT_DIR, "system_architecture.png")
    plt.savefig(out_file, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print("Saved:", out_file)


def plot_hardware_block_diagram():
    fig, ax = plt.subplots(figsize=(11, 7), dpi=300)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 7)
    ax.axis("off")
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")

    # Title
    ax.text(5.5, 6.6, "ESP32 DevKit V1 Hardware Interconnect & Block Diagram",
            ha="center", va="center", color="#0f172a", fontsize=14, fontweight="bold")

    # Central ESP32 Box
    mcu = patches.FancyBboxPatch((4.0, 1.5), 3.0, 4.2, boxstyle="round,pad=0.2",
                                facecolor="#e0e7ff", edgecolor="#4338ca", linewidth=2)
    ax.add_patch(mcu)
    ax.text(5.5, 5.3, "ESP32 DevKit V1", ha="center", va="center", color="#1e1b4b", fontsize=13, fontweight="bold")
    ax.text(5.5, 4.9, "Xtensa Dual-Core LX6 @ 240MHz", ha="center", va="center", color="#3730a3", fontsize=9)
    ax.text(5.5, 4.5, "520 KB SRAM · 4 MB Flash · 2.4 GHz Wi-Fi", ha="center", va="center", color="#4338ca", fontsize=8)

    # Sensor Inputs (Left side)
    inputs = [
        ("HC-SR04 Ultrasonic", "TRIG: GPIO 32\nECHO: GPIO 33 (10k/20k divider)", 5.2),
        ("DHT11 Temp & Humidity", "DATA: GPIO 15 (Single-Bus)", 4.1),
        ("RC522 RFID Reader", "SPI: SS=5, RST=4, SCK=18\nMOSI=23, MISO=19 (3.3V)", 3.0),
        ("MQ-2 Gas Sensor", "AO: GPIO 34 (ADC1)\nDO: GPIO 35 (Comparator)", 1.9),
        ("LDR Light Sensor", "Analog: GPIO 36 (ADC1)\nDivider: 3.3V-LDR-10k-GND", 0.8),
    ]

    for title, desc, y in inputs:
        b = patches.FancyBboxPatch((0.5, y - 0.4), 2.7, 0.8, boxstyle="round,pad=0.1",
                                   facecolor="#f0fdf4", edgecolor="#15803d", linewidth=1.2)
        ax.add_patch(b)
        ax.text(1.85, y + 0.1, title, ha="center", va="center", color="#14532d", fontsize=9, fontweight="bold")
        ax.text(1.85, y - 0.2, desc, ha="center", va="center", color="#166534", fontsize=7.5)
        # Arrow to MCU
        ax.annotate("", xy=(4.0, y), xytext=(3.2, y),
                    arrowprops=dict(arrowstyle="->", color="#15803d", lw=1.5))

    # Output Actuators & Inputs (Right side)
    outputs = [
        ("I2C 16×2 LCD Display", "SDA: GPIO 21, SCL: GPIO 22\nPCF8574 Backpack (5V)", 5.0),
        ("Red Stock Alert LED", "GPIO 26 via 180Ω Resistor\nActive High Current: ~7mA", 3.9),
        ("Piezo Acoustic Buzzer", "GPIO 13 (PWM / Tone)\nWarning chirps & Emergency siren", 2.8),
        ("Tactile Pushbuttons", "BTN1 (Order): GPIO 12\nBTN2 (Emergency): GPIO 14", 1.7),
        ("Power Delivery", "VIN: 5V (USB)\n3V3: Internal Regulator\nGND: Common Ground", 0.6),
    ]

    for title, desc, y in outputs:
        b = patches.FancyBboxPatch((7.8, y - 0.4), 2.7, 0.8, boxstyle="round,pad=0.1",
                                   facecolor="#fef2f2", edgecolor="#b91c1c", linewidth=1.2)
        ax.add_patch(b)
        ax.text(9.15, y + 0.1, title, ha="center", va="center", color="#7f1d1d", fontsize=9, fontweight="bold")
        ax.text(9.15, y - 0.2, desc, ha="center", va="center", color="#991b1b", fontsize=7.5)
        # Arrow from MCU
        if "Buttons" in title or "Power" in title:
            ax.annotate("", xy=(7.0, y), xytext=(7.8, y),
                        arrowprops=dict(arrowstyle="->", color="#b91c1c", lw=1.5))
        else:
            ax.annotate("", xy=(7.8, y), xytext=(7.0, y),
                        arrowprops=dict(arrowstyle="->", color="#b91c1c", lw=1.5))

    plt.tight_layout()
    out_file = os.path.join(OUTPUT_DIR, "hardware_block_diagram.png")
    plt.savefig(out_file, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print("Saved:", out_file)


def plot_model_results():
    metrics_path = os.path.join(OUTPUT_DIR, "..", "..", "backend", "model", "metrics.json")
    if not os.path.exists(metrics_path):
        return
    with open(metrics_path) as f:
        metrics = json.load(f)

    # Feature Importance Plot
    fi = metrics.get("feature_importance", {})
    sorted_fi = sorted(fi.items(), key=lambda x: x[1])
    features = [k for k, v in sorted_fi]
    importances = [v * 100 for k, v in sorted_fi]

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=300)
    bars = ax.barh(features, importances, color="#3b82f6", edgecolor="#1d4ed8", height=0.6)
    ax.set_xlabel("Relative Importance (%)", fontsize=10, fontweight="bold")
    ax.set_title("Random Forest Feature Importance (250 Trees, Depth 10)", fontsize=11, fontweight="bold")
    ax.grid(axis="x", linestyle="--", alpha=0.5)

    for bar in bars:
        w = bar.get_width()
        ax.text(w + 0.5, bar.get_y() + bar.get_height()/2, f"{w:.1f}%",
                va="center", ha="left", fontsize=8.5, color="#1e293b")

    ax.set_xlim(0, max(importances) + 8)
    plt.tight_layout()
    out_file = os.path.join(OUTPUT_DIR, "feature_importance.png")
    plt.savefig(out_file, bbox_inches="tight")
    plt.close()
    print("Saved:", out_file)


if __name__ == "__main__":
    plot_system_architecture()
    plot_hardware_block_diagram()
    plot_model_results()
