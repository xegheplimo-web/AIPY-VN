# DE XUAT AI AGENT & THU VIEN MA NGUON MO CHO VIETSTORE RAG

## 1. AI AGENT / ORCHESTRATION FRAMEWORKS

| Thu vien | Mo ta | Uu diem | Nhuoc diem | Phu hop? |
|----------|-------|---------|------------|----------|
| **LlamaIndex** | Framework RAG + Agent orchestration | Hotro tot vector search, query engine, tool use | Hoi nang, learning curve | ✅ Phu hop nhat cho RAG search |
| **LangChain** | Framework LLM + chain + agent | Cong dong lon, nhieu integrations, ReAct agent | Over-engineered, chong chenh | ✅ Phu hop neu can nhieu tool chain |
| **Pydantic AI** | Lightweight agent framework tu Anthropic | Type-safe, async-native, nhe | Con moi, ecosystem it hon | ✅ Phu hop neu muon nhe + type-safe |
| **CrewAI** | Multi-agent framework | De dung, multi-agent collaboration | It linh hoat hon LangChain | ⚠️ Qua muc cho project 1-5 nguoi |
| **AutoGen (Microsoft)** | Multi-agent conversation | Manh cho multi-agent, code generation | Phuc tap setup | ❌ Khong can thiet cho MVP |

**De xuat chinh: Pydantic AI hoac LlamaIndex**

---

## 2. LLM MODELS (Local & Cloud)

### 2a. Local Deployment (On-premise / Self-hosted)

| Model | Size | Yeu cau VRAM | Tieng Viet | Uu diem |
|-------|------|-------------|------------|---------|
| **Qwen2.5** | 7B/14B/32B/72B | 8-24GB | Tot | Alibaba, manh da ngon ngu, coding tot |
| **Llama 3.3** | 8B/70B | 8-48GB | Trung binh | Meta, ecosystem lon, quantization tot |
| **Vistral-7B** | 7B | 8GB | **Rat tot** | Viet AI, fine-tuned cho tieng Viet |
| **PhoGPT** | 4B/7B/13B | 6-24GB | **Rat tot** | Vin AI, chuyen tieng Viet |
| **Gemma 3** | 4B/12B/27B | 6-24GB | Tot | Google, nhe, efficient |
| **DeepSeek-V3/R1** | 32B/671B | 24GB+ | Tot | Reasoning tot, open weights |

**De xuat cho VietStore:**
- **Development**: `Qwen2.5-7B-Instruct` hoac `Vistral-7B-Chat`
- **Production VPS**: `PhoGPT-4B` (nhe, chay tot tren CPU) hoac `Qwen2.5-14B`
- **API fallback**: OpenRouter (gom nhieu model, gia re)

### 2b. Inference Engine (Chay model local)

| Engine | Mo ta | Phu hop? |
|--------|-------|----------|
| **llama.cpp** | C++ inference, quantization tot | ✅ Nhat dinh dung cho local model |
| **vLLM** | High-throughput serving | ✅ Tot cho production API |
| **Ollama** | De dung, one-command | ✅ Tot cho development |
| **Text Generation Inference (HuggingFace)** | Production serving | ⚠️ Hoi nang cho single server |

---

## 3. VECTOR SEARCH / RAG (Thay the / Bo sung Qdrant)

| Thu vien | Mo ta | Uu diem | Phu hop? |
|----------|-------|---------|----------|
| **Qdrant** (da co) | Vector DB, hybrid search | Tot, san sang production | ✅ Giu lai |
| **ChromaDB** | Embedded vector DB | De setup, khong can server rieng | ⚠️ Khong tot cho scale |
| **Milvus/Zilliz** | Distributed vector DB | Enterprise, manh | ❌ Qua nang cho MVP |
| **pgvector** | PostgreSQL extension | Mot DB cho ca relational + vector | ✅ **Rat de xuat** — them vao PostgreSQL hien tai |
| **Faiss** (Facebook) | In-memory vector search | Cuc nhanh, khong can server | ⚠️ Khong persistent |

