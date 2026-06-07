# BAO CAO THONG KE CHI TIET - VIETSTORE RAG
## (Kiem tra thuc te codebase ngay 2026-06-07)

---

## 1. DATABASE MODELS (Bang trong PostgreSQL)

### Da co (12 bang):
| # | Bang | Model file | Migration | Ghi chu |
|---|------|------------|-----------|---------|
| 1 | stores | models/store.py | Co | Day du thong tin |
| 2 | products | models/store.py | Co | Day du |
| 3 | categories | models/store.py | Co | Day du |
| 4 | product_variants | models/order.py | Co | Day du |
| 5 | users | models/user.py | Co | Day du |
| 6 | addresses | models/user.py | Co | Day du |
| 7 | carts | models/order.py | Co | Day du |
| 8 | cart_items | models/order.py | Co | Day du |
| 9 | orders | models/order.py | Co | Day du |
| 10 | order_items | models/order.py | Co | Day du |
| 11 | messages | models/chat.py | Co | Day du |
| 12 | reviews | models/review.py | Co | Day du |

### CON THIEU (khong co trong code):
| # | Bang | Ly do can | Trong spec? |
|---|------|-----------|-------------|
| 1 | oauth_accounts | Dang nhap Google/Facebook | ROADMAP ghi "Done" nhung KO co trong migration/model! |
| 2 | favorites / wishlist | Luu SP yeu thich | TODO_AI.md ghi chua lam |
| 3 | notifications | Push notification, email queue | TODO_AI.md ghi chua lam |
| 4 | push_tokens | Firebase device tokens | Chua co |
| 5 | promotions / coupons | Giam gia, voucher | Khong co trong spec ro rang |
| 6 | payment_transactions | Lich su thanh toan Momo/ZaloPay | Chi co payment_status trong orders |
| 7 | store_documents | Giay phep kinh doanh upload | API dang ky co nhung khong co bang luu |
| 8 | store_layout | Ban do ke trong cua hang | Spec co nhung khong co model |
| 9 | audit_logs | Log thay doi du lieu (admin) | Chua co |
| 10 | store_staff | Nhan vien cua hang, phan quyen | Chua co |

---

## 2. THU VIEN / DEPENDENCIES

### Backend (api-server/pyproject.toml) - Da co:
- fastapi, uvicorn, pydantic, sqlalchemy, asyncpg, alembic
- redis, python-multipart, python-jose, passlib[bcrypt]
- httpx, numpy, pillow, python-dotenv
- sentence-transformers, qdrant-client
- cryptography, pyjwt
- Dev: pytest, pytest-asyncio, pytest-cov, aiosqlite

### Backend CON THIEU:
| Thu vien | Muc dich | Ghi chu |
|----------|----------|---------|
| faster-whisper | Voice search STT | voice.py dang TODO, chua install |
| firebase-admin | Push notifications | TODO_AI.md ghi chua lam |
| momo-sdk / zalopay SDK | Thanh toan | Chi co UI, chua tich hop API |
| stripe | Thanh toan quoc te (optional) | Khong co |
| celery / rq | Background jobs (gui email, tinh toan) | Chua co |
| postgis / geoalchemy2 | Spatial query (tim gan day toi uu) | Dang dung haversine tay, chua dung PostGIS |

### Frontend web-customer - Da co:
- react, react-dom, react-router-dom, axios
- zustand, @tanstack/react-query, framer-motion
- lucide-react, clsx, tailwind-merge
- react-leaflet, leaflet
- Dev: vite, typescript, tailwindcss, eslint, prettier

### Frontend web-owner - CON THIEU nhieu:
| Thu vien | Trong web-customer | Trong web-owner | Can bo sung? |
|----------|-------------------|-----------------|--------------|
| zustand | Co | THIEU | Can neu dung state management |
| @tanstack/react-query | Co | THIEU | Can neu goi API phuc tap |
| framer-motion | Co | THIEU | Optional |
| clsx | Co | THIEU | Optional |
| prettier | Co | THIEU | Dev experience |
| eslint-plugin-* | Co | THIEU | Linting |
| node_modules | Co | **KHONG CO** | **BLOCKING - chua install** |

### Frontend web-admin - CON THIEU:
- Tuong tu web-owner: thieu zustand, react-query, framer-motion, clsx
- **node_modules KHONG CO** - chua install

---

## 3. API ENDPOINTS

