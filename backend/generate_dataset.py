"""
generate_dataset.py
-------------------
Generates the synthetic training dataset for the Smart Warehouse demand model.

120 days x 3 products = 360 samples.

Features (exactly as in the project specification):
    orders, avg_temp_c, occupancy_pct, ambient_light_adc, promo_flag,
    day_of_week, stock_on_hand, reorder_point
Target:
    next_day_demand (0-20 units)

Design notes
  * Seasonality is injected through temperature and occupancy (both are model
    features), so the model can actually learn the seasonal effect.
  * Each product has a fixed reorder_point, which implicitly tells the model
    which product a row belongs to (different base demand per product).
  * Milk is temperature-sensitive (demand rises on hot days).
  * Weekends and promotions boost demand.
"""

import csv
import math
import os

import numpy as np

SEED = 42
DAYS = 120
OUT_PATH = os.path.join(os.path.dirname(__file__), "data", "warehouse_demand.csv")

# product_id: (name, base_demand, temp_sensitivity, reorder_point, initial_stock)
PRODUCTS = {
    "P001": ("Rice", 10.0, 0.10, 8, 40),
    "P002": ("Milk", 13.0, 0.55, 12, 45),
    "P003": ("Beans", 6.5, 0.05, 5, 30),
}

FIELDS = [
    "day", "product_id", "product_name",
    "orders", "avg_temp_c", "occupancy_pct", "ambient_light_adc",
    "promo_flag", "day_of_week", "stock_on_hand", "reorder_point",
    "next_day_demand",
]


def generate(seed: int = SEED):
    rng = np.random.default_rng(seed)
    rows = []

    for pid, (name, base, temp_sens, reorder_point, stock) in PRODUCTS.items():
        for day in range(DAYS):
            dow = day % 7                                   # 0 = Monday
            season = math.sin(2 * math.pi * day / 60.0)     # ~2-month cycle

            avg_temp = float(np.clip(25 + 3.5 * season + rng.normal(0, 0.8), 20, 30))
            occupancy = float(np.clip(40 + 11 * season + rng.normal(0, 1.5), 25, 55))
            light_adc = float(np.clip(rng.normal(2600, 600), 0, 4095))
            promo = int(rng.random() < 0.15)
            orders = int(rng.integers(0, 6))                # 0-5

            demand = (
                base
                + temp_sens * (avg_temp - 25)               # temperature effect
                + 0.12 * (occupancy - 40)                   # busy warehouse -> more flow
                + 4.0 * promo                               # promotion boost
                + (2.5 if dow >= 5 else 0.0)                # weekend boost
                + 0.7 * orders                              # momentum from yesterday
                + rng.normal(0, 0.5)                        # noise
            )
            demand = int(np.clip(round(demand), 0, 20))

            rows.append({
                "day": day, "product_id": pid, "product_name": name,
                "orders": orders, "avg_temp_c": round(avg_temp, 2),
                "occupancy_pct": round(occupancy, 2),
                "ambient_light_adc": round(light_adc, 0),
                "promo_flag": promo, "day_of_week": dow,
                "stock_on_hand": stock, "reorder_point": reorder_point,
                "next_day_demand": demand,
            })

            # simple inventory dynamics: consume, restock when low
            stock = max(0, stock - demand)
            if stock < reorder_point:
                stock += int(rng.integers(30, 50))

    return rows


def main():
    rows = generate()
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} samples -> {OUT_PATH}")


if __name__ == "__main__":
    main()
