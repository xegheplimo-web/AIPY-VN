"""
ECC (Elliptic Curve Cryptography) Service for VietStore RAG

Provides:
- ECDSA for JWT token signing and verification
- ECDH for key exchange (end-to-end encryption)
- Digital signatures for API request signing
- Secure key generation and management
"""

import base64
import json
import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

logger = logging.getLogger(__name__)


class ECCService:
    """Service for ECC cryptographic operations"""

    # Use P-256 curve (NIST) for balance of security and performance
    CURVE = ec.SECP256R1()

    def __init__(self, private_key_pem: str | None = None):
        """
        Initialize ECC service with optional existing private key.

        Args:
            private_key_pem: PEM-formatted private key string. If None, generates new key.
        """
        if private_key_pem:
            self.private_key = serialization.load_pem_private_key(
                private_key_pem.encode(), password=None, backend=default_backend()
            )
        else:
            self.private_key = ec.generate_private_key(self.CURVE, default_backend())

        self.public_key = self.private_key.public_key()

    def get_private_key_pem(self) -> str:
        """Export private key in PEM format"""
        return self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()

    def get_public_key_pem(self) -> str:
        """Export public key in PEM format"""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

    def get_public_key_bytes(self) -> bytes:
        """Export public key in raw bytes format (for key exchange)"""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    @staticmethod
    def public_key_from_bytes(public_key_bytes: bytes) -> ec.EllipticCurvePublicKey:
        """Reconstruct public key from raw bytes"""
        return serialization.load_pem_public_key(
            public_key_bytes, backend=default_backend()
        )

    def sign(self, data: bytes) -> bytes:
        """
        Sign data using ECDSA.

        Args:
            data: Data to sign

        Returns:
            Signature bytes
        """
        signature = self.private_key.sign(data, ec.ECDSA(hashes.SHA256()))
        return signature

    def verify(
        self,
        signature: bytes,
        data: bytes,
        public_key: ec.EllipticCurvePublicKey | None = None,
    ) -> bool:
        """
        Verify signature using ECDSA.

        Args:
            signature: Signature to verify
            data: Original data
            public_key: Public key for verification (uses own if None)

        Returns:
            True if signature is valid
        """
        key = public_key or self.public_key
        try:
            key.verify(signature, data, ec.ECDSA(hashes.SHA256()))
            return True
        except InvalidSignature:
            logger.warning("Signature verification failed: Invalid signature")
            return False
        except Exception as e:
            logger.error(f"Signature verification error: {e}", exc_info=True)
            return False

    def derive_shared_secret(self, peer_public_key: ec.EllipticCurvePublicKey) -> bytes:
        """
        Derive shared secret using ECDH key exchange.

        Args:
            peer_public_key: Other party's public key

        Returns:
            Shared secret bytes (32 bytes for P-256)
        """
        shared_secret = self.private_key.exchange(ec.ECDH(), peer_public_key)
        return shared_secret

    @staticmethod
    def derive_aes_key(shared_secret: bytes, salt: bytes = None) -> bytes:
        """
        Derive AES-256 key from shared secret using HKDF.

        Args:
            shared_secret: ECDH shared secret
            salt: Optional salt for HKDF

        Returns:
            32-byte AES-256 key
        """
        if salt is None:
            salt = b"vietstore-rag-ecc-salt"

        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,  # AES-256
            salt=salt,
            info=b"vietstore-rag-e2e-encryption",
            backend=default_backend(),
        )
        return hkdf.derive(shared_secret)

    @staticmethod
    def encrypt_message(message: str, aes_key: bytes) -> dict[str, str]:
        """
        Encrypt message using AES-GCM.

        Args:
            message: Plaintext message
            aes_key: 32-byte AES key

        Returns:
            Dict with 'ciphertext' and 'nonce' (base64 encoded)
        """
        aesgcm = AESGCM(aes_key)
        nonce = os.urandom(12)  # 96-bit nonce for GCM
        ciphertext = aesgcm.encrypt(nonce, message.encode(), None)

        return {
            "ciphertext": base64.b64encode(ciphertext).decode(),
            "nonce": base64.b64encode(nonce).decode(),
        }

    @staticmethod
    def decrypt_message(encrypted_data: dict[str, str], aes_key: bytes) -> str:
        """
        Decrypt message using AES-GCM.

        Args:
            encrypted_data: Dict with 'ciphertext' and 'nonce' (base64 encoded)
            aes_key: 32-byte AES key

        Returns:
            Decrypted plaintext message
        """
        aesgcm = AESGCM(aes_key)
        ciphertext = base64.b64decode(encrypted_data["ciphertext"])
        nonce = base64.b64decode(encrypted_data["nonce"])

        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode()


