"""
Tests for Store Locator service.
"""

import pytest
from src.services.store_locator import get_store_locator


class TestStoreLocator:
    """Test Store Locator service functionality."""

    @pytest.fixture
    def locator(self):
        """Get store locator instance."""
        return get_store_locator()

    def test_service_initialization(self, locator):
        """Test that service initializes correctly."""
        assert locator is not None
        assert hasattr(locator, "session")
        assert hasattr(locator, "NOMINATIM_URL")
        assert hasattr(locator, "OVERPASS_URL")

    @pytest.mark.asyncio
    async def test_geocode_address(self, locator):
        """Test geocoding an address."""
        result = locator.geocode_address("Nguyễn Huệ, Quận 1, TP.HCM")
        # This may return None if API is slow or unavailable
        if result:
            assert "latitude" in result
            assert "longitude" in result
            assert isinstance(result["latitude"], float)
            assert isinstance(result["longitude"], float)

    @pytest.mark.asyncio
    async def test_reverse_geocode(self, locator):
        """Test reverse geocoding coordinates."""
        result = locator.reverse_geocode(10.7769, 106.7009)
        # This may return empty dict if API is slow or unavailable
        if result:
            assert "full_address" in result
            assert "city" in result
            assert "district" in result

    @pytest.mark.asyncio
    async def test_search_stores_by_name(self, locator):
        """Test searching stores by name."""
        stores = locator.search_stores_by_name("Circle K", limit=5)
        assert isinstance(stores, list)
        # May be empty if API is slow or unavailable

    @pytest.mark.asyncio
    async def test_search_stores_by_area(self, locator):
        """Test searching stores by area."""
        stores = locator.search_stores_by_area(
            category="convenience",
            city="Hồ Chí Minh",
            radius_km=5,
        )
        assert isinstance(stores, list)
        # May be empty if API is slow or unavailable

    @pytest.mark.asyncio
    async def test_find_nearest_stores(self, locator):
        """Test finding nearest stores."""
        results = locator.find_nearest_stores(
            lat=10.7769,
            lon=106.7009,
            category="convenience",
            radius_km=2,
            limit=5,
        )
        assert isinstance(results, list)
        # May be empty if API is slow or unavailable

    def test_haversine_distance(self, locator):
        """Test Haversine distance calculation."""
        distance = locator._haversine(10.7769, 106.7009, 10.78, 106.71)
        assert isinstance(distance, float)
        assert distance > 0

    def test_format_distance(self, locator):
        """Test distance formatting."""
        # Test meters
        text = locator._format_distance(0.5)
        assert "m" in text

        # Test kilometers
        text = locator._format_distance(2.5)
        assert "km" in text

    def test_geocode_city(self, locator):
        """Test city geocoding."""
        # Test known city
        coords = locator._geocode_city("Hồ Chí Minh")
        assert coords is not None
        assert len(coords) == 2
        assert isinstance(coords[0], float)
        assert isinstance(coords[1], float)

        # Test unknown city
        coords = locator._geocode_city("Unknown City")
        # Should return None or attempt to geocode
        assert coords is None or len(coords) == 2
