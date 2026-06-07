from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["Orders"])


@router.post("/orders")
async def create_order(order: dict):
    return {"id": "order_new", "status": "pending"}


@router.get("/orders/{order_id}")
async def get_order_detail(order_id: str):
    return {"id": order_id, "status": "pending"}


@router.get("/users/me/orders")
async def get_user_orders():
    return {"orders": []}


@router.post("/orders/{order_id}/confirm")
async def confirm_order(order_id: str):
    return {"id": order_id, "status": "confirmed"}