class JWTService:
    """JWT service using ECDSA for signing"""

    def __init__(self, ecc_service: ECCService):
        self.ecc = ecc_service
        self.algorithm = "ES256"  # ECDSA with SHA-256

    def create_token(self, payload: dict[str, Any], expires_in: int = 3600) -> str:
        """
        Create JWT token signed with ECDSA.

        Args:
            payload: Token payload (will include exp, iat, jti)
            expires_in: Expiration time in seconds (default 1 hour)

        Returns:
            JWT token string
        """
        now = datetime.now(UTC)

        # Add standard claims
        token_payload = {
            **payload,
            "iat": now,
            "exp": now + timedelta(seconds=expires_in),
            "jti": os.urandom(16).hex(),  # Unique token ID
        }

        # Sign with ECDSA using private key
        private_key_pem = self.ecc.get_private_key_pem()
        token = jwt.encode(token_payload, private_key_pem, algorithm=self.algorithm)

        return token

    def verify_token(
        self, token: str, public_key_pem: str | None = None
    ) -> dict[str, Any] | None:
        """
        Verify JWT token signature.

        Args:
            token: JWT token string
            public_key_pem: Public key for verification (uses own if None)

        Returns:
            Decoded payload if valid, None otherwise
        """
        try:
            key = public_key_pem or self.ecc.get_public_key_pem()
            payload = jwt.decode(token, key, algorithms=[self.algorithm])
            return payload
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}", exc_info=True)
            return None


class APIRequestSigner:
    """Sign API requests using ECDSA for sensitive operations"""

    def __init__(self, ecc_service: ECCService):
        self.ecc = ecc_service

    def sign_request(
        self, method: str, path: str, body: str = "", timestamp: str = None
    ) -> str:
        """
        Sign API request.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path
            body: Request body (JSON string)
            timestamp: ISO timestamp (default: current time)

        Returns:
            Base64-encoded signature
        """
        if timestamp is None:
            timestamp = datetime.now(UTC).isoformat()

        # Create signature string
        signature_string = f"{method}:{path}:{body}:{timestamp}"
        signature_bytes = signature_string.encode()

        # Sign with ECDSA
        signature = self.ecc.sign(signature_bytes)

        # Return base64-encoded signature
        return base64.b64encode(signature).decode()

    def verify_request(
        self,
        signature: str,
        method: str,
        path: str,
        body: str = "",
        timestamp: str = None,
    ) -> bool:
        """
        Verify API request signature.

        Args:
            signature: Base64-encoded signature
            method: HTTP method
            path: API path
            body: Request body
            timestamp: ISO timestamp

        Returns:
            True if signature is valid
        """
        try:
            # Decode signature
            signature_bytes = base64.b64decode(signature)

            # Recreate signature string
            signature_string = f"{method}:{path}:{body}:{timestamp}"
            signature_data = signature_string.encode()

            # Verify signature
            is_valid = self.ecc.verify(signature_bytes, signature_data)
            return is_valid
        except Exception as e:
            logger.error(f"Request signature verification error: {e}", exc_info=True)
            return False


