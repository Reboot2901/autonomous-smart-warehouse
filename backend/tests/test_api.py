"""
test_api.py
-----------
API endpoint integration tests using Flask test client:
- POST /api/predict
- GET  /api/status
- POST /api/log
- GET  /api/history
- GET  /api/inventory
- GET  /api/forecast
"""

import sys
import os
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app as flask_app
import storage


@pytest.fixture(scope="module")
def client():
    # Setup test in-memory or temp db
    test_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_warehouse.db")
    storage.DB_PATH = test_db
    try:
        if os.path.exists(test_db):
            os.remove(test_db)
    except Exception:
        pass
    storage.init_db()
    flask_app.load_model()
    flask_app.app.config["TESTING"] = True

    with flask_app.app.test_client() as client:
        yield client

    try:
        if os.path.exists(test_db):
            os.remove(test_db)
    except Exception:
        pass


def test_status_endpoint(client):
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "online"
    assert data["model_loaded"] is True
    assert "model_metrics" in data
    assert data["model_metrics"]["r2"] >= 0.90


def test_predict_endpoint_success(client):
    payload = {
        "orders": 2,
        "avg_temp_c": 25.4,
        "occupancy_pct": 38.5,
        "ambient_light_adc": 2400.0,
        "promo_flag": 0,
        "day_of_week": 1,
        "stock_on_hand": 30,
        "reorder_point": 8,
        "product_id": "P001"
    }
    res = client.post("/api/predict", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert "predicted_demand" in data
    assert 0 <= data["predicted_demand"] <= 20
    assert "restock_recommendation" in data
    assert "timestamp" in data


def test_predict_endpoint_validation_missing_field(client):
    payload = {
        "orders": 2,
        "avg_temp_c": 25.4
        # missing rest of fields
    }
    res = client.post("/api/predict", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 400
    data = res.get_json()
    assert data["status"] == "error"
    assert "Missing fields" in data["message"]


def test_log_and_history_endpoint(client):
    payload = {
        "device_id": "esp32-test",
        "distance": 28.5,
        "temperature": 24.8,
        "humidity": 55.0,
        "mqAnalog": 800,
        "gasAlert": 0,
        "lightAdc": 2500,
        "lightPercent": 61,
        "cardUID": "A1 B2 C3 D4",
        "productId": "P001",
        "stockLevel": 39,
        "event": "ORDER"
    }
    res = client.post("/api/log", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "logged"
    assert data["total_logs"] >= 1
    assert "inventory" in data

    # Check history
    h_res = client.get("/api/history?limit=10")
    assert h_res.status_code == 200
    h_data = h_res.get_json()
    assert h_data["count"] >= 1
    assert h_data["data"][-1]["temperature"] == 24.8
    assert h_data["data"][-1]["event"] == "ORDER"
