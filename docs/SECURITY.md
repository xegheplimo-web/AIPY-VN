# Security Rules

## Secrets

Never commit:

- `.env`
- API keys
- Passwords
- Access tokens
- Private keys
- Session files
- **ECC private keys** (ECC_PRIVATE_KEY_PEM)

## ECC Cryptography Guidelines

### Key Management

- **Private Key Storage**: Store ECC_PRIVATE_KEY_PEM in environment variables or secure secret manager (AWS Secrets Manager, HashiCorp Vault)
- **Key Rotation**: Rotate ECC keys every 90 days in production
- **Key Backup**: Always backup private keys securely (encrypted at rest)
- **Never hardcode keys**: Do not commit private keys to repository

### JWT Token Security

- **Algorithm**: Uses ES256 (ECDSA with SHA-256) on P-256 curve
- **Token Expiry**: 
  - Access tokens: 1 hour
  - Refresh tokens: 7 days
  - Password reset tokens: 1 hour
- **Token Storage**: Store tokens in httpOnly cookies or secure localStorage
- **Token Blacklist**: Implement Redis-based token blacklist for logout

### End-to-End Encryption (Chat)

- **Key Exchange**: ECDH (Elliptic Curve Diffie-Hellman) for session key generation
- **Encryption**: AES-256-GCM for message encryption
- **Session Management**: Session keys stored in memory only, cleared on logout
- **Forward Secrecy**: Each chat session uses unique ephemeral keys

### API Request Signing

- **When to Sign**: High-value operations (orders > 1M VND, admin actions)
- **Algorithm**: ECDSA with SHA-256
- **Signature Headers**: Include X-Signature and X-Timestamp headers
- **Timestamp Validation**: Reject requests with timestamps > 5 minutes old
- **Replay Prevention**: Include unique nonce in signed requests

### Password Security

- **Hashing**: Bcrypt with cost factor 12
- **Requirements**: 
  - Minimum 8 characters
  - At least 1 uppercase letter
  - At least 1 lowercase letter
  - At least 1 digit
- **Reset Flow**: JWT-based reset tokens with 1-hour expiry

### Role-Based Access Control (RBAC)

- **Roles**: customer, owner, admin
- **Permissions**:
  - customer: GET, POST (own resources)
  - owner: GET, POST, PUT, DELETE (own store resources)
  - admin: Full system access
- **Middleware**: AuthMiddleware validates all protected routes

### Public Endpoints

No authentication required for:
- `/health`
- `/docs`
- `/api/chat/search`
- `/api/suggestions`
- `/api/stores` (read-only)
- `/api/products` (read-only)

### Rate Limiting

- **Default**: 200 requests per 60 seconds
- **Backend**: In-memory (development), Redis (production)
- **Sensitive Endpoints**: Stricter limits for auth endpoints

## Dangerous Actions

AI must not:

- Delete user profile or drives
- Modify registry without explanation
- Disable antivirus/firewall
- Exfiltrate credentials
- Upload private files
- Install unknown binaries silently
- **Generate or expose private keys in logs**
- **Disable ECC encryption for production**

## Dependency Safety

Before adding dependency:

1. Check if existing dependency solves the problem
2. Prefer official/popular packages
3. Avoid abandoned packages
4. Explain why package is needed
5. **For cryptography**: Use `cryptography` library (Python standard)

## Git Safety

- Work on feature branch
- Do not force push unless requested
- Do not commit secrets
- Show diff summary before commit
- **Use .gitignore for sensitive files**: `*.pem`, `*.key`, `.env`

## Security Testing

Run ECC security tests:
```bash
cd apps/api-server
uv run pytest tests/test_ecc.py -v
```

## Production Checklist

Before deploying to production:

- [ ] Set ECC_PRIVATE_KEY_PEM environment variable
- [ ] Enable Redis for token blacklist
- [ ] Configure HTTPS/TLS for all endpoints
- [ ] Enable rate limiting with Redis backend
- [ ] Set up key rotation schedule
- [ ] Configure backup for private keys
- [ ] Enable audit logging for auth events
- [ ] Review and restrict CORS origins
- [ ] Enable security headers (CSP, HSTS, X-Frame-Options)