class E2EEncryptionService:
    """End-to-end encryption service for chat messages"""

    def __init__(self, ecc_service: ECCService):
        self.ecc = ecc_service
        self.session_keys: dict[str, bytes] = {}  # session_id -> aes_key
        self.session_expiry: dict[str, float] = {}

    def generate_session_key(
        self, peer_public_key_pem: str, session_id: str, ttl_seconds: int = 3600
    ) -> str:
        """
        Generate session key for E2E encryption.

        Args:
            peer_public_key_pem: Peer's public key in PEM format
            session_id: Unique session identifier
            ttl_seconds: Time-to-live for session key

        Returns:
            Base64-encoded encrypted session key
        """
        try:
            # Load peer public key
            peer_public_key = ECCService.public_key_from_bytes(
                peer_public_key_pem.encode()
            )

            # Derive shared secret
            shared_secret = self.ecc.derive_shared_secret(peer_public_key)

            # Derive AES key
            aes_key = ECCService.derive_aes_key(shared_secret)

            # Store session key
            self.session_keys[session_id] = aes_key
            self.session_expiry[session_id] = (
                datetime.now(UTC).timestamp() + ttl_seconds
            )

            # Encrypt session key with peer's public key (simplified - in production use proper key wrapping)
            encrypted_key = ECCService.encrypt_message(
                base64.b64encode(aes_key).decode(), aes_key
            )

            return json.dumps(encrypted_key)
        except Exception as e:
            logger.error(f"Session key generation error: {e}", exc_info=True)
            raise

    def encrypt_message(self, session_id: str, message: str) -> dict[str, str]:
        """
        Encrypt message for session.

        Args:
            session_id: Session identifier
            message: Plaintext message

        Returns:
            Encrypted message dict with ciphertext and nonce
        """
        try:
            # Get session key
            aes_key = self.session_keys.get(session_id)
            if not aes_key:
                raise ValueError("Session not found or expired")

            # Check expiry
            expiry = self.session_expiry.get(session_id, 0)
            if datetime.now(UTC).timestamp() > expiry:
                del self.session_keys[session_id]
                del self.session_expiry[session_id]
                raise ValueError("Session expired")

            # Encrypt message
            encrypted = ECCService.encrypt_message(message, aes_key)
            return encrypted
        except Exception as e:
            logger.error(f"Message encryption error: {e}", exc_info=True)
            raise

    def decrypt_message(self, session_id: str, encrypted_data: dict[str, str]) -> str:
        """
        Decrypt message from session.

        Args:
            session_id: Session identifier
            encrypted_data: Encrypted message dict

        Returns:
            Decrypted plaintext message
        """
        try:
            # Get session key
            aes_key = self.session_keys.get(session_id)
            if not aes_key:
                raise ValueError("Session not found or expired")

            # Check expiry
            expiry = self.session_expiry.get(session_id, 0)
            if datetime.now(UTC).timestamp() > expiry:
                del self.session_keys[session_id]
                del self.session_expiry[session_id]
                raise ValueError("Session expired")

            # Decrypt message
            decrypted = ECCService.decrypt_message(encrypted_data, aes_key)
            return decrypted
        except Exception as e:
            logger.error(f"Message decryption error: {e}", exc_info=True)
            raise

    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        now = datetime.now(UTC).timestamp()
        expired = [sid for sid, exp in self.session_expiry.items() if exp < now]
        for sid in expired:
            self.session_keys.pop(sid, None)
            self.session_expiry.pop(sid, None)
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")


# Global service instances
_ecc_service: ECCService | None = None
_jwt_service: JWTService | None = None
_request_signer: APIRequestSigner | None = None
_e2e_service: E2EEncryptionService | None = None


def init_ecc_service(private_key_pem: str | None = None) -> None:
    """Initialize global ECC service instance"""
    global _ecc_service, _jwt_service, _request_signer, _e2e_service

    _ecc_service = ECCService(private_key_pem)
    _jwt_service = JWTService(_ecc_service)
    _request_signer = APIRequestSigner(_ecc_service)
    _e2e_service = E2EEncryptionService(_ecc_service)

    logger.info("ECC service initialized")


def get_ecc_service() -> ECCService:
    """Get global ECC service instance"""
    if _ecc_service is None:
        raise RuntimeError(
            "ECC service not initialized. Call init_ecc_service() first."
        )
    return _ecc_service


def get_jwt_service() -> JWTService:
    """Get global JWT service instance"""
    if _jwt_service is None:
        raise RuntimeError(
            "JWT service not initialized. Call init_ecc_service() first."
        )
    return _jwt_service


def get_request_signer() -> APIRequestSigner:
    """Get global API request signer instance"""
    if _request_signer is None:
        raise RuntimeError(
            "Request signer not initialized. Call init_ecc_service() first."
        )
    return _request_signer


def get_e2e_service() -> E2EEncryptionService:
    """Get global E2E encryption service instance"""
    if _e2e_service is None:
        raise RuntimeError(
            "E2E service not initialized. Call init_ecc_service() first."
        )
    return _e2e_service
