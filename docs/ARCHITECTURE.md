# Architecture

## Overview

VietStore RAG là nền tảng tìm kiếm sản phẩm gần đây kết hợp AI chat interface, cho phép người dùng tìm sản phẩm bằng ngôn ngữ tự nhiên và xác định cửa hàng gần nhất.

## Main Modules

```
apps/
├── api-server/          # FastAPI backend (REST + WebSocket)
├── web-customer/        # React frontend (chat search, store cards)
├── web-owner/           # Owner portal (product management)
└── web-admin/           # Admin dashboard

packages/
├── shared-ui/           # React components (Button, Card, MapPicker)
├── shared-utils/        # Geo calc, shipping logic, validators
└── shared-db/           # SQLAlchemy models, Alembic migrations
```

## Data Flow

1. User nhập query qua ChatSearch component
2. Frontend gọi `/api/chat/search` với query + GPS location
3. Backend xử lý query, tìm trong database/vector DB
4. Backend trả về stores + products + distance
5. Frontend hiển thị StoreCards với actions (chỉ đường, thêm giỏ, chat)

## Frontend Stack

- React 18.3 + TypeScript 5.4
- Vite (build tool)
- Tailwind CSS 3.4 (styling)
- Zustand (client state)
- React Query v5 (server state, caching)
- React Router v6 (routing)
- Axios (API client)

## Backend Stack

- FastAPI 0.115 (async API framework)
- SQLAlchemy 2.0 (async ORM)
- Pydantic v2 (validation)
- PostgreSQL 16 (primary DB)
- Redis 7 (cache, sessions, pub/sub)
- SentenceTransformers (embeddings)
- Qdrant (vector search)

## Database Schema

### Core Tables

- `users` - Người dùng (customer, owner, admin)
- `stores` - Cửa hàng (location, hours, contact)
- `products` - Sản phẩm (price, stock, shelf_location)
- `categories` - Danh mục phân cấp
- `carts` / `cart_items` - Giỏ hàng
- `orders` / `order_items` - Đơn hàng
- `messages` - Chat store-user

## Important Constraints

- Mọi API đều async (FastAPI + SQLAlchemy async)
- GPS tự động detect, fallback manual input
- Cart lưu localStorage + DB sync
- Chat real-time qua WebSocket
- Shipping fee tính real-time dựa trên distance + weight
