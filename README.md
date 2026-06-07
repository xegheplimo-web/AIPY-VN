# VietStore RAG

Nền tảng thương mại điện tử kết hợp AI tìm kiếm sản phẩm gần đây.

## Tính năng chính

- 🤖 AI Chat Search - Tìm sản phẩm bằng ngôn ngữ tự nhiên
- 📍 GPS Location - Tự động xác định vị trí
- 🏪 Store Cards - Hiển thị cửa hàng với khoảng cách, giờ mở cửa, đánh giá
- 🛒 Giỏ hàng + Checkout - Thanh toán với tính phí ship
- 💬 Chat với cửa hàng - Real-time WebSocket
- 📊 Owner Portal - Quản lý sản phẩm, đơn hàng

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Backend | FastAPI, SQLAlchemy 2.0, Pydantic v2 |
| Database | PostgreSQL 16, Redis 7 |
| AI/Search | SentenceTransformers, Qdrant |
| DevOps | Docker Compose, Turborepo |

## Quick Start

### Yêu cầu

- Node.js >= 18
- Python >= 3.11
- Docker Desktop

### Setup

```powershell
# Clone và setup
./scripts/setup.ps1
```

### Run

```powershell
# Backend + Frontend
./scripts/run.ps1 -Service all
```

### API Documentation

Sau khi chạy backend, truy cập: http://127.0.0.1:9000/docs

## Cấu trúc dự án

```
vietstore-rag/
├── apps/
│   ├── api-server/          # FastAPI backend
│   ├── web-customer/        # React frontend
│   ├── web-owner/           # Owner portal
│   └── web-admin/           # Admin dashboard
├── packages/
│   ├── shared-ui/           # Components chung
│   ├── shared-utils/        # Geo, shipping logic
│   └── shared-db/           # DB models
├── scripts/                 # Automation scripts
└── docker-compose.yml
```

## License

MIT
