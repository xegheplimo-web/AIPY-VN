import math


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two GPS coordinates in meters."""
    R = 6371e3
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def calculate_shipping_fee(distance_km: float, weight_grams: float = 0, order_value: float = 0, delivery_method: str = "standard") -> dict:
    """Calculate shipping fee based on distance, weight, order value."""
    if distance_km <= 2:
        base_fee = 15000
    elif distance_km <= 5:
        base_fee = 25000
    elif distance_km <= 10:
        base_fee = 40000
    else:
        base_fee = 40000 + math.ceil((distance_km - 10) / 2) * 10000

    weight_fee = 0
    if weight_grams > 1000:
        extra_kg = math.ceil((weight_grams - 1000) / 1000)
        weight_fee = extra_kg * 5000

    method_multiplier = 1
    if delivery_method == "express":
        method_multiplier = 1.5
    elif delivery_method == "instant":
        method_multiplier = 2.0

    discount = 0
    if order_value >= 500000:
        discount = 10000
    elif order_value >= 300000:
        discount = 5000

    total = (base_fee + weight_fee) * method_multiplier - discount
    if order_value >= 1000000:
        total = 0

    return {
        "base_fee": round(base_fee * method_multiplier),
        "weight_fee": round(weight_fee * method_multiplier),
        "discount": round(discount),
        "total": max(0, round(total)),
        "is_free": total <= 0,
    }
