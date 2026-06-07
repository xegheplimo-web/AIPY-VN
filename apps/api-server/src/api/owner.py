from fastapi import APIRouter

router = APIRouter(prefix="/api/owner", tags=["Owner"])


@router.get("/products")
async def owner_list_products(store_id: str):
    return {"products": [], "store_id": store_id}


@router.post("/products")
async def owner_create_product(product: dict):
    return {"id": "product_new", "status": "created"}


@router.put("/products/{product_id}")
async def owner_update_product(product_id: str, product: dict):
    return {"id": product_id, "status": "updated"}


@router.post("/products/bulk-upload")
async def owner_bulk_upload(file: dict, store_id: str):
    return {"uploaded": 0, "errors": []}


@router.get("/analytics/summary")
async def owner_analytics_summary(store_id: str):
    return {"store_id": store_id, "sales": 0, "orders": 0}
