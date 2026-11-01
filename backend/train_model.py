"""
train_model.py
--------------
Trains the Random Forest demand model and saves it together with its metrics.

Spec parameters: n_estimators=250, max_depth=10, min_samples_split=5,
min_samples_leaf=2, 75/25 train/test split.
"""

import csv
import json
import os
from datetime import datetime, timezone

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

BASE = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE, "data", "warehouse_demand.csv")
MODEL_DIR = os.path.join(BASE, "model")
MODEL_PATH = os.path.join(MODEL_DIR, "demand_model.joblib")
METRICS_PATH = os.path.join(MODEL_DIR, "metrics.json")

FEATURES = [
    "orders", "avg_temp_c", "occupancy_pct", "ambient_light_adc",
    "promo_flag", "day_of_week", "stock_on_hand", "reorder_point",
]
TARGET = "next_day_demand"


def load_data():
    if not os.path.exists(DATA_PATH):
        import generate_dataset
        generate_dataset.main()
    with open(DATA_PATH) as f:
        rows = list(csv.DictReader(f))
    X = np.array([[float(r[c]) for c in FEATURES] for r in rows])
    y = np.array([float(r[TARGET]) for r in rows])
    return X, y


def main():
    X, y = load_data()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42
    )

    model = RandomForestRegressor(
        n_estimators=250,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    pred = model.predict(X_test)
    metrics = {
        "r2": round(float(r2_score(y_test, pred)), 4),
        "mae": round(float(mean_absolute_error(y_test, pred)), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(y_test, pred))), 4),
        "within_2_units_pct": round(float(np.mean(np.abs(pred - y_test) <= 2) * 100), 2),
        "n_train": int(len(y_train)),
        "n_test": int(len(y_test)),
        "features": FEATURES,
        "feature_importance": {
            f: round(float(i), 4) for f, i in zip(FEATURES, model.feature_importances_)
        },
        "params": {"n_estimators": 250, "max_depth": 10,
                   "min_samples_split": 5, "min_samples_leaf": 2},
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    print(json.dumps({k: metrics[k] for k in ("r2", "mae", "rmse", "within_2_units_pct")}, indent=2))
    if metrics["r2"] < 0.90:
        raise SystemExit("Model R2 below 0.90 target!")


if __name__ == "__main__":
    main()
