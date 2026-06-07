"""add_postgis_spatial_schema

Revision ID: postgis_spatial
Revises: b8f3d2e1c4a5
Create Date: 2026-06-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = 'postgis_spatial'
down_revision = 'b8f3d2e1c4a5'
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade: Create PostGIS spatial schema for Vietnam geo data."""
    
    # Enable PostGIS extensions
    op.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    op.execute(text("CREATE EXTENSION IF NOT EXISTS postgis_topology"))
    op.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
    op.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent"))
    op.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))
    
    # Create admin tables
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS provinces (
            code INTEGER PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            name_en VARCHAR(100),
            full_name VARCHAR(150),
            slug VARCHAR(100),
            type VARCHAR(30),
            geom GEOMETRY(MultiPolygon, 4326),
            center GEOMETRY(Point, 4326),
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """))
    
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS districts (
            code INTEGER PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            name_en VARCHAR(100),
            full_name VARCHAR(150),
            slug VARCHAR(100),
            type VARCHAR(30),
            province_code INTEGER REFERENCES provinces(code),
            geom GEOMETRY(MultiPolygon, 4326),
            center GEOMETRY(Point, 4326),
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """))
    
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS wards (
            code INTEGER PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            name_en VARCHAR(100),
            full_name VARCHAR(150),
            slug VARCHAR(100),
            type VARCHAR(30),
            district_code INTEGER REFERENCES districts(code),
            geom GEOMETRY(MultiPolygon, 4326),
            center GEOMETRY(Point, 4326),
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """))
    
    # Create store-related tables
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS store_categories (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            name_vi VARCHAR(100) NOT NULL,
            slug VARCHAR(100) UNIQUE NOT NULL,
            icon VARCHAR(50),
            parent_id INTEGER REFERENCES store_categories(id),
            sort_order INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """))
    
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS brands (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            slug VARCHAR(200) UNIQUE NOT NULL,
            category_id INTEGER REFERENCES store_categories(id),
            logo_url VARCHAR(500),
            website VARCHAR(500),
            phone VARCHAR(50),
            description TEXT,
            is_chain BOOLEAN DEFAULT TRUE,
            country VARCHAR(50) DEFAULT 'VN',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """))
    
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS stores (
            id BIGSERIAL PRIMARY KEY,
            name VARCHAR(300) NOT NULL,
            slug VARCHAR(300),
            brand_id INTEGER REFERENCES brands(id),
            category_id INTEGER REFERENCES store_categories(id),
            house_number VARCHAR(20),
            street VARCHAR(200),
            ward_code INTEGER REFERENCES wards(code),
            district_code INTEGER REFERENCES districts(code),
            province_code INTEGER REFERENCES provinces(code),
            full_address TEXT,
            location GEOMETRY(Point, 4326) NOT NULL,
            latitude DOUBLE PRECISION GENERATED ALWAYS AS (ST_Y(location)) STORED,
            longitude DOUBLE PRECISION GENERATED ALWAYS AS (ST_X(location)) STORED,
            phone VARCHAR(50),
            email VARCHAR(200),
            website VARCHAR(500),
            opening_hours JSONB,
            description TEXT,
            images JSONB DEFAULT '[]',
            tags TEXT[] DEFAULT '{}',
            rating DECIMAL(2,1) DEFAULT 0,
            review_count INTEGER DEFAULT 0,
            is_verified BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            source VARCHAR(50) DEFAULT 'manual',
            source_id VARCHAR(100),
            extra_data JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """))
    
    # Create Vietnamese search functions
    op.execute(text("""
        CREATE OR REPLACE FUNCTION vn_unaccent(text)
        RETURNS text AS $$
            SELECT translate(
                unaccent($1),
                'đĐ',
                'dD'
            );
        $$ LANGUAGE sql IMMUTABLE
    """))
    
    # Add search columns
    op.execute(text("""
        ALTER TABLE stores 
        ADD COLUMN IF NOT EXISTS search_text TSVECTOR,
        ADD COLUMN IF NOT EXISTS name_normalized VARCHAR(300)
    """))
    
    # Create search trigger
    op.execute(text("""
        CREATE OR REPLACE FUNCTION stores_search_trigger()
        RETURNS trigger AS $$
        BEGIN
            NEW.name_normalized := lower(vn_unaccent(NEW.name));
            NEW.search_text := 
                setweight(to_tsvector('simple', coalesce(NEW.name, '')), 'A') ||
                setweight(to_tsvector('simple', coalesce(vn_unaccent(NEW.name), '')), 'A') ||
                setweight(to_tsvector('simple', coalesce(NEW.full_address, '')), 'B') ||
                setweight(to_tsvector('simple', coalesce(vn_unaccent(NEW.full_address), '')), 'B') ||
                setweight(to_tsvector('simple', coalesce(NEW.description, '')), 'C');
            NEW.updated_at := NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """))
    
    op.execute(text("""
        CREATE TRIGGER trg_stores_search
            BEFORE INSERT OR UPDATE ON stores
            FOR EACH ROW
            EXECUTE FUNCTION stores_search_trigger()
    """))
    
    # Create indexes
    op.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_stores_location 
        ON stores USING GIST (location)
    """))
    
    op.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_stores_search_text 
        ON stores USING GIN (search_text)
    """))
    
    op.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_stores_name_trgm 
        ON stores USING GIN (name_normalized gin_trgm_ops)
    """))
    
    op.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_stores_category 
        ON stores (category_id) WHERE is_active = TRUE
    """))
    
    op.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_stores_brand 
        ON stores (brand_id) WHERE is_active = TRUE
    """))
    
    op.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_stores_province ON stores (province_code)
    """))
    
    op.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_stores_district ON stores (district_code)
    """))
    
    op.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_stores_ward ON stores (ward_code)
    """))
    
    op.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_stores_rating 
        ON stores (rating DESC) WHERE is_active = TRUE
    """))
    
    op.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_provinces_geom ON provinces USING GIST (geom)
    """))
    
    op.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_districts_geom ON districts USING GIST (geom)
    """))
    
    op.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_wards_geom ON wards USING GIST (geom)
    """))
    
    # Create stored procedures
    op.execute(text("""
        CREATE OR REPLACE FUNCTION find_nearest_stores(
            p_lat DOUBLE PRECISION,
            p_lng DOUBLE PRECISION,
            p_radius_km DOUBLE PRECISION DEFAULT 5,
            p_category_id INTEGER DEFAULT NULL,
            p_brand_id INTEGER DEFAULT NULL,
            p_limit INTEGER DEFAULT 20
        )
        RETURNS TABLE (
            store_id BIGINT,
            store_name VARCHAR,
            lat DOUBLE PRECISION,
            lng DOUBLE PRECISION,
            distance_meters DOUBLE PRECISION,
            distance_text VARCHAR,
            full_address TEXT,
            phone VARCHAR,
            brand_name VARCHAR,
            category_name VARCHAR,
            category_icon VARCHAR,
            rating DECIMAL,
            opening_hours JSONB
        )
        LANGUAGE sql STABLE AS $$
            SELECT 
                s.id,
                s.name,
                s.latitude,
                s.longitude,
                ST_Distance(
                    s.location::geography,
                    ST_SetSRID(ST_MakePoint(p_lng, p_lat), 4326)::geography
                ) AS distance_meters,
                CASE 
                    WHEN ST_Distance(
                        s.location::geography,
                        ST_SetSRID(ST_MakePoint(p_lng, p_lat), 4326)::geography
                    ) < 1000 
                    THEN ROUND(ST_Distance(
                        s.location::geography,
                        ST_SetSRID(ST_MakePoint(p_lng, p_lat), 4326)::geography
                    ))::VARCHAR || 'm'
                    ELSE ROUND(ST_Distance(
                        s.location::geography,
                        ST_SetSRID(ST_MakePoint(p_lng, p_lat), 4326)::geography
                    ) / 1000.0, 1)::VARCHAR || 'km'
                END AS distance_text,
                s.full_address,
                s.phone,
                b.name,
                c.name_vi,
                c.icon,
                s.rating,
                s.opening_hours
            FROM stores s
            LEFT JOIN brands b ON s.brand_id = b.id
            LEFT JOIN store_categories c ON s.category_id = c.id
            WHERE s.is_active = TRUE
                AND ST_DWithin(
                    s.location::geography,
                    ST_SetSRID(ST_MakePoint(p_lng, p_lat), 4326)::geography,
                    p_radius_km * 1000
                )
                AND (p_category_id IS NULL OR s.category_id = p_category_id)
                AND (p_brand_id IS NULL OR s.brand_id = p_brand_id)
            ORDER BY distance_meters
            LIMIT p_limit;
        $$
    """))
    
    op.execute(text("""
        CREATE OR REPLACE FUNCTION search_stores(
            p_query TEXT,
            p_lat DOUBLE PRECISION DEFAULT NULL,
            p_lng DOUBLE PRECISION DEFAULT NULL,
            p_radius_km DOUBLE PRECISION DEFAULT 50,
            p_category_id INTEGER DEFAULT NULL,
            p_limit INTEGER DEFAULT 20
        )
        RETURNS TABLE (
            store_id BIGINT,
            store_name VARCHAR,
            lat DOUBLE PRECISION,
            lng DOUBLE PRECISION,
            distance_meters DOUBLE PRECISION,
            full_address TEXT,
            brand_name VARCHAR,
            category_name VARCHAR,
            rating DECIMAL,
            relevance REAL
        )
        LANGUAGE sql STABLE AS $$
            SELECT 
                s.id,
                s.name,
                s.latitude,
                s.longitude,
                CASE 
                    WHEN p_lat IS NOT NULL AND p_lng IS NOT NULL
                    THEN ST_Distance(
                        s.location::geography,
                        ST_SetSRID(ST_MakePoint(p_lng, p_lat), 4326)::geography
                    )
                    ELSE NULL
                END AS distance_meters,
                s.full_address,
                b.name,
                c.name_vi,
                s.rating,
                GREATEST(
                    ts_rank(s.search_text, plainto_tsquery('simple', p_query)),
                    ts_rank(s.search_text, plainto_tsquery('simple', vn_unaccent(p_query))),
                    similarity(s.name_normalized, lower(vn_unaccent(p_query)))
                ) AS relevance
            FROM stores s
            LEFT JOIN brands b ON s.brand_id = b.id
            LEFT JOIN store_categories c ON s.category_id = c.id
            WHERE s.is_active = TRUE
                AND (
                    s.search_text @@ plainto_tsquery('simple', p_query)
                    OR s.search_text @@ plainto_tsquery('simple', vn_unaccent(p_query))
                    OR s.name_normalized % lower(vn_unaccent(p_query))
                    OR s.name_normalized ILIKE '%' || vn_unaccent(p_query) || '%'
                )
                AND (p_category_id IS NULL OR s.category_id = p_category_id)
                AND (
                    p_lat IS NULL OR p_lng IS NULL
                    OR ST_DWithin(
                        s.location::geography,
                        ST_SetSRID(ST_MakePoint(p_lng, p_lat), 4326)::geography,
                        p_radius_km * 1000
                    )
                )
            ORDER BY relevance DESC, s.rating DESC
            LIMIT p_limit;
        $$
    """))
    
    op.execute(text("""
        CREATE OR REPLACE FUNCTION geocode_address(
            p_query TEXT
        )
        RETURNS TABLE (
            lat DOUBLE PRECISION,
            lng DOUBLE PRECISION,
            display_name TEXT,
            ward_name VARCHAR,
            district_name VARCHAR,
            province_name VARCHAR,
            confidence REAL
        )
        LANGUAGE sql STABLE AS $$
            SELECT 
                ST_Y(w.center),
                ST_X(w.center),
                w.full_name || ', ' || d.full_name || ', ' || p.full_name,
                w.name,
                d.name,
                p.name,
                similarity(
                    lower(vn_unaccent(w.name || ' ' || d.name || ' ' || p.name)),
                    lower(vn_unaccent(p_query))
                )
            FROM wards w
            JOIN districts d ON w.district_code = d.code
            JOIN provinces p ON d.province_code = p.code
            WHERE 
                lower(vn_unaccent(w.name || ' ' || d.name || ' ' || p.name)) 
                % lower(vn_unaccent(p_query))
                OR w.name ILIKE '%' || p_query || '%'
                OR d.name ILIKE '%' || p_query || '%'
            ORDER BY similarity(
                lower(vn_unaccent(w.name || ' ' || d.name || ' ' || p.name)),
                lower(vn_unaccent(p_query))
            ) DESC
            LIMIT 5;
        $$
    """))
    
    # Create view
    op.execute(text("""
        CREATE OR REPLACE VIEW v_stores_full AS
        SELECT 
            s.id,
            s.name,
            s.latitude,
            s.longitude,
            s.full_address,
            s.phone,
            s.opening_hours,
            s.rating,
            s.review_count,
            b.name AS brand_name,
            b.logo_url AS brand_logo,
            c.name_vi AS category_name,
            c.icon AS category_icon,
            w.name AS ward_name,
            d.name AS district_name,
            p.name AS province_name
        FROM stores s
        LEFT JOIN brands b ON s.brand_id = b.id
        LEFT JOIN store_categories c ON s.category_id = c.id
        LEFT JOIN wards w ON s.ward_code = w.code
        LEFT JOIN districts d ON s.district_code = d.code
        LEFT JOIN provinces p ON s.province_code = p.code
        WHERE s.is_active = TRUE
    """))


