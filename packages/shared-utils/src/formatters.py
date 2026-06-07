from datetime import datetime


def format_price(price: float, currency: str = "đ") -> str:
    """Format price in Vietnamese format."""
    if price is None:
        return f"0 {currency}"
    return f"{price:,.0f} {currency}".replace(",", ".")


def format_distance(meters: float) -> str:
    """Format distance in human-readable format."""
    if meters is None:
        return ""
    if meters < 1000:
        return f"{meters:.0f}m"
    return f"{meters / 1000:.1f}km"


def format_datetime(dt_str: str) -> str:
    """Format ISO datetime to Vietnamese format."""
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y %H:%M")
    except (ValueError, TypeError):
        return dt_str or ""
