# KIEM TRA TOAN BO DU AN - CON THIEU NHUNG GI
## VietStore RAG - Cap nhat sau quet toan bo codebase (2026-06-07)

---

## 1. BACKEND (apps/api-server/src) - 32 file .py

### Da co day du:
| Thanh phan | File | Trang thai |
|------------|------|------------|
| API Routers | 12 file (search, stores, products, cart, orders, shipping, chat, owner, admin, voice, auth) | Day du CRUD |
| Middleware | 6 file (auth, error, logging, rate_limit, validation) | Day du |
| Services | 3 file (ecc.py, geo.py, llm.py) | Day du |
| Utils | 3 file (pagination, uuid) | Co ban |
| Core | main.py, db.py, config.py, cache.py, embeddings.py, vector_db.py, seed.py, verify_db.py | Day du |

### Backend CON THIEU:
| Thu | Thanh phan | Mo ta | Muc do |
|-----|-----------|-------|--------|
| 1 | **Models __init__.py** | Khong co file models/__init__.py de export | Thieu |
| 2 | **Payment API** | Khong co router payment.py (chi co payment_method string trong orders) | Thieu |
| 3 | **Notification API** | Khong co router notifications.py | Thieu |
| 4 | **Wishlist/Favorites API** | Khong co router | Thieu |
| 5 | **Upload/Image processing** | Co pillow dependency nhung khong co service xu ly anh | Chua dung |
| 6 | **Background Jobs** | Khong co Celery/ARQ integration (du co Redis) | Thieu |
| 7 | **WebSocket persistent** | In-memory broadcast, chua dung Redis pub/sub | Can cai thien |
| 8 | **API versioning** | Routers co prefix /api/v1 nhung chua co version management thuc su | Co ban |
| 9 | **API Documentation tags** | Co tags=[...] nhung chua co mo ta chi tiet | Co ban |

---

## 2. FRONTEND - 43 file .tsx/.ts

### web-customer (27 file) - Da co:
- 7 pages: Home, Cart, Checkout, StoreDetail, ProductDetail, OrderTracking, UserProfile
- 7 components: ChatSearch, StoreCard, SearchResults, MapEmbed, VoiceSearchButton, Header, Layout, LoadingSpinner, ErrorMessage
- 5 hooks: useSearch, useCart, useOrders, useProduct, useStore
- 3 validations: checkout.ts, user.ts, index.ts (dung zod!)
- services/api.ts

### web-customer CON THIEU:
| Thu | Thanh phan | Mo ta |
|-----|-----------|-------|
| 1 | **shadcn/ui components** | Chua cai dat shadcn/ui du spec de cap den |
| 2 | **Error Boundary** | Khong co React Error Boundary |
| 3 | **PWA config** | Khong co vite-plugin-pwa, manifest.json |
| 4 | **i18n** | Khong co da ngon ngu (chi tieng Viet cung) |
| 5 | **E2E Test** | Khong co Playwright/Cypress |
| 6 | **Unit Test** | Khong co Vitest/Jest setup |
| 7 | **Storybook** | Khong co |
| 8 | **Analytics** | Khong co Google Analytics/Plausible script |

### web-owner (8 file) - CON THIEU NHIEU:
| Thu | Thanh phan | Mo ta |
|-----|-----------|-------|
| 1 | **Hooks** | Khong co hook nao (useState thuan trong pages) |
| 2 | **Components** | Khong co components/ folder - code truc tiep trong pages |
| 3 | **Validations** | Khong co zod schemas |
| 4 | **Analytics dashboard** | Page co nhung chua co charts/bieu do |
| 5 | **CSV upload component** | Co API nhung UI chua co component rieng |
| 6 | **Store settings** | Khong co trang cai dat cua hang |
| 7 | **Staff management** | Khong co quan ly nhan vien |

### web-admin (8 file) - CON THIEU NHIEU:
| Thu | Thanh phan | Mo ta |
|-----|-----------|-------|
| 1 | **Hooks** | Khong co |
| 2 | **Components** | Khong co components/ folder |
| 3 | **Charts/Analytics** | Khong co charts |
| 4 | **Audit logs** | Khong co trang xem log |
| 5 | **System settings** | Khong co cau hinh he thong |
| 6 | **Content management** | Khong co CMS cho categories/industries |

---

## 3. SHARED PACKAGES - 9 file