def downgrade():
    """Downgrade: Remove PostGIS spatial schema."""
    
    # Drop view
    op.execute(text("DROP VIEW IF EXISTS v_stores_full"))
    
    # Drop stored procedures
    op.execute(text("DROP FUNCTION IF EXISTS geocode_address"))
    op.execute(text("DROP FUNCTION IF EXISTS search_stores"))
    op.execute(text("DROP FUNCTION IF EXISTS find_nearest_stores"))
    
    # Drop indexes
    op.execute(text("DROP INDEX IF EXISTS idx_wards_geom"))
    op.execute(text("DROP INDEX IF EXISTS idx_districts_geom"))
    op.execute(text("DROP INDEX IF EXISTS idx_provinces_geom"))
    op.execute(text("DROP INDEX IF EXISTS idx_stores_rating"))
    op.execute(text("DROP INDEX IF EXISTS idx_stores_ward"))
    op.execute(text("DROP INDEX IF EXISTS idx_stores_district"))
    op.execute(text("DROP INDEX IF EXISTS idx_stores_province"))
    op.execute(text("DROP INDEX IF EXISTS idx_stores_brand"))
    op.execute(text("DROP INDEX IF EXISTS idx_stores_category"))
    op.execute(text("DROP INDEX IF EXISTS idx_stores_name_trgm"))
    op.execute(text("DROP INDEX IF EXISTS idx_stores_search_text"))
    op.execute(text("DROP INDEX IF EXISTS idx_stores_location"))
    
    # Drop trigger and function
    op.execute(text("DROP TRIGGER IF EXISTS trg_stores_search ON stores"))
    op.execute(text("DROP FUNCTION IF EXISTS stores_search_trigger"))
    
    # Drop columns
    op.execute(text("ALTER TABLE stores DROP COLUMN IF EXISTS name_normalized"))
    op.execute(text("ALTER TABLE stores DROP COLUMN IF EXISTS search_text"))
    
    # Drop tables
    op.execute(text("DROP TABLE IF EXISTS stores"))
    op.execute(text("DROP TABLE IF EXISTS brands"))
    op.execute(text("DROP TABLE IF EXISTS store_categories"))
    op.execute(text("DROP TABLE IF EXISTS wards"))
    op.execute(text("DROP TABLE IF EXISTS districts"))
    op.execute(text("DROP TABLE IF EXISTS provinces"))
    
    # Drop functions
    op.execute(text("DROP FUNCTION IF EXISTS vn_unaccent")
    
    # Drop extensions
    op.execute(text("DROP EXTENSION IF EXISTS btree_gist"))
    op.execute(text("DROP EXTENSION IF EXISTS unaccent"))
    op.execute(text("DROP EXTENSION IF EXISTS pg_trgm"))
    op.execute(text("DROP EXTENSION IF EXISTS postgis_topology"))
    op.execute(text("DROP EXTENSION IF EXISTS postgis"))
