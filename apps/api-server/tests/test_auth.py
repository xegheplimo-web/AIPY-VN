"""
Unit tests for authentication API
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestAuthAPI:
    """Test authentication API endpoints"""

    def test_register_user_success(self, client):
        """Test successful user registration"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "TestPass123",
                "full_name": "Test User",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"

    def test_register_user_weak_password(self, client):
        """Test registration with weak password"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "weak",
                "full_name": "Test User",
            },
        )

        assert response.status_code == 422

    def test_register_user_duplicate_email(self, client):
        """Test registration with duplicate email"""
        # First registration
        client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "TestPass123",
                "full_name": "Test User",
            },
        )

        # Second registration with same email
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "TestPass123",
                "full_name": "Test User 2",
            },
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_login_user_success(self, client):
        """Test successful user login"""
        # First register
        client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "TestPass123",
                "full_name": "Test User",
            },
        )

        # Then login
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_user_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "WrongPass123",
            },
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_logout_user(self, client):
        """Test user logout"""
        # Register and login
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "TestPass123",
                "full_name": "Test User",
            },
        )
        token = register_response.json()["access_token"]

        # Logout
        response = client.post(
            "/api/auth/logout", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()
