# ROADMAP — VietStore RAG

> Tổng quan toàn bộ dự án: phần **ĐÃ HOÀN THÀNH** và phần **CHƯA HOÀN THÀNH** (dựa trên codebase hiện tại tại `A:\AIPY\vietstore-rag\`).

---

## PHẦN 1: ĐÃ HOÀN THÀNH (Completed)

### 1.1 Infrastructure & Dev Environment

| STT | Hạng mục | Mô tả | File chính |
|-----|----------|-------|------------|
| 1 | Monorepo Structure | Cấu trúc `apps/` + `packages/` + `turbo.json`, `pnpm` workspace | `package.json`, `turbo.json` |
| 2 | Python Toolchain | UV + Ruff + pyproject.toml root | `pyproject.toml` |
| 3 | Docker Compose | PostgreSQL 16 + Redis 7 chạy local dev | `docker-compose.yml` |
| 4 | Setup Scripts | PowerShell script khởi tạo môi trường | `scripts/setup.ps1` |
| 5 | Run Scripts | PowerShell script chạy backend/frontend/all | `scripts/run.ps1` |
| 6 | Documentation | AGENTS.md, ARCHITECTURE.md, INSTALLATION.md, TESTING.md, SECURITY.md, TODO_AI.md | `docs/*` |

### 1.2 Backend — API Server (FastAPI)

| STT | Hạng mục | Mô tả | File chính |
|-----|----------|-------|------------|
| 1 | FastAPI Scaffold | App chính với CORS, lifespan, health check | `apps/api-server/src/main.py` |
| 2 | Router Registration | Tất cả 8 module routers đã mount (search, stores, products, owner, admin, orders, cart, chat) | `apps/api-server/src/main.py` |
| 3 | SQLAlchemy Models | Store, Product, Category, User, Order models định nghĩa đầy đủ | `apps/api-server/src/models/*.py` |
| 4 | Database Connection | Async PostgreSQL engine + session factory | `apps/api-server/src/db.py` |
| 5 | Alembic Migration | Initial migration tạo toàn bộ bảng | `apps/api-server/alembic/versions/a6f8c5ce8bce_initial_migration_create_all_tables.py` |
| 6 | Seed Data Script | Script seed dữ liệu test (stores, products) | `apps/api-server/src/seed.py` |
| 7 | Verify DB Script | Script kiểm tra kết nối DB | `apps/api-server/src/verify_db.py` |
| 8 | Geo Service | Haversine distance calculation (backend) | `apps/api-server/src/services/geo.py` |
| 9 | Search API (Basic) | Endpoint `/api/chat/search` + Pydantic models + mock data | `apps/api-server/src/api/search.py` |
| 10 | Search API (Suggestions) | Endpoint `/api/suggestions` cơ bản | `apps/api-server/src/api/search.py` |

### 1.3 Frontend — Web Customer (React + Vite + TS)

| STT | Hạng mục | Mô tả | File chính |
|-----|----------|-------|------------|
| 1 | React Scaffold | Vite + TypeScript + Tailwind CSS + React Router | `apps/web-customer/` |
| 2 | ChatSearch Component | UI chat input, message list, loading state, auto-scroll | `apps/web-customer/src/components/ChatSearch.tsx` |
| 3 | StoreCard Component | Hiển thị tên, địa chỉ, khoảng cách, sản phẩm, giá, tồn kho | `apps/web-customer/src/components/StoreCard.tsx` |
| 4 | SearchResults Component | Hiển thị danh sách kết quả từ API | `apps/web-customer/src/components/SearchResults.tsx` |
| 5 | API Client | Axios instance cơ bản, base URL config | `apps/web-customer/src/services/api.ts` |
| 6 | useSearch Hook | Hook gọi API search + quản lý state | `apps/web-customer/src/hooks/useSearch.ts` |
| 7 | Home Page | Page chính render ChatSearch | `apps/web-customer/src/pages/Home.tsx` |
| 8 | App Routing | React Router với route `/` | `apps/web-customer/src/App.tsx` |

### 1.4 DevOps & Tooling

| STT | Hạng mục | Mô tả | File chính |
|-----|----------|-------|------------|
| 1 | CodeGraph Index | Codebase đã được index bởi CodeGraph MCP | `.codegraph/` |
| 2 | Devin Config | Project config cho Devin AI sessions | `.devin/project-config.json` |

---

## PHẦN 2: CHƯA HOÀN THÀNH (Pending / In Progress)

### 2.1 Backend — Database & Core Logic (High Priority)

| STT | Hạng mục | Trạng thái | Mô tả chi tiết | Ưu tiên |
|-----|----------|------------|----------------|---------|
| 1 | **Cart API (DB Integration)** | 🔴 Stub | Chỉ trả mock JSON, chưa lưu DB thật | Cao |
| 2 | **Orders API (DB Integration)** | 🔴 Stub | Chỉ trả mock JSON, chưa lưu DB thật | Cao |
| 3 | **Stores API (DB Integration)** | 🔴 Stub | List/detail/products/layout đều mock | Cao |
| 4 | **Products API (DB Integration)** | 🔴 Stub | (Chưa kiểm tra nhưng theo pattern tương tự) | Cao |
| 5 | **Owner API (DB Integration)** | 🔴 Stub | Đăng ký cửa hàng, upload SP chưa thực | Cao |
| 6 | **Admin API (DB Integration)** | 🔴 Stub | Dashboard, match queue chưa thực | Cao |
| 7 | **Chat API (DB Integration)** | 🔴 Stub | Lịch sử chat, context chưa thực | Cao |
| 8 | **Vector Search (Qdrant/Typesense)** | 🔴 Chưa có | Search hiện chỉ mock, chưa kết nối vector DB | Cao |
| 9 | **Authentication & Authorization** | 🔴 Chưa có | JWT, OAuth, phân quyền user/store/admin | Cao |
| 10 | **PostGIS Integration** | 🔴 Chưa có | Tính khoảng cách bằng PostGIS thay vì Python | Trung bình |

### 2.2 Backend — E-commerce Features (High Priority)

| STT | Hạng mục | Trạng thái | Mô tả chi tiết | Ưu tiên |
|-----|----------|------------|----------------|---------|
| 1 | **Shipping Calculator** | 🔴 Chưa có | `/api/shipping/calculate` — tính phí ship theo km, cân nặng | Cao |
| 2 | **Inventory Management** | 🔴 Chưa có | Cập nhật tồn kho real-time khi đặt hàng | Cao |
| 3 | **Order Confirmation Flow** | 🔴 Chưa có | Xác nhận đơn, gửi noti cho store | Cao |
| 4 | **Payment Integration** | 🔴 Chưa có | Momo, ZaloPay, COD gateway | Trung bình |
| 5 | **Webhook Handlers** | 🔴 Chưa có | Nhận callback từ payment provider | Trung bình |
| 6 | **Reviews & Ratings API** | 🔴 Chưa có | Đánh giá cửa hàng/sản phẩm | Thấp |
| 7 | **Wishlist API** | 🔴 Chưa có | Lưu SP yêu thích | Thấp |

### 2.3 Backend — Real-time & Communication (Medium Priority)

| STT | Hạng mục | Trạng thái | Mô tả chi tiết | Ưu tiên |
|-----|----------|------------|----------------|---------|
| 1 | **WebSocket Chat** | 🔴 Chưa có | Chat real-time giữa customer và store | Trung bình |
| 2 | **Push Notifications** | 🔴 Chưa có | Firebase Cloud Messaging cho order status | Trung bình |
| 3 | **Email/SMS Notifications** | 🔴 Chưa có | Gửi email/xác nhận đơn hàng | Trung bình |

### 2.4 Frontend — Web Customer (High Priority)

| STT | Hạng mục | Trạng thái | Mô tả chi tiết | Ưu tiên |
|-----|----------|------------|----------------|---------|
| 1 | **Cart Page** | 🔴 Chưa có | Trang giỏ hàng đầy đủ (add/remove/update quantity) | Cao |
| 2 | **Checkout Flow** | 🔴 Chưa có | Chọn delivery/pickup, nhập địa chỉ, tính ship | Cao |
| 3 | **Store Detail Page** | 🔴 Chưa có | Trang chi tiết cửa hàng: ảnh, logo, giờ mở cửa, map | Cao |
| 4 | **Product Detail Page** | 🔴 Chưa có | Trang chi tiết sản phẩm, biến thể (size/color) | Cao |
| 5 | **Order Tracking Page** | 🔴 Chưa có | Theo dõi trạng thái đơn hàng | Trung bình |
| 6 | **User Profile Page** | 🔴 Chưa có | Lịch sử đơn hàng, địa chỉ đã lưu | Trung bình |
| 7 | **Search Suggestions (Frontend)** | 🔴 Chưa có | Gợi ý khi gõ trong input | Trung bình |
| 8 | **Voice Search** | 🔴 Chưa có | Nhận diện giọng nói tiếng Việt | Thấp |
| 9 | **Filter & Sort UI** | 🔴 Chưa có | Lọc theo giá, khoảng cách, đánh giá | Trung bình |
| 10 | **Map Integration** | 🟡 Partial | Có map_url mở Google Maps nhưng chưa embed map | Trung bình |

### 2.5 Frontend — Web Owner (High Priority)

| STT | Hạng mục | Trạng thái | Mô tả chi tiết | Ưu tiên |
|-----|----------|------------|----------------|---------|
| 1 | **Web Owner Scaffold** | 🔴 Chưa có | Dự án React chưa được tạo (`apps/web-owner/`) | Cao |
| 2 | **Store Registration Wizard** | 🔴 Chưa có | Form đăng ký cửa hàng nhiều bước | Cao |
| 3 | **Product CRUD Dashboard** | 🔴 Chưa có | Thêm/sửa/xóa sản phẩm | Cao |
| 4 | **Bulk Upload CSV** | 🔴 Chưa có | Upload file CSV sản phẩm hàng loạt | Cao |
| 5 | **Order Management** | 🔴 Chưa có | Xem và xác nhận đơn hàng | Cao |
| 6 | **Inventory Dashboard** | 🔴 Chưa có | Quản lý tồn kho | Cao |
| 7 | **Revenue Analytics** | 🔴 Chưa có | Biểu đồ doanh thu, đơn hàng | Trung bình |

### 2.6 Frontend — Web Admin (Medium Priority)

| STT | Hạng mục | Trạng thái | Mô tả chi tiết | Ưu tiên |
|-----|----------|------------|----------------|---------|
| 1 | **Web Admin Scaffold** | 🔴 Chưa có | Dự án React chưa được tạo (`apps/web-admin/`) | Trung bình |
| 2 | **Admin Dashboard** | 🔴 Chưa có | Tổng quan hệ thống, metrics | Trung bình |
| 3 | **Match Queue Management** | 🔴 Chưa có | Duyệt cửa hàng đăng ký | Trung bình |
| 4 | **User Management** | 🔴 Chưa có | Quản lý tài khoản user/store | Trung bình |
| 5 | **System Analytics** | 🔴 Chưa có | Thống kê search, conversion | Thấp |

### 2.7 Deployment & CI/CD (Medium Priority)

| STT | Hạng mục | Trạng thái | Mô tả chi tiết | Ưu tiên |
|-----|----------|------------|----------------|---------|
| 1 | **GitHub Actions CI/CD** | 🔴 Chưa có | Automated test, build, deploy | Trung bình |
| 2 | **Vercel Config** | 🔴 Chưa có | Deploy frontend customer/owner/admin | Trung bình |
| 3 | **Railway/Render Config** | 🔴 Chưa có | Deploy backend FastAPI | Trung bình |
| 4 | **HTTPS/SSL** | 🔴 Chưa có | SSL certificate cho production | Trung bình |
| 5 | **Environment Management** | 🟡 Partial | Có `.env.example` nhưng chưa có docs đầy đủ | Trung bình |

### 2.8 Mobile & PWA (Low Priority)

| STT | Hạng mục | Trạng thái | Mô tả chi tiết | Ưu tiên |
|-----|----------|------------|----------------|---------|
| 1 | **PWA Support** | 🔴 Chưa có | Service worker, manifest, offline mode | Thấp |
| 2 | **React Native App** | 🔴 Chưa có | App iOS/Android | Thấp |

---

## PHẦN 3: ĐỀ XUẤT LỘ TRÌNH TRIỂN KHAI (Suggested Timeline)

### Tuần 1: Core Search + Database Real
- [ ] Kết nối Search API với DB thật (truy vấn PostgreSQL, tính khoảng cách)
- [ ] Hoàn thiện Stores API với DB integration
- [ ] Hoàn thiện Products API với DB integration
- [ ] Seed data đa dạng hơn (nhiều cửa hàng, ngành hàng)

### Tuần 2: Cart + Checkout + Shipping
- [ ] Cart API với DB (CRUD giỏ hàng theo session/user)
- [ ] Orders API với DB (tạo đơn, trạng thái)
- [ ] Shipping calculator endpoint
- [ ] Cart Page + Checkout Flow frontend
- [ ] Store Detail Page frontend

### Tuần 3: Owner Portal
- [ ] Tạo `apps/web-owner/` project scaffold
- [ ] Store Registration Wizard
- [ ] Product CRUD Dashboard
- [ ] Owner API backend (register, products CRUD)

### Tuần 4: Chat + Notifications + Polish
- [ ] Chat WebSocket (hoặc HTTP polling fallback)
- [ ] Push notifications cơ bản
- [ ] Order tracking page
- [ ] Test end-to-end, fix UX

### Tuần 5-6: Admin + Payment + Deploy
- [ ] Tạo `apps/web-admin/` project scaffold
- [ ] Admin dashboard + match queue
- [ ] Payment integration (Momo/ZaloPay test sandbox)
- [ ] CI/CD GitHub Actions
- [ ] Deploy staging environment

---

## PHẦN 4: THỐNG KÊ TỔNG QUAN

| Loại | Số lượng |
|------|----------|
| **Đã hoàn thành** | 24 hạng mục |
| **Chưa hoàn thành** | 44 hạng mục |
| **Tổng số** | 68 hạng mục |
| **Tiến độ ước tính** | ~35% |

### Phân bổ theo phase:
- **Phase 1 (MVP Core)**: Search + DB + Cart + Checkout — ~60% hoàn thành phần scaffold, cần DB integration
- **Phase 2 (E-commerce)**: Payment + Owner + Chat — ~10% hoàn thành
- **Phase 3 (Scale)**: Admin + Analytics + Deploy — ~5% hoàn thành

---

*Roadmap được tạo tự động dựa trên phân tích codebase `vietstore-rag` ngày 2026-06-07.*
