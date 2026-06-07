import re


def validate_phone(phone: str) -> bool:
    """Validate Vietnamese phone number."""
    if not phone:
        return False
    pattern = r"^(0|\+84)[35789]\d{8}$"
    return bool(re.match(pattern, phone.replace(" ", "")))


def validate_email(email: str) -> bool:
    """Validate email address."""
    if not email:
        return False
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_location(lat: float, lng: float) -> dict:
    """Validate GPS coordinates."""
    if not (-90 <= lat <= 90):
        return {"valid": False, "message": "Latitude must be between -90 and 90"}
    if not (-180 <= lng <= 180):
        return {"valid": False, "message": "Longitude must be between -180 and 180"}
    return {"valid": True, "message": "Location is valid"}
