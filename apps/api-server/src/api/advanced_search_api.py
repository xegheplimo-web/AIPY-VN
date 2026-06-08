"""
Advanced search API endpoints
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from pydantic import BaseModel, Field
from src.middleware.auth_middleware import require_auth
from src.models.user import User
from src.services.advanced_search import (
    advanced_search_service,
    SearchFilter,
)

router = APIRouter(prefix="/api/search", tags=["Advanced Search"])


class SearchFilterModel(BaseModel):
    """Search filter model"""
    field: str
    operator: str = Field(..., pattern="^(eq|ne|gt|gte|lt|lte|like|ilike|in|not_in|is_null)$")
    value: any


class ProductSearchRequest(BaseModel):
    """Product search request model"""
    query: Optional[str] = None
    filters: Optional[List[SearchFilterModel]] = None
    category_id: Optional[str] = None
    store_id: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    in_stock_only: bool = False
    sort_by: str = "name"
    sort_order: str = "asc"
    page: int = 1
    limit: int = 20


class StoreSearchRequest(BaseModel):
    """Store search request model"""
    query: Optional[str] = None
    filters: Optional[List[SearchFilterModel]] = None
    category: Optional[str] = None
    is_verified: Optional[bool] = None
    min_rating: Optional[float] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    radius_km: Optional[float] = None
    sort_by: str = "name"
    sort_order: str = "asc"
    page: int = 1
    limit: int = 20


@router.post("/products")
async def search_products(request: ProductSearchRequest):
    """
    Search products with advanced filters
    
    - Supports text search
    - Supports custom filters
    - Supports category and store filtering
    - Supports price range filtering
    - Supports stock filtering
    - Supports sorting and pagination
    """
    # Convert filter models to SearchFilter objects
    filters = None
    if request.filters:
        filters = [
            SearchFilter(field=f.field, operator=f.operator, value=f.value)
            for f in request.filters
        ]
    
    result = await advanced_search_service.search_products(
        query=request.query,
        filters=filters,
        category_id=request.category_id,
        store_id=request.store_id,
        min_price=request.min_price,
        max_price=request.max_price,
        in_stock_only=request.in_stock_only,
        sort_by=request.sort_by,
        sort_order=request.sort_order,
        page=request.page,
        limit=request.limit,
    )
    
    return result


@router.post("/stores")
async def search_stores(request: StoreSearchRequest):
    """
    Search stores with advanced filters
    
    - Supports text search
    - Supports custom filters
    - Supports category/industry filtering
    - Supports verification status filtering
    - Supports rating filtering
    - Supports geo search with radius
    - Supports sorting and pagination
    """
    # Convert filter models to SearchFilter objects
    filters = None
    if request.filters:
        filters = [
            SearchFilter(field=f.field, operator=f.operator, value=f.value)
            for f in request.filters
        ]
    
    result = await advanced_search_service.search_stores(
        query=request.query,
        filters=filters,
        category=request.category,
        is_verified=request.is_verified,
        min_rating=request.min_rating,
        lat=request.lat,
        lng=request.lng,
        radius_km=request.radius_km,
        sort_by=request.sort_by,
        sort_order=request.sort_order,
        page=request.page,
        limit=request.limit,
    )
    
    return result


@router.get("/suggestions")
async def get_suggestions(
    query: str = Query(..., min_length=2),
    limit: int = Query(5, ge=1, le=20),
):
    """
    Get search suggestions
    
    - Returns product and store name suggestions
    - Based on partial query match
    """
    suggestions = await advanced_search_service.get_search_suggestions(query, limit)
    
    return {"suggestions": suggestions}


@router.get("/filter-options")
async def get_filter_options():
    """
    Get available filter options
    
    - Returns available categories
    - Returns price range
    - Returns available industries
    """
    options = await advanced_search_service.get_filter_options()
    
    return options