**De xuat:**
1. **Them pgvector** vao PostgreSQL hien tai → khong can Qdrant server rieng
2. **Giu Qdrant** lam option cho advanced vector search

---

## 4. EMBEDDING MODELS (Thay the all-MiniLM-L6-v2)

| Model | Dimensions | Tieng Viet | Dung luong | Phu hop? |
|-------|-----------|------------|------------|----------|
| **BAAI/bge-m3** | 1024 | Rat tot | Nho | ✅ **Tot nhat da ngon ngu** |
| **intfloat/multilingual-e5-large** | 1024 | Tot | Trung binh | ✅ Tot cho RAG |
| **sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2** | 384 | Tot | Nho | ✅ Co trong code hien tai |
| **VoVanPhu/vietnamese-bi-encoder** | 768 | **Chuyen Viet** | Trung binh | ✅ Neu chi tieng Viet |

**De xuat:** Thay `all-MiniLM-L6-v2` bang `BAAI/bge-m3` hoac `multilingual-e5-large`.

---

## 5. VOICE / SPEECH (Thay the Whisper mock)

| Thu vien / Model | Mo ta | Tieng Viet | Offline? | Phu hop? |
|------------------|-------|------------|----------|----------|
| **faster-whisper** (da co) | Whisper optimized | Tot | ✅ Yes | ✅ Giu lai, can implement |
| **WhisperX** | Whisper + diarization + alignment | Tot | ✅ Yes | ⚠️ Them tinh nang khong can thiet |
| **VietASR / wav2vec 2.0 Viet** | Chuyen tieng Viet | **Rat tot** | ✅ Yes | ✅ Tot hon Whisper cho tieng Viet |
| **SenseVoice** (Alibaba) | Multilingual ASR | Tot | ✅ Yes | ✅ Nhe, nhanh, da ngon ngu |
| **FunASR** (Alibaba) | Full ASR toolkit | Tot | ✅ Yes | ⚠️ Framework lon |

**De xuat:**
- **faster-whisper** + model `whisper-large-v3` hoac ` SenseVoiceSmall`
- **Option Viet tot hon:** `VietASR` hoac fine-tuned wav2vec 2.0 Viet

---

## 6. UI / UX LIBRARIES (React + E-commerce)

| Thu vien | Mo ta | Phu hop? |
|----------|-------|----------|
| **shadcn/ui** | Copy-paste components | ✅ Da co trong spec, nen them vao |
| **TanStack Table** | Data tables (owner/admin) | ✅ **Rat can** cho product/orders table |
| **TanStack Virtual** | Virtualization (long lists) | ✅ Tot cho infinite scroll product list |
| **React Hook Form** | Form validation | ✅ **Rat can** cho checkout, registration |
| **Zod** | Schema validation (TS) | ✅ Tot cho form + API validation |
| **Recharts** | Charts/Analytics | ✅ Cho owner/admin dashboard |
| **React Leaflet** (da co) | Maps | ✅ Giu lai |
| **Framer Motion** (da co) | Animations | ✅ Giu lai |

**De xuat them:**
```bash
# Customer
npm add react-hook-form zod @hookform/resolvers

# Owner/Admin  
npm add @tanstack/react-table @tanstack/virtual recharts react-hook-form zod
```

---

## 7. PAYMENT GATEWAY (Momo, ZaloPay, COD)

| Thu vien | Mo ta | Phu hop? |
|----------|-------|----------|
| **momo-payment-sdk** (unofficial) | Momo integration | ⚠️ Can verify maintenance |
| **zalopay-nodejs** (unofficial) | ZaloPay integration | ⚠️ Can verify maintenance |
| **Stripe** | Quoc te | ✅ Nen co lam option |
| **Self-implement** | HTTP client goi API truc tiep | ✅ **Khuyen nghi** — API Momo/ZaloPay don gian |

**De xuat:** Tu implement HTTP client goi Momo/ZaloPay API (khong can SDK, chi can `httpx` da co).

---

## 8. NOTIFICATIONS (Push + Email + SMS)

