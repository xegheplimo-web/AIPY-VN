"""
Unit tests for utility functions.
"""

import pytest
from sqlalchemy import select
from src.utils.pagination import paginate, get_pagination_metadata
from src.utils.uuid import safe_uuid, validate_uuid


class TestPagination:
    """Test pagination utility functions."""

    def test_paginate_default_values(self):
        """Test paginate with default values."""
        stmt = select()
        result = paginate(stmt)
        # Should apply default pagination
        assert result is not None

    def test_paginate_with_custom_values(self):
        """Test paginate with custom page and limit."""
        stmt = select()
        result = paginate(stmt, page=2, limit=10)
        assert result is not None

    def test_paginate_page_less_than_one(self):
        """Test paginate with page < 1 should default to 1."""
        stmt = select()
        result = paginate(stmt, page=0, limit=10)
        assert result is not None

    def test_paginate_limit_too_high(self):
        """Test paginate with limit > 100 should default to 100."""
        stmt = select()
        result = paginate(stmt, page=1, limit=200)
        assert result is not None

    def test_get_pagination_metadata(self):
        """Test pagination metadata calculation."""
        metadata = get_pagination_metadata(total=100, page=1, limit=10)
        
        assert metadata["total"] == 100
        assert metadata["page"] == 1
        assert metadata["limit"] == 10
        assert metadata["total_pages"] == 10
        assert metadata["has_next"] is True
        assert metadata["has_prev"] is False

    def test_get_pagination_metadata_last_page(self):
        """Test pagination metadata for last page."""
        metadata = get_pagination_metadata(total=100, page=10, limit=10)
        
        assert metadata["total"] == 100
        assert metadata["page"] == 10
        assert metadata["total_pages"] == 10
        assert metadata["has_next"] is False
        assert metadata["has_prev"] is True

    def test_get_pagination_metadata_empty(self):
        """Test pagination metadata with no items."""
        metadata = get_pagination_metadata(total=0, page=1, limit=10)
        
        assert metadata["total"] == 0
        assert metadata["total_pages"] == 0
        assert metadata["has_next"] is False
        assert metadata["has_prev"] is False


class TestUUID:
    """Test UUID utility functions."""

    def test_safe_uuid_valid(self):
        """Test safe_uuid with valid UUID string."""
        valid_uuid = "123e4567-e89b-12d3-a456-426614174000"
        result = safe_uuid(valid_uuid)
        assert str(result) == valid_uuid

    def test_safe_uuid_invalid(self):
        """Test safe_uuid with invalid UUID string."""
        from fastapi import HTTPException
        
        invalid_uuid = "not-a-uuid"
        with pytest.raises(HTTPException) as exc_info:
            safe_uuid(invalid_uuid)
        
        assert exc_info.value.status_code == 422

    def test_validate_uuid_valid(self):
        """Test validate_uuid with valid UUID."""
        valid_uuid = "123e4567-e89b-12d3-a456-426614174000"
        assert validate_uuid(valid_uuid) is True

    def test_validate_uuid_invalid(self):
        """Test validate_uuid with invalid UUID."""
        invalid_uuid = "not-a-uuid"
        assert validate_uuid(invalid_uuid) is False

    def test_validate_uuid_empty(self):
        """Test validate_uuid with empty string."""
        assert validate_uuid("") is False

    def test_validate_uuid_none(self):
        """Test validate_uuid with None."""
        assert validate_uuid(None) is False
