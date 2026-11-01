"""
app.py
------
Flask REST API for the Autonomous Smart Warehouse Monitoring System.

Spec endpoints:
    POST /api/predict           -> demand prediction + restock recommendation
    GET  /api/status            -> system status + model metrics
    POST /api/log               -> store ESP32 sensor data
    GET  /api/history?limit=N   -> last N sensor records

Dashboard endpoints (bonus):
    GET  /                      -> web dashboard
    GET  /api/alerts            -> alert log
    GET  /api/events            -> RFID / button events
    GET  /api/inventory         -> product stock, reorder point, expiry
    POST /api/inventory/<id>    -> update stock / reorder point / expiry
    GET  /api/forecast          -> model forecast for every product, from live data
    GET  /api/predictions       -> prediction history (trend chart)

Run:  python app.py      (listens on 0.0.0.0:5000 so the ESP32 can reach it)
"""

import json
import math
import os
import time
from datetime import date, datetime, timezone

import joblib
import numpy as np
from flask import Flask, jsonify, request, send_from_directory

import storage

BASE = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_DIR = os.path.join(BASE, "..", "dashboard")
MODEL_PATH = os.path.join(BASE, "model", "demand_model.joblib")
METRICS_PATH = os.path.join(BASE, "model", "metrics.json")

FEATURES = [
    "orders", "avg_temp_c", "occupancy_pct", "ambient_light_adc",
    "promo_flag", "day_of_week", "stock_on_hand", "reorder_point",
]

# Alert thresholds (keep in sync with firmware config.h)
DISTANCE_ALERT_CM = 15
GAS_THRESHOLD_ADC = 2000
TEMP_HIGH_C = 30
HUMIDITY_HIGH_PCT = 80
EXPIRY_WARN_DAYS = 3
BIN_DEPTH_CM = 60          # empty-bin distance used to convert distance -> occupancy

app = Flask(__name__, static_folder=None)
START_TIME = time.time()

model = None
metrics = {}


def load_model():
    global model, metrics
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
        model.n_jobs = 1   # single-row inference: avoid thread-pool overhead
    if os.path.exists(METRICS_PATH):
        with open(METRICS_PATH) as f:
            metrics = json.load(f)


# ------------------------------------------------------------------ helpers
@app.after_request
def add_cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resp


def error(msg, code=400):
    return jsonify({"status": "error", "message": msg}), code


def restock_recommendation(pred_demand, stock, reorder_point):
    """Spec formula: max(reorder_point, pred_demand x 1.25 - stock)."""
    return int(max(reorder_point, math.ceil(pred_demand * 1.25 - stock)))


def run_prediction(features: dict):
    x = np.array([[float(features[f]) for f in FEATURES]])
    pred = int(np.clip(round(float(model.predict(x)[0])), 0, 20))
    restock = restock_recommendation(
        pred, float(features["stock_on_hand"]), float(features["reorder_point"])
    )
    return pred, restock


def distance_to_occupancy(distance_cm):
    if distance_cm is None:
        return 40.0
    return float(np.clip((1 - distance_cm / BIN_DEPTH_CM) * 100, 0, 100))


def days_to_expiry(expiry_iso):
    try:
        return (date.fromisoformat(expiry_iso) - date.today()).days
    except (TypeError, ValueError):
        return None


def evaluate_alerts(d: dict):
    """Raise alerts from an incoming sensor payload."""
    dist = d.get("distance")
    if dist is not None and 0 < dist < DISTANCE_ALERT_CM:
        storage.insert_alert("warning", "distance",
                             f"Bin nearly full / obstruction: {dist:.0f} cm (<{DISTANCE_ALERT_CM} cm)")
    mq = d.get("mqAnalog")
    if d.get("gasAlert") or (mq is not None and mq > GAS_THRESHOLD_ADC):
        storage.insert_alert("critical", "gas", f"Gas level high: ADC {mq}")
    t = d.get("temperature")
    if t is not None and t > TEMP_HIGH_C:
        storage.insert_alert("warning", "temperature", f"High temperature: {t:.1f} °C")
    h = d.get("humidity")
    if h is not None and h > HUMIDITY_HIGH_PCT:
        storage.insert_alert("warning", "humidity", f"High humidity: {h:.0f} %")
    if str(d.get("event", "")).upper() == "EMERGENCY":
        storage.insert_alert("critical", "emergency", "Emergency button pressed!")


def check_stock_alert(product):
    if product and product["stock"] < product["reorder_point"]:
        storage.insert_alert(
            "warning", f"stock_{product['id']}",
            f"{product['name']} stock low: {product['stock']} < reorder point {product['reorder_point']}",
        )


# --------------------------------------------------------------- dashboard
@app.route("/")
def dashboard():
    return send_from_directory(DASHBOARD_DIR, "index.html")


@app.route("/dashboard/<path:filename>")
def dashboard_static(filename):
    return send_from_directory(DASHBOARD_DIR, filename)


# ------------------------------------------------------------ spec endpoints
@app.route("/api/predict", methods=["POST", "OPTIONS"])
def predict():
    if request.method == "OPTIONS":
        return "", 204
    if model is None:
        return error("Model not loaded. Run train_model.py first.", 503)
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error("Expected a JSON object body.")
    missing = [f for f in FEATURES if f not in data]
    if missing:
        return error(f"Missing fields: {', '.join(missing)}")
    try:
        features = {f: float(data[f]) for f in FEATURES}
    except (TypeError, ValueError):
        return error("All feature values must be numeric.")
    if not 0 <= features["day_of_week"] <= 6:
        return error("day_of_week must be 0-6 (0=Monday).")
    if features["promo_flag"] not in (0, 1):
        return error("promo_flag must be 0 or 1.")

    pred, restock = run_prediction(features)
    storage.insert_prediction(data.get("product_id"), pred, restock, features)
    return jsonify({
        "status": "success",
        "predicted_demand": pred,
        "timestamp": storage.now_iso(),
        "restock_recommendation": restock,
    })


