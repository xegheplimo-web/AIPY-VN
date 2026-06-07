import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_list_stores():
    response = client.get("/api/stores/")
    assert response.status_code == 200
    data = response.json()
    assert "stores" in data
    assert "total" in data
    assert data["page"] == 1


def test_list_stores_with_filter():
    response = client.get("/api/stores/?industry=Bán lẻ dược phẩm")
    assert response.status_code == 200
    data = response.json()
    assert "stores" in data


def test_store_detail():
    response = client.get("/api/stores/")
    data = response.json()
    if data["stores"]:
        store_id = data["stores"][0]["id"]
        detail = client.get(f"/api/stores/{store_id}")
        assert detail.status_code == 200
        store = detail.json()
        assert "name" in store
        assert "products_count" in store


def test_store_not_found():
    response = client.get("/api/stores/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_validate_location():
    response = client.post(
        "/api/stores/validate-location",
        json={"lat": 10.7743, "lng": 106.7009},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True


def test_validate_location_invalid():
    response = client.post(
        "/api/stores/validate-location",
        json={"lat": 200, "lng": 106.7009},
    )
    assert response.status_code == 422
