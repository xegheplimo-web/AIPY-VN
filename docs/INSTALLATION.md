# Installation Guide

## 1. Prerequisites

- Node.js >= 18.18.0
- Python >= 3.11
- Docker Desktop (optional but recommended)

## 2. JavaScript / TypeScript

```bash
# Install pnpm if not available
npm install -g pnpm

# Install dependencies
pnpm install
```

## 3. Python

```bash
# Install uv if not available
pip install uv

# Setup Python workspace
uv sync
```

## 4. Database

```bash
# Start PostgreSQL + Redis
docker compose up -d

# Verify
docker compose ps
```

## 5. Environment

```bash
copy .env.example .env
# Edit .env with your values
```

## 6. First Run

```bash
# Terminal 1: Backend
cd apps/api-server
uv run uvicorn src.main:app --reload --port 8000

# Terminal 2: Frontend
cd apps/web-customer
npm run dev
```

## 7. Verify

- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000
