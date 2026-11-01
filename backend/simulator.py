"""
simulator.py
------------
Simulates the ESP32 so the dashboard can be demonstrated without hardware.
Sends the same JSON payload as the firmware's sendToBackend() every 5 s,
random RFID scans / orders, occasional gas & emergency events, and an
ML prediction request every 60 s (5 min on real hardware).

Usage:  python simulator.py [--url http://localhost:5000] [--interval 5]
"""

import argparse
import json
import math
import random
import time
import urllib.request
from datetime import datetime

PRODUCTS = {
    "P001": {"uid": "A1 B2 C3 D4", "stock": 40, "rp": 8},
    "P002": {"uid": "11 22 33 44", "stock": 18, "rp": 12},
    "P003": {"uid": "DE AD BE EF", "stock": 25, "rp": 5},
}


def post(url, payload):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())


def get(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return json.loads(r.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:5000")
    ap.add_argument("--interval", type=float, default=5.0)
    args = ap.parse_args()

    # sync stock with server inventory
    try:
        for p in get(f"{args.url}/api/inventory")["data"]:
            if p["id"] in PRODUCTS:
                PRODUCTS[p["id"]]["stock"] = p["stock"]
    except Exception as e:
        print("Could not read inventory:", e)

    t0 = time.time()
    last_pred = 0
    distance = 35.0
    print(f"Simulating ESP32 -> {args.url}  (Ctrl+C to stop)")

    while True:
        t = time.time() - t0
        distance = max(4, min(58, distance + random.uniform(-3, 3)))
        payload = {
            "device_id": "esp32-sim",
            "distance": round(distance, 1),
            "temperature": round(26 + 2.5 * math.sin(t / 120) + random.uniform(-0.4, 0.4), 1),
            "humidity": round(60 + 8 * math.sin(t / 200) + random.uniform(-1, 1), 0),
            "mqAnalog": int(900 + 150 * math.sin(t / 90) + random.uniform(-60, 60)),
            "gasAlert": 0,
            "lightAdc": int(2800 + 600 * math.sin(t / 150) + random.uniform(-80, 80)),
        }
        payload["lightPercent"] = int(payload["lightAdc"] / 4095 * 100)

        r = random.random()
        if r < 0.04:                                   # gas leak spike
            payload["mqAnalog"] = random.randint(2300, 3200)
            payload["gasAlert"] = 1
        elif r < 0.06:
            payload["event"] = "EMERGENCY"
        elif r < 0.30:                                 # RFID scan + order
            pid = random.choice(list(PRODUCTS))
            prod = PRODUCTS[pid]
            if prod["stock"] <= 2 or random.random() < 0.1:
                prod["stock"] += random.randint(20, 35)
                payload["event"] = "RESTOCK"
            else:
                prod["stock"] -= random.randint(1, 3)
                payload["event"] = "ORDER"
            payload.update({"cardUID": prod["uid"], "productId": pid,
                            "stockLevel": prod["stock"]})

        try:
            res = post(f"{args.url}/api/log", payload)
            print(f"[{datetime.now():%H:%M:%S}] logged #{res['total_logs']}  "
                  f"T={payload['temperature']}  D={payload['distance']}  "
                  f"{payload.get('event', '')}")
        except Exception as e:
            print("POST /api/log failed:", e)

        if time.time() - last_pred > 60:
            last_pred = time.time()
            pid = random.choice(list(PRODUCTS))
            prod = PRODUCTS[pid]
            feat = {
                "product_id": pid,
                "orders": random.randint(0, 5),
                "avg_temp_c": payload["temperature"],
                "occupancy_pct": round(max(0, (1 - distance / 60) * 100), 1),
                "ambient_light_adc": payload["lightAdc"],
                "promo_flag": int(random.random() < 0.15),
                "day_of_week": datetime.now().weekday(),
                "stock_on_hand": prod["stock"],
                "reorder_point": prod["rp"],
            }
            try:
                res = post(f"{args.url}/api/predict", feat)
                print(f"   prediction {pid}: demand={res['predicted_demand']} "
                      f"restock={res['restock_recommendation']}")
            except Exception as e:
                print("POST /api/predict failed:", e)

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