| Package | File | Trang thai | Thieu |
|---------|------|------------|-------|
| shared-db | __init__.py, base.py | Co AsyncEngine + Base | Models export rong, khong export User/Store... |
| shared-utils | __init__.py, formatters.py, geo.py, validators.py | Co ban | formatters chua co, validators co ban |
| shared-ui | Button.tsx, Card.tsx, Input.tsx | 3 component | Chua du dung, thieu nhieu component (Modal, Select, Table...) |

---

## 4. TESTS - 15 file

| File | Trang thai | Ghi chu |
|------|------------|---------|
| test_search.py | 0 pass, all ERROR | Async fixture trong sync test |
| test_api_integration.py | 0 pass, all ERROR | Sync engine voi async SQLite |
| test_stores.py | Pass/Error lan lon | Co the pass neu fix conftest |
| test_auth.py | Pass/Error lan lon | Co the pass neu fix conftest |
| test_orders.py | Pass/Error lan lon | Co the pass neu fix conftest |
| test_ecc.py | 14/19 pass (5 fail) | RawCompressed loi cryptography 48 |
| test_geo.py | 4/4 pass | OK |
| test_config.py | ~30 pass | OK |
| test_middleware_simple.py | Pass | OK (khong can DB) |
| test_middleware.py | ? | Co the loi DB |
| test_models.py | ? | Co the loi DB |
| test_ollama.py | Skip neu khong co API key | OK |
| test_utils.py | ? | Co the OK |
| conftest.py | Co fixture day du | Nhung async fixture + sync test = conflict |

### Tests CON THIEU:
| Thu | Loai test | Mo ta |
|-----|-----------|-------|
| 1 | E2E tests (frontend) | Khong co Playwright/Cypress |
| 2 | Performance tests | Khong co locust/k6 |
| 3 | Contract tests | Khong co Pact |
| 4 | Security tests | Khong co OWASP ZAP test |
| 5 | Load tests | Khong co |

---

## 5. DATABASE - 12 bang co + CON THIEU

### Da co (12 bang):
stores, products, categories, product_variants, users, addresses, carts, cart_items, orders, order_items, messages, reviews

### CON THIEU (10+ bang):
| Bang | Ly do |
|------|-------|
| oauth_accounts | OAuth login Google/Facebook |
| favorites | Wishlist san pham |
| notifications | Push + email + SMS queue |
| push_tokens | Firebase device tokens |
| payment_transactions | Lich su thanh toan chi tiet |
| store_documents | Giay phep KD upload |
| store_layout | Ban do ke trong cua hang |
| audit_logs | Log thay doi du lieu |
| store_staff | Nhan vien & phan quyen |
| promotions/coupons | Giam gia, voucher |
| conversations | Quan ly cuoc hoi thoai (hien dung conversation_id trong messages) |

---

## 6. DEVOPS & INFRASTRUCTURE

| Thanh phan | Trang thai | Thieu |
|------------|------------|-------|
| docker-compose.yml | Co (postgres+redis+qdrant) | Khong co api-server trong compose |
| docker-compose.prod.yml | Co | Chua test |
| Dockerfile | Co (api-server) | Thieu Dockerfile cho frontend |
| GitHub Actions CI | Co (.github/workflows/ci.yml) | Tests fail = CI do |
| scripts/setup.ps1 | Co | Chi cai backend + web-customer, thieu owner/admin |
| scripts/run.ps1 | Co | Chi chay backend + web-customer, thieu owner/admin |
| scripts/setup-env.ps1 | Co | Chua chay |
| scripts/check-env.ps1 | Co | Chua chay |
| scripts/update.ps1 | Co | Chua chay |
| .env | KHONG CO | Can copy tu .env.example |
| nginx config | KHONG CO | Can cho production reverse proxy |
| SSL/TLS | KHONG CO | Can Let's Encrypt hoac Cloudflare |

---

## 7. DEPENDENCIES - CON THIEU

### Backend thieu:
| Thu vien | Muc dich | Trong pyproject.toml? |
|----------|----------|---------------------|
| faster-whisper | Voice STT | Khong (!) chi co comment TODO |
| firebase-admin | Push notifications | Khong |
| celery[redis] | Background jobs | Khong |
| resend | Email API | Khong |
| pydantic-ai / llama-index | AI Agent | Khong |
| pgvector | Vector trong PostgreSQL | Khong |
| ollama | Local LLM | Khong |
| stripe | Payment quoc te | Khong |
| sentry-sdk | Error tracking | Khong |

