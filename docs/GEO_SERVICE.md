# Geo Service - Bộ nhớ cache địa chỉ & tọa độ

Hệ thống cache geocoding với 2 tầng: Redis (L1) + SQLite (L2 backup) để tiết kiệm quota API và tăng tốc độ phản hồi.

## 🎯 Tính năng

- ✅ 2-tier cache: Redis (L1) + SQLite (L2 backup)
- ✅ Tự động fallback khi Redis unavailable
- ✅ Chuẩn hóa địa chỉ tiếng Việt
- ✅ Log mọi API calls
- ✅ Thống kê cache hit/miss
- ✅ Hoạt động offline (từ SQLite)

## 📁 Cấu trúc

```
apps/api-server/src/
├── services/
│   ├── geo_cache.py        # Redis cache + SQLite backup
│   └── geo_sqlite_cache.py # SQLite persistent cache
└── api/
    └── geo.py              # REST API endpoints
```

## 🚀 Sử dụng

### 1. Sử dụng Geo Cache Service

```python
from src.services.geo_cache import geo_cache

# Geocode với auto-cache
cached = await geo_cache.get_geocode("227 Nguyễn Văn Cừ, Quận 5, TP.HCM")
if not cached:
    # Gọi API
    result = await call_geocoding_api(address)
    # Lưu vào cả Redis và SQLite
    await geo_cache.set_geocode(address, result)

# Reverse geocode
cached = await geo_cache.get_reverse_geocode(10.7590, 106.6822)
```

### 2. Sử dụng REST API

```bash
# Thống kê cache
GET /api/v1/geo/cache/stats
# Trả về: redis_l1 + sqlite_l2 stats

# Invalidate cache
POST /api/v1/geo/cache/invalidate?pattern=nearby:*

# Flush toàn bộ cache
POST /api/v1/geo/cache/flush
```

## 🔧 Cấu trúc Cache

### L1 - Redis Cache (Primary)
- **Nearby search**: 15 minutes
- **Full-text search**: 10 minutes
- **Geocoding**: 1 hour
- **Reverse geocoding**: 1 hour
- **Categories**: 1 hour
- **Brands**: 1 hour
- **Autocomplete**: 5 minutes

### L2 - SQLite Cache (Backup)
- **Persistent offline cache**
- **Chuẩn hóa địa chỉ tiếng Việt**
- **Hash-based lookup**
- **Access tracking**
- **API call logging**

## 📊 Hiệu năng

```
┌─────────────────┬──────────────┬───────────────┬────────────┐
│     Phương thức  │  Thời gian   │  Chi phí API  │  Độ tin cậy│
├─────────────────┼──────────────┼───────────────┼────────────┤
│ Redis L1 Cache  │  1-5ms       │  Chỉ lần đầu  │  Cao       │
│ SQLite L2 Cache │  5-20ms      │  Chỉ lần đầu  │  Rất cao   │
│ Gọi API trực tiếp│  300-2000ms  │  Mỗi lần gọi │  Phụ thuộc │
│ ⚡ Tốc độ nhanh  │  x60-x2000   │  Tiết kiệm    │            │
│    hơn           │  lần!        │  >90% calls   │            │
└─────────────────┴──────────────┴───────────────┴────────────┘
```

## 🎮 Tích hợp với hệ thống hiện có

Geo cache đã được tích hợp vào:
- `GeoCacheService` - Layer cache chính
- `GeoSearchService` - Service tìm kiếm địa lý
- `Geo API` - REST endpoints

Khi Redis không khả dụng, hệ thống tự động fallback sang SQLite cache.
