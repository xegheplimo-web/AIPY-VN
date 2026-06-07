"""
Tests for ECC cryptographic operations

Tests:
- ECC key generation and export
- ECDSA signing and verification
- ECDH key exchange
- AES-GCM encryption/decryption
- JWT token creation and verification
- API request signing
"""

import pytest
import base64
from src.services.ecc import (
    ECCService,
    JWTService,
    APIRequestSigner,
    E2EEncryptionService,
    init_ecc_service,
    get_ecc_service,
    get_jwt_service,
)


class TestECCService:
    """Test ECC core functionality"""

    def test_key_generation(self):
        """Test that keys are generated correctly"""
        ecc = ECCService()

        # Should have private and public keys
        assert ecc.private_key is not None
        assert ecc.public_key is not None

        # Keys should be exportable
        private_pem = ecc.get_private_key_pem()
        public_pem = ecc.get_public_key_pem()

        assert "-----BEGIN PRIVATE KEY-----" in private_pem
        assert "-----BEGIN PUBLIC KEY-----" in public_pem

    def test_key_from_pem(self):
        """Test loading keys from PEM"""
        ecc1 = ECCService()
        private_key_pem = ecc1.get_private_key_pem()

        # Create new instance from PEM
        ecc2 = ECCService(private_key_pem)

        # Should have same public key
        assert ecc1.get_public_key_pem() == ecc2.get_public_key_pem()

    def test_sign_and_verify(self):
        """Test ECDSA signing and verification"""
        ecc = ECCService()
        data = b"Test message for signing"

        # Sign data
        signature = ecc.sign(data)
        assert signature is not None
        assert len(signature) > 0

        # Verify signature
        is_valid = ecc.verify(signature, data)
        assert is_valid is True

        # Verify with wrong data should fail
        is_valid = ecc.verify(signature, b"Wrong data")
        assert is_valid is False

    def test_public_key_bytes(self):
        """Test public key bytes export/import"""
        ecc = ECCService()

        # Export as bytes
        pub_bytes = ecc.get_public_key_bytes()
        assert len(pub_bytes) > 0

        # Import from bytes
        pub_key = ECCService.public_key_from_bytes(pub_bytes)
        assert pub_key is not None

        # Should be able to verify with imported key
        data = b"Test data"
        signature = ecc.sign(data)
        is_valid = ecc.verify(signature, data, pub_key)
        assert is_valid is True

    def test_ecdh_key_exchange(self):
        """Test ECDH key exchange between two parties"""
        ecc1 = ECCService()
        ecc2 = ECCService()

        # Exchange public keys
        pub1_bytes = ecc1.get_public_key_bytes()
        pub2_bytes = ecc2.get_public_key_bytes()

        pub2 = ECCService.public_key_from_bytes(pub2_bytes)
        pub1 = ECCService.public_key_from_bytes(pub1_bytes)

        # Derive shared secrets
        secret1 = ecc1.derive_shared_secret(pub2)
        secret2 = ecc2.derive_shared_secret(pub1)

        # Secrets should be identical
        assert secret1 == secret2
        assert len(secret1) == 32  # P-256 produces 32-byte shared secret

    def test_aes_key_derivation(self):
        """Test AES key derivation from shared secret"""
        ecc1 = ECCService()
        ecc2 = ECCService()

        # Perform key exchange
        pub2 = ECCService.public_key_from_bytes(ecc2.get_public_key_bytes())
        shared_secret = ecc1.derive_shared_secret(pub2)

        # Derive AES key
        aes_key = ECCService.derive_aes_key(shared_secret)

        assert len(aes_key) == 32  # AES-256 key

    def test_encrypt_decrypt_message(self):
        """Test AES-GCM encryption and decryption"""
        # Generate test key
        aes_key = b"\x00" * 32  # Test key (not for production)

        message = "Secret message"

        # Encrypt
        encrypted = ECCService.encrypt_message(message, aes_key)
        assert "ciphertext" in encrypted
        assert "nonce" in encrypted

        # Decrypt
        decrypted = ECCService.decrypt_message(encrypted, aes_key)
        assert decrypted == message


