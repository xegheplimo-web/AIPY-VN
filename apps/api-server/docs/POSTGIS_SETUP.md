# PostGIS Integration for VietStore RAG

## Overview

This module provides self-hosted spatial search capabilities using PostGIS, eliminating dependency on external APIs like Google Maps or OpenStreetMap.

## Features

- ✅ **Zero API Cost** - No external API dependencies
- ✅ **Vietnam-Optimized** - Full-text search with Vietnamese text normalization
- ✅ **High Performance** - PostGIS GIST index for < 5ms spatial queries
- ✅ **Fuzzy Matching** - Trigram index for typo-tolerant search
- ✅ **Offline Ready** - Runs without internet connection
- ✅ **Scalable** - Can handle millions of POI records

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Self-Hosted Geo Stack                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  FastAPI → GeoSearchService → PostgreSQL + PostGIS      │
│                                                          │
│  Data Sources:                                          │
│  - Vietnam admin data (63 provinces, 713 districts)     │
│  - OpenStreetMap POI (stores, restaurants, etc.)         │
│  - User-generated data (Owner Portal)                   │
│                                                          │
│  Search Capabilities:                                    │
│  - Full-text search (Vietnamese)                         │
│  - Fuzzy matching (trigram)                             │
│  - Spatial queries (nearby search)                       │
│  - Geocoding & reverse geocoding                         │
│  - Category & brand filtering                            │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Setup Instructions

### Prerequisites

1. PostgreSQL 16+ with PostGIS extension
2. Python 3.12+
3. Alembic for migrations

### Step 1: Enable PostGIS Extensions

Run the setup script:

```bash
cd apps/api-server
python scripts/setup_postgis.py
```

This will:
- Enable PostGIS extensions (postgis, postgis_topology, pg_trgm, unaccent, btree_gist)
- Create Vietnamese text normalization function
- Check existing schema
- Test sample queries

### Step 2: Run Alembic Migration

```bash
cd apps/api-server
alembic upgrade head
```

This will create:
- Admin tables (provinces, districts, wards)
- Store tables (store_categories, brands, stores)
- Search columns and triggers
- Spatial and search indexes
- Stored procedures
- Views

### Step 3: Import Data (Optional)

#### Import Vietnam Admin Data

```bash
python -m src.db.postgis_importer
```

This imports:
- 63 provinces/cities
- 713 districts
- 11,162 wards/communes

#### Import OpenStreetMap Data

```bash
python -m src.db.osm_importer
```

This imports:
- POI data from OpenStreetMap
- Stores, restaurants, cafes, etc.
- ~50,000+ POI for Vietnam

### Step 4: Test the API

```bash
# Start the server
cd apps/api-server
python -m uvicorn src.main:app --reload

# Test endpoints
curl http://localhost:8000/api/geo/categories
curl http://localhost:8000/api/geo/brands
curl http://localhost:8000/api/geo/search?q=Circle+K
curl http://localhost:8000/api/geo/nearby?lat=10.7769&lng=106.7009
```

## API Endpoints

### Search Stores

```http
GET /api/geo/search?q=Circle K&lat=10.77&lng=106.70&radius=5&limit=20
```

**Features:**
- Full-text search with Vietnamese support
- Fuzzy matching (gõ sai vẫn tìm được)
- Geo-spatial filtering
- Category and brand filtering
- Relevance scoring

### Find Nearby

```http
GET /api/geo/nearby?lat=10.7769&lng=106.7009&radius=2&category=cafe
```

**Features:**
- PostGIS spatial query (< 5ms)
- Distance calculation
- Category filtering
- Sorted by distance

### Geocode

```http
GET /api/geo/geocode?address=Nguyễn+Huệ,+Quận+1
```

**Features:**
- Address → coordinates
- Vietnam admin data lookup
- Confidence scoring

### Reverse Geocode

```http
GET /api/geo/reverse?lat=10.7769&lng=106.7009
```

**Features:**
- Coordinates → address
- Ward, district, province lookup
- Street name extraction

### Categories & Brands

```http
GET /api/geo/categories
GET /api/geo/brands?category=cafe
```

**Features:**
- List all categories with icons
- List brands with store counts
- Category filtering

### Autocomplete

```http
GET /api/geo/autocomplete?q=ca&lat=10.77&lng=106.70
```

**Features:**
- Real-time suggestions
- Geo-aware results
- Optimized for UX

## Database Schema

### Admin Tables

```sql
provinces (63 records)
├── code (PK)
├── name, name_en
├── full_name, slug
├── type
├── geom (MultiPolygon)
└── center (Point)

districts (713 records)
├── code (PK)
├── name, name_en
├── full_name, slug
├── type
├── province_code (FK)
├── geom (MultiPolygon)
└── center (Point)

wards (11,162 records)
├── code (PK)
├── name, name_en
├── full_name, slug
├── type
├── district_code (FK)
├── geom (MultiPolygon)
└── center (Point)
```

### Store Tables

