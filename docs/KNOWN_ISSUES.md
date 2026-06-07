# Known Issues

## Open Issues

### ISSUE-001: ESLint config chưa hoàn chỉnh
- Status: Open
- Area: Frontend tooling
- Description: ESLint 9.x conflict với React plugins
- Workaround: Tạm thời chưa enforce strict linting
- Suggested Fix: Cập nhật eslint.config.js với flat config

### ISSUE-002: WebSocket chat chưa persistent
- Status: Open
- Area: Backend real-time
- Description: WebSocket messages chưa lưu vào DB
- Workaround: Dùng HTTP POST fallback
- Suggested Fix: Thêm Redis pub/sub cho multi-instance

### ISSUE-003: Vector search chưa implement
- Status: Open
- Area: AI search
- Description: Chat search hiện dùng mock data
- Workaround: Hardcoded mock responses
- Suggested Fix: Tích hợp Qdrant + SentenceTransformers

## Fixed Issues

None yet.
