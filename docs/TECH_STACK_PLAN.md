# TECH STACK DECISIONS & IMPLEMENTATION PLAN

## 📊 SUMMARY OF DECISIONS

### AI Agent Framework
- **Chosen**: Pydantic AI (type-safe, lightweight, async-native)
- **Alternative**: LlamaIndex (nếu cần RAG chuyên sâu)
- **Rationale**: Project 1-5 người, không cần multi-agent phức tạp như CrewAI

### LLM Model
- **Development**: Qwen2.5-7B-Instruct hoặc Vistral-7B-Chat
- **Production VPS**: PhoGPT-4B (nhẹ, chạy tốt trên CPU)
- **API Fallback**: OpenRouter (nhiều model, giá rẻ)
- **Inference**: Ollama (dev) + vLLM (production)

### Vector Search
- **Primary**: pgvector trong PostgreSQL hiện tại
- **Secondary**: Qdrant (đã có, giữ lại cho advanced search)
- **Rationale**: Đơn giản hóa infrastructure, một DB cho cả relational + vector

### Embedding Model
- **Chosen**: BAAI/bge-m3 (1024 dimensions, đa ngôn ngữ tốt)
- **Alternative**: multilingual-e5-large
- **Rationale**: Cải thiện search quality so với all-MiniLM-L6-v2 hiện tại

### Voice Search
- **Chosen**: faster-whisper + model whisper-large-v3 hoặc SenseVoiceSmall
- **Vietnamese Option**: VietASR hoặc fine-tuned wav2vec 2.0 Viet
- **Rationale**: Thay thế mock hiện tại, hỗ trợ offline

### UI/UX Libraries
- **Forms**: react-hook-form + zod (validation type-safe)
- **Tables**: @tanstack/react-table (owner/admin dashboard)
- **Components**: shadcn/ui (consistent design system)
- **Charts**: Recharts (analytics dashboard)

### Payment Gateway
- **Chosen**: Self-implement HTTP client (httpx) cho Momo/ZaloPay
- **Rationale**: API đơn giản, không cần SDK, dễ maintain

### Notifications
- **Push**: Firebase Admin SDK
- **Background Jobs**: Celery + Redis
- **Email**: Resend hoặc SendGrid

---

## 🗓 IMPLEMENTATION TIMELINE

### Phase 1: Core AI + UX Improvements (Week 1-2)

#### Priority 1: pgvector Integration
**Impact**: 🔴 High | **Effort**: Medium | **Risk**: Low

**Steps**:
1. Enable pgvector in PostgreSQL Docker
2. Update database schema with vector columns
3. Integrate pgvector into SQLAlchemy models
4. Implement vector search endpoints
5. Migrate from Qdrant to pgvector

**Commands**:
```bash
# Enable pgvector
docker exec postgres psql -c "CREATE EXTENSION vector;"

# Install Python dependencies
uv add pgvector psycopg2-binary
```

**Files to modify**:
- `docker-compose.yml`: Add pgvector setup
- `src/models/store.py`: Add vector columns
- `src/api/search.py`: Implement pgvector search
- `alembic/versions/`: Migration files

#### Priority 2: bge-m3 Embedding Model
**Impact**: 🔴 High | **Effort**: Medium | **Risk**: Low

**Steps**:
1. Install sentence-transformers
2. Create embedding service
3. Generate embeddings for existing products
4. Update search API
5. Benchmark vs old embedding

**Commands**:
```bash
uv add sentence-transformers
```

**Files to create/modify**:
- `src/services/embedding.py`: New embedding service
- `src/api/search.py`: Update search logic
- `scripts/generate_embeddings.py`: Embedding generation script

#### Priority 3: Form Validation (react-hook-form + zod)
**Impact**: 🔴 High | **Effort**: Low | **Risk**: Low

**Steps**:
1. Install dependencies
2. Create Zod schemas
3. Implement form components
4. Replace existing forms
5. Add validation feedback

**Commands**:
```bash
cd apps/web-customer
npm install react-hook-form zod @hookform/resolvers
```

**Files to create/modify**:
- `src/lib/validations/`: Zod schemas
- `src/components/forms/`: Form components
- `src/pages/CheckoutPage.tsx`: Update form
- `src/pages/UserProfilePage.tsx`: Update form

#### Priority 4: TanStack Table (Owner/Admin)
**Impact**: 🟡 Medium | **Effort**: Medium | **Risk**: Low

**Steps**:
1. Install dependencies
2. Create reusable table component
3. Implement product table
4. Implement order table
5. Add pagination

**Commands**:
```bash
cd apps/web-owner
npm install @tanstack/react-table @tanstack/virtual recharts

cd apps/web-admin
npm install @tanstack/react-table @tanstack/virtual recharts
```

**Files to create/modify**:
- `src/components/ui/DataTable.tsx`: Reusable table
- `src/pages/owner/ProductsPage.tsx`: Product table
- `src/pages/owner/OrdersPage.tsx`: Order table

#### Priority 5: shadcn/ui Setup
**Impact**: 🟡 Medium | **Effort**: Low | **Risk**: Low

**Steps**:
1. Setup shadcn/ui for each app
2. Add needed components
3. Replace existing UI
4. Apply consistent styling

**Commands**:
```bash
cd apps/web-customer
npx shadcn-ui@latest init

cd apps/web-owner
npx shadcn-ui@latest init

cd apps/web-admin
npx shadcn-ui@latest init
```

