from fastapi import APIRouter

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/stats")
async def admin_stats():
    return {"stores": 0, "products": 0, "users": 0}


@router.get("/match-queue")
async def admin_match_queue(status: str = "pending"):
    return {"matches": []}


@router.post("/matches/{match_id}/approve")
async def admin_approve_match(match_id: str):
    return {"match_id": match_id, "status": "approved"}


@router.get("/industries")
async def admin_list_industries():
    return {"industries": []}