### Frontend thieu:
| Thu vien | Muc dich | Trong package.json? |
|----------|----------|---------------------|
| shadcn/ui | UI components | Khong (!) spec noi nhung chua cai |
| @tanstack/react-table | Data tables | Khong |
| recharts | Charts | Khong |
| react-hook-form | Forms | Khong (!) du validations dung zod |
| zod (owner/admin) | Validation | Khong |
| framer-motion (owner/admin) | Animation | Khong |
| zustand (owner/admin) | State | Khong |
| @tanstack/react-query (owner/admin) | Server state | Khong |
| vite-plugin-pwa | PWA | Khong |
| @playwright/test | E2E tests | Khong |

---

## 8. AI / ML - CON THIEU

| Thanh phan | Trang thai hien tai | Can co |
|------------|-------------------|--------|
| LLM integration | Co llm.py (Ollama Cloud) nhung chua tich hop vao search | Tich hop vao search.py de generate summary thong minh |
| Vector search | Co Qdrant client + embeddings nhung search van dung SQL ILIKE | Tich hop that su |
| Voice search | Mock hoan toan | faster-whisper hoac SenseVoice |
| RAG Pipeline | Khong co | LlamaIndex hoac Pydantic AI |
| Recommendation | Khong co | Collaborative filtering hoac vector similarity |

---

## 9. BUG DA BIET (can fix)

| # | Bug | File | Muc do |
|---|-----|------|--------|
| 1 | `memo` chua import | ChatSearch.tsx | 🔴 Runtime crash |
| 2 | ECC `RawCompressed` loi cryptography 48 | ecc.py | 🔴 5 tests fail |
| 3 | Async fixture trong sync test | test_search.py, test_api_integration.py | 🔴 ~70 tests error |
| 4 | Pydantic class Config deprecated | Nhieu file API | 🟡 Warning |
| 5 | seed.py encoding tieng Viet bi loi | seed.py | 🟡 Data khong dung |
| 6 | Owner analytics mock (0 orders/revenue) | owner.py | 🟡 Khong co du lieu that |
| 7 | Admin match-queue mock | admin.py | 🟡 Tra ve [] |
| 8 | ESLint config loi | KNOWN_ISSUE-001 | 🟡 Khong lint duoc |

---

## 10. TOM TAT TOAN BO

| He thong | Co | Thieu | Ti le thuc te |
|----------|-----|-------|---------------|
| Backend API | 12 routers | Payment, Notification, Wishlist | ~80% |
| Database | 12 bang | 10+ bang | ~55% |
| Frontend Customer | 27 file | shadcn, PWA, i18n, tests | ~65% |
| Frontend Owner | 8 file | Hooks, components, validations, charts | ~35% |
| Frontend Admin | 8 file | Hooks, components, validations, charts | ~35% |
| Tests | 15 file | E2E, perf, load | ~40% pass rate |
| AI/ML | llm.py co | Chua tich hop vao search, vector chua dung | ~20% |
| DevOps | Docker, CI co | nginx, SSL, env | ~50% |
| Security | ECC, JWT, RBAC | Audit logs, rate limiter Redis | ~75% |
| Docs | 12 file | API docs chi tiet, runbook | ~60% |
| **TONG CONG** | | | **~50-55%** |

---

## 11. UU TIEN FIX

### Cap 1 - Fix ngay (chay duoc):
1. Sua bug `memo` import trong ChatSearch.tsx
2. Tao `.env` tu `.env.example`
3. Sua ECC `RawCompressed` -> `UncompressedPoint`
4. Sua test_search.py: them `@pytest.mark.asyncio` + `async def`
5. Sua test_api_integration.py: doi `create_engine` -> `create_async_engine`

### Cap 2 - Them tinh nang co ban (1-2 tuan):
6. Tich hop `llm.py` vao `search.py` (generate summary tu LLM)
7. Them `pgvector` + tich hop vector search that su
8. Cai `shadcn/ui` cho toan bo frontend
9. Them `@tanstack/react-table` cho owner/admin
10. Them `react-hook-form + zod` cho owner/admin

### Cap 3 - Production ready (1 thang):
11. Them bang `oauth_accounts`, `favorites`, `notifications`
12. Tich hop Momo/ZaloPay API
13. Them Firebase push notifications
14. Them Celery + Redis background jobs
15. Them Sentry error tracking
16. Viet E2E tests (Playwright)
17. Cai nginx + SSL config

---

*Cap nhat: 2026-06-07 - Sau quet toan bo codebase bang subagents*