### Phase 2: AI Agent + Voice Search (Week 3-4)

#### Priority 1: Pydantic AI Integration
**Impact**: 🔴 High | **Effort**: High | **Risk**: Medium

**Steps**:
1. Install Pydantic AI
2. Create AI agent architecture
3. Implement tool use (search, product lookup)
4. Integrate with existing API
5. Test agent responses

**Commands**:
```bash
uv add pydantic-ai
```

**Files to create/modify**:
- `src/agents/`: Agent definitions
- `src/api/agent.py`: Agent API endpoints
- `src/services/agent_orchestrator.py`: Agent orchestration

#### Priority 2: Ollama + Local LLM
**Impact**: 🔴 High | **Effort**: Medium | **Risk**: Medium

**Steps**:
1. Install Ollama separately
2. Pull chosen model (Qwen2.5-7B or Vistral-7B)
3. Configure Ollama integration
4. Test local inference
5. Implement fallback to cloud API

**Commands**:
```bash
# Ollama setup (separate installation)
ollama pull qwen2.5:7b
# or
ollama pull vistral:7b
```

**Files to create/modify**:
- `src/services/llm.py`: LLM service wrapper
- `src/config.py`: Add Ollama configuration
- `.env`: Add Ollama URL

#### Priority 3: faster-whisper Voice Search
**Impact**: 🟡 Medium | **Effort**: Medium | **Risk**: Low

**Steps**:
1. Install faster-whisper
2. Implement voice-to-text
3. Integrate with search API
4. Add voice UI component
5. Test Vietnamese recognition

**Commands**:
```bash
uv add faster-whisper
```

**Files to create/modify**:
- `src/services/voice.py`: Voice STT service
- `src/api/voice.py`: Voice API endpoints
- `apps/web-customer/src/components/VoiceSearch.tsx`: Voice UI

#### Priority 4: Firebase Push Notifications
**Impact**: 🟡 Medium | **Effort**: Medium | **Risk**: Low

**Steps**:
1. Install Firebase Admin SDK
2. Configure Firebase project
3. Implement push service
4. Add device token management
5. Test push notifications

**Commands**:
```bash
uv add firebase-admin
```

**Files to create/modify**:
- `src/services/push.py`: Push notification service
- `src/api/push.py`: Push API endpoints
- `.env`: Add Firebase credentials

### Phase 3: Scale & Production (Week 5+)

#### Priority 1: Celery + Redis Background Jobs
**Impact**: 🟡 Medium | **Effort**: High | **Risk**: Medium

**Steps**:
1. Install Celery and Redis
2. Configure Celery app
3. Create background tasks
4. Implement job monitoring
5. Test async workflows

**Commands**:
```bash
uv add celery[redis]
```

**Files to create/modify**:
- `src/celery_app.py`: Celery configuration
- `src/tasks/`: Background task definitions
- `docker-compose.yml`: Add Redis service

#### Priority 2: Sentry Error Tracking
**Impact**: 🟡 Medium | **Effort**: Low | **Risk**: Low

**Steps**:
1. Install Sentry SDK
2. Configure Sentry project
3. Add error tracking
4. Set up alerts
5. Test error reporting

**Commands**:
```bash
uv add sentry-sdk[fastapi]
```

**Files to create/modify**:
- `src/config.py`: Add Sentry configuration
- `src/main.py`: Initialize Sentry

#### Priority 3: vLLM High-Throughput Serving
**Impact**: 🟢 Low | **Effort**: High | **Risk**: Medium

**Steps**:
1. Install vLLM
2. Configure vLLM server
3. Migrate from Ollama
4. Load balance multiple instances
5. Monitor performance

**Commands**:
```bash
uv add vllm
```

#### Priority 4: Stripe International Payment
**Impact**: 🟢 Low | **Effort**: Medium | **Risk**: Low

**Steps**:
1. Install Stripe SDK
2. Configure Stripe account
3. Implement payment flow
4. Add webhook handling
5. Test international payments

**Commands**:
```bash
uv add stripe
```

---

## 🎯 SUCCESS METRICS

### Phase 1 Success Criteria
- [ ] pgvector integrated and working
- [ ] bge-m3 embeddings generated for all products
- [ ] Form validation implemented for checkout/registration
- [ ] TanStack tables working in owner/admin
- [ ] shadcn/ui components integrated
- [ ] Search quality improved (measurable)

### Phase 2 Success Criteria
- [ ] Pydantic AI agent responding to queries
- [ ] Local LLM (Ollama) working with fallback
- [ ] Voice search functional with Vietnamese support
- [ ] Push notifications working
- [ ] Agent able to use tools (search, product lookup)

### Phase 3 Success Criteria
- [ ] Background jobs processing async tasks
- [ ] Error tracking active in production
- [ ] LLM serving scaled for production load
- [ ] International payment option available

---

## 📝 NOTES

### Risk Mitigation
- **LLM Fallback**: Always have cloud API backup (OpenRouter)
- **Vector Search**: Keep Qdrant as backup if pgvector insufficient
- **Payment**: Start with Momo/ZaloPay, add Stripe later
- **Background Jobs**: Start with FastAPI BackgroundTasks, migrate to Celery

### Testing Strategy
- Unit tests for all new services
- Integration tests for AI agent
- E2E tests for critical user flows
- Load testing for LLM serving

### Monitoring
- Log LLM responses and performance
- Track search quality metrics
- Monitor error rates with Sentry
- Set up uptime monitoring for critical services
