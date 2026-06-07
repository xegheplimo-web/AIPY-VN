"""
Tests for PostGIS setup and Geo Search service.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


class TestPostGISManager:
    """Test PostGIS manager functionality."""

    @pytest.mark.asyncio
    async def test_postgis_extensions(self, session: AsyncSession):
        """Test that PostGIS extensions are enabled."""
        result = await session.execute(text("SELECT PostGIS_Version()"))
        version = result.scalar()
        assert version is not None
        print(f"PostGIS version: {version}")

    @pytest.mark.asyncio
    async def test_pg_trgm_extension(self, session: AsyncSession):
        """Test that pg_trgm extension is enabled."""
        result = await session.execute(text("SELECT * FROM pg_extension WHERE extname = 'pg_trgm'"))
        row = result.fetchone()
        assert row is not None

    @pytest.mark.asyncio
    async def test_unaccent_extension(self, session: AsyncSession):
        """Test that unaccent extension is enabled."""
        result = await session.execute(text("SELECT * FROM pg_extension WHERE extname = 'unaccent'"))
        row = result.fetchone()
        assert row is not None

    @pytest.mark.asyncio
    async def test_vn_unaccent_function(self, session: AsyncSession):
        """Test Vietnamese unaccent function."""
        result = await session.execute(
            text("SELECT vn_unaccent('Cà phê ngon quá')"),
        )
        normalized = result.scalar()
        assert normalized == "ca phe ngon qua"

    @pytest.mark.asyncio
    async def test_admin_tables_exist(self, session: AsyncSession):
        """Test that admin tables exist."""
        tables = ["provinces", "districts", "wards"]
        for table in tables:
            result = await session.execute(
                text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')")
            )
            exists = result.scalar()
            assert exists, f"Table {table} should exist"

    @pytest.mark.asyncio
    async def test_store_tables_exist(self, session: AsyncSession):
        """Test that store tables exist."""
        tables = ["store_categories", "brands", "stores"]
        for table in tables:
            result = await session.execute(
                text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')")
            )
            exists = result.scalar()
            assert exists, f"Table {table} should exist"

    @pytest.mark.asyncio
    async def test_search_columns_exist(self, session: AsyncSession):
        """Test that search columns exist in stores table."""
        columns = ["search_text", "name_normalized"]
        for column in columns:
            result = await session.execute(
                text(f"SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'stores' AND column_name = '{column}')")
            )
            exists = result.scalar()
            assert exists, f"Column {column} should exist in stores table"

    @pytest.mark.asyncio
    async def test_spatial_indexes_exist(self, session: AsyncSession):
        """Test that spatial indexes exist."""
        indexes = ["idx_stores_location", "idx_stores_search_text", "idx_stores_name_trgm"]
        for index in indexes:
            result = await session.execute(
                text(f"SELECT EXISTS (SELECT FROM pg_indexes WHERE indexname = '{index}')")
            )
            exists = result.scalar()
            assert exists, f"Index {index} should exist"

    @pytest.mark.asyncio
    async def test_stored_procedures_exist(self, session: AsyncSession):
        """Test that stored procedures exist."""
        procedures = ["find_nearest_stores", "search_stores", "geocode_address"]
        for proc in procedures:
            result = await session.execute(
                text(f"SELECT EXISTS (SELECT FROM pg_proc WHERE proname = '{proc}')")
            )
            exists = result.scalar()
            assert exists, f"Procedure {proc} should exist"

    @pytest.mark.asyncio
    async def test_view_exists(self, session: AsyncSession):
        """Test that v_stores_full view exists."""
        result = await session.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.views WHERE table_name = 'v_stores_full')")
        )
        exists = result.scalar()
        assert exists, "View v_stores_full should exist"


class TestGeoSearchService:
    """Test Geo Search service functionality."""

    @pytest.fixture
    def geo_service(self, session: AsyncSession):
        """Get GeoSearchService instance."""
        from src.services.geo_search import GeoSearchService
        return GeoSearchService(session)

    @pytest.mark.asyncio
    async def test_get_categories(self, geo_service):
        """Test getting store categories."""
        categories = await geo_service.get_categories()
        assert isinstance(categories, list)
        assert len(categories) > 0
        assert "name_vi" in categories[0]
        assert "icon" in categories[0]

    @pytest.mark.asyncio
    async def test_get_brands(self, geo_service):
        """Test getting brands."""
        brands = await geo_service.get_brands()
        assert isinstance(brands, list)
        assert len(brands) > 0
        assert "name" in brands[0]
        assert "slug" in brands[0]

    @pytest.mark.asyncio
    async def test_geocode_empty(self, geo_service):
        """Test geocoding with empty database."""
        result = await geo_service.geocode("Test Address")
        assert "query" in result
        assert "results" in result
        # May be empty if no admin data imported

    @pytest.mark.asyncio
    async def test_reverse_geocode(self, geo_service):
        """Test reverse geocoding."""
        result = await geo_service.reverse_geocode(10.7769, 106.7009)
        assert "lat" in result
        assert "lng" in result
        assert "address" in result

    @pytest.mark.asyncio
    async def test_search_empty(self, geo_service):
        """Test search with empty database."""
        result = await geo_service.search("Circle K")
        assert "query" in result
        assert "total" in result
        assert "stores" in result

    @pytest.mark.asyncio
    async def test_find_nearby_empty(self, geo_service):
        """Test nearby search with empty database."""
        result = await geo_service.find_nearby(10.7769, 106.7009)
        assert "center" in result
        assert "total" in result
        assert "stores" in result

    @pytest.mark.asyncio
    async def test_format_distance(self, geo_service):
        """Test distance formatting."""
        assert geo_service._format_distance(500) == "500m"
        assert geo_service._format_distance(1500) == "1.5km"
        assert geo_service._format_distance(None) is None
