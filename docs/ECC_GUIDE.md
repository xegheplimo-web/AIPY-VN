# ECC Cryptography Guide for VietStore RAG

## Overview

VietStore RAG uses Elliptic Curve Cryptography (ECC) for:
- **JWT Token Signing**: ECDSA with ES256 algorithm
- **End-to-End Encryption**: ECDH key exchange for chat messages
- **API Request Signing**: Digital signatures for sensitive operations
- **Secure Key Management**: P-256 curve for optimal security/performance balance

## Architecture

### Components

1. **ECCService** (`src/services/ecc.py`)
   - Core ECC operations (sign, verify, key exchange)
   - Key generation and export
   - AES-GCM encryption/decryption

2. **JWTService** (`src/services/ecc.py`)
   - JWT token creation with ECDSA signing
   - Token verification with public key
   - Access and refresh token management

3. **APIRequestSigner** (`src/services/ecc.py`)
   - Request signing for sensitive operations
   - Signature verification
   - Timestamp-based replay prevention

4. **E2EEncryptionService** (`src/services/ecc.py`)
   - ECDH key exchange for chat
   - Session key management
   - Message encryption/decryption

5. **AuthMiddleware** (`src/middleware/auth_middleware.py`)
   - JWT token validation
   - Role-based access control
   - Protected route enforcement

6. **Auth API** (`src/api/auth.py`)
   - User registration and login
   - Token generation and refresh
   - Password reset flow

## Getting Started

### 1. Initialization

The ECC service is automatically initialized on application startup:

```python
from src.services.ecc import init_ecc_service, get_ecc_service

# Initialize with existing key (production)
init_ecc_service(private_key_pem=os.getenv("ECC_PRIVATE_KEY_PEM"))

# Or generate new key (development)
init_ecc_service()

# Get service instance
ecc = get_ecc_service()
```

### 2. Key Management

#### Generate New Keys

```python
from src.services.ecc import ECCService

ecc = ECCService()

# Export keys
private_key_pem = ecc.get_private_key_pem()
public_key_pem = ecc.get_public_key_pem()

# Save private key securely (NEVER commit to repo)
os.environ["ECC_PRIVATE_KEY_PEM"] = private_key_pem
```

#### Load Existing Keys

```python
from src.services.ecc import ECCService

# Load from environment
private_key_pem = os.getenv("ECC_PRIVATE_KEY_PEM")
ecc = ECCService(private_key_pem)
```

#### Export Public Key for Clients

```python
from src.services.ecc import get_ecc_service

ecc = get_ecc_service()
public_key = ecc.get_public_key_pem()

# Share with clients for JWT verification
# Available at: GET /api/auth/public-key
```

## Usage Examples

### JWT Authentication

#### Create Token

```python
from src.services.ecc import get_jwt_service

jwt_service = get_jwt_service()

# Create access token (1 hour)
payload = {
    "sub": "user123",
    "email": "user@example.com",
    "role": "customer"
}
access_token = jwt_service.create_token(payload, expires_in=3600)

# Create refresh token (7 days)
refresh_payload = {**payload, "type": "refresh"}
refresh_token = jwt_service.create_token(refresh_payload, expires_in=604800)
```

#### Verify Token

```python
from src.services.ecc import get_jwt_service

jwt_service = get_jwt_service()

# Verify token
payload = jwt_service.verify_token(token)
if payload:
    print(f"User: {payload['sub']}, Role: {payload['role']}")
else:
    print("Invalid token")
```

### API Request Signing

#### Sign Request

```python
from src.services.ecc import get_request_signer

signer = get_request_signer()

# Sign sensitive request
signature = signer.sign_request(
    method="POST",
    path="/api/orders",
    body='{"items": [...], "total": 1500000}',
    timestamp=datetime.utcnow().isoformat()
)

# Include in headers
headers = {
    "X-Signature": signature,
    "X-Timestamp": timestamp
}
```

#### Verify Request

```python
from src.services.ecc import get_request_signer

signer = get_request_signer()

is_valid = signer.verify_request(
    signature=request.headers["X-Signature"],
    method=request.method,
    path=request.url.path,
    body=await request.body(),
    timestamp=request.headers["X-Timestamp"]
)
```

### End-to-End Chat Encryption

#### Key Exchange

```python
from src.services.ecc import get_ecc_service, get_e2e_service
import base64

ecc = get_ecc_service()
e2e = get_e2e_service()

# Client generates their key pair
client_ecc = ECCService()
client_pub_bytes = client_ecc.get_public_key_bytes()
client_pub_b64 = base64.b64encode(client_pub_bytes).decode()

# Send to server: POST /api/messages/key-exchange
# Request: {"store_id": "...", "public_key": client_pub_b64}

# Server responds with its public key
server_pub_b64 = response["server_public_key"]
server_pub_bytes = base64.b64decode(server_pub_b64)

# Both derive shared secret independently
server_pub = ECCService.public_key_from_bytes(server_pub_bytes)
session_id, aes_key = e2e.generate_session_key(client_pub_bytes)
```

#### Encrypt Message

```python
from src.services.ecc import get_e2e_service

e2e = get_e2e_service()

# Encrypt message
encrypted = e2e.encrypt_chat_message(
    message="Hello, this is secret",
    session_id=session_id
)

# Send to server
# POST /api/messages
# {
#   "encrypted": true,
#   "session_id": session_id,
#   "ciphertext": encrypted["ciphertext"],
#   "nonce": encrypted["nonce"]
# }
```

#### Decrypt Message