```sql
store_categories (18 categories)
├── id (PK)
├── name, name_vi
├── slug, icon
├── parent_id (FK)
└── sort_order

brands (25+ brands)
├── id (PK)
├── name, slug
├── category_id (FK)
├── logo_url, website
├── phone, description
└── is_chain

stores (main table)
├── id (PK)
├── name, slug
├── brand_id (FK)
├── category_id (FK)
├── ward_code, district_code, province_code (FK)
├── full_address
├── location (Point, 4326) - PostGIS
├── latitude, longitude (generated)
├── phone, email, website
├── opening_hours (JSONB)
├── images (JSONB)
├── tags (TEXT[])
├── rating, review_count
├── is_verified, is_active
├── source, source_id
└── extra_data (JSONB)
```

## Performance

### Indexes

- **idx_stores_location** - GIST spatial index (nearby search < 5ms)
- **idx_stores_search_text** - GIN full-text index (search < 20ms)
- **idx_stores_name_trgm** - GIN trigram index (fuzzy search)
- **idx_stores_category** - B-tree index (category filtering)
- **idx_stores_brand** - B-tree index (brand filtering)
- **idx_stores_rating** - B-tree index (rating sorting)

### Query Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Nearby search | < 5ms | PostGIS GIST index |
| Full-text search | < 20ms | GIN + trigram index |
| Autocomplete | < 10ms | Optimized query |
| Geocoding | < 15ms | Admin data lookup |
| Reverse geocode | < 15ms | Spatial query |

## Vietnamese Text Search

### Features

- **Accent removal**: "Cà phê" → "ca phe"
- **Fuzzy matching**: "hailend cofe" → "Highlands Coffee"
- **No-diacritic search**: "ca phe" → "Cà phê"
- **Trigram similarity**: Gõ sai vẫn tìm được

### Implementation

```sql
-- Vietnamese normalization function
CREATE OR REPLACE FUNCTION vn_unaccent(text)
RETURNS text AS $$
    SELECT translate(
        unaccent($1),
        'đĐ',
        'dD'
    );
$$ LANGUAGE sql IMMUTABLE;

-- Search trigger
CREATE TRIGGER trg_stores_search
    BEFORE INSERT OR UPDATE ON stores
    FOR EACH ROW
    EXECUTE FUNCTION stores_search_trigger()
```

## Stored Procedures

### find_nearest_stores

```sql
SELECT * FROM find_nearest_stores(
    10.7769,  -- lat
    106.7009, -- lng
    5,        -- radius_km
    NULL,     -- category_id
    NULL,     -- brand_id
    20        -- limit
);
```

### search_stores

```sql
SELECT * FROM search_stores(
    'Circle K',  -- query
    10.7769,    -- lat (optional)
    106.7009,   -- lng (optional)
    50,         -- radius_km
    NULL,       -- category_id
    20          -- limit
);
```

### geocode_address

```sql
SELECT * FROM geocode_address('Nguyễn Huệ, Quận 1');
```

## Data Import Pipeline

### Vietnam Admin Data

Source: https://provinces.open-api.vn/api

- 63 provinces/cities
- 713 districts
- 11,162 wards/communes
- Geocoded center coordinates

### OpenStreetMap Data

Source: https://download.geofabrik.de/asia/vietnam-latest.osm.pbf

- ~50,000+ POI for Vietnam
- Stores, restaurants, cafes, etc.
- Opening hours, phone numbers
- Brand detection

### Custom Data

- Owner Portal user submissions
- Manual data entry
- Data validation and normalization

## Testing

Run the test suite:

```bash
cd apps/api-server
pytest tests/test_postgis.py -v
```

Test coverage:
- PostGIS extensions
- Vietnamese text normalization
- Admin tables
- Store tables
- Search columns
- Spatial indexes
- Stored procedures
- GeoSearchService

## Troubleshooting

### PostGIS Extension Not Found

```bash
# Install PostGIS on Ubuntu/Debian
sudo apt-get install postgis postgresql-16-postgis-3

# Install PostGIS on macOS
brew install postgis

# Install PostGIS on Windows
# Use Stack Builder with PostgreSQL installation
```

### Migration Fails

```bash
# Check if PostGIS is installed
psql -U postgres -d vietstore -c "SELECT PostGIS_Version()"

# Manually enable extensions
psql -U postgres -d vietstore -c "CREATE EXTENSION postgis;"
```

### Slow Queries

```sql
-- Check index usage
EXPLAIN ANALYZE SELECT * FROM find_nearest_stores(10.7769, 106.7009, 5);

-- Rebuild indexes if needed
REINDEX INDEX idx_stores_location;
REINDEX INDEX idx_stores_search_text;
```

## Performance Optimization

### Configuration

```postgresql
# postgresql.conf
shared_buffers = 512MB
effective_cache_size = 1536MB
work_mem = 16MB
maintenance_work_mem = 128MB
max_connections = 200
```

### Query Optimization

- Use stored procedures for complex queries
- Add appropriate indexes
- Use materialized views for heavy aggregations
- Implement query result caching with Redis

## Future Enhancements

- [ ] Real-time data synchronization
- [ ] Map tile server integration
- [ ] Self-hosted Nominatim for full geocoding
- [ ] VALHALLA routing engine
- [ ] Data quality monitoring
- [ ] Automated data updates

## References

- [PostGIS Documentation](https://postgis.net/documentation/)
- [Vietnam Admin API](https://provinces.open-api.vn/api)
- [OpenStreetMap](https://www.openstreetmap.org/)
- [PostgreSQL Full-Text Search](https://www.postgresql.org/docs/current/textsearch.html)

## License

This module is part of VietStore RAG project.
