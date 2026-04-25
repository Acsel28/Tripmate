import pytest

from planner import calculate_total_cost, is_affordable, parse_dates


def test_cost_calculation():
    assert calculate_total_cost(1000, 2000, 500, 0.1) == 3850.0


def test_affordability_logic():
    assert is_affordable(4500, 5000) is True
    assert is_affordable(5200, 5000) is False


def test_invalid_dates():
    with pytest.raises(ValueError):
        parse_dates("2026-05-10", "2026-05-08")
