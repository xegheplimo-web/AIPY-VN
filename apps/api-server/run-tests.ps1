# Script để chạy tests với biến môi trường

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

# Chạy pytest
python -m pytest $args
