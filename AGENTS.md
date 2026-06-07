# AGENTS.md — AI Coding Guide for VietStore RAG

## 1. Tổng quan dự án

- Tên dự án: VietStore RAG
- Loại dự án: Full-stack e-commerce marketplace với AI search
- Mục tiêu: Nền tảng tìm kiếm sản phẩm gần đây kết hợp AI chat interface
- Stack chính: React + TypeScript + Vite (Frontend), FastAPI + SQLAlchemy (Backend)
- Package manager: pnpm (frontend), uv (Python)
- Database: PostgreSQL 16, Redis 7
- Deployment: Docker Compose (local dev)

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
uv run uvicorn src.main:app --reload --port 8000

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
