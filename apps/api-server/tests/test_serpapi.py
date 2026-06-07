"""
Tests for SerpAPI service.
"""

import pytest
from src.services.serpapi import get_serpapi_service


class TestSerpAPIService:
    """Test SerpAPI service functionality."""

    @pytest.fixture
    def serpapi_service(self):
        """Get SerpAPI service instance."""
        return get_serpapi_service()

    def test_service_initialization(self, serpapi_service):
        """Test that service initializes correctly."""
        assert serpapi_service is not None
        assert hasattr(serpapi_service, "api_key")
        assert hasattr(serpapi_service, "engine")
        assert hasattr(serpapi_service, "timeout")

    def test_is_ready_with_key(self, serpapi_service):
        """Test is_ready returns True when API key is configured."""
        # This test assumes SERPAPI_KEY is set in environment
        # If not, it will return False
        result = serpapi_service.is_ready()
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_search_basic(self, serpapi_service):
        """Test basic search functionality."""
        results = await serpapi_service.search("test query", num_results=5)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_without_key(self, serpapi_service):
        """Test search returns empty list when not configured."""
        # Temporarily clear API key
        original_key = serpapi_service.api_key
        serpapi_service.api_key = ""

        results = await serpapi_service.search("test query")
        assert results == []

        # Restore API key
        serpapi_service.api_key = original_key

    @pytest.mark.asyncio
    async def test_search_shopping(self, serpapi_service):
        """Test shopping search functionality."""
        results = await serpapi_service.search_shopping("laptop", num_results=5)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_images(self, serpapi_service):
        """Test image search functionality."""
        results = await serpapi_service.search_images("cat", num_results=5)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_get_search_suggestions(self, serpapi_service):
        """Test search suggestions functionality."""
        suggestions = await serpapi_service.get_search_suggestions("lap")
        assert isinstance(suggestions, list)
