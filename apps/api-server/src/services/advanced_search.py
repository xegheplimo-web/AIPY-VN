"""
Advanced search service with filters
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from src.database import async_session
from src.models.product import Product
from src.models.store import Store
from src.models.category import Category

logger = logging.getLogger(__name__)


class SearchFilter:
    """Search filter class"""
    
    def __init__(
        self,
        field: str,
        operator: str,
        value: Any,
    ):
        self.field = field
        self.operator = operator
        self.value = value


class AdvancedSearchService:
    """Service for advanced search with filters"""
    
    def __init__(self):
        self.supported_operators = {
            'eq': lambda field, value: field == value,
            'ne': lambda field, value: field != value,
            'gt': lambda field, value: field > value,
            'gte': lambda field, value: field >= value,
            'lt': lambda field, value: field < value,
            'lte': lambda field, value: field <= value,
            'like': lambda field, value: field.ilike(f'%{value}%'),
            'ilike': lambda field, value: field.ilike(f'%{value}%'),
            'in': lambda field, value: field.in_(value),
            'not_in': lambda field, value: field.not_in(value),
            'is_null': lambda field, value: field.is_(None) if value else field.isnot(None),
        }
    
    def _build_filter_condition(self, model, filter_obj: SearchFilter):
        """Build SQLAlchemy filter condition from SearchFilter"""
        field = getattr(model, filter_obj.field)
        operator_func = self.supported_operators.get(filter_obj.operator)
        
        if not operator_func:
            logger.warning(f"Unsupported operator: {filter_obj.operator}")
            return None
        
        return operator_func(field, filter_obj.value)
    
    async def search_products(
        self,
        query: Optional[str] = None,
        filters: Optional[List[SearchFilter]] = None,
        category_id: Optional[str] = None,
        store_id: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock_only: bool = False,
        sort_by: str = 'name',
        sort_order: str = 'asc',
        page: int = 1,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Search products with advanced filters
        
        Args:
            query: Search query string
            filters: List of SearchFilter objects
            category_id: Filter by category
            store_id: Filter by store
            min_price: Minimum price
            max_price: Maximum price
            in_stock_only: Only show in-stock products
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            page: Page number
            limit: Items per page
        
        Returns:
            Dictionary with products and pagination info
        """
        async with async_session() as session:
            # Build base query
            stmt = select(Product).options(selectinload(Product.store))
            
            # Build conditions
            conditions = []
            
            # Text search
            if query:
                conditions.append(
                    or_(
                        Product.name.ilike(f'%{query}%'),
                        Product.description.ilike(f'%{query}%'),
                    )
                )
            
            # Category filter
            if category_id:
                conditions.append(Product.category_id == category_id)
            
            # Store filter
            if store_id:
                conditions.append(Product.store_id == store_id)
            
            # Price range
            if min_price is not None:
                conditions.append(Product.price >= min_price)
            
            if max_price is not None:
                conditions.append(Product.price <= max_price)
            
            # Stock filter
            if in_stock_only:
                conditions.append(Product.stock > 0)
            
            # Custom filters
            if filters:
                for filter_obj in filters:
                    condition = self._build_filter_condition(Product, filter_obj)
                    if condition:
                        conditions.append(condition)
            
            # Apply conditions
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            # Get total count
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = await session.execute(count_stmt)
            total = total.scalar() or 0
            
            # Sorting
            sort_field = getattr(Product, sort_by, Product.name)
            if sort_order == 'desc':
                stmt = stmt.order_by(sort_field.desc())
            else:
                stmt = stmt.order_by(sort_field.asc())
            
            # Pagination
            offset = (page - 1) * limit
            stmt = stmt.offset(offset).limit(limit)
            
            # Execute query
            result = await session.execute(stmt)
            products = result.scalars().all()
            
            # Calculate pagination metadata
            total_pages = (total + limit - 1) // limit if total > 0 else 0
            
            return {
                'products': [self._product_to_dict(p) for p in products],
                'total': total,
                'page': page,
                'limit': limit,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1,
            }
    
    async def search_stores(
        self,
        query: Optional[str] = None,
        filters: Optional[List[SearchFilter]] = None,
        category: Optional[str] = None,
        is_verified: Optional[bool] = None,
        min_rating: Optional[float] = None,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        radius_km: Optional[float] = None,
        sort_by: str = 'name',
        sort_order: str = 'asc',
        page: int = 1,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Search stores with advanced filters
        
        Args:
            query: Search query string
            filters: List of SearchFilter objects
            category: Filter by industry/category
            is_verified: Filter by verification status
            min_rating: Minimum rating
            lat: Latitude for geo search
            lng: Longitude for geo search
            radius_km: Search radius in km
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            page: Page number
            limit: Items per page
        
        Returns:
            Dictionary with stores and pagination info
        """
        async with async_session() as session:
            # Build base query
            stmt = select(Store)
            
            # Build conditions
            conditions = []
            
            # Text search
            if query:
                conditions.append(
                    or_(
                        Store.name.ilike(f'%{query}%'),
                        Store.address.ilike(f'%{query}%'),
                    )
                )
            
            # Category filter
            if category:
                conditions.append(Store.industry == category)
            
            # Verification filter
            if is_verified is not None:
                conditions.append(Store.is_verified == is_verified)
            
            # Rating filter
            if min_rating is not None:
                conditions.append(Store.rating >= min_rating)
            
            # Custom filters
            if filters:
                for filter_obj in filters:
                    condition = self._build_filter_condition(Store, filter_obj)
                    if condition:
                        conditions.append(condition)
            
            # Apply conditions
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            # Get total count
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = await session.execute(count_stmt)
            total = total.scalar() or 0
            
            # Sorting
            sort_field = getattr(Store, sort_by, Store.name)
            if sort_order == 'desc':
                stmt = stmt.order_by(sort_field.desc())
            else:
                stmt = stmt.order_by(sort_field.asc())
            
            # Pagination
            offset = (page - 1) * limit
            stmt = stmt.offset(offset).limit(limit)
            
            # Execute query
            result = await session.execute(stmt)
            stores = result.scalars().all()
            
            # Filter by distance if geo coordinates provided
            if lat and lng and radius_km:
                stores = self._filter_by_distance(stores, lat, lng, radius_km)
            
            # Calculate pagination metadata
            total_pages = (total + limit - 1) // limit if total > 0 else 0
            
            return {
                'stores': [self._store_to_dict(s) for s in stores],
                'total': total,
                'page': page,
                'limit': limit,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1,
            }
    
    def _filter_by_distance(self, stores: List[Store], lat: float, lng: float, radius_km: float) -> List[Store]:
        """Filter stores by distance from coordinates"""
        from math import radians, cos, sin, asin, sqrt
        
        filtered_stores = []
        
        for store in stores:
            if store.latitude and store.longitude:
                # Calculate distance using Haversine formula
                dlat = radians(store.latitude - lat)
                dlon = radians(store.longitude - lng)
                a = sin(dlat / 2) ** 2 + cos(radians(lat)) * cos(radians(store.latitude)) * sin(dlon / 2) ** 2
                c = 2 * asin(sqrt(a))
                distance = 6371 * c  # Earth's radius in km
                
                if distance <= radius_km:
                    store.distance_m = distance * 1000
                    filtered_stores.append(store)
        
        return filtered_stores
    
    def _product_to_dict(self, product: Product) -> Dict[str, Any]:
        """Convert Product model to dictionary"""
        return {
            'id': str(product.id),
            'name': product.name,
            'price': product.price,
            'stock': product.stock,
            'in_stock': product.stock > 0,
            'shelf_location': product.shelf_location,
            'category_id': str(product.category_id) if product.category_id else None,
            'store_id': str(product.store_id) if product.store_id else None,
            'images': product.images or [],
            'description': product.description,
            'created_at': product.created_at.isoformat() if product.created_at else None,
        }
    
    def _store_to_dict(self, store: Store) -> Dict[str, Any]:
        """Convert Store model to dictionary"""
        return {
            'id': str(store.id),
            'name': store.name,
            'address': store.address,
            'latitude': store.latitude,
            'longitude': store.longitude,
            'phone': store.phone,
            'email': store.email,
            'logo_url': store.logo_url,
            'cover_image_url': store.cover_image_url,
            'rating': store.rating,
            'review_count': store.review_count,
            'is_verified': store.is_verified,
            'is_open_now': store.is_open_now,
            'industry': store.industry,
            'distance_m': getattr(store, 'distance_m', None),
            'created_at': store.created_at.isoformat() if store.created_at else None,
        }
    
    async def get_search_suggestions(self, query: str, limit: int = 5) -> List[str]:
        """
        Get search suggestions
        
        Args:
            query: Search query
            limit: Number of suggestions
        
        Returns:
            List of suggestion strings
        """
        async with async_session() as session:
            # Search product names
            product_stmt = select(Product.name).where(
                Product.name.ilike(f'%{query}%')
            ).limit(limit)
            
            product_result = await session.execute(product_stmt)
            product_names = [row[0] for row in product_result.fetchall()]
            
            # Search store names
            store_stmt = select(Store.name).where(
                Store.name.ilike(f'%{query}%')
            ).limit(limit)
            
            store_result = await session.execute(store_stmt)
            store_names = [row[0] for row in store_result.fetchall()]
            
            # Combine and deduplicate
            suggestions = list(set(product_names + store_names))
            
            return suggestions[:limit]
    
    async def get_filter_options(self) -> Dict[str, Any]:
        """
        Get available filter options
        
        Returns:
            Dictionary with filter options
        """
        async with async_session() as session:
            # Get categories
            category_stmt = select(Category)
            category_result = await session.execute(category_stmt)
            categories = [
                {'id': str(c.id), 'name': c.name}
                for c in category_result.scalars().all()
            ]
            
            # Get price range
            price_stmt = select(
                func.min(Product.price),
                func.max(Product.price),
            )
            price_result = await session.execute(price_stmt)
            min_price, max_price = price_result.first()
            
            # Get industries
            industry_stmt = select(Store.industry).distinct()
            industry_result = await session.execute(industry_stmt)
            industries = [row[0] for row in industry_result.fetchall() if row[0]]
            
            return {
                'categories': categories,
                'price_range': {
                    'min': min_price,
                    'max': max_price,
                },
                'industries': industries,
            }


# Global advanced search service instance
advanced_search_service = AdvancedSearchService()
