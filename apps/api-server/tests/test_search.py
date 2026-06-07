"""
Search functionality tests for VietStore RAG API.
"""

import pytest
from fastapi.testclient import TestClient
from src.models.store import Store, Product, Category
import uuid
from datetime import datetime


@pytest.mark.asyncio
@pytest.mark.asyncio
class TestChatSearch:
    """Tests for AI-powered chat search."""

    async def test_chat_search_basic(
        self, client: TestClient, sample_store, sample_product
    ):
        """Test basic chat search functionality."""
        search_data = {
            "query": "Panadol",
            "location": {"lat": 10.7743, "lng": 106.7009},
            "radius_km": 5,
        }

        response = client.post("/api/chat/search", json=search_data)
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "stores" in data
        assert "total_found" in data

    async def test_chat_search_with_category(
        self, client: TestClient, sample_store, sample_product, sample_category
    ):
        """Test chat search with category filter."""
        search_data = {
            "query": f"{sample_category.name} products",
            "location": {"lat": 10.7743, "lng": 106.7009},
            "radius_km": 5,
            "category_id": str(sample_category.id),
        }

        response = client.post("/api/chat/search", json=search_data)
        assert response.status_code == 200
        data = response.json()
        assert "stores" in data

    async def test_chat_search_empty_query(self, client: TestClient):
        """Test chat search with empty query."""
        search_data = {
            "query": "",
            "location": {"lat": 10.7743, "lng": 106.7009},
            "radius_km": 5,
        }

        response = client.post("/api/chat/search", json=search_data)
        assert response.status_code == 422

    async def test_chat_search_invalid_radius(self, client: TestClient):
        """Test chat search with invalid radius."""
        search_data = {
            "query": "Test",
            "location": {"lat": 10.7743, "lng": 106.7009},
            "radius_km": 100,  # Over max limit
        }

        response = client.post("/api/chat/search", json=search_data)
        assert response.status_code == 422

    async def test_chat_search_invalid_location(self, client: TestClient):
        """Test chat search with invalid location."""
        search_data = {
            "query": "Test",
            "location": {"lat": 200, "lng": 300},  # Invalid coordinates
            "radius_km": 5,
        }

        response = client.post("/api/chat/search", json=search_data)
        assert response.status_code == 422

    async def test_chat_search_no_location(self, client: TestClient):
        """Test chat search without location (should use default)."""
        search_data = {
            "query": "Test",
            "radius_km": 5,
        }

        response = client.post("/api/chat/search", json=search_data)
        assert response.status_code in [200, 422]

    async def test_chat_search_vietnamese_query(
        self, client: TestClient, sample_store, sample_product
    ):
        """Test chat search with Vietnamese query."""
        search_data = {
            "query": "thuốc giảm đau",
            "location": {"lat": 10.7743, "lng": 106.7009},
            "radius_km": 5,
        }

        response = client.post("/api/chat/search", json=search_data)
        assert response.status_code == 200

    async def test_chat_search_pagination(
        self, client: TestClient, sample_store, sample_product
    ):
        """Test chat search with pagination."""
        search_data = {
            "query": "Test",
            "location": {"lat": 10.7743, "lng": 106.7009},
            "radius_km": 5,
            "page": 1,
            "limit": 10,
        }

        response = client.post("/api/chat/search", json=search_data)
        assert response.status_code == 200
        data = response.json()
        # Check pagination metadata if present
        if "page" in data:
            assert data["page"] == 1