```python
from src.services.ecc import get_e2e_service

e2e = get_e2e_service()

# Decrypt received message
decrypted = e2e.decrypt_chat_message({
    "session_id": session_id,
    "ciphertext": ciphertext,
    "nonce": nonce
})
```

## API Endpoints

### Authentication

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "phone": "+84912345678",
  "password": "SecurePass123",
  "full_name": "John Doe"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123"
}

Response:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {...}
}
```

#### Refresh Token
```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ..."
}
```

#### Get Current User
```http
GET /api/auth/me
Authorization: Bearer {access_token}
```

#### Get Public Key
```http
GET /api/auth/public-key

Response:
{
  "public_key": "-----BEGIN PUBLIC KEY-----\n...",
  "algorithm": "ES256",
  "curve": "P-256"
}
```

### Chat Encryption

#### Key Exchange
```http
POST /api/messages/key-exchange
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "store_id": "uuid",
  "public_key": "base64-encoded-public-key"
}

Response:
{
  "server_public_key": "base64-encoded-server-public-key",
  "session_id": "uuid"
}
```

#### Send Encrypted Message
```http
POST /api/messages
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "sender_id": "uuid",
  "store_id": "uuid",
  "encrypted": true,
  "session_id": "uuid",
  "ciphertext": "base64-encoded-ciphertext",
  "nonce": "base64-encoded-nonce"
}
```

## Security Best Practices

### 1. Key Storage

**DO:**
- Store private keys in environment variables
- Use secret managers (AWS Secrets Manager, HashiCorp Vault)
- Encrypt private keys at rest
- Rotate keys every 90 days

**DON'T:**
- Commit private keys to repository
- Hardcode keys in source code
- Store keys in config files
- Share keys via email/chat

### 2. Token Management

**DO:**
- Use short-lived access tokens (1 hour)
- Implement token blacklist on logout
- Store tokens in httpOnly cookies
- Validate tokens on every request

**DON'T:**
- Use long-lived access tokens
- Store tokens in localStorage without protection
- Reuse tokens across sessions
- Ignore token expiration

### 3. Request Signing

**DO:**
- Sign high-value operations (> 1M VND)
- Include timestamp in signature
- Validate timestamp freshness (< 5 min)
- Use unique nonces for replay prevention

**DON'T:**
- Sign all requests (performance overhead)
- Ignore signature validation
- Reuse signatures
- Sign without timestamp

### 4. E2E Encryption

**DO:**
- Use unique session keys per chat
- Clear session keys on logout
- Validate peer public keys
- Use authenticated encryption (AES-GCM)

**DON'T:**
- Reuse session keys across chats
- Store session keys persistently
- Skip key exchange validation
- Use unauthenticated encryption

## Testing

### Run ECC Tests

```bash
cd apps/api-server
uv run pytest tests/test_ecc.py -v
```

### Test Coverage

The test suite covers:
- Key generation and export
- ECDSA signing and verification
- ECDH key exchange
- AES-GCM encryption/decryption
- JWT token creation and verification
- API request signing
- E2E chat encryption
- Cross-key verification

## Troubleshooting

### Common Issues

#### 1. "Invalid or expired token"
- Check token expiration time
- Verify server clock is synchronized
- Ensure correct public key is used

#### 2. "Key exchange failed"
- Verify public key format (base64 encoded)
- Check curve compatibility (both using P-256)
- Ensure public key is not corrupted

#### 3. "Signature verification failed"
- Check timestamp is recent (< 5 min)
- Verify request body matches signature
- Ensure correct signing method is used

#### 4. "Decryption failed"
- Verify session_id is valid
- Check nonce and ciphertext format
- Ensure both parties derived same shared secret

## Performance Considerations

### ECC vs RSA

- **Key Size**: ECC P-256 (32 bytes) vs RSA 2048 (256 bytes)
- **Signature Size**: ECC P-256 (64 bytes) vs RSA 2048 (256 bytes)
- **Computation**: ECC is faster for signing, similar for verification
- **Security**: ECC P-256 ≈ RSA 3072 equivalent security

### Optimization Tips

1. **Cache Public Keys**: Store verified public keys in memory
2. **Reuse Sessions**: Maintain E2E sessions for chat duration
3. **Async Operations**: Use async for cryptographic operations
4. **Batch Verification**: Verify multiple signatures in parallel

## Migration Guide

### From RSA to ECDSA

If migrating from existing RSA-based JWT:

1. **Generate ECC Keys**
   ```python
   from src.services.ecc import ECCService
   ecc = ECCService()
   # Save private key securely
   ```

2. **Update Token Verification**
   ```python
   # Old: RSA
   jwt.decode(token, rsa_public_key, algorithms=["RS256"])
   
   # New: ECDSA
   from src.services.ecc import get_jwt_service
   jwt_service = get_jwt_service()
   payload = jwt_service.verify_token(token)
   ```

3. **Update Clients**
   - Fetch new public key from `/api/auth/public-key`
   - Update JWT library to support ES256
   - Test token verification

4. **Graceful Transition**
   - Support both RSA and ECDSA during transition
   - Mark tokens with algorithm in payload
   - Phase out RSA after all clients updated

## References

- [NIST Digital Signature Standard (DSS)](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.186-4.pdf)
- [RFC 7518: JSON Web Algorithms (JWA)](https://tools.ietf.org/html/rfc7518)
- [SEC 1: Elliptic Curve Cryptography](https://www.secg.org/sec1-v2.pdf)
- [AES-GCM Specification](https://csrc.nist.gov/publications/detail/sp/800-38d/final)

## Support

For issues or questions:
1. Check test suite for examples
2. Review SECURITY.md guidelines
3. Consult cryptography library documentation
4. Check GitHub issues for similar problems
