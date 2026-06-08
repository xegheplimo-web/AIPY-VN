"""
Voice Search API Endpoints

Provides speech-to-text and voice-powered product search using faster-whisper.
"""

import base64
import logging
import re

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.database import async_session
from src.models.store import Category, Product
from src.services.geo import haversine_distance
from src.services.voice import get_voice_service

router = APIRouter(prefix="/api/voice", tags=["Voice"])
logger = logging.getLogger(__name__)


def sanitize_search_term(term: str) -> str:
    """Remove potentially dangerous characters from search term."""
    sanitized = re.sub(r"[;'\"]", "", term)
    return sanitized[:200]


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class VoiceSearchRequest(BaseModel):
    audio_base64: str = Field(..., description="Audio file encoded as base64")
    language: str = Field(default="vi", description="Language code: vi, en")
    location: dict | None = Field(None, description="User location {lat, lng}")
    radius_km: float = Field(default=5.0, ge=0.1, le=50.0)


class ProductResult(BaseModel):
    id: str
    name: str
    price: float | None
    stock: int | None
    in_stock: bool
    shelf_location: str
    category: str | None


class StoreResult(BaseModel):
    id: str
    name: str
    address: str
    latitude: float
    longitude: float
    distance_m: float | None
    industry: str | None
    products: list[ProductResult]
    map_url: str


class VoiceSearchResponse(BaseModel):
    transcript: str
    query: str
    summary: str
    stores: list[StoreResult]
    total_found: int


class VoiceUploadResponse(BaseModel):
    transcript: str
    language: str
    duration_s: float | None = None


# ---------------------------------------------------------------------------
# Helper: perform the actual product/store search
# ---------------------------------------------------------------------------


