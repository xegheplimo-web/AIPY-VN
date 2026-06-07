# TODO for AI Sessions

## High Priority (Tuần 1)

- [x] Hoàn thiện database schema với Alembic migrations
- [x] Tạo seed data cho testing (stores, products, categories)
- [x] Implement full chat search API với vector search (Qdrant)
- [x] Tạo Cart page component với giỏ hàng đầy đủ
- [x] Tạo Checkout flow với tính phí ship

## Medium Priority (Tuần 2)

- [x] Owner Portal - Store registration wizard
- [x] Owner Portal - Product CRUD + bulk upload
- [x] Real-time chat WebSocket hoàn chỉnh
- [x] Order tracking page
- [ ] Push notifications (Firebase)

## Low Priority (Tuần 3+)

- [ ] Payment integration (Momo, ZaloPay)
- [x] Admin dashboard với match queue
- [x] Reviews & ratings system
- [ ] Wishlist functionality
- [ ] Mobile app (React Native) hoặc PWA

## Security & ECC Integration (COMPLETED)

- [x] ECC core service implementation (ECDSA, ECDH, AES-GCM)
- [x] JWT token signing with ECDSA (ES256)
- [x] Authentication API (register, login, token refresh)
- [x] Auth middleware with RBAC
- [x] API request signing for sensitive operations
- [x] End-to-end encryption for chat messages
- [x] Key management system
- [x] Password hashing with bcrypt
- [x] Password reset flow
- [x] ECC security tests
- [x] Security documentation (SECURITY.md, ECC_GUIDE.md)

## Completed

- [x] Monorepo structure với Turbo
- [x] Docker Compose (PostgreSQL + Redis)
- [x] FastAPI backend với SQLAlchemy models
- [x] React frontend với ChatSearch component
- [x] StoreCard component với distance calculation
- [x] Setup scripts (PowerShell)
- [x] Full authentication system with ECC
- [x] End-to-end encrypted chat
- [x] API request signing
- [x] Comprehensive security documentation
