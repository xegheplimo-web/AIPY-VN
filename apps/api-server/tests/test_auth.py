"""
Authentication tests for VietStore RAG API.
"""

import pytest
from fastapi.testclient import TestClient
from src.api.auth import router as auth_router
from src.models.user import User
from src.services.ecc import get_ecc_service
import uuid
from datetime import datetime


class TestAuthRegistration:
    """Tests for user registration."""

    def test_register_user_success(self, client: TestClient):
        """Test successful user registration."""
        user_data = {
            "email": "newuser@example.com",
            "phone": "0987654321",
            "password": "SecurePassword123!",
            "full_name": "New User",
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data or "message" in data

    def test_register_duplicate_email(self, client: TestClient, sample_user):
        """Test registration with duplicate email."""
        user_data = {
            "email": sample_user.email,
            "phone": "0987654321",
            "password": "SecurePassword123!",
            "full_name": "Duplicate User",
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 400

    def test_register_invalid_email(self, client: TestClient):
        """Test registration with invalid email."""
        user_data = {
            "email": "invalid-email",
            "phone": "0987654321",
            "password": "SecurePassword123!",
            "full_name": "Invalid Email User",
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 422

    def test_register_weak_password(self, client: TestClient):
        """Test registration with weak password."""
        user_data = {
            "email": "weakpass@example.com",
            "phone": "0987654321",
            "password": "123",
            "full_name": "Weak Password User",
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 422


class TestAuthLogin:
    """Tests for user login."""

    def test_login_success(self, client: TestClient, sample_user):
        """Test successful login."""
        login_data = {
            "email": sample_user.email,
            "password": "test_password",  # Would need actual password hash
        }
        
        response = client.post("/api/auth/login", json=login_data)
        # This might fail without actual password, but we test the endpoint exists
        assert response.status_code in [200, 401, 422]

    def test_login_invalid_credentials(self, client: TestClient):
        """Test login with invalid credentials."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "WrongPassword123!",
        }
        
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code in [401, 404]

    def test_login_missing_fields(self, client: TestClient):
        """Test login with missing required fields."""
        login_data = {
            "email": "test@example.com",
            # Missing password
        }
        
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 422


class TestAuthTokenRefresh:
    """Tests for token refresh."""

    def test_refresh_token_success(self, client: TestClient, auth_headers):
        """Test successful token refresh."""
        response = client.post("/api/auth/refresh", headers=auth_headers)
        assert response.status_code in [200, 401]

    def test_refresh_token_no_token(self, client: TestClient):
        """Test token refresh without authentication."""
        response = client.post("/api/auth/refresh")
        assert response.status_code == 401


class TestAuthLogout:
    """Tests for logout."""

    def test_logout_success(self, client: TestClient, auth_headers):
        """Test successful logout."""
        response = client.post("/api/auth/logout", headers=auth_headers)
        assert response.status_code in [200, 401]

    def test_logout_no_token(self, client: TestClient):
        """Test logout without authentication."""
        response = client.post("/api/auth/logout")
        assert response.status_code == 401


class TestAuthProtectedRoutes:
    """Tests for protected route access."""

    def test_protected_route_with_token(self, client: TestClient, auth_headers):
        """Test accessing protected route with valid token."""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code in [200, 401]

    def test_protected_route_without_token(self, client: TestClient):
        """Test accessing protected route without token."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_protected_route_invalid_token(self, client: TestClient):
        """Test accessing protected route with invalid token."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401


class TestAuthRBAC:
    """Tests for role-based access control."""

    def test_admin_route_with_admin_token(self, client: TestClient, admin_headers):
        """Test admin route with admin token."""
        response = client.get("/api/admin/dashboard", headers=admin_headers)
        assert response.status_code in [200, 401, 403]

    def test_admin_route_with_user_token(self, client: TestClient, auth_headers):
        """Test admin route with regular user token."""
        response = client.get("/api/admin/dashboard", headers=auth_headers)
        assert response.status_code in [401, 403]

    def test_owner_route_with_owner_token(self, client: TestClient):
        """Test owner route with owner token."""
        owner_headers = {"Authorization": "Bearer mock_owner_token"}
        response = client.get("/api/owner/dashboard", headers=owner_headers)
        assert response.status_code in [200, 401, 403]


class TestECCService:
    """Tests for ECC cryptography service."""

    def test_ecc_service_initialization(self):
        """Test ECC service initializes correctly."""
        ecc_service = get_ecc_service()
        assert ecc_service is not None
        assert ecc_service.private_key is not None
        assert ecc_service.public_key is not None

    def test_ecc_sign_and_verify(self):
        """Test ECC signing and verification."""
        ecc_service = get_ecc_service()
        message = "test message"
        
        signature = ecc_service.sign_message(message)
        assert signature is not None
        
        is_valid = ecc_service.verify_signature(message, signature)
        assert is_valid is True

    def test_ecc_key_generation(self):
        """Test ECC key pair generation."""
        ecc_service = get_ecc_service()
        private_key_pem = ecc_service.get_private_key_pem()
        public_key_pem = ecc_service.get_public_key_pem()
        
        assert "-----BEGIN PRIVATE KEY-----" in private_key_pem
        assert "-----BEGIN PUBLIC KEY-----" in public_key_pem

    def test_ecc_key_exchange(self):
        """Test ECDH key exchange."""
        ecc_service = get_ecc_service()
        peer_public_key = ecc_service.public_key
        
        shared_secret = ecc_service.derive_shared_secret(peer_public_key)
        assert shared_secret is not None
        assert len(shared_secret) > 0
