# Script để chạy ứng dụng với biến môi trường mà không cần file .env

$env:DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/vietstore"
$env:REDIS_URL = "redis://localhost:6379/0"
$env:QDRANT_URL = "http://localhost:6333"
$env:ENVIRONMENT = "development"
$env:DEBUG = "true"
$env:CSRF_SECRET_KEY = "dev-secret-key"
$env:CORS_ORIGINS = "http://localhost:3000,http://localhost:5173,http://localhost:3001,http://localhost:3002"
$env:RATE_LIMIT_MAX_REQUESTS = "200"
$env:RATE_LIMIT_WINDOW_SECONDS = "60"
$env:LOG_LEVEL = "info"
$env:SERPAPI_KEY = "d3427bacea59fab22364b9586ea3753b99918e695fd138930b655d67d6054b42"
$env:SERPAPI_ENGINE = "google"

# Chạy lệnh được truyền vào
$command = $args[0]
if ($command) {
    & $command $args[1..($args.Length-1)]
} else {
    # Mặc định chạy health check
    python -c "from src.main import app; from fastapi.testclient import TestClient; client = TestClient(app); response = client.get('/health'); print('Status:', response.status_code); print('Response:', response.json())"
}
