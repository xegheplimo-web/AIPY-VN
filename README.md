# VietStore RAG

Nền tảng thương mại điện tử kết hợp AI tìm kiếm sản phẩm gần đây.

## 🌟 Tính năng chính

- 🤖 **AI Chat Search** - Tìm sản phẩm bằng ngôn ngữ tự nhiên với vector search
- 📍 **GPS Location** - Tự động xác định vị trí và tính khoảng cách
- 🏪 **Store Cards** - Hiển thị cửa hàng với khoảng cách, giờ mở cửa, đánh giá
- 🛒 **Giỏ hàng + Checkout** - Thanh toán với tính phí ship tự động
- 💬 **Chat với cửa hàng** - Real-time WebSocket với E2E encryption
- 📊 **Owner Portal** - Quản lý sản phẩm, đơn hàng
- 🔒 **ECC Security** - ECDSA signing, ECDH key exchange, AES-GCM encryption

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, React Router, Zustand, React Query |
| **Backend** | FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic |
| **Database** | PostgreSQL 16, Redis 7 |
| **AI/Search** | SentenceTransformers, Qdrant Vector Database |
| **Security** | ECC Cryptography (ECDSA, ECDH, AES-GCM) |
| **DevOps** | Docker Compose, Turborepo, GitHub Actions |

## 📋 Yêu cầu hệ thống

- Node.js >= 18
- Python >= 3.11
- Docker Desktop
- PostgreSQL 16
- Redis 7
- Qdrant (optional, cho vector search)

## 🚀 Quick Start

### 1. Clone repository

```bash
git clone <repository-url>
cd vietstore-rag
```

### 2. Setup môi trường

```powershell
# Windows PowerShell
./scripts/setup.ps1
```

Hoặc thủ công:

```bash
# Backend
cd apps/api-server
uv sync

# Frontend Customer
cd apps/web-customer
npm install

# Frontend Admin
cd apps/web-admin
npm install
```

### 3. Cấu hình environment variables

Copy file `.env.example` sang `.env` và cập nhật:

```bash
cp apps/api-server/.env.example apps/api-server/.env
```

**Các biến quan trọng:**

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/vietstore

# Redis
REDIS_URL=redis://localhost:6379/0

# ECC (Tạo mới hoặc sử dụng key có sẵn)
ECC_PRIVATE_KEY_PEM=

# Environment
ENVIRONMENT=development
DEBUG=true
```

### 4. Chạy ứng dụng

```powershell
# Chạy tất cả services
./scripts/run.ps1 -Service all

# Hoặc chạy riêng lẻ
./scripts/run.ps1 -Service backend    # FastAPI on port 9000
./scripts/run.ps1 -Service frontend   # React customer on port 5173
./scripts/run.ps1 -Service admin      # React admin on port 3002
```

### 5. Database Migration

```bash
cd apps/api-server
uv run alembic upgrade head
```

### 6. Seed dữ liệu test

```bash
cd apps/api-server
uv run python src/seed.py
```

## 📚 API Documentation

Sau khi chạy backend, truy cập:
- **Swagger UI**: http://127.0.0.1:9000/docs
- **ReDoc**: http://127.0.0.1:9000/redoc
- **Health Check**: http://127.0.0.1:9000/health

## 🏗️ Cấu trúc dự án

```
vietstore-rag/
├── apps/
│   ├── api-server/          # FastAPI backend
│   │   ├── src/
│   │   │   ├── api/         # API routes
│   │   │   ├── models/      # SQLAlchemy models
│   │   │   ├── middleware/  # Custom middleware
│   │   │   ├── services/    # Business logic
│   │   │   ├── utils/       # Utilities (pagination, UUID)
│   │   │   └── config.py    # Configuration management
│   │   ├── alembic/         # Database migrations
│   │   └── tests/           # Unit tests
│   ├── web-customer/        # React frontend người dùng
│   │   ├── src/
│   │   │   ├── components/  # React components
│   │   │   ├── pages/       # Page components
│   │   │   ├── hooks/       # Custom hooks
│   │   │   └── services/    # API client
│   ├── web-admin/           # React admin dashboard
│   └── web-owner/           # React owner portal (coming soon)
├── packages/                # Shared packages (coming soon)
│   ├── shared-ui/           # Reusable components
│   ├── shared-utils/        # Shared utilities
│   └── shared-db/           # Shared database models
├── docs/                    # Documentation
├── scripts/                 # Automation scripts
└── docker-compose.yml       # Docker orchestration
```

## 🔐 Security

### ECC Cryptography

Dự án sử dụng Elliptic Curve Cryptography cho:

- **JWT Signing**: ECDSA với curve P-256 (ES256)
- **Key Exchange**: ECDH cho end-to-end encryption
- **Digital Signatures**: API request signing cho high-value orders
- **Message Encryption**: AES-GCM cho chat messages

### Authentication

- JWT tokens signed với ECDSA
- Role-based access control (RBAC)
- Password hashing với bcrypt (cost factor 12)
- Token refresh mechanism

### Protected Routes

Tất cả routes trừ public endpoints require JWT authentication:
- **Public**: `/health`, `/docs`, `/api/chat/search`, `/api/stores` (read-only)
- **Protected**: Tất cả routes khác (require `Authorization: Bearer {token}`)

## 🧪 Testing

```bash
# Backend tests
cd apps/api-server
uv run pytest

# Frontend lint
cd apps/web-customer
npm run lint

# Frontend format
npm run format
```

## 📊 Performance

### Database Indexes

Các indexes đã được thêm để tối ưu query performance:
- `idx_store_status`, `idx_store_location`, `idx_store_industry`
- `idx_product_store_id`, `idx_product_status`, `idx_product_name`
- `idx_user_email`, `idx_user_role`, `idx_user_is_active`
- `idx_order_user_id`, `idx_order_status`, `idx_order_created_at`

### Frontend Optimization

- Lazy loading cho tất cả routes
- React.memo cho components
- API response caching (5 minutes)
- Code splitting với Vite

## 🔧 Development

### Code Style

- **Backend**: Python type hints, Ruff formatter
- **Frontend**: TypeScript strict mode, ESLint, Prettier
- **Commit messages**: Conventional Commits

### Lint & Format

```bash
# Backend
cd apps/api-server
uv run ruff check .
uv run ruff format .

# Frontend Customer
cd apps/web-customer
npm run lint
npm run format:check
npm run format

# Frontend Admin
cd apps/web-admin
npm run lint
npm run format
```

## 🐛 Troubleshooting

### Database connection failed

```bash
# Kiểm tra PostgreSQL đang chạy
docker ps | grep postgres

# Kiểm tra connection string
echo $DATABASE_URL
```

### Redis connection failed

```bash
# Kiểm tra Redis đang chạy
docker ps | grep redis

# Test connection
redis-cli ping
```

### ECC key errors

```bash
# Generate new key (development only)
# Key sẽ được auto-generated khi start app
# Lưu key từ console output và set ECC_PRIVATE_KEY_PEM
```

## 📝 License

MIT

## 🤝 Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📞 Support

- **Documentation**: Xem `docs/` folder
- **Issues**: Open GitHub issue
- **Discussions**: GitHub Discussions

---

**Generated with [Devin](https://cli.devin.ai/docs)**