### Da implement (ket noi DB that):
| Endpoint | File | Trang thai |
|----------|------|------------|
| POST /api/chat/search | search.py | ✅ SQL ILIKE + radius filter |
| GET /api/suggestions | search.py | ✅ |
| GET/POST/PUT/DELETE /api/stores/* | stores.py | ✅ Full CRUD |
| GET /api/products/:id | products.py | ✅ |
| GET /api/cart | cart.py | ✅ |
| POST /api/cart/items | cart.py | ✅ |
| PUT /api/cart/items/:id | cart.py | ✅ |
| DELETE /api/cart/items/:id | cart.py | ✅ |
| POST /api/orders | orders.py | ✅ + ECC signature check |
| POST /api/shipping/calculate | shipping.py | ✅ |
| GET/POST /api/owner/products/* | owner.py | ✅ CRUD + CSV upload |
| GET /api/admin/stats | admin.py | ✅ |
| GET /api/admin/industries | admin.py | ✅ |
| GET/POST /api/messages/* | chat.py | ✅ + ECDH key exchange |
| WS /api/ws/chat/:store_id | chat.py | ✅ In-memory broadcast |
| POST /api/auth/register | auth.py | ✅ + bcrypt |
| POST /api/auth/login | auth.py | ✅ + ECDSA JWT |
| POST /api/auth/refresh | auth.py | ✅ |

### API CON THIEU / MOCK:
| Endpoint | File | Trang thai thuc te | Ghi chu |
|----------|------|-------------------|---------|
| POST /api/voice/search | voice.py | ❌ MOCK HARD | Tra ve "Tim Panadol gan day" co dinh |
| POST /api/voice/upload | voice.py | ❌ MOCK | Chi nhan file, khong transcribe |
| GET /api/admin/match-queue | admin.py | ❌ MOCK | Tra ve [], total=0 |
| POST /api/admin/matches/:id/approve | admin.py | ❌ MOCK | Tra ve status="approved" |
| GET /api/owner/analytics/summary | owner.py | ⚠️ PARTIAL | total_orders=0, revenue=0 (mock) |
| Payment webhooks | Khong co | ❌ CHUA CO | Can Momo/ZaloPay callback |
| Push notifications | Khong co | ❌ CHUA CO | Can Firebase integration |
| Vector search | search.py | ❌ CHUA DUNG | Co Qdrant client nhung search dung SQL |

---

## 4. INIT / SETUP / CONFIG CON THIEU

| # | File/Thu muc | Trang thai | Van de |
|---|-------------|------------|--------|
| 1 | .env | ❌ KHONG TON TAI | Chi co .env.example, chua copy |
| 2 | apps/web-owner/node_modules | ❌ KHONG TON TAI | Chua pnpm install |
| 3 | apps/web-admin/node_modules | ❌ KHONG TON TAI | Chua pnpm install |
| 4 | models/__init__.py | ❌ KHONG TON TAI | Khong co file nay |
| 5 | setup.ps1 - cai owner/admin | ⚠️ THIEU | Script chi cai root + backend |
| 6 | run.ps1 - chay owner/admin | ⚠️ THIEU | Script chi chay backend + web-customer |
| 7 | turbo.json - build owner/admin | ⚠️ CO THE THIEU | Can kiem tra co include khong |
| 8 | docker-compose.prod.yml | ✅ CO | Da co nhung chua test |
| 9 | .github/workflows/ci.yml | ✅ CO | Nhung tests fail = CI do |
| 10 | eslint.config.js | ⚠️ LOI | KNOWN_ISSUE-001: ESLint 9.x conflict |

---

## 5. BUG / VAN DE DA BIET (Known Issues)

| # | Van de | File | Muc do | Ghi chu |
|---|--------|------|--------|---------|
| 1 | `memo` chua import | ChatSearch.tsx:76 | 🔴 HIGH | StoreCard dung `memo` nhung khong import tu React. Runtime crash. |
| 2 | Tests fail hoan toan | tests/ | 🔴 HIGH | Doi PostgreSQL running, khong co SQLite test DB |
| 3 | Seed data encoding loi | seed.py | 🟡 MED | "Thu?c & Du?c ph?m" - tieng Viet bi hoi |
| 4 | WebSocket khong persistent | chat.py | 🟡 MED | In-memory only, mat du lieu khi restart server |
| 5 | Owner analytics mock | owner.py | 🟡 MED | total_orders=0, revenue=0.0 co dinh |
| 6 | Rate limiter in-memory | rate_limiter.py | 🟡 MED | Khong hoat dong khi scale multi-instance |
| 7 | shared-db export rong | shared-db/src/models/__init__.py | 🟢 LOW | Khong export gi |
| 8 | shared-ui chi co 3 component | shared-ui/src/components/ | 🟢 LOW | Button, Card, Input - chua du dung chung |

---

## 6. TOM TAT TI LE HOAN THANH THUC TE

| He thong | Hoan thanh | Con thieu | Ti le thuc te |
|----------|-----------|-----------|---------------|
| Backend API (CRUD) | 85% | Voice search mock, payment webhook, vector search chua dung | ~85% |
| Database Schema | 75% | Thieu oauth_accounts, favorites, notifications, payments | ~75% |
| Frontend Customer | 80% | Build duoc, nhung co bug memo + chua tich hop payment thuc | ~80% |
| Frontend Owner | 35% | Chua install node_modules, thieu nhieu dependencies | ~35% |
| Frontend Admin | 35% | Chua install node_modules, thieu nhieu dependencies | ~35% |
| AI / Vector Search | 15% | Co Qdrant client + embeddings service nhung chua tich hop vao search | ~15% |
| Tests | 10% | Test viet nhieu nhung khong chay duoc vi thieu DB | ~10% |
| DevOps / Deploy | 60% | Docker co, CI co nhung do tests | ~60% |
| Security / ECC | 90% | JWT, E2E encryption, API signing hoat dong | ~90% |
| **TONG CONG THUC TE** | **~55-60%** | Nhieu hon MVP nhung xa 100% | **~55-60%** |

---

## 7. CAN LAM NGAY (Uu tien)

### Tuan 1 - Fix chay duoc:
1. Tao .env tu .env.example
2. Chay docker-compose up -d (PostgreSQL + Redis + Qdrant)
3. Sua bug `ChatSearch.tsx`: them `import { memo } from 'react'`
4. pnpm install trong web-owner va web-admin
5. Chay alembic upgrade head + seed.py

### Tuan 2 - Tich hop thuc te:
6. Tich hop Qdrant + embeddings vao search.py (that su dung vector search)
7. Them model oauth_accounts (ROADMAP ghi Done nhung thieu)
8. Implement Whisper voice search that su (faster-whisper)
9. Viet test dung SQLite in-memory (aiosqlite) de tests chay duoc

### Tuan 3 - Tinh nang nang cao:
10. Tich hop Momo/ZaloPay API that
11. Firebase push notifications
12. Them bang favorites, notifications
13. Persistent WebSocket voi Redis pub/sub
