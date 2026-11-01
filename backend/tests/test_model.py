"""
test_model.py
-------------
Validates the trained machine learning model against the specification targets:
- R2 score > 0.90
- MAE < 2.0 units
- RMSE < 2.5 units
- 8 specified features
"""

import json
import os
import joblib
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "model", "demand_model.joblib")
METRICS_PATH = os.path.join(BASE_DIR, "model", "metrics.json")

EXPECTED_FEATURES = [
    "orders", "avg_temp_c", "occupancy_pct", "ambient_light_adc",
    "promo_flag", "day_of_week", "stock_on_hand", "reorder_point",
]


def test_model_files_exist():
    assert os.path.exists(MODEL_PATH), f"Model file missing at {MODEL_PATH}"
    assert os.path.exists(METRICS_PATH), f"Metrics file missing at {METRICS_PATH}"


def test_model_performance_targets():
    with open(METRICS_PATH, "r") as f:
        metrics = json.load(f)

    assert metrics["r2"] >= 0.90, f"R2 score {metrics['r2']} is below minimum target of 0.90"
    assert metrics["mae"] <= 2.0, f"MAE {metrics['mae']} exceeds maximum allowed 2.0 units"
    assert metrics["rmse"] <= 2.5, f"RMSE {metrics['rmse']} exceeds maximum allowed 2.5 units"
    assert metrics["within_2_units_pct"] >= 90.0, "Expected >=90% of predictions within +-2 units"


def test_model_inference():
    model = joblib.load(MODEL_PATH)
    # Sample feature vector: [orders, avg_temp_c, occupancy_pct, ambient_light_adc, promo_flag, day_of_week, stock_on_hand, reorder_point]
    sample_input = np.array([[2, 26.5, 42.0, 2750.0, 0, 3, 25, 8]])
    pred = model.predict(sample_input)[0]
    assert 0 <= pred <= 20, f"Predicted demand {pred} out of expected range [0, 20]"