| Thu vien | Mo ta | Phu hop? |
|----------|-------|----------|
| **Firebase Admin SDK** | FCM push notifications | ✅ **Can co** cho push |
| **Celery + Redis** | Background job queue | ✅ Can cho async tasks |
| **FastAPI BackgroundTasks** | Built-in | ⚠️ Khong persistent |
| **Resend / SendGrid** | Email API | ✅ Cho transactional email |
| **Twilio** | SMS | ⚠️ Dat, co the dung local SMS gateway |

**De xuat:**
```bash
uv add firebase-admin celery[redis] resend
```

---

## 9. KIEM TRA DU LIEU / MONITORING

| Thu vien | Mo ta | Phu hop? |
|----------|-------|----------|
| **Sentry** | Error tracking | ✅ **Rat nen co** |
| **Prometheus + Grafana** | Metrics | ⚠️ Qua muc cho MVP |
| **OpenTelemetry** | Tracing | ⚠️ Co the them sau |
| **Uptime Kuma** | Uptime monitoring | ✅ Self-hosted, nhe |

---

## 10. TOM TAT DE XUAT CHO VIETSTORE RAG

### Ngan han (Tuan 1-2):
| Thu vien | Muc dich | Lenh cai dat |
|----------|----------|-------------|
| **pgvector** | Vector search trong PostgreSQL | `docker exec postgres psql -c "CREATE EXTENSION vector;"` |
| **bge-m3** | Embedding model da ngon ngu | Tu dong tai khi chay |
| **faster-whisper** | Voice search | `uv add faster-whisper` |
| **react-hook-form + zod** | Form validation | `npm add react-hook-form zod @hookform/resolvers` |
| **TanStack Table** | Data tables admin/owner | `npm add @tanstack/react-table` |

### Trung han (Tuan 3-4):
| Thu vien | Muc dich | Lenh cai dat |
|----------|----------|-------------|
| **Pydantic AI** hoac **LlamaIndex** | AI Agent orchestration | `uv add pydantic-ai` hoac `uv add llama-index` |
| **Ollama** | Local LLM serving | Cai dat rieng |
| **Qwen2.5-7B** hoac **Vistral-7B** | LLM local | `ollama pull qwen2.5:7b` |
| **firebase-admin** | Push notifications | `uv add firebase-admin` |
| **celery[redis]** | Background jobs | `uv add celery[redis]` |

### Dai han (Tuan 5+):
| Thu vien | Muc dich |
|----------|----------|
| **Sentry SDK** | Error tracking |
| **Stripe** | Payment quoc te |
| **vLLM** | High-throughput LLM serving |
| **OpenTelemetry** | Distributed tracing |

---

## 11. KIEN TRUC DE XUAT CAP NHAT

```
Frontend (React + Vite + Tailwind + shadcn/ui + TanStack)
                    |
Backend (FastAPI + SQLAlchemy + Pydantic AI / LlamaIndex)
                    |
    +---------------+---------------+
    |               |               |
PostgreSQL      Redis          Qdrant (optional)
+ pgvector      (cache/jobs)     (vector advanced)
    |
    +-- Local: Ollama (Qwen2.5/Vistral)
    +-- Cloud: OpenRouter / Gemini API
```

---

## 12. SO SANH VOI HIEN TAI

| Khu vuc | Hien tai | De xuat | Loi ich |
|---------|----------|---------|---------|
| Embedding | all-MiniLM-L6-v2 (384d) | bge-m3 (1024d) | Tieng Viet tot hon, 200+ ngon ngu |
| Vector DB | Qdrant (chua dung) | pgvector + Qdrant | Don gian hon, dung PostgreSQL san co |
| LLM | Khong co | Qwen2.5/Vistral + Ollama | Search summary thong minh hon |
| Voice | Mock | faster-whisper / SenseVoice | Voice search that su |
| Forms | Native React state | react-hook-form + zod | Validation chuan, UX tot hon |
| Tables | Custom | TanStack Table | Sort, filter, pagination san co |
| Jobs | Khong co | Celery + Redis | Background tasks (email, sync) |
| Push | Khong co | Firebase Admin | Push notifications |

---

*Cap nhat: 2026-06-07*
