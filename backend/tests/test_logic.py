"""
test_logic.py
-------------
Unit tests for business logic:
- Restock recommendation formula: max(reorder_point, ceil(pred_demand * 1.25 - stock))
- Distance to occupancy conversion
- Alert threshold triggers
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import restock_recommendation, distance_to_occupancy, evaluate_alerts


def test_restock_formula():
    # Case 1: stock (10) < pred_demand (12) * 1.25 (15) -> diff = 5, reorder_point = 8 -> max(8, 5) = 8
    assert restock_recommendation(12, 10, 8) == 8

    # Case 2: high demand (16) * 1.25 = 20, stock = 2 -> diff = 18, reorder_point = 10 -> max(10, 18) = 18
    assert restock_recommendation(16, 2, 10) == 18

    # Case 3: high stock (40), demand 8 * 1.25 = 10 -> diff = -30, reorder_point = 8 -> max(8, -30) = 8
    assert restock_recommendation(8, 40, 8) == 8

    # Case 4: zero stock, demand 10 * 1.25 = 12.5 -> ceil = 13, reorder_point = 5 -> max(5, 13) = 13
    assert restock_recommendation(10, 0, 5) == 13


def test_distance_to_occupancy():
    # 0 cm distance -> bin completely full -> 100% occupancy
    assert distance_to_occupancy(0) == 100.0

    # 60 cm distance -> bin empty -> 0% occupancy
    assert distance_to_occupancy(60) == 0.0

    # 30 cm distance -> half empty -> 50% occupancy
    assert distance_to_occupancy(30) == 50.0

    # >60 cm distance clamped to 0%
    assert distance_to_occupancy(75) == 0.0

    # None distance defaults to 40.0%
    assert distance_to_occupancy(None) == 40.0
