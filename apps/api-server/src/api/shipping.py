from fastapi import APIRouter
from pydantic import BaseModel, Field
from src.services.geo import calculate_shipping_fee

router = APIRouter(prefix="/api/shipping", tags=["Shipping"])


class ShippingCalculateRequest(BaseModel):
    distance_km: float = Field(..., ge=0)
    weight_grams: float = Field(default=0, ge=0)
    order_value: float = Field(default=0, ge=0)
    delivery_method: str = Field(default="standard")
    province_from: str = Field(default="")
    province_to: str = Field(default="")


class ShippingCalculateResponse(BaseModel):
    base_fee: float
    weight_fee: float
    province_fee: float
    discount: float
    total: float
    is_free: bool
    breakdown: str


@router.post("/calculate", response_model=ShippingCalculateResponse)
async def calculate_shipping(data: ShippingCalculateRequest):
    result = calculate_shipping_fee(
        distance_km=data.distance_km,
        weight_grams=data.weight_grams,
        order_value=data.order_value,
        delivery_method=data.delivery_method,
    )

    # Build human-readable breakdown
    breakdown_parts = []
    if result["base_fee"] > 0:
        breakdown_parts.append(f"Base: {result['base_fee']:,}đ")
    if result["weight_fee"] > 0:
        breakdown_parts.append(f"Weight: {result['weight_fee']:,}đ")
    if result["discount"] > 0:
        breakdown_parts.append(f"Discount: -{result['discount']:,}đ")
    if result["is_free"]:
        breakdown_parts.append("FREE SHIPPING")

    return ShippingCalculateResponse(
        base_fee=result["base_fee"],
        weight_fee=result["weight_fee"],
        province_fee=result.get("province_fee", 0),
        discount=result["discount"],
        total=result["total"],
        is_free=result["is_free"],
        breakdown=" | ".join(breakdown_parts) if breakdown_parts else "Standard shipping",
    )
