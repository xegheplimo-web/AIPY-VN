# AGENTS.md — AI Coding Guide for VietStore RAG

## 1. Tổng quan dự án

- Tên dự án: VietStore RAG
- Loại dự án: Full-stack e-commerce marketplace với AI search
- Mục tiêu: Nền tảng tìm kiếm sản phẩm gần đây kết hợp AI chat interface
- Stack chính: React + TypeScript + Vite (Frontend), FastAPI + SQLAlchemy (Backend)
- Package manager: pnpm (frontend), uv (Python)
- Database: PostgreSQL 16, Redis 7
- Deployment: Docker Compose (local dev)
- **Security**: ECC cryptography (ECDSA, ECDH, AES-GCM) for JWT, E2E encryption, API signing

## 2. Cấu trúc thư mục

```
vietstore-rag/
├── apps/
│   ├── api-server/          # FastAPI backend
│   ├── web-customer/        # React frontend người dùng
│   ├── web-owner/           # React frontend chủ shop
│   └── web-admin/           # React admin dashboard
├── packages/
│   ├── shared-ui/           # React components dùng chung
│   ├── shared-utils/        # Utils chung (geo, shipping)
│   └── shared-db/           # SQLAlchemy models, Alembic
├── docker-compose.yml
├── turbo.json
├── package.json
├── pyproject.toml
└── scripts/
```

## 3. Commands chuẩn

### Setup
```powershell
# Powershell (Windows)
./scripts/setup.ps1
```

### Run
```powershell
# Backend only
./scripts/run.ps1 -Service backend

# Frontend only
./scripts/run.ps1 -Service frontend

# Both
./scripts/run.ps1 -Service all
```

### Manual
```bash
# Backend
cd apps/api-server
$env:PYTHONPATH="A:\AIPY\vietstore-rag\apps\api-server"
uv run uvicorn src.main:app --reload --port 9000

# Frontend
cd apps/web-customer
npm install
npm run dev
```

## 4. Quy tắc code

- TypeScript strict mode
- Python type hints
- FastAPI auto-docs tại /docs
- SQLAlchemy 2.0 async ORM
- Tailwind CSS + shadcn/ui style
- Zustand cho client state
- React Query cho server state

## 5. Security & ECC Integration

### Authentication System

- **JWT Tokens**: Signed using ECDSA (ES256 algorithm) with P-256 curve
- **Auth Middleware**: Validates JWT tokens on protected routes
- **RBAC**: Role-based access control (customer, owner, admin)
- **Password Security**: Bcrypt hashing with cost factor 12

### ECC Services Location

- **Core Service**: `src/services/ecc.py` - All ECC operations
- **Auth API**: `src/api/auth.py` - Registration, login, token management
- **Auth Middleware**: `src/middleware/auth_middleware.py` - JWT validation
- **Tests**: `tests/test_ecc.py` - Comprehensive ECC test suite

### Security Guidelines

- **NEVER** commit private keys or secrets
- **ALWAYS** use ECC for sensitive operations (high-value orders)
- **USE** E2E encryption for chat messages
- **IMPLEMENT** proper key rotation in production
- **FOLLOW** guidelines in `docs/SECURITY.md` and `docs/ECC_GUIDE.md`

### Protected Routes

All routes except public endpoints require JWT authentication:
- Public: `/health`, `/docs`, `/api/chat/search`, `/api/stores` (read-only)
- Protected: All other routes (require `Authorization: Bearer {token}` header)

### Key Management

- Development: Keys auto-generated on startup
- Production: Set `ECC_PRIVATE_KEY_PEM` environment variable
- Key rotation: Every 90 days recommended
- Backup: Encrypt and backup private keys securely
