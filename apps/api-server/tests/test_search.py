import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_suggestions():
    response = client.get("/api/suggestions?q=panadol&limit=3")
    assert response.status_code == 200
    data = response.json()
    assert "suggestions" in data


def test_chat_search():
    response = client.post(
        "/api/chat/search",
        json={
            "query": "Panadol",
            "location": {"lat": 10.7743, "lng": 106.7009},
            "radius_km": 5,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "stores" in data
    assert "total_found" in data
    assert data["total_found"] >= 0


def test_chat_search_invalid_radius():
    response = client.post(
        "/api/chat/search",
        json={
            "query": "Panadol",
            "location": {"lat": 10.7743, "lng": 106.7009},
            "radius_km": 100,
        },
    )
    assert response.status_code == 422


def test_chat_search_empty_query():
    response = client.post(
        "/api/chat/search",
        json={"query": ""},
    )
    assert response.status_code == 422
