from fastapi import APIRouter

router = APIRouter(prefix="/api/cart", tags=["Cart"])


@router.get("/")
async def get_cart():
    return {"items": []}


@router.post("/items")
async def add_to_cart(item: dict):
    return {"item_id": "item_new", "status": "added"}


@router.put("/items/{item_id}")
async def update_cart_item(item_id: str, quantity: int):
    return {"item_id": item_id, "quantity": quantity}


@router.delete("/items/{item_id}")
async def remove_from_cart(item_id: str):
    return {"item_id": item_id, "status": "removed"}
