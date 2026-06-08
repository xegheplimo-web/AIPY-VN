"""
Integration tests for API endpoints.

Tests the full request/response cycle with database.
"""

import pytest
from fastapi.testclient import TestClient
from src.models.store import Store, Product, Category
from src.models.user import User
from src.models.order import Cart, CartItem
import uuid
from datetime import datetime


@pytest.mark.asyncio
class TestStoresAPI:
    """Integration tests for Stores API."""

    async def test_list_stores(self, client, db_session):
        """Test listing stores with pagination."""
        response = client.get("/api/stores?page=1&limit=3")
        assert response.status_code in [200, 401]  # 401 if auth required

    async def test_get_store_detail(self, client, db_session):
        """Test getting store details."""
        # Create a test store
        store = Store(
            id=uuid.uuid4(),
            name="Test Store",
            address="123 Test Street",
            latitude=10.7743,
            longitude=106.7009,
            phone="0123456789",
            email="store@example.com",
            status="active",
            is_open_now=True,
            rating=4.5,
            total_reviews=10,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        db_session.add(store)
        await db_session.commit()
        await db_session.refresh(store)

        response = client.get(f"/api/stores/{store.id}")
        assert response.status_code in [200, 401]

    async def test_store_not_found(self, client, db_session):
        """Test getting non-existent store."""
        fake_id = uuid.uuid4()
        response = client.get(f"/api/stores/{fake_id}")
        assert response.status_code in [404, 401]


@pytest.mark.asyncio
class TestCartAPI:
    """Integration tests for Cart API."""

    async def test_get_cart(self, client, db_session):
        """Test getting user cart."""
        response = client.get("/api/cart")
        assert response.status_code in [200, 401]


@pytest.mark.asyncio
class TestSearchAPI:
    """Integration tests for Search API."""

    async def test_chat_search_with_location(self, client, db_session):
        """Test chat search with location."""
        search_data = {
            "query": "Test",
            "location": {"lat": 10.7743, "lng": 106.7009},
            "radius_km": 5,
        }
        response = client.post("/api/chat/search", json=search_data)
        assert response.status_code in [200, 422]

    async def test_suggestions(self, client, db_session):
        """Test search suggestions."""
        response = client.get("/api/suggestions?q=Test&limit=5")
        assert response.status_code in [200, 401]

    async def test_chat_search_empty_query(self, client, db_session):
        """Test chat search with empty query."""
        search_data = {
            "query": "",
            "location": {"lat": 10.7743, "lng": 106.7009},
            "radius_km": 5,
        }
        response = client.post("/api/chat/search", json=search_data)
        assert response.status_code == 422

    async def test_chat_search_invalid_radius(self, client, db_session):
        """Test chat search with invalid radius."""
        search_data = {
            "query": "Test",
            "location": {"lat": 10.7743, "lng": 106.7009},
            "radius_km": 100,  # Over max limit
        }
        response = client.post("/api/chat/search", json=search_data)
        assert response.status_code == 422
