"""
Pagination utility for SQLAlchemy queries.

Provides consistent pagination across all API endpoints.
"""

from typing import TypeVar
from sqlalchemy import Select

T = TypeVar('T')


def paginate(stmt: Select[T], page: int = 1, limit: int = 20) -> Select[T]:
    """
    Apply pagination to SQLAlchemy statement.
    
    Args:
        stmt: SQLAlchemy Select statement
        page: Page number (1-indexed)
        limit: Number of items per page
        
    Returns:
        Paginated Select statement
        
    Example:
        >>> stmt = select(Store).where(Store.status == "active")
        >>> stmt = paginate(stmt, page=2, limit=10)
        >>> result = await session.execute(stmt)
    """
    if page < 1:
        page = 1
    if limit < 1:
        limit = 20
    if limit > 100:
        limit = 100  # Max limit to prevent excessive queries
    
    offset = (page - 1) * limit
    return stmt.offset(offset).limit(limit)


def get_pagination_metadata(total: int, page: int, limit: int) -> dict:
    """
    Calculate pagination metadata.
    
    Args:
        total: Total number of items
        page: Current page number
        limit: Items per page
        
    Returns:
        Dictionary with pagination metadata
    """
    total_pages = (total + limit - 1) // limit if total > 0 else 0
    has_next = page < total_pages
    has_prev = page > 1
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "has_next": has_next,
        "has_prev": has_prev,
    }
