"""
storage.py
----------
SQLite persistence layer for sensor logs, alerts, predictions and inventory.
"""

import json
import os
import sqlite3
import threading
from datetime import date, datetime, timedelta, timezone

DB_PATH = os.environ.get(
    "WAREHOUSE_DB", os.path.join(os.path.dirname(__file__), "data", "warehouse.db")
)

_lock = threading.Lock()

# Default product master (P001-P003 from the specification)
DEFAULT_PRODUCTS = [
    # id, name, rfid_uid, stock, reorder_point, expiry offset (days from today)
    ("P001", "Rice",  "A1 B2 C3 D4", 40, 8, 180),
    ("P002", "Milk",  "11 22 33 44", 18, 12, 4),
    ("P003", "Beans", "DE AD BE EF", 25, 5, 90),
]


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _lock, _connect() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS sensor_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                device_id TEXT,
                distance_cm REAL, temperature REAL, humidity REAL,
                mq_analog INTEGER, gas_alert INTEGER,
                light_pct INTEGER, light_adc INTEGER,
                stock_level INTEGER, product_id TEXT, card_uid TEXT,
                event TEXT, raw TEXT
            );
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL, level TEXT, type TEXT, message TEXT
            );
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL, product_id TEXT,
                predicted_demand INTEGER, restock_recommendation INTEGER,
                features TEXT
            );
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY, name TEXT, rfid_uid TEXT,
                stock INTEGER, reorder_point INTEGER, expiry_date TEXT,
                updated_at TEXT
            );
            """
        )
        if c.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
            today = date.today()
            c.executemany(
                "INSERT INTO products VALUES (?,?,?,?,?,?,?)",
                [
                    (pid, name, uid, stock, rp,
                     (today + timedelta(days=exp)).isoformat(), now_iso())
                    for pid, name, uid, stock, rp, exp in DEFAULT_PRODUCTS
                ],
            )


# ---------------------------------------------------------------- sensor logs
def insert_log(d: dict) -> int:
    with _lock, _connect() as c:
        c.execute(
            """INSERT INTO sensor_logs
               (ts, device_id, distance_cm, temperature, humidity, mq_analog,
                gas_alert, light_pct, light_adc, stock_level, product_id,
                card_uid, event, raw)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                d.get("timestamp") or now_iso(), d.get("device_id", "esp32-01"),
                d.get("distance"), d.get("temperature"), d.get("humidity"),
                d.get("mqAnalog"), int(bool(d.get("gasAlert", 0))),
                d.get("lightPercent"), d.get("lightAdc"),
                d.get("stockLevel"), d.get("productId"), d.get("cardUID"),
                d.get("event"), json.dumps(d),
            ),
        )
        return c.execute("SELECT COUNT(*) FROM sensor_logs").fetchone()[0]


def count_logs() -> int:
    with _connect() as c:
        return c.execute("SELECT COUNT(*) FROM sensor_logs").fetchone()[0]


def get_history(limit: int = 100):
    with _connect() as c:
        rows = c.execute(
            "SELECT * FROM sensor_logs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    out = [dict(r) for r in rows][::-1]  # chronological order
    for r in out:
        r.pop("raw", None)
    return out


def latest_log():
    h = get_history(1)
    return h[0] if h else None


def get_events(limit: int = 20):
    with _connect() as c:
        rows = c.execute(
            """SELECT ts, event, product_id, card_uid, stock_level FROM sensor_logs
               WHERE event IS NOT NULL AND event != '' ORDER BY id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


# --------------------------------------------------------------------- alerts
def insert_alert(level: str, type_: str, message: str):
    with _lock, _connect() as c:
        # De-duplicate: skip identical alert type raised in the last 30 s
        last = c.execute(
            "SELECT ts FROM alerts WHERE type=? ORDER BY id DESC LIMIT 1", (type_,)
        ).fetchone()
        if last:
            try:
                age = datetime.now(timezone.utc) - datetime.fromisoformat(last["ts"])
                if age.total_seconds() < 30:
                    return
            except ValueError:
                pass
        c.execute(
            "INSERT INTO alerts (ts, level, type, message) VALUES (?,?,?,?)",
            (now_iso(), level, type_, message),
        )


def get_alerts(limit: int = 50):
    with _connect() as c:
        rows = c.execute(
            "SELECT * FROM alerts ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def count_recent_alerts(minutes: int = 10) -> int:
    since = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat(timespec="seconds")
    with _connect() as c:
        return c.execute("SELECT COUNT(*) FROM alerts WHERE ts >= ?", (since,)).fetchone()[0]


# ---------------------------------------------------------------- predictions
def insert_prediction(product_id, demand, restock, features):
    with _lock, _connect() as c:
        c.execute(
            """INSERT INTO predictions (ts, product_id, predicted_demand,
               restock_recommendation, features) VALUES (?,?,?,?,?)""",
            (now_iso(), product_id, demand, restock, json.dumps(features)),
        )


def get_predictions(limit: int = 50):
    with _connect() as c:
        rows = c.execute(
            "SELECT * FROM predictions ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    out = [dict(r) for r in rows][::-1]
    for r in out:
        r["features"] = json.loads(r["features"] or "{}")
    return out


# ------------------------------------------------------------------ inventory
def get_products():
    with _connect() as c:
        rows = c.execute("SELECT * FROM products ORDER BY id").fetchall()
    return [dict(r) for r in rows]


def get_product(pid):
    with _connect() as c:
        r = c.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    return dict(r) if r else None


def find_product_by_uid(uid):
    with _connect() as c:
        r = c.execute(
            "SELECT * FROM products WHERE UPPER(rfid_uid)=UPPER(?)", (uid.strip(),)
        ).fetchone()
    return dict(r) if r else None


def update_product(pid, **fields):
    allowed = {"stock", "reorder_point", "expiry_date", "name", "rfid_uid"}
    fields = {k: v for k, v in fields.items() if k in allowed}
    if not fields:
        return get_product(pid)
    sets = ", ".join(f"{k}=?" for k in fields) + ", updated_at=?"
    with _lock, _connect() as c:
        c.execute(
            f"UPDATE products SET {sets} WHERE id=?",
            (*fields.values(), now_iso(), pid),
        )
    return get_product(pid)
