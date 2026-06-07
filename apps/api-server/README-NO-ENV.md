# Chạy ứng dụng mà không cần file .env

## Môi trường ảo đã được tạo

Môi trường ảo Python đã được tạo tại: `apps/api-server/.venv`

## Scripts tiện ích

### 1. Chạy Health Check
```powershell
powershell -ExecutionPolicy Bypass -File run-with-env.ps1
```

### 2. Chạy Development Server
```powershell
powershell -ExecutionPolicy Bypass -File run-dev-server.ps1
```

### 3. Chạy Tests
```powershell
powershell -ExecutionPolicy Bypass -File run-tests.ps1
```

### 4. Chạy tests cụ thể
```powershell
powershell -ExecutionPolicy Bypass -File run-tests.ps1 tests/test_middleware.py -v
```

## Biến môi trường mặc định

Các script này tự động set các biến môi trường sau:

```powershell
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/vietstore
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333
ENVIRONMENT=development
DEBUG=true
CSRF_SECRET_KEY=dev-secret-key
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:3001,http://localhost:3002
RATE_LIMIT_MAX_REQUESTS=200
RATE_LIMIT_WINDOW_SECONDS=60
LOG_LEVEL=info
```

## Kích hoạt môi trường ảo thủ công

Nếu bạn muốn kích hoạt môi trường ảo thủ công:

```powershell
cd apps/api-server
.venv\Scripts\activate
```

Sau đó set biến môi trường và chạy lệnh:

```powershell
$env:DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/vietstore"
$env:REDIS_URL = "redis://localhost:6379/0"
$env:QDRANT_URL = "http://localhost:6333"
python -m uvicorn src.main:app --reload
```

## Cài đặt lại môi trường ảo

Nếu cần cài đặt lại:

```powershell
cd apps/api-server
Remove-Item -Recurse -Force .venv
uv venv
uv pip install -e .
```

## Yêu cầu dịch vụ bên ngoài

Để chạy ứng dụng đầy đủ, bạn cần các dịch vụ sau:

- **PostgreSQL 16**: Đang chạy trên localhost:5432
- **Redis 7**: Đang chạy trên localhost:6379
- **Qdrant**: Đang chạy trên localhost:6333

Nếu bạn đã chạy `docker-compose up -d` từ thư mục gốc, các dịch vụ này đã sẵn sàng.

## Kiểm tra trạng thái

```powershell
# Kiểm tra Docker containers
docker ps

# Kiểm tra health check
powershell -ExecutionPolicy Bypass -File run-with-env.ps1
```

## Lưu ý bảo mật

⚠️ **QUAN TRỌNG**: Các biến môi trường trong scripts này chỉ dành cho **DEVELOPMENT**.

Để chạy trong **PRODUCTION**, bạn phải:
1. Sử dụng file .env thực tế với credentials bảo mật
2. Set `ECC_PRIVATE_KEY_PEM` với key thực
3. Set `CSRF_SECRET_KEY` với secret key mạnh
4. Set `ENVIRONMENT=production`
5. Không commit file .env vào repository
