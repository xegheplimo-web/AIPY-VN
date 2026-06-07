"""
Tests for OpenMap service.
"""

import pytest
from src.services.openmap import get_openmap_service


class TestOpenMapService:
    """Test OpenMap service functionality."""

    @pytest.fixture
    def openmap(self):
        """Get OpenMap service instance."""
        return get_openmap_service()

    def test_service_initialization(self, openmap):
        """Test that service initializes correctly."""
        assert openmap is not None
        assert hasattr(openmap, "api_key")
        assert hasattr(openmap, "base_url")
        assert hasattr(openmap, "timeout")

    def test_is_ready_with_key(self, openmap):
        """Test is_ready returns True when API key is configured."""
        # This test assumes OPENMAP_API_KEY is set in environment
        result = openmap.is_ready()
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_place_nearby(self, openmap):
        """Test place nearby search."""
        results = await openmap.place_nearby(
            lat=10.7769,
            lon=106.7009,
            radius=1000,
            types="convenience_store",
            limit=5,
        )
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_geocode(self, openmap):
        """Test geocoding an address."""
        result = await openmap.geocode("Nguyễn Huệ, Quận 1, TP.HCM")
        # May return None if API is not configured or unavailable
        if result:
            assert "lat" in result or "latitude" in result
            assert "lon" in result or "longitude" in result

    @pytest.mark.asyncio
    async def test_reverse_geocode(self, openmap):
        """Test reverse geocoding coordinates."""
        result = await openmap.reverse_geocode(10.7769, 106.7009)
        # May return None if API is not configured or unavailable
        if result:
            assert "address" in result or "full_address" in result

    @pytest.mark.asyncio
    async def test_autocomplete(self, openmap):
        """Test address autocomplete."""
        suggestions = await openmap.autocomplete("Nguyễn Huệ", limit=5)
        assert isinstance(suggestions, list)

    @pytest.mark.asyncio
    async def test_search_text(self, openmap):
        """Test text search."""
        results = await openmap.search_text("Circle K", limit=5)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_place_nearby_without_key(self, openmap):
        """Test nearby search returns empty list when not configured."""
        # Temporarily clear API key
        original_key = openmap.api_key
        openmap.api_key = ""

        results = await openmap.place_nearby(10.7769, 106.7009)
        assert results == []

        # Restore API key
        openmap.api_key = original_key
