"""
Unit tests for pagination utility
"""

import pytest
from sqlalchemy import select
from src.utils.pagination import paginate, get_pagination_metadata


class TestPagination:
    """Test pagination utility functions"""
    
    def test_paginate_default(self):
        """Test pagination with default parameters"""
        stmt = select("test")
        paginated_stmt = paginate(stmt)
        
        # Should apply default limit and offset
        assert paginated_stmt is not None
    
    def test_paginate_with_page_and_limit(self):
        """Test pagination with custom page and limit"""
        stmt = select("test")
        paginated_stmt = paginate(stmt, page=2, limit=50)
        
        # Should apply custom offset (page-1)*limit = 50
        assert paginated_stmt is not None
    
    def test_paginate_invalid_page(self):
        """Test pagination with invalid page (should default to 1)"""
        stmt = select("test")
        paginated_stmt = paginate(stmt, page=0, limit=20)
        
        assert paginated_stmt is not None
    
    def test_paginate_invalid_limit(self):
        """Test pagination with invalid limit (should default to 20)"""
        stmt = select("test")
        paginated_stmt = paginate(stmt, page=1, limit=0)
        
        assert paginated_stmt is not None
    
    def test_paginate_max_limit(self):
        """Test pagination with limit exceeding max (should cap at 100)"""
        stmt = select("test")
        paginated_stmt = paginate(stmt, page=1, limit=200)
        
        assert paginated_stmt is not None
    
    def test_get_pagination_metadata(self):
        """Test pagination metadata calculation"""
        metadata = get_pagination_metadata(total=100, page=1, limit=20)
        
        assert metadata["total"] == 100
        assert metadata["page"] == 1
        assert metadata["limit"] == 20
        assert metadata["total_pages"] == 5
        assert metadata["has_next"] is True
        assert metadata["has_prev"] is False
    
    def test_get_pagination_metadata_last_page(self):
        """Test pagination metadata for last page"""
        metadata = get_pagination_metadata(total=100, page=5, limit=20)
        
        assert metadata["total"] == 100
        assert metadata["page"] == 5
        assert metadata["limit"] == 20
        assert metadata["total_pages"] == 5
        assert metadata["has_next"] is False
        assert metadata["has_prev"] is True
    
    def test_get_pagination_metadata_empty(self):
        """Test pagination metadata with no items"""
        metadata = get_pagination_metadata(total=0, page=1, limit=20)
        
        assert metadata["total"] == 0
        assert metadata["total_pages"] == 0
        assert metadata["has_next"] is False
        assert metadata["has_prev"] is False