class TestJWTService:
    """Test JWT service with ECDSA"""

    def test_create_token(self):
        """Test JWT token creation"""
        ecc = ECCService()
        jwt_service = JWTService(ecc)

        payload = {"sub": "user123", "email": "test@example.com", "role": "customer"}
        token = jwt_service.create_token(payload, expires_in=3600)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_token(self):
        """Test JWT token verification"""
        ecc = ECCService()
        jwt_service = JWTService(ecc)

        payload = {"sub": "user123", "email": "test@example.com", "role": "customer"}
        token = jwt_service.create_token(payload, expires_in=3600)

        # Verify token
        verified = jwt_service.verify_token(token)
        assert verified is not None
        assert verified["sub"] == "user123"
        assert verified["email"] == "test@example.com"
        assert verified["role"] == "customer"

    def test_verify_invalid_token(self):
        """Test verification of invalid token"""
        ecc = ECCService()
        jwt_service = JWTService(ecc)

        # Verify invalid token
        verified = jwt_service.verify_token("invalid.token.here")
        assert verified is None

    def test_cross_key_verification(self):
        """Test verification with different public key"""
        ecc1 = ECCService()
        ecc2 = ECCService()

        jwt_service1 = JWTService(ecc1)
        jwt_service2 = JWTService(ecc2)

        # Create token with ecc1
        payload = {"sub": "user123"}
        token = jwt_service1.create_token(payload)

        # Try to verify with ecc2 (should fail)
        verified = jwt_service2.verify_token(token, ecc2.get_public_key_pem())
        assert verified is None

        # Verify with correct key (should succeed)
        verified = jwt_service1.verify_token(token)
        assert verified is not None


class TestAPIRequestSigner:
    """Test API request signing"""

    def test_sign_request(self):
        """Test request signing"""
        ecc = ECCService()
        signer = APIRequestSigner(ecc)

        signature = signer.sign_request(
            method="POST",
            path="/api/orders",
            body='{"items": []}',
            timestamp="2024-01-01T00:00:00",
        )

        assert signature is not None
        assert isinstance(signature, str)

    def test_verify_request(self):
        """Test request verification"""
        ecc = ECCService()
        signer = APIRequestSigner(ecc)

        timestamp = "2024-01-01T00:00:00"
        signature = signer.sign_request(
            method="POST", path="/api/orders", body='{"items": []}', timestamp=timestamp
        )

        # Verify
        is_valid = signer.verify_request(
            signature=signature,
            method="POST",
            path="/api/orders",
            body='{"items": []}',
            timestamp=timestamp,
        )

        assert is_valid is True

    def test_verify_tampered_request(self):
        """Test verification of tampered request"""
        ecc = ECCService()
        signer = APIRequestSigner(ecc)

        timestamp = "2024-01-01T00:00:00"
        signature = signer.sign_request(
            method="POST", path="/api/orders", body='{"items": []}', timestamp=timestamp
        )

        # Verify with tampered body
        is_valid = signer.verify_request(
            signature=signature,
            method="POST",
            path="/api/orders",
            body='{"items": ["tampered"]}',
            timestamp=timestamp,
        )

        assert is_valid is False


class TestE2EEncryptionService:
    """Test end-to-end encryption service"""

    def test_generate_session_key(self):
        """Test session key generation"""
        ecc = ECCService()
        e2e = E2EEncryptionService(ecc)

        # Simulate peer public key
        peer_ecc = ECCService()
        peer_pub_pem = peer_ecc.get_public_key_pem()

        # Generate session key with provided session_id
        session_id = "test_session_123"
        encrypted_key = e2e.generate_session_key(peer_pub_pem, session_id)

        assert encrypted_key is not None
        assert session_id in e2e.session_keys
        assert e2e.session_keys[session_id] is not None
        assert len(e2e.session_keys[session_id]) == 32

    def test_encrypt_decrypt_chat_message(self):
        """Test chat message encryption/decryption"""
        ecc = ECCService()
        e2e = E2EEncryptionService(ecc)

        # Setup session
        peer_ecc = ECCService()
        peer_pub_pem = peer_ecc.get_public_key_pem()
        session_id = "test_session_456"
        e2e.generate_session_key(peer_pub_pem, session_id)

        # Encrypt message
        message = "Hello, this is a secret message"
        encrypted = e2e.encrypt_message(session_id, message)

        assert "ciphertext" in encrypted
        assert "nonce" in encrypted

        # Decrypt message
        decrypted = ECCService.decrypt_message(encrypted, e2e.session_keys[session_id])
        assert decrypted == message

    def test_invalid_session(self):
        """Test encryption with invalid session"""
        ecc = ECCService()
        e2e = E2EEncryptionService(ecc)

        with pytest.raises(ValueError, match="Session not found"):
            e2e.encrypt_message("invalid_session_id", "test")


class TestGlobalServices:
    """Test global service instances"""

    def test_init_and_get_services(self):
        """Test initialization and retrieval of global services"""
        # Initialize
        init_ecc_service()

        # Get services
        ecc = get_ecc_service()
        jwt = get_jwt_service()

        assert ecc is not None
        assert jwt is not None
        assert isinstance(ecc, ECCService)
        assert isinstance(jwt, JWTService)

    def test_singleton_behavior(self):
        """Test that services are singletons"""
        init_ecc_service()

        ecc1 = get_ecc_service()
        ecc2 = get_ecc_service()

        # Should be the same instance
        assert ecc1 is ecc2