async def _search_products_by_query(
    query: str,
    location: dict | None = None,
    radius_km: float = 5.0,
    limit: int = 10,
) -> tuple[list[StoreResult], str]:
    """
    Search for products matching *query* and return store results.

    Returns:
        (stores, summary) tuple
    """
    search_term = f"%{sanitize_search_term(query)}%"

    async with async_session() as session:
        stmt = (
            select(Product)
            .where(Product.name.ilike(search_term))
            .where(Product.stock > 0)
            .where(Product.status == "active")
            .options(selectinload(Product.store))
        )
        result = await session.execute(stmt)
        products = result.scalars().all()

        # Group by store
        store_products: dict[str, dict] = {}
        for p in products:
            store_id = str(p.store_id)
            if store_id not in store_products:
                store_products[store_id] = {"store": p.store, "products": []}
            store_products[store_id]["products"].append(p)

        # Resolve categories
        category_ids = {p.category_id for p in products if p.category_id}
        category_map: dict[str, str] = {}
        if category_ids:
            cat_stmt = select(Category).where(Category.id.in_(category_ids))
            cat_result = await session.execute(cat_stmt)
            category_map = {str(c.id): c.name for c in cat_result.scalars().all()}

        # Calculate distances & filter by radius
        user_lat = location.get("lat") if location else None
        user_lng = location.get("lng") if location else None

        stores_result: list[StoreResult] = []
        for store_id, data in store_products.items():
            store = data["store"]
            distance_m = None

            if user_lat is not None and user_lng is not None:
                distance_m = haversine_distance(
                    user_lat, user_lng, store.latitude, store.longitude
                )
                if distance_m > radius_km * 1000:
                    continue

            product_results = [
                ProductResult(
                    id=str(p.id),
                    name=p.name,
                    price=float(p.price) if p.price else None,
                    stock=p.stock,
                    in_stock=p.stock > 0,
                    shelf_location=p.shelf_location or "",
                    category=(
                        category_map.get(str(p.category_id))
                        if p.category_id
                        else None
                    ),
                )
                for p in data["products"]
            ]

            encoded_name = store.name.replace(" ", "+")
            map_url = (
                f"https://www.google.com/maps/dir/?api=1"
                f"&destination={store.latitude},{store.longitude}"
                f"&q={encoded_name}"
            )

            stores_result.append(
                StoreResult(
                    id=str(store.id),
                    name=store.name,
                    address=store.address,
                    latitude=store.latitude,
                    longitude=store.longitude,
                    distance_m=round(distance_m, 1) if distance_m is not None else None,
                    industry=store.industry,
                    products=product_results,
                    map_url=map_url,
                )
            )

    # Sort nearest-first
    stores_result.sort(key=lambda x: x.distance_m if x.distance_m else float("inf"))
    stores_result = stores_result[:limit]

    # Build summary
    total = len(stores_result)
    if total == 0:
        summary = (
            f"Khong tim thay '{query}' trong ban kinh {radius_km}km. "
            f"Ban thu tim tu khoa khac nhe!"
        )
    else:
        summary = f"Tim thay {total} cua hang co '{query}' gan ban"
        if stores_result[0].distance_m and stores_result[0].distance_m < 500:
            summary += f" • Gan nhat chi {stores_result[0].distance_m}m"
        summary += ". Nhan vao cua hang de xem chi tiet!"

    return stores_result, summary


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/search", response_model=VoiceSearchResponse)
async def voice_search(data: VoiceSearchRequest):
    """
    Voice search endpoint.

    1. Decode base64 audio payload
    2. Transcribe using VoiceSearchService (faster-whisper)
    3. Use the transcript as a search query
    4. Return matching stores / products
    """
    voice_service = get_voice_service()

    if not voice_service.is_ready():
        raise HTTPException(
            status_code=503,
            detail="Dich vu giong noi chua san sang. Whisper model chua duoc tai. Vui long thu lai sau.",
        )

    # Decode base64 audio
    try:
        audio_bytes = base64.b64decode(data.audio_base64)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Du lieu audio_base64 khong hop le. Khong the giai ma base64.",
        )

    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Du lieu audio trong.")

    # Transcribe
    try:
        transcript = await voice_service.transcribe_audio_bytes(
            audio_bytes,
            language=data.language,
        )
    except RuntimeError as e:
        logger.error(f"Transcription runtime error: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected transcription error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Loi chuyen doi giong noi: {e!s}"
        )

    if not transcript:
        return VoiceSearchResponse(
            transcript="",
            query="",
            summary="Khong the nhan dien giong noi. Vui long thu lai.",
            stores=[],
            total_found=0,
        )

    # Use transcript as search query
    query = transcript.strip()
    try:
        stores, summary = await _search_products_by_query(
            query=query,
            location=data.location,
            radius_km=data.radius_km,
        )
    except Exception as e:
        logger.error(f"Search error for voice query '{query}': {e}")
        # Still return the transcript even if search fails
        return VoiceSearchResponse(
            transcript=transcript,
            query=query,
            summary=f"Da chuyen doi giong noi nhung tim kiem that bai: {e!s}",
            stores=[],
            total_found=0,
        )

    return VoiceSearchResponse(
        transcript=transcript,
        query=query,
        summary=summary,
        stores=stores,
        total_found=len(stores),
    )


@router.post("/upload", response_model=VoiceUploadResponse)
async def voice_upload(
    file: UploadFile = File(..., description="Audio file (webm, wav, mp3, ogg)"),
    language: str = "vi",
):
    """
    Upload an audio file for transcription.

    1. Receive audio file upload
    2. Transcribe using VoiceSearchService (faster-whisper)
    3. Return transcript text
    """
    voice_service = get_voice_service()

    if not voice_service.is_ready():
        raise HTTPException(
            status_code=503,
            detail="Dich vu giong noi chua san sang. Whisper model chua duoc tai. Vui long thu lai sau.",
        )

    # Validate content type
    allowed_prefixes = ("audio/",)
    if not file.content_type or not file.content_type.startswith(allowed_prefixes):
        raise HTTPException(
            status_code=400,
            detail=f"File phai la file audio. Nhan duoc: {file.content_type}",
        )

    # Read audio bytes
    try:
        audio_bytes = await file.read()
    except Exception as e:
        logger.error(f"Failed to read uploaded audio: {e}")
        raise HTTPException(status_code=400, detail="Khong the doc file audio.")

    if not audio_bytes:
        raise HTTPException(status_code=400, detail="File audio trong.")

    # Transcribe
    try:
        transcript = await voice_service.transcribe_audio_bytes(
            audio_bytes,
            language=language,
            content_type=file.content_type,
        )
    except RuntimeError as e:
        logger.error(f"Transcription runtime error: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected transcription error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Loi chuyen doi giong noi: {e!s}"
        )

    return VoiceUploadResponse(
        transcript=transcript or "",
        language=language,
        duration_s=None,  # Could be populated from whisper info if needed
    )
