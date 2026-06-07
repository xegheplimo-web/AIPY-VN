# Architecture Decision Records

## ADR-001: Monorepo + Turborepo

- Date: 2025-01-15
- Context: Cần quản lý nhiều app (customer, owner, admin) + shared code
- Decision: Dùng Monorepo với Turborepo để build incremental
- Alternatives: Polyrepo (tách repo riêng)
- Consequences: Code dùng chung 1 chỗ, build riêng từng app, CI/CD tập trung

## ADR-002: FastAPI + SQLAlchemy 2.0 Async

- Date: 2025-01-15
- Context: Backend cần async, type-safe, auto-docs
- Decision: FastAPI + Pydantic v2 + SQLAlchemy 2.0 async
- Alternatives: Django, Flask, Express.js
- Consequences: Auto-docs, async DB, type safety, Python ecosystem AI-ready

## ADR-003: React + Vite (không Next.js)

- Date: 2025-01-15
- Context: Frontend đơn giản, không cần SSR ban đầu
- Decision: React 18 + TypeScript + Vite
- Alternatives: Next.js 14, Vue, Svelte
- Consequences: Nhanh, nhẹ, dễ migrate sang Next.js sau nếu cần SSR

## ADR-004: PostgreSQL + Redis

- Date: 2025-01-15
- Context: Cần relational DB + cache/real-time
- Decision: PostgreSQL 16 (primary) + Redis 7 (cache, pub/sub)
- Alternatives: MongoDB, MySQL, SQLite
- Consequences: Mạnh cho geospatial, JSONB, ACID transactions

## ADR-005: Vector Search với Qdrant

- Date: 2025-01-15
- Context: AI search cần semantic similarity
- Decision: Qdrant (self-hosted) + SentenceTransformers
- Alternatives: Pinecone, Weaviate, Milvus
- Consequences: Self-hosted, Rust-based, fast, compatible với Docker Compose
