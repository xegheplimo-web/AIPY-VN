from fastapi import APIRouter

router = APIRouter(prefix="/api/products", tags=["Products"])


@router.get("/{product_id}")
async def get_product_detail(product_id: str):
    return {"id": product_id, "name": "Product", "price": 0}


@router.get("/{product_id}/alternatives")
async def get_alternatives(product_id: str):
    return {"alternatives": []}