@app.route("/api/status")
def status():
    latest = storage.latest_log()
    return jsonify({
        "status": "online",
        "model_loaded": model is not None,
        "model_metrics": {k: metrics.get(k) for k in ("r2", "mae", "rmse", "within_2_units_pct", "trained_at")},
        "uptime_seconds": int(time.time() - START_TIME),
        "total_logs": storage.count_logs(),
        "last_device_contact": latest["ts"] if latest else None,
        "active_alerts_10min": storage.count_recent_alerts(10),
        "server_time": storage.now_iso(),
    })


@app.route("/api/log", methods=["POST", "OPTIONS"])
def log_data():
    if request.method == "OPTIONS":
        return "", 204
    d = request.get_json(silent=True)
    if not isinstance(d, dict):
        return error("Expected a JSON object body.")

    # Resolve product from RFID UID if productId not given
    product = None
    if d.get("productId"):
        product = storage.get_product(d["productId"])
    elif d.get("cardUID"):
        product = storage.find_product_by_uid(d["cardUID"])
        if product:
            d["productId"] = product["id"]

    if product and d.get("stockLevel") is not None:
        product = storage.update_product(product["id"], stock=int(d["stockLevel"]))

    total = storage.insert_log(d)
    evaluate_alerts(d)
    check_stock_alert(product)
    inventory_sync = [
        {"id": p["id"], "stock": p["stock"], "reorder_point": p["reorder_point"]}
        for p in storage.get_products()
    ]
    return jsonify({"status": "logged", "total_logs": total,
                    "timestamp": storage.now_iso(), "inventory": inventory_sync})


@app.route("/api/history")
def history():
    try:
        limit = max(1, min(int(request.args.get("limit", 100)), 1000))
    except ValueError:
        return error("limit must be an integer")
    rows = storage.get_history(limit)
    return jsonify({"status": "success", "count": len(rows), "data": rows})


# ------------------------------------------------------- dashboard endpoints
@app.route("/api/alerts")
def alerts():
    limit = int(request.args.get("limit", 50))
    return jsonify({"status": "success", "data": storage.get_alerts(limit)})


@app.route("/api/events")
def events():
    limit = int(request.args.get("limit", 20))
    return jsonify({"status": "success", "data": storage.get_events(limit)})


@app.route("/api/inventory")
def inventory():
    products = storage.get_products()
    for p in products:
        p["days_to_expiry"] = days_to_expiry(p["expiry_date"])
        p["low_stock"] = p["stock"] < p["reorder_point"]
        if p["days_to_expiry"] is not None and p["days_to_expiry"] <= EXPIRY_WARN_DAYS:
            storage.insert_alert("warning", f"expiry_{p['id']}",
                                 f"{p['name']} expires in {p['days_to_expiry']} day(s)")
    return jsonify({"status": "success", "data": products})


@app.route("/api/inventory/<pid>", methods=["POST", "OPTIONS"])
def update_inventory(pid):
    if request.method == "OPTIONS":
        return "", 204
    if not storage.get_product(pid):
        return error("Unknown product", 404)
    d = request.get_json(silent=True) or {}
    p = storage.update_product(pid, **d)
    check_stock_alert(p)
    return jsonify({"status": "success", "data": p})


@app.route("/api/forecast")
def forecast():
    """Predict next-day demand for every product using live sensor context."""
    if model is None:
        return error("Model not loaded", 503)
    hist = storage.get_history(50)
    temps = [r["temperature"] for r in hist if r["temperature"] is not None]
    latest = hist[-1] if hist else {}
    promo = int(request.args.get("promo", 0))
    today = datetime.now().weekday()
    today_iso = date.today().isoformat()

    out = []
    for p in storage.get_products():
        orders_today = sum(
            1 for e in storage.get_events(200)
            if e["product_id"] == p["id"] and str(e["event"]).upper() == "ORDER"
            and str(e["ts"]).startswith(today_iso)
        )
        features = {
            "orders": min(orders_today, 5),
            "avg_temp_c": round(float(np.mean(temps)), 2) if temps else 25.0,
            "occupancy_pct": round(distance_to_occupancy(latest.get("distance_cm")), 1),
            "ambient_light_adc": float(latest.get("light_adc") or 2600),
            "promo_flag": promo,
            "day_of_week": today,
            "stock_on_hand": p["stock"],
            "reorder_point": p["reorder_point"],
        }
        pred, restock = run_prediction(features)
        out.append({
            "product_id": p["id"], "name": p["name"],
            "predicted_demand": pred, "restock_recommendation": restock,
            "stock_after_demand": p["stock"] - pred,
            "features": features,
        })
    return jsonify({"status": "success", "timestamp": storage.now_iso(), "data": out})


@app.route("/api/model")
def model_info():
    if not metrics:
        return error("Model metrics not found", 404)
    return jsonify(metrics)


@app.route("/api/predictions")
def predictions():
    limit = int(request.args.get("limit", 50))
    return jsonify({"status": "success", "data": storage.get_predictions(limit)})


# ---------------------------------------------------------------------- main
storage.init_db()
load_model()

if __name__ == "__main__":
    print(f"Model loaded: {model is not None}  |  Dashboard: http://localhost:5000/")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
