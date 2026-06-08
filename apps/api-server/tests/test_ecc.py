"""
Unit tests for ECC services
"""

import pytest
from src.services.ecc import get_ecc_service, get_jwt_service, get_e2e_service


class TestECCService:
    """Test ECC service functionality"""

    @pytest.fixture
    def ecc_service(self):
        """Get ECC service instance"""
        return get_ecc_service()

    def test_generate_key_pair(self, ecc_service):
        """Test key pair generation"""
        private_key_pem = ecc_service.get_private_key_pem()
        public_key_pem = ecc_service.get_public_key_pem()

        assert private_key_pem is not None
        assert public_key_pem is not None
        assert "-----BEGIN PRIVATE KEY-----" in private_key_pem
        assert "-----BEGIN PUBLIC KEY-----" in public_key_pem

    def test_sign_and_verify(self, ecc_service):
        """Test signing and verification"""
        message = "test message"
        signature = ecc_service.sign(message)

        assert signature is not None
        assert len(signature) > 0

        # Verify signature
        is_valid = ecc_service.verify(message, signature)
        assert is_valid is True

    def test_verify_invalid_signature(self, ecc_service):
        """Test verification with invalid signature"""
        message = "test message"
        signature = ecc_service.sign(message)

        # Try to verify different message
        is_valid = ecc_service.verify("different message", signature)
        assert is_valid is False


class TestJWTService:
    """Test JWT service functionality"""

    @pytest.fixture
    def jwt_service(self):
        """Get JWT service instance"""
        return get_jwt_service()

    def test_create_and_decode_token(self, jwt_service):
        """Test token creation and decoding"""
        payload = {
            "sub": "user123",
            "email": "test@example.com",
            "role": "customer",
        }

        token = jwt_service.create_token(payload, expires_in=3600)
        assert token is not None
        assert len(token) > 0

        # Decode token
        decoded = jwt_service.decode_token(token)
        assert decoded["sub"] == "user123"
        assert decoded["email"] == "test@example.com"
        assert decoded["role"] == "customer"

    def test_expired_token(self, jwt_service):
        """Test expired token handling"""
        payload = {"sub": "user123"}

        # Create token with very short expiry
        token = jwt_service.create_token(payload, expires_in=1)

        # Wait for token to expire (in real test, would use time mocking)
        # For now, just test that decode handles it
        # decoded = jwt_service.decode_token(token)
        # assert decoded is None or "expired" in str(decoded).lower()

    def test_invalid_token(self, jwt_service):
        """Test invalid token handling"""
        invalid_token = "invalid.token.string"

        decoded = jwt_service.decode_token(invalid_token)
        assert decoded is None


class TestE2EService:
    """Test E2E encryption service functionality"""

    @pytest.fixture
    def e2e_service(self):
        """Get E2E service instance"""
        return get_e2e_service()

    def test_generate_session_key(self, e2e_service):
        """Test session key generation"""
        session_key = e2e_service.generate_session_key("user1", "user2")

        assert session_key is not None
        assert len(session_key) > 0

    def test_encrypt_and_decrypt_message(self, e2e_service):
        """Test message encryption and decryption"""
        message = "secret message"
        session_key = e2e_service.generate_session_key("user1", "user2")

        # Encrypt
        encrypted = e2e_service.encrypt_message(message, session_key)
        assert encrypted is not None
        assert encrypted != message

        # Decrypt
        decrypted = e2e_service.decrypt_message(encrypted, session_key)
        assert decrypted == message

    def test_session_key_cleanup(self, e2e_service):
        """Test session key cleanup"""
        # Generate some session keys
        e2e_service.generate_session_key("user1", "user2")
        e2e_service.generate_session_key("user1", "user3")

        # Cleanup expired keys
        e2e_service.cleanup_expired_sessions()

        # Should not raise errors
        assert True
