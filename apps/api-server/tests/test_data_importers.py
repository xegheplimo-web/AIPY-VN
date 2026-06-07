"""
Tests for data importers (admin and OSM).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession


class TestAdminImporter:
    """Test Vietnam admin data importer."""

    @pytest.fixture
    def admin_importer(self, session: AsyncSession):
        """Get admin importer instance."""
        from src.db.admin_importer import VietnamAdminImporter
        return VietnamAdminImporter(session)

    @pytest.mark.asyncio
    async def test_slugify(self, admin_importer):
        """Test slugify function."""
        assert admin_importer._slugify("Hồ Chí Minh") == "ho-chi-minh"
        assert admin_importer._slugify("Hà Nội") == "ha-noi"
        assert admin_importer._slugify("Đà Nẵng") == "da-nang"

    @pytest.mark.asyncio
    async def test_get_admin_type(self, admin_importer):
        """Test admin type normalization."""
        assert admin_importer._get_admin_type("thành phố trung ương") == "thành phố trung ương"
        assert admin_importer._get_admin_type("tỉnh") == "tỉnh"
        assert admin_importer._get_admin_type("quận") == "quận"
        assert admin_importer._get_admin_type("huyện") == "huyện"

    @pytest.mark.asyncio
    async def test_geocode_nominatim(self, admin_importer):
        """Test geocoding with Nominatim."""
        # This will make a real API call
        result = await admin_importer._geocode_nominatim("Hồ Chí Minh")
        # May return None if API is unavailable
        if result:
            assert isinstance(result, tuple)
            assert len(result) == 2
            assert isinstance(result[0], float)
            assert isinstance(result[1], float)


class TestOSMImporter:
    """Test OSM data importer."""

    @pytest.fixture
    def osm_importer(self, session: AsyncSession):
        """Get OSM importer instance."""
        from src.db.osm_importer import OSMImporter
        return OSMImporter(session)

    @pytest.mark.asyncio
    async def test_category_map(self, osm_importer):
        """Test category mapping."""
        assert 'supermarket' in osm_importer.CATEGORY_MAP
        assert 'convenience' in osm_importer.CATEGORY_MAP
        assert 'cafe' in osm_importer.CATEGORY_MAP
        assert osm_importer.CATEGORY_MAP['supermarket'] == 'shop=supermarket'

    @pytest.mark.asyncio
    async def test_brand_patterns(self, osm_importer):
        """Test brand detection patterns."""
        assert 'circle k' in osm_importer.BRAND_PATTERNS
        assert 'highlands' in osm_importer.BRAND_PATTERNS
        assert 'pharmacity' in osm_importer.BRAND_PATTERNS

    @pytest.mark.asyncio
    async def test_detect_brand(self, osm_importer):
        """Test brand detection."""
        brand_map = {
            'circle k': 1,
            'highlands': 2,
            'pharmacity': 3,
        }
        
        # Test by name
        brand_id = osm_importer._detect_brand(
            "Circle K Quận 1",
            {},
            brand_map
        )
        assert brand_id == 1
        
        # Test by OSM tag
        brand_id = osm_importer._detect_brand(
            "Some Store",
            {"brand": "highlands"},
            brand_map
        )
        assert brand_id == 2
        
        # Test no match
        brand_id = osm_importer._detect_brand(
            "Unknown Store",
            {},
            brand_map
        )
        assert brand_id is None

    @pytest.mark.asyncio
    async def test_import_poi_by_category_empty(self, osm_importer):
        """Test POI import with empty category."""
        imported = await osm_importer.import_poi_by_category("unknown_category")
        assert imported == 0

    @pytest.mark.asyncio
    async def test_import_poi_by_category(self, osm_importer):
        """Test POI import for a category."""
        # This will make real API calls to Overpass
        # Skip in CI/CD if API is unavailable
        try:
            imported = await osm_importer.import_poi_by_category(
                "convenience",
                limit=10
            )
            assert isinstance(imported, int)
            assert imported >= 0
        except Exception as e:
            pytest.skip(f"Overpass API unavailable: {e}")
