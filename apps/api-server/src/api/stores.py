from fastapi import APIRouter

router = APIRouter(prefix="/api/stores", tags=["Stores"])


@router.get("/")
async def list_stores(province: str = None, industry: str = None):
    return {"stores": [], "total": 0}


@router.get("/{store_id}")
async def get_store_detail(store_id: str):
    return {"id": store_id, "name": "Store", "products": []}


@router.get("/{store_id}/products")
async def get_store_products(store_id: str, page: int = 1):
    return {"products": [], "page": page, "total": 0}


@router.get("/{store_id}/layout")
async def get_store_layout(store_id: str):
    return {"zones": []}


@router.post("/register")
async def register_store(data: dict):
    return {"id": "store_new", "status": "pending"}


@router.post("/validate-location")
async def validate_location(lat: float, lng: float):
    return {"valid": True, "address": ""}
