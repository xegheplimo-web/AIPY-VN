# Data Import Guide - PostGIS Phase 2

## Overview

This guide explains how to import Vietnam administrative data and OpenStreetMap POI data into the PostGIS database for the self-hosted geo search system.

## Data Sources

### 1. Vietnam Admin Data

**Source**: https://provinces.open-api.vn/api  
**License**: Free, no API key required  
**Data**:
- 63 provinces/cities
- 713 districts/counties
- 11,162 wards/communes

### 2. OpenStreetMap POI Data

**Source**: Overpass API (https://overpass-api.de/api/interpreter)  
**License**: ODbL (Open Database License)  
**Data**:
- ~50,000+ POI for Vietnam
- Stores, restaurants, cafes, pharmacies, banks, etc.
- Opening hours, phone numbers, websites

## Import Process

### Step 1: Verify PostGIS Setup

First, ensure PostGIS extensions are enabled:

```bash
cd apps/api-server
python scripts/setup_postgis.py
```

This will check:
- PostGIS extensions are enabled
- Admin tables exist
- Store tables exist
- Search functions are working

### Step 2: Run Alembic Migration

If not already done, run the migration to create all tables:

```bash
alembic upgrade head
```

This will create:
- Admin tables (provinces, districts, wards)
- Store tables (store_categories, brands, stores)
- Search columns and triggers
- Spatial and search indexes
- Stored procedures

### Step 3: Import Vietnam Admin Data

Run the data import script:

```bash
python scripts/import_data.py
```

This will:
1. Import 63 provinces/cities with center coordinates
2. Import 713 districts/counties
3. Import 11,162 wards/communes
4. Import initial store categories (18 categories)
5. Import initial brands (25+ brands)
6. Import OSM POI data for all categories

### Step 4: Verify Import

Check the import statistics:

```bash
# Connect to PostgreSQL
psql -U postgres -d vietstore

# Check counts
SELECT 
    (SELECT COUNT(*) FROM provinces) as provinces,
    (SELECT COUNT(*) FROM districts) as districts,
    (SELECT COUNT(*) FROM wards) as wards,
    (SELECT COUNT(*) FROM stores) as stores,
    (SELECT COUNT(*) FROM brands) as brands,
    (SELECT COUNT(*) FROM store_categories) as categories;
```

Expected output:
```
 provinces | districts | wards  | stores | brands | categories
----------+-----------+--------+--------+--------+-----------
        63 |       713 |  11162 |      0 |     25 |        18
```

## Manual Import (Individual Components)

### Import Admin Data Only

```python
from src.db.admin_importer import import_admin_data
from src.db import async_session

async with async_session() as session:
    await import_admin_data(session)
```

### Import OSM Data Only

```python
from src.db.osm_importer import import_osm_data
from src.db import async_session

async with async_session() as session:
    await import_osm_data(session)
```

### Import Specific Category

```python
from src.db.osm_importer import OSMImporter
from src.db import async_session

async with async_session() as session:
    importer = OSMImporter(session)
    await importer.import_poi_by_category("convenience", limit=100)
```

## Categories Imported

The following categories are imported from OpenStreetMap:

| Category | OSM Tag | Description |
|----------|----------|-------------|
| supermarket | shop=supermarket | Siêu thị |
| convenience | shop=convenience | Cửa hàng tiện lợi |
| cafe | amenity=cafe | Quán cà phê |
| restaurant | amenity=restaurant | Nhà hàng |
| pharmacy | amenity=pharmacy | Nhà thuốc |
| bank | amenity=bank | Ngân hàng |
| atm | amenity=atm | ATM |
| hospital | amenity=hospital | Bệnh viện |
| school | amenity=school | Trường học |
| fuel | amenity=fuel | Cây xăng |
| bakery | shop=bakery | Tiệm bánh |
| fast_food | amenity=fast_food | Đồ ăn nhanh |
| clothes | shop=clothes | Cửa hàng quần áo |
| electronics | shop=electronics | Cửa hàng điện tử |
| mobile_phone | shop=mobile_phone | Cửa hàng điện thoại |

## Brand Detection

The importer automatically detects popular Vietnamese brands:

### Convenience Stores
- Circle K
- GS25
- Ministop
- 7-Eleven
- Bách Hóa Xanh

### Coffee Chains
- Highlands Coffee
- Phúc Long
- The Coffee House
- Trung Nguyên
- Starbucks

### Electronics
- Thế Giới Di Động
- FPT Shop
- CellphoneS
- Điện Máy Xanh

### Pharmacy
- Pharmacity
- Long Châu
- An Khang

### Fast Food
- KFC
- Lotteria
- Jollibee
- Pizza Hut

## Performance Considerations

### Rate Limiting

- Overpass API: 5 second delay between category imports
- Nominatim API: 1 second delay between geocoding requests

### Import Time Estimates

- Admin data: ~5-10 minutes
- OSM data (all categories): ~30-60 minutes
- Single category: ~2-5 minutes

### Database Performance

After import, the following indexes ensure fast queries:
- `idx_stores_location` - GIST spatial index (< 5ms nearby search)
- `idx_stores_search_text` - GIN full-text index (< 20ms search)
- `idx_stores_name_trgm` - GIN trigram index (fuzzy matching)

## Troubleshooting

### Import Fails - Database Connection

```bash
# Check database is running
docker ps | grep postgres

# Check connection string
echo $DATABASE_URL

# Test connection
psql -U postgres -d vietstore -c "SELECT 1"
```

### Import Fails - Overpass API Timeout

```bash
# Test Overpass API manually
curl -X POST "https://overpass-api.de/api/interpreter" \
  -d "data=[out:json];node[shop=convenience](area.VN);out;"

# If timeout, try reducing limit
# Edit src/db/osm_importer.py and reduce limit parameter
```

### Import Fails - Missing Tables

```bash
# Run migration
alembic upgrade head

# Check tables exist
psql -U postgres -d vietstore -c "\dt"
```

### Slow Import Performance

```sql
-- Check index usage
EXPLAIN ANALYZE SELECT * FROM find_nearest_stores(10.7769, 106.7009, 5);

-- Rebuild indexes if needed
REINDEX INDEX idx_stores_location;
REINDEX INDEX idx_stores_search_text;
```

## Next Steps

After data import is complete:

1. **Test the API**
   ```bash
   curl http://localhost:8000/api/geo/categories
   curl http://localhost:8000/api/geo/brands
   curl http://localhost:8000/api/geo/search?q=Circle+K
   ```

2. **Test Nearby Search**
   ```bash
   curl "http://localhost:8000/api/geo/nearby?lat=10.7769&lng=106.7009&radius=2"
   ```

3. **Test Geocoding**
   ```bash
   curl "http://localhost:8000/api/geo/geocode?address=Nguyễn+Huệ,+Quận+1"
   ```

4. **Implement Redis Caching** (Phase 3)
   - Cache geo search results
   - Cache geocoding results
   - Reduce database load

## Data Updates

### Scheduled Updates

To keep data current, schedule regular imports:

```bash
# Add to crontab
0 2 * * * cd /path/to/apps/api-server && python scripts/import_data.py
```

This will run import daily at 2 AM.

### Manual Updates

To update specific data:

```python
# Update admin data (rarely changes)
from src.db.admin_importer import import_admin_data
await import_admin_data(session)

# Update OSM data (more frequent)
from src.db.osm_importer import import_osm_data
await import_osm_data(session)
```

## Data Quality

### Validation

The importer includes basic validation:
- Coordinates must be valid (lat: -90 to 90, lng: -180 to 180)
- Names must not be empty
- Addresses are normalized

### Duplicate Detection

- Uses ON CONFLICT DO NOTHING to prevent duplicates
- Source ID tracking (OSM node ID)
- Unique constraints on slugs

### Brand Detection

- Case-insensitive matching
- Multiple pattern matching
- OSM brand tag support

## Storage Requirements

### Estimated Database Size

- Admin data: ~5-10 MB
- OSM POI data: ~50-100 MB
- Indexes: ~20-30 MB
- Total: ~75-140 MB

### Growth

With regular updates:
- Monthly growth: ~5-10 MB
- Yearly growth: ~50-100 MB

## Backup Recommendations

```bash
# Backup database
pg_dump -U postgres vietstore > backup_$(date +%Y%m%d).sql

# Restore database
psql -U postgres vietstore < backup_20260608.sql
```

## Monitoring

### Import Progress

Monitor import progress by checking row counts:

```sql
SELECT 
    (SELECT COUNT(*) FROM stores) as total_stores,
    (SELECT COUNT(*) FROM provinces) as provinces,
    (SELECT COUNT(*) FROM districts) as districts,
    (SELECT COUNT(*) FROM wards) as wards;
```

### Performance Monitoring

Monitor query performance:

```sql
-- Check slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

## References

- [Vietnam Admin API](https://provinces.open-api.vn/api)
- [Overpass API](https://overpass-api.de/)
- [OpenStreetMap](https://www.openstreetmap.org/)
- [PostGIS Documentation](https://postgis.net/documentation/)