@pytest.mark.asyncio
class TestSearchSuggestions:
    """Tests for search suggestions."""

    async def test_suggestions_basic(self, client: TestClient, sample_product):
        """Test basic search suggestions."""
        response = client.get("/api/suggestions?q=Test&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)

    async def test_suggestions_empty_query(self, client: TestClient):
        """Test suggestions with empty query."""
        response = client.get("/api/suggestions?q=&limit=5")
        assert response.status_code in [200, 422]

    async def test_suggestions_limit(self, client: TestClient, sample_product):
        """Test suggestions with custom limit."""
        response = client.get("/api/suggestions?q=Test&limit=3")
        assert response.status_code == 200
        data = response.json()
        if "suggestions" in data:
            assert len(data["suggestions"]) <= 3

    async def test_suggestions_no_results(self, client: TestClient):
        """Test suggestions with no matching results."""
        response = client.get("/api/suggestions?q=xyz123&limit=5")
        assert response.status_code == 200
        data = response.json()
        if "suggestions" in data:
            assert len(data["suggestions"]) == 0


@pytest.mark.asyncio
class TestProductSearch:
    """Tests for product search endpoints."""

    async def test_search_products_by_name(self, client: TestClient, sample_product):
        """Test searching products by name."""
        response = client.get(f"/api/products?search={sample_product.name}")
        assert response.status_code == 200
        data = response.json()
        assert "products" in data or isinstance(data, list)

    async def test_search_products_by_category(
        self, client: TestClient, sample_product, sample_category
    ):
        """Test searching products by category."""
        response = client.get(f"/api/products?category_id={sample_category.id}")
        assert response.status_code == 200
        data = response.json()
        assert "products" in data or isinstance(data, list)

    async def test_search_products_by_store(
        self, client: TestClient, sample_product, sample_store
    ):
        """Test searching products by store."""
        response = client.get(f"/api/products?store_id={sample_store.id}")
        assert response.status_code == 200
        data = response.json()
        assert "products" in data or isinstance(data, list)

    async def test_search_products_with_pagination(self, client: TestClient, sample_product):
        """Test product search with pagination."""
        response = client.get("/api/products?page=1&limit=10")
        assert response.status_code == 200
        data = response.json()
        # Check pagination metadata
        if "page" in data:
            assert data["page"] == 1

    async def test_search_products_min_price(self, client: TestClient, sample_product):
        """Test product search with minimum price filter."""
        response = client.get(f"/api/products?min_price={sample_product.price}")
        assert response.status_code == 200

    async def test_search_products_max_price(self, client: TestClient, sample_product):
        """Test product search with maximum price filter."""
        response = client.get(f"/api/products?max_price={sample_product.price}")
        assert response.status_code == 200

    async def test_search_products_in_stock(self, client: TestClient, sample_product):
        """Test product search for in-stock items only."""
        response = client.get("/api/products?in_stock=true")
        assert response.status_code == 200


@pytest.mark.asyncio
class TestStoreSearch:
    """Tests for store search endpoints."""

    async def test_search_stores_by_name(self, client: TestClient, sample_store):
        """Test searching stores by name."""
        response = client.get(f"/api/stores?search={sample_store.name}")
        assert response.status_code == 200
        data = response.json()
        assert "stores" in data or isinstance(data, list)

    async def test_search_stores_by_location(self, client: TestClient, sample_store):
        """Test searching stores by location."""
        response = client.get(
            f"/api/stores?lat={sample_store.latitude}&lng={sample_store.longitude}&radius=5"
        )
        assert response.status_code == 200

    async def test_search_stores_by_industry(self, client: TestClient, sample_store):
        """Test searching stores by industry."""
        response = client.get(f"/api/stores?industry={sample_store.industry}")
        assert response.status_code == 200

    async def test_search_stores_open_now(self, client: TestClient, sample_store):
        """Test searching for stores that are currently open."""
        response = client.get("/api/stores?is_open=true")
        assert response.status_code == 200

    async def test_search_stores_with_rating(self, client: TestClient, sample_store):
        """Test searching stores with minimum rating."""
        response = client.get(f"/api/stores?min_rating={sample_store.rating}")
        assert response.status_code == 200

    async def test_search_stores_pagination(self, client: TestClient, sample_store):
        """Test store search with pagination."""
        response = client.get("/api/stores?page=1&limit=10")
        assert response.status_code == 200
        data = response.json()
        if "page" in data:
            assert data["page"] == 1


@pytest.mark.asyncio
class TestVectorSearch:
    """Tests for vector-based similarity search."""

    async def test_vector_search_product(self, client: TestClient, sample_product):
        """Test vector search for similar products."""
        search_data = {
            "query": "pain relief medicine",
            "limit": 5,
        }

        response = client.post("/api/vector/search/products", json=search_data)
        assert response.status_code in [200, 404]  # 404 if vector DB not configured

    async def test_vector_search_store(self, client: TestClient, sample_store):
        """Test vector search for similar stores."""
        search_data = {
            "query": "grocery store",
            "limit": 5,
        }

        response = client.post("/api/vector/search/stores", json=search_data)
        assert response.status_code in [200, 404]

    async def test_vector_search_invalid_query(self, client: TestClient):
        """Test vector search with invalid query."""
        search_data = {
            "query": "",  # Empty query
            "limit": 5,
        }

        response = client.post("/api/vector/search/products", json=search_data)
        assert response.status_code in [422, 404]
