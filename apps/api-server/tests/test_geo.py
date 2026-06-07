from src.services.geo import haversine_distance, calculate_shipping_fee


def test_haversine_distance_same_point():
    dist = haversine_distance(10.7743, 106.7009, 10.7743, 106.7009)
    assert dist == pytest.approx(0, abs=1)


def test_haversine_distance_known():
    dist = haversine_distance(10.7743, 106.7009, 10.7751, 106.7002)
    assert dist > 0
    assert dist < 1000


def test_shipping_fee_free():
    fee = calculate_shipping_fee(1, 0, 1000000, "standard")
    assert fee["is_free"] is True
    assert fee["total"] == 0


def test_shipping_fee_standard():
    fee = calculate_shipping_fee(3, 500, 100000, "standard")
    assert fee["base_fee"] == 25000
    assert fee["total"] > 0
    assert fee["is_free"] is False


def test_shipping_fee_express():
    fee = calculate_shipping_fee(3, 0, 100000, "express")
    assert fee["base_fee"] == 37500


import pytest
