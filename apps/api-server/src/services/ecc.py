"""
ECC (Elliptic Curve Cryptography) Service for VietStore RAG

Provides:
- ECDSA for JWT token signing and verification
- ECDH for key exchange (end-to-end encryption)
- Digital signatures for API request signing
- Secure key generation and management
"""

import os
import json
import base64
from typing import Tuple, Optional, Dict, Any
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature
import jwt


class ECCService:
    """Service for ECC cryptographic operations"""

    # Use P-256 curve (NIST) for balance of security and performance
    CURVE = ec.SECP256R1()

    def __init__(self, private_key_pem: Optional[str] = None):
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
        public_key: Optional[ec.EllipticCurvePublicKey] = None,
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
            return False
        except Exception:
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
    def encrypt_message(message: str, aes_key: bytes) -> Dict[str, str]:
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
    def decrypt_message(encrypted_data: Dict[str, str], aes_key: bytes) -> str:
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

    def create_token(self, payload: Dict[str, Any], expires_in: int = 3600) -> str:
        """
        Create JWT token signed with ECDSA.

        Args:
            payload: Token payload (will include exp, iat, jti)
            expires_in: Expiration time in seconds (default 1 hour)

        Returns:
            JWT token string
        """
        now = datetime.utcnow()

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
        self, token: str, public_key_pem: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
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
        except jwt.InvalidTokenError:
            return None
        except Exception:
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
            path: Request path
            body: Request body (empty string for GET)
            timestamp: ISO format timestamp (uses current if None)

        Returns:
            Base64-encoded signature
        """
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()

        # Create canonical request string
        canonical = f"{method}\n{path}\n{body}\n{timestamp}"

        # Sign canonical string
        signature = self.ecc.sign(canonical.encode())

        return base64.b64encode(signature).decode()

    def verify_request(
        self,
        signature: str,
        method: str,
        path: str,
        body: str = "",
        timestamp: str = None,
        public_key: Optional[ec.EllipticCurvePublicKey] = None,
    ) -> bool:
        """
        Verify API request signature.

        Args:
            signature: Base64-encoded signature
            method: HTTP method
            path: Request path
            body: Request body
            timestamp: ISO format timestamp
            public_key: Public key for verification

        Returns:
            True if signature is valid
        """
        try:
            canonical = f"{method}\n{path}\n{body}\n{timestamp}"
            signature_bytes = base64.b64decode(signature)
            return self.ecc.verify(signature_bytes, canonical.encode(), public_key)
        except Exception:
            return False


class E2EEncryptionService:
    """End-to-end encryption for chat messages using ECDH"""

    def __init__(self, ecc_service: ECCService):
        self.ecc = ecc_service
        self.session_keys: Dict[str, bytes] = {}  # session_id -> aes_key

    def generate_session_key(self, peer_public_key_bytes: bytes) -> Tuple[str, bytes]:
        """
        Generate session key for E2E encryption.

        Args:
            peer_public_key_bytes: Peer's public key in raw bytes

        Returns:
            Tuple of (session_id, aes_key)
        """
        peer_public_key = ECCService.public_key_from_bytes(peer_public_key_bytes)
        shared_secret = self.ecc.derive_shared_secret(peer_public_key)
        aes_key = ECCService.derive_aes_key(shared_secret)

        session_id = os.urandom(16).hex()
        self.session_keys[session_id] = aes_key

        return session_id, aes_key

    def encrypt_chat_message(self, message: str, session_id: str) -> Dict[str, str]:
        """
        Encrypt chat message for E2E.

        Args:
            message: Plaintext message
            session_id: Session ID for key lookup

        Returns:
            Dict with encrypted data
        """
        if session_id not in self.session_keys:
            raise ValueError("Session not found")

        aes_key = self.session_keys[session_id]
        encrypted = ECCService.encrypt_message(message, aes_key)

        return {
            "session_id": session_id,
            "ciphertext": encrypted["ciphertext"],
            "nonce": encrypted["nonce"],
        }

    def decrypt_chat_message(self, encrypted_data: Dict[str, str]) -> str:
        """
        Decrypt chat message from E2E.

        Args:
            encrypted_data: Dict with session_id, ciphertext, nonce

        Returns:
            Decrypted plaintext message
        """
        session_id = encrypted_data["session_id"]
        if session_id not in self.session_keys:
            raise ValueError("Session not found")

        aes_key = self.session_keys[session_id]
        return ECCService.decrypt_message(
            {
                "ciphertext": encrypted_data["ciphertext"],
                "nonce": encrypted_data["nonce"],
            },
            aes_key,
        )


# Global instance (will be initialized with keys from environment or storage)
_ecc_service: Optional[ECCService] = None
_jwt_service: Optional[JWTService] = None
_request_signer: Optional[APIRequestSigner] = None
_e2e_service: Optional[E2EEncryptionService] = None


def init_ecc_service(private_key_pem: Optional[str] = None) -> None:
    """Initialize global ECC services"""
    global _ecc_service, _jwt_service, _request_signer, _e2e_service

    _ecc_service = ECCService(private_key_pem)
    _jwt_service = JWTService(_ecc_service)
    _request_signer = APIRequestSigner(_ecc_service)
    _e2e_service = E2EEncryptionService(_ecc_service)


def get_ecc_service() -> ECCService:
    """Get global ECC service instance"""
    if _ecc_service is None:
        init_ecc_service()
    return _ecc_service


def get_jwt_service() -> JWTService:
    """Get global JWT service instance"""
    if _jwt_service is None:
        init_ecc_service()
    return _jwt_service


def get_request_signer() -> APIRequestSigner:
    """Get global request signer instance"""
    if _request_signer is None:
        init_ecc_service()
    return _request_signer


def get_e2e_service() -> E2EEncryptionService:
    """Get global E2E encryption service instance"""
    if _e2e_service is None:
        init_ecc_service()
    return _e2e_service
