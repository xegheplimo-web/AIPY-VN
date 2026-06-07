# ROADMAP -- VietStore RAG

> Thong ke toan bo du an dua tren **codebase thuc te** (`A:\AIPY\vietstore-rag\`) va **specification day du** tu `AI-SHOP.VN.md`.

---

## TONG QUAN THONG KE

| Chi so | So luong | Ghi chu |
|--------|----------|---------|
| **Tong hang muc du kien** | 120+ | Theo spec AI-SHOP.VN.md |
| **Da hoan thanh** | 28 | Co code/file thuc te trong repo |
| **Dang stub / placeholder** | 16 | File ton tai nhung logic chi mock |
| **Chua bat dau** | 76+ | Chua co file hoac chua implement |
| **Tien do uoc tinh** | ~23% | Tinh theo hang muc co the dem |

---

## PHAN 1: DA HOAN THANH (Completed) -- 28 hang muc

### 1.1 Infrastructure & Dev Environment (6)

| STT | Hang muc | File/Location | Mo ta |
|-----|----------|---------------|-------|
| 1 | Monorepo Structure | `package.json`, `turbo.json` | Cau truc `apps/` + `packages/`, pnpm workspace |
| 2 | Python Toolchain | `pyproject.toml` (root) | UV + Ruff + workspace config |
| 3 | Docker Compose | `docker-compose.yml` | PostgreSQL 16 + Redis 7 + healthchecks |
| 4 | Setup Scripts | `scripts/setup.ps1` | PowerShell khoi tao moi truong |
| 5 | Run Scripts | `scripts/run.ps1` | Chay backend/frontend/all |
| 6 | Documentation | `docs/` | AGENTS.md, ARCHITECTURE.md, INSTALLATION.md, TESTING.md, SECURITY.md, TODO_AI.md, DECISIONS.md, ENVIRONMENT.md, KNOWN_ISSUES.md |

### 1.2 Backend -- API Server (FastAPI) (12)

| STT | Hang muc | File | Mo ta |
|-----|----------|------|-------|
| 1 | FastAPI App Scaffold | `src/main.py` | App chinh voi CORS, lifespan, health check `/health` |
| 2 | Router Registration | `src/main.py` | 8 module routers da mount |
| 3 | SQLAlchemy Base & Engine | `src/db.py` | Async PostgreSQL engine, session factory, init_db |
| 4 | Store Model | `src/models/store.py` | Store, Product, Category (UUID, JSON, ARRAY, DECIMAL) |
| 5 | User Model | `src/models/user.py` | User, Role, OAuth accounts |
| 6 | Order Model | `src/models/order.py` | Order, OrderItem, OrderStatus |
| 7 | Alembic Migration | `alembic/versions/...initial_migration...` | Migration tao toan bo bang |
| 8 | Alembic Config | `alembic.ini`, `alembic/env.py` | Config migration chuan |
| 9 | Seed Data Script | `src/seed.py` | Seed stores, products, categories test |
| 10 | Verify DB Script | `src/verify_db.py` | Kiem tra ket noi DB |
| 11 | Geo Service | `src/services/geo.py` | Haversine distance calculation |
| 12 | Search API (Mock) | `src/api/search.py` | `POST /api/chat/search` + Pydantic models + mock data (2 stores) |

### 1.3 Frontend -- Web Customer (React + Vite + TS) (8)

| STT | Hang muc | File | Mo ta |
|-----|----------|------|-------|
| 1 | React Scaffold | `apps/web-customer/` | Vite + TypeScript + Tailwind CSS + React Router + Lucide icons |
| 2 | ChatSearch Component | `src/components/ChatSearch.tsx` | UI chat: input, message list, loading, auto-scroll, GPS location |
| 3 | StoreCard Component | `src/components/StoreCard.tsx` | Card hien thi ten, dia chi, khoang cach, san pham, gia, ton kho, nut chi duong |
| 4 | SearchResults Component | `src/components/SearchResults.tsx` | Danh sach ket qua tu API |
| 5 | API Client | `src/services/api.ts` | Axios instance, base URL `http://localhost:8000` |
| 6 | useSearch Hook | `src/hooks/useSearch.ts` | Hook goi `/api/chat/search`, quan ly loading/error |
| 7 | Home Page | `src/pages/Home.tsx` | Page chinh render ChatSearch |
| 8 | App Routing | `src/App.tsx` | React Router voi route `/` |

### 1.4 DevOps & Tooling (2)

| STT | Hang muc | File | Mo ta |
|-----|----------|------|-------|
| 1 | CodeGraph Index | `.codegraph/` | Codebase da index boi CodeGraph MCP |
| 2 | Devin Config | `.devin/project-config.json` | Project config cho AI sessions |

---

## PHAN 2: DANG STUB / PLACEHOLDER (File ton tai, logic mock) -- 16 hang muc

> Cac file nay da duoc tao theo spec nhung chi tra ve mock/placeholder. Can ket noi DB that.

### 2.1 Backend API Routers (8 stub)

| STT | Hang muc | File | Trang thai hien tai |
|-----|----------|------|---------------------|
| 1 | Stores API | `src/api/stores.py` | `GET /api/stores/` tra `{stores:[]}`; detail tra mock; register tra `{status:pending}` |
| 2 | Products API | `src/api/products.py` | Chua doc nhung theo pattern tuong tu -- stub |
| 3 | Owner API | `src/api/owner.py` | Chua doc nhung theo pattern tuong tu -- stub |
| 4 | Admin API | `src/api/admin.py` | Chua doc nhung theo pattern tuong tu -- stub |
| 5 | Orders API | `src/api/orders.py` | `POST /api/orders` tra `{id:order_new,status:pending}`; confirm tra `{status:confirmed}` |
| 6 | Cart API | `src/api/cart.py` | `GET /api/cart/` tra `{items:[]}`; add/update/delete tra mock |
| 7 | Chat API | `src/api/chat.py` | Chua doc nhung theo pattern tuong tu -- stub |
| 8 | Suggestions API | `src/api/search.py` | `GET /api/suggestions` -- filter hardcoded array, chua query DB |

### 2.2 Database Schema Gaps (8 stub/placeholder)

| STT | Hang muc | Vi tri | Trang thai hien tai |
|-----|----------|--------|---------------------|
| 1 | `product_variants` table | Chua tao | Theo spec can co: id, product_id, name, sku, price, stock, attributes JSONB |
| 2 | `carts` table | Chua tao | Theo spec can co: id, user_id, store_id, status |
| 3 | `cart_items` table | Chua tao | Theo spec can co: id, cart_id, product_id, variant_id, quantity, unit_price |
| 4 | `orders` table | Chua tao | Theo spec can co: order_number, delivery_method, payment, status timeline |
| 5 | `order_items` table | Chua tao | Theo spec can co: order_id, product_id, variant_id, quantity, unit_price, subtotal |
| 6 | `messages` table | Chua tao | Theo spec can co: conversation_id, sender_id, store_id, content, type, is_read |
| 7 | `reviews` table | Chua tao | Theo spec: ratings, comments cho store/product |
| 8 | Vector DB Wrapper | Chua co | Qdrant/Typesense/FAISS chua integrate |

---

## PHAN 3: CHUA HOAN THANH (Chua bat dau / chua co file) -- 76+ hang muc

### 3.1 Theo 5 Goi Trien Khai (AI-SHOP.VN.md)

| Goi | Noi dung theo spec | Trang thai thuc te | Chi tiet thieu |
|-----|--------------------|--------------------|----------------|
| **Goi 1** Monorepo Starter | Cau truc apps/ + packages/ + turbo.json + uv + ruff + Docker Compose (PG+Redis) | **80%** | Thieu `packages/shared-ui/`, `packages/shared-utils/`, `packages/shared-db/`, `apps/web-owner/`, `apps/web-admin/`, `tooling/` |
| **Goi 2** Database + Migrations | SQL schema day du + Alembic migration + Vector DB wrapper | **40%** | Migration initial co nhung thieu `product_variants`, `carts`, `cart_items`, `orders`, `order_items`, `messages`, `reviews`. Chua co Vector DB wrapper |
| **Goi 3** Core APIs (FastAPI) | `/api/chat/search` (full), `/api/cart/*`, `/api/orders`, `/api/shipping/calculate`, `/api/voice/search` | **15%** | Search co mock; Cart/Orders stub; Shipping, Voice chua co; chua ket noi DB that |
| **Goi 4** Frontend UI (React) | ChatSearch, StoreCard, Cart, Checkout + hooks + API client | **30%** | ChatSearch + StoreCard co; Cart Page, Checkout Flow, Product Detail, Store Detail chua co |
| **Goi 5** Deployment + CI/CD | GitHub Actions workflow + Vercel/Railway config + HTTPS + env management | **5%** | Chi co `.env.example`; chua co CI/CD workflows |

### 3.2 Theo Checklists trong Spec (4 checklists)

#### Checklist 1: MVP Chat Search (1 tuan) -- 7 ngay

| Ngay | Cong viec | Trang thai thuc te |
|------|-----------|--------------------|
| 1 | Tao endpoint `/api/chat/search` + vector query co ban | **Partial** -- endpoint co nhung mock, chua vector |
| 2 | Xay Chat UI component (React) + get GPS location | **Done** |
| 3 | Tich hop tinh khoang cach + filter radius | **Partial** -- khoang cach tinh frontend + backend nhung data mock |
| 4 | Them product info + price + stock vao response | **Partial** -- mock data co du fields |
| 5 | Generate map_url + test open Google Maps | **Done** -- map_url co trong mock |
| 6 | Them loading state + error handling + empty state | **Partial** -- loading co, error basic |
| 7 | Test end-to-end tren mobile + optimize performance | **Not started** |

#### Checklist 2: Kien truc Ung dung -- 4 tuan (Search -> Stores -> Owner -> Admin)

| Tuan | Cong viec | Trang thai thuc te |
|------|-----------|--------------------|
| **Tuan 1** Core Search | Setup FastAPI + PostgreSQL + Vector DB; Tao endpoint `/api/chat/search`; Xay Chat UI; Test end-to-end | **~50%** -- FastAPI + PG + Chat UI done; Vector DB + end-to-end test chua |
| **Tuan 2** Store Management | API `/api/stores/*` (CRUD); Trang Store Detail; Location picker + validation | **~15%** -- Store API stub, chua CRUD that; Store Detail page chua co |
| **Tuan 3** Owner Portal | API `/api/owner/products/*`; Trang dang ky cua hang; Bulk upload CSV | **~5%** -- Owner API stub; web-owner app chua ton tai |
| **Tuan 4** Admin + Polish | Admin dashboard + match queue; Analytics endpoints; Performance optimization + deploy | **~5%** -- Admin API stub; web-admin app chua ton tai |

#### Checklist 3: E-commerce Full Features -- 4 tuan

| Tuan | Cong viec | Trang thai thuc te |
|------|-----------|--------------------|
| **Tuan 1** Core E-commerce | Cart system (add/remove/update); Checkout flow; Order creation API; Shipping calculator | **~10%** -- Cart/Order API stub; chua co DB tables; chua co frontend pages |
| **Tuan 2** Store Features | Store detail page (anh, logo, hours); Product variants (size, color); Inventory management; Order confirmation flow | **~5%** -- Chua co page; variants table chua co |
| **Tuan 3** Communication | Chat system (WebSocket + HTTP fallback); Phone/Zalo/Email quick contact; Push notifications (order status); Review & rating system | **~5%** -- Chat API stub; WebSocket chua co |
| **Tuan 4** Payment & Polish | Payment integration (Momo, ZaloPay, COD); Order tracking page; Email/SMS notifications; Performance optimization | **~0%** -- Chua bat dau |

#### Checklist 4: Monorepo Setup -- 3 ngay

| Ngay | Cong viec | Trang thai thuc te |
|------|-----------|--------------------|
| 1 | Khoi tao Monorepo (pnpm/turbo hoac uv workspace) | **Done** |
| 2 | Di chuyen code chung vao `packages/` | **Not started** -- `packages/` trong |
| 3 | Cau hinh build rieng + CI/CD co ban | **Not started** -- chua co GitHub Actions |

### 3.3 Theo Danh sach Trang & API Mapping (11 trang)

#### A. Trang cho Nguoi dung cuoi (Customer) -- 5 trang

| STT | Trang | API can goi | Frontend status | Backend status |
|-----|-------|-------------|-----------------|----------------|
| 1 | Chat Search (Trang chu) | `POST /api/chat/search`<br>`GET /api/suggestions`<br>`POST /api/voice/search` | **Done** (ChatSearch.tsx) | **Partial** (search mock, suggestions mock, voice chua co) |
| 2 | Store Detail | `GET /api/stores/:id`<br>`GET /api/stores/:id/products`<br>`GET /api/stores/:id/layout` | **Not started** | **Stub** |
| 3 | Product Detail | `GET /api/products/:id`<br>`GET /api/products/:id/alternatives` | **Not started** | **Stub** |
| 4 | Navigation (Map) | `GET /api/stores/:id/map-url` | **Not started** | **Partial** (map_url co trong mock) |
| 5 | User Profile | `GET /api/users/:id/history`<br>`GET /api/users/:id/favorites` | **Not started** | **Not started** |

#### B. Trang cho Chu cua hang (Store Owner) -- 3 trang

| STT | Trang | API can goi | Frontend status | Backend status |
|-----|-------|-------------|-----------------|----------------|
| 6 | Store Registration | `POST /api/stores/register`<br>`POST /api/stores/validate-location`<br>`POST /api/stores/upload-docs` | **Not started** (web-owner chua ton tai) | **Stub** |
| 7 | Product Management | `GET /api/owner/products`<br>`POST /api/owner/products`<br>`PUT /api/owner/products/:id`<br>`DELETE /api/owner/products/:id`<br>`POST /api/owner/products/bulk-upload` | **Not started** | **Stub** |
| 8 | Dashboard Analytics | `GET /api/owner/analytics/summary`<br>`GET /api/owner/analytics/searches`<br>`GET /api/owner/analytics/products` | **Not started** | **Not started** |

#### C. Trang cho Admin (Quan tri he thong) -- 3 trang

| STT | Trang | API can goi | Frontend status | Backend status |
|-----|-------|-------------|-----------------|----------------|
| 9 | Admin Dashboard | `GET /api/admin/stats`<br>`GET /api/admin/recent-stores` | **Not started** (web-admin chua ton tai) | **Stub** |
| 10 | Data Match Queue | `GET /api/admin/match-queue`<br>`POST /api/admin/matches/:id/approve`<br>`POST /api/admin/matches/:id/reject` | **Not started** | **Stub** |
| 11 | Taxonomy Manager | `GET /api/admin/industries`<br>`POST /api/admin/industries`<br>`GET /api/admin/categories` | **Not started** | **Not started** |

### 3.4 Theo API Endpoints Chi tiet (~25 endpoints)

#### Module: Search & Chat (4 endpoints)

| Endpoint | Method | Mo ta | Trang thai |
|----------|--------|-------|------------|
| `/api/chat/search` | POST | Tim kiem bang chat, tra store + products | **Mock** -- hardcoded data |
| `/api/suggestions` | GET | Goi y tu khoa khi go | **Mock** -- filter hardcoded array |
| `/api/voice/search` | POST | Tim kiem bang giong noi tieng Viet | **Not started** |
| `/ws/chat/{store_id}` | WS | Real-time chat WebSocket | **Not started** |

#### Module: Stores (6 endpoints)

| Endpoint | Method | Mo ta | Trang thai |
|----------|--------|-------|------------|
| `/api/stores/` | GET | Danh sach cua hang (filter province/industry) | **Stub** -- tra `[]` |
| `/api/stores/{store_id}` | GET | Chi tiet 1 cua hang | **Stub** -- mock name |
| `/api/stores/{store_id}/products` | GET | San pham cua cua hang (phan trang) | **Stub** -- tra `[]` |
| `/api/stores/{store_id}/layout` | GET | So do ke hang (2D zones) | **Stub** -- tra `[]` |
| `/api/stores/register` | POST | Chu cua hang dang ky moi | **Stub** -- tra pending |
| `/api/stores/validate-location` | POST | Kiem tra toa do hop le | **Stub** -- tra valid |

#### Module: Products (2 endpoints)

| Endpoint | Method | Mo ta | Trang thai |
|----------|--------|-------|------------|
| `/api/products/{product_id}` | GET | Chi tiet SP + gia tai cac store | **Stub** |
| `/api/products/{product_id}/alternatives` | GET | San pham thay the tuong tu | **Not started** |

#### Module: Owner Portal (5 endpoints)

| Endpoint | Method | Mo ta | Trang thai |
|----------|--------|-------|------------|
| `/api/owner/products` | GET | Chu store xem danh sach SP | **Stub** |
| `/api/owner/products` | POST | Them san pham moi | **Stub** |
| `/api/owner/products/{product_id}` | PUT | Cap nhat SP (gia, ton kho) | **Stub** |
| `/api/owner/products/bulk-upload` | POST | Upload CSV danh sach SP | **Stub** |
| `/api/owner/analytics/summary` | GET | Thong ke: luot xem, tim kiem, doanh thu | **Stub** |

#### Module: Admin (4 endpoints)

| Endpoint | Method | Mo ta | Trang thai |
|----------|--------|-------|------------|
| `/api/admin/stats` | GET | Tong quan: stores, products, users | **Stub** |
| `/api/admin/match-queue` | GET | Danh sach store can duyet match | **Stub** |
| `/api/admin/matches/{match_id}/approve` | POST | Duyet khop seed + registered | **Stub** |
| `/api/admin/industries` | GET/POST | Quan ly nganh nghe chuan | **Not started** |

#### Module: Orders (4 endpoints)

| Endpoint | Method | Mo ta | Trang thai |
|----------|--------|-------|------------|
| `/api/orders` | POST | Tao don hang moi | **Stub** -- tra mock id |
| `/api/orders/{order_id}` | GET | Chi tiet don hang | **Stub** -- tra mock |
| `/api/users/me/orders` | GET | Lich su don hang cua user | **Stub** -- tra `[]` |
| `/api/orders/{order_id}/confirm` | POST | Chu store xac nhan don | **Stub** -- tra confirmed |

#### Module: Cart (4 endpoints)

| Endpoint | Method | Mo ta | Trang thai |
|----------|--------|-------|------------|
| `/api/cart/` | GET | Lay gio hang hien tai | **Stub** -- tra `{items:[]}` |
| `/api/cart/items` | POST | Them san pham vao gio | **Stub** -- tra mock |
| `/api/cart/items/{item_id}` | PUT | Cap nhat so luong | **Stub** -- tra mock |
| `/api/cart/items/{item_id}` | DELETE | Xoa khoi gio | **Stub** -- tra mock |

#### Module: Chat (2 endpoints)

| Endpoint | Method | Mo ta | Trang thai |
|----------|--------|-------|------------|
| `/api/stores/{store_id}/messages` | GET | Lay lich su chat voi store | **Stub** |
| `/api/messages` | POST | Gui tin nhan (HTTP fallback) | **Stub** |

#### Module: Shipping (1 endpoint)

| Endpoint | Method | Mo ta | Trang thai |
|----------|--------|-------|------------|
| `/api/shipping/calculate` | POST | Tinh phi ship: base + weight + province + method + discount | **Not started** -- logic co trong spec nhung chua implement |

### 3.5 Theo Database Schema (12+ bang theo spec)

| STT | Bang | Trang thai | Ghi chu |
|-----|------|------------|---------|
| 1 | `stores` | **Done** | Co trong initial migration |
| 2 | `products` | **Done** | Co trong initial migration |
| 3 | `categories` | **Done** | Co trong initial migration |
| 4 | `users` | **Done** | Co trong initial migration |
| 5 | `product_variants` | **Not started** | Can migration moi |
| 6 | `carts` | **Not started** | Can migration moi |
| 7 | `cart_items` | **Not started** | Can migration moi |
| 8 | `orders` | **Not started** | Can migration moi |
| 9 | `order_items` | **Not started** | Can migration moi |
| 10 | `messages` | **Not started** | Can migration moi |
| 11 | `reviews` / `ratings` | **Not started** | Theo spec Tuan 3 |
| 12 | Vector embeddings | **Not started** | Qdrant/Typesense/FAISS |

### 3.6 Theo Frontend Components

#### Web Customer -- Components can co (theo spec)

| STT | Component/Page | Trang thai | Ghi chu |
|-----|---------------|------------|---------|
| 1 | ChatSearch | **Done** | Full component voi GPS |
| 2 | StoreCard | **Done** | Card voi distance, price, stock |
| 3 | SearchResults | **Done** | List wrapper |
| 4 | **CartPage** | **Not started** | `pages/Cart.jsx` -- gio hang day du |
| 5 | **CheckoutPage** | **Not started** | `pages/Checkout.jsx` -- delivery/pickup, address, ship fee |
| 6 | **StoreDetailPage** | **Not started** | `pages/StoreDetail.jsx` -- anh, logo, hours, map, products |
| 7 | **ProductDetailPage** | **Not started** | `pages/ProductDetail.jsx` -- variants, so sanh gia |
| 8 | **OrderTrackingPage** | **Not started** | `pages/OrderTracking.jsx` -- theo doi trang thai |
| 9 | **UserProfilePage** | **Not started** | `pages/UserProfile.jsx` -- lich su, favorites |
| 10 | **ChatWithStore** | **Not started** | `pages/ChatWithStore.jsx` -- WebSocket chat + contact |
| 11 | SearchSuggestions (dropdown) | **Not started** | Goi y tu khoa khi go |
| 12 | FilterChips | **Not started** | Loc radius, price, rating |
| 13 | VoiceSearchButton | **Not started** | Nut microphone, nhan dien tieng Viet |
| 14 | MapEmbed | **Not started** | Hien thi ban do embed thay vi link redirect |
| 15 | useCart Hook | **Not started** | Quan ly gio hang (localStorage + API) |
| 16 | useStore Hook | **Not started** | SWR cache cho store detail |
| 17 | useOrders Hook | **Not started** | Lich su don hang |
| 18 | ShippingCalculator | **Not started** | Component hien thi chi tiet phi ship |

#### Web Owner -- App chua ton tai

| STT | Component/Page | Trang thai |
|-----|---------------|------------|
| 1 | Project Scaffold (`apps/web-owner/`) | **Not started** |
| 2 | StoreRegistrationWizard | **Not started** |
| 3 | ProductManagementDashboard | **Not started** |
| 4 | BulkUploadCSV | **Not started** |
| 5 | OrderManagement | **Not started** |
| 6 | InventoryDashboard | **Not started** |
| 7 | RevenueAnalytics | **Not started** |

#### Web Admin -- App chua ton tai

| STT | Component/Page | Trang thai |
|-----|---------------|------------|
| 1 | Project Scaffold (`apps/web-admin/`) | **Not started** |
| 2 | AdminDashboard (stats cards, charts) | **Not started** |
| 3 | MatchQueueTable (approve/reject) | **Not started** |
| 4 | UserManagementTable | **Not started** |
| 5 | TaxonomyManager | **Not started** |

### 3.7 Tinh nang AI / Vector Search

| STT | Tinh nang | Trang thai | Mo ta |
|-----|-----------|------------|-------|
| 1 | Intent Extraction (LLM) | **Not started** | Phan tich "Tim Panadol gan day" -> intent + location + product |
| 2 | Vector Embedding (Query) | **Not started** | Embed cau hoi user thanh vector |
| 3 | Vector Search (Product) | **Not started** | Search SP tuong dong ngu nghia trong vector DB |
| 4 | Hybrid Search (Vector + Metadata) | **Not started** | Ket hop vector similarity + filter radius/industry/stock |
| 5 | LLM Summary Generation | **Not started** | GPT/LLM tom tat ket qua thanh van ban tu nhien tieng Viet |
| 6 | Local RAG Pipeline | **Not started** | LlamaIndex orchestration: query -> extract -> search -> summarize |

### 3.8 Authentication & Security

| STT | Tinh nang | Trang thai | Mo ta |
|-----|-----------|------------|-------|
| 1 | JWT Authentication | **Not started** | Login/register, token refresh |
| 2 | OAuth (Google/Zalo/Facebook) | **Not started** | Social login |
| 3 | Role-based Access Control | **Not started** | Customer / Store Owner / Admin |
| 4 | API Rate Limiting | **Not started** | Redis-based rate limit |
| 5 | Input Validation & Sanitization | **Partial** | Pydantic models co, nhung chua day du |
| 6 | CORS Production Config | **Partial** | Chi allow localhost |

### 3.9 DevOps & Deploy

| STT | Tinh nang | Trang thai | Mo ta |
|-----|-----------|------------|-------|
| 1 | GitHub Actions CI | **Not started** | Test + lint + build on PR |
| 2 | GitHub Actions CD | **Not started** | Deploy staging/production |
| 3 | Vercel Config (web-customer) | **Not started** | `vercel.json` |
| 4 | Vercel Config (web-owner) | **Not started** | `vercel.json` |
| 5 | Vercel Config (web-admin) | **Not started** | `vercel.json` |
| 6 | Railway/Render Config (backend) | **Not started** | `railway.toml` / `render.yaml` |
| 7 | Dockerfile (api-server) | **Not started** | Multi-stage build |
| 8 | Dockerfile (frontend) | **Not started** | Nginx serve static |
| 9 | Production HTTPS | **Not started** | SSL certificate |
| 10 | Environment Secrets Management | **Partial** | `.env.example` co nhung chua co docs chi tiet |
| 11 | Monitoring (Sentry/Logtail) | **Not started** | Error tracking |
| 12 | Database Backup Strategy | **Not started** | Automated PG backup |

---

## PHAN 4: CHIEN LUOC & LO TRINH DE XUAT

### Chien luoc: "Core First -> Validate -> Scale"

Uu tien 4 tinh nang song con:
1. Chat Search + Toa do + Khoang cach (DB that)
2. Store Card + Gia + Ton kho + Nut "Chi duong"
3. Gio hang + Checkout + Tinh phi ship co ban
4. Owner Portal (dang ky cua hang + upload SP)

(Chat real-time, Payment online, Admin Match Queue se lam Phase 2)

### Lo trinh 6 tuan de xuat

| Tuan | Focus | Deliverables chinh | Metrics thanh cong |
|------|-------|--------------------|--------------------|
| **Tuan 1** | DB Integration + Search that | - Search API ket noi PostgreSQL (query stores + products + distance)<br>- Bo sung migration: carts, orders, messages<br>- Seed data da dang hon (50+ stores, 200+ products) | Query <500ms; tra dung du lieu DB; GPS hoat dong |
| **Tuan 2** | Cart + Checkout + Shipping | - Cart API voi DB (CRUD)<br>- Orders API voi DB (tao don, trang thai)<br>- `/api/shipping/calculate` endpoint<br>- CartPage + CheckoutPage frontend | Checkout flow hoan chinh; tinh ship chinh xac |
| **Tuan 3** | Owner Portal Scaffold | - Tao `apps/web-owner/` (Vite + TS)<br>- Store Registration Wizard<br>- Product CRUD Dashboard<br>- Owner API backend (register, products CRUD that) | 10 store test upload thanh cong |
| **Tuan 4** | Chat + Notifications + Polish | - Chat HTTP API hoan chinh<br>- Order tracking page<br>- Store Detail page<br>- Test end-to-end, fix UX | Search success >85%; khong loi state |
| **Tuan 5** | Admin + Auth + Shared Packages | - Tao `apps/web-admin/`<br>- JWT Auth (login/register)<br>- Admin dashboard + match queue<br>- Di chuyen shared code vao `packages/` | RBAC hoat dong; admin duyet store |
| **Tuan 6** | Payment + Deploy Staging | - Payment sandbox (Momo/ZaloPay test)<br>- GitHub Actions CI/CD<br>- Deploy staging (Railway + Vercel)<br>- Performance optimization | Retention D1 >40%; deploy staging chay duoc |

---

## PHAN 5: THONG KE TONG QUAN CHI TIET

### Theo trang thai

| Trang thai | So luong | Ty le |
|------------|----------|-------|
| Done (hoan chinh) | 28 | 23% |
| Partial / Stub | 16 | 13% |
| Not started | 76 | 63% |
| **Tong** | **120** | **100%** |

### Theo Phase

| Phase | Tien do | Ghi chu |
|-------|---------|---------|
| **Phase 1: MVP Core** (Search + DB + Cart + Checkout) | ~30% | Scaffold nhieu, logic that it |
| **Phase 2: E-commerce** (Payment + Owner + Chat) | ~10% | Chua co web-owner, payment chua bat dau |
| **Phase 3: Scale** (Admin + Analytics + Deploy) | ~5% | web-admin chua ton tai, CI/CD chua co |

### Theo he thong

| He thong | Da xong | Dang stub | Chua co | Tong |
|----------|---------|-----------|---------|------|
| Backend API | 3 | 21 | 6 | 30 |
| Database | 4 | 0 | 8 | 12 |
| Frontend Customer | 4 | 0 | 14 | 18 |
| Frontend Owner | 0 | 0 | 7 | 7 |
| Frontend Admin | 0 | 0 | 5 | 5 |
| AI / Vector | 0 | 0 | 6 | 6 |
| Auth / Security | 0 | 2 | 4 | 6 |
| DevOps / Deploy | 2 | 0 | 10 | 12 |
| Infrastructure | 6 | 0 | 4 | 10 |
| Docs / Tooling | 9 | 0 | 0 | 9 |
| **Tong cong** | **28** | **23** | **69** | **120** |

---

## PHAN 6: CAC TEP SPEC QUAN TRONG

| Tep | Mo ta | Vi tri |
|-----|-------|--------|
| `AI-SHOP.VN.md` | Specification day du nhat -- 6000+ dong, chua toan bo design: chat UI, DB schema, API endpoints, frontend components, shipping logic, checklists 4 tuan | `A:\AIPY\AI-SHOP.VN.md` |
| `ROADMAP.md` | Tai lieu nay -- thong ke tien do | `A:\AIPY\vietstore-rag\ROADMAP.md` |
| `AGENTS.md` | Huong dan AI coding cho du an | `A:\AIPY\vietstore-rag\AGENTS.md` |
| `TODO_AI.md` | Todo list cho AI sessions | `A:\AIPY\vietstore-rag\docs\TODO_AI.md` |

---

*Roadmap duoc tao tu dong dua tren phan tich codebase `vietstore-rag` va spec `AI-SHOP.VN.md` ngay 2026-06-07.*
