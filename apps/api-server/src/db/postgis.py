"""
PostGIS Setup for VietStore RAG

This module sets up the PostGIS extension and creates the spatial database schema
for Vietnam geographic data (provinces, districts, wards, stores, brands, categories).
"""

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class PostGISManager:
    """
    Manages PostGIS extension and spatial schema setup.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def enable_postgis(self) -> bool:
        """
        Enable PostGIS and related extensions.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Enable PostGIS core
            await self.session.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            logger.info("✅ PostGIS extension enabled")

            # Enable PostGIS topology (for advanced spatial operations)
            await self.session.execute(text("CREATE EXTENSION IF NOT EXISTS postgis_topology"))
            logger.info("✅ PostGIS topology extension enabled")

            # Enable pg_trgm for fuzzy text search
            await self.session.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
            logger.info("✅ pg_trgm extension enabled")

            # Enable unaccent for Vietnamese text normalization
            await self.session.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent"))
            logger.info("✅ unaccent extension enabled")

            # Enable btree_gist for spatial indexes
            await self.session.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))
            logger.info("✅ btree_gist extension enabled")

            await self.session.commit()
            return True

        except Exception as e:
            logger.error(f"❌ Failed to enable PostGIS extensions: {e}")
            await self.session.rollback()
            return False

    async def create_admin_schema(self) -> bool:
        """
        Create administrative area schema (provinces, districts, wards).
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Provinces table (63 provinces/cities)
            await self.session.execute(text("""
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
            logger.info("✅ Provinces table created")

            # Districts table (713 districts)
            await self.session.execute(text("""
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
            logger.info("✅ Districts table created")

            # Wards table (11,162 wards/communes)
            await self.session.execute(text("""
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
            logger.info("✅ Wards table created")

            await self.session.commit()
            return True

        except Exception as e:
            logger.error(f"❌ Failed to create admin schema: {e}")
            await self.session.rollback()
            return False

    async def create_store_schema(self) -> bool:
        """
        Create store-related schema (categories, brands, stores).
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Store categories table
            await self.session.execute(text("""
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
            logger.info("✅ Store categories table created")

            # Brands table
            await self.session.execute(text("""
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
            logger.info("✅ Brands table created")

            # Stores table (main table)
            await self.session.execute(text("""
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
            logger.info("✅ Stores table created")

            await self.session.commit()
            return True

        except Exception as e:
            logger.error(f"❌ Failed to create store schema: {e}")
            await self.session.rollback()
            return False

    async def create_search_functions(self) -> bool:
        """
        Create Vietnamese text search functions and triggers.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Vietnamese unaccent function
            await self.session.execute(text("""
                CREATE OR REPLACE FUNCTION vn_unaccent(text)
                RETURNS text AS $$
                    SELECT translate(
                        unaccent($1),
                        'đĐ',
                        'dD'
                    );
                $$ LANGUAGE sql IMMUTABLE
            """))
            logger.info("✅ vn_unaccent function created")

            # Add search columns to stores
            await self.session.execute(text("""
                ALTER TABLE stores 
                ADD COLUMN IF NOT EXISTS search_text TSVECTOR,
                ADD COLUMN IF NOT EXISTS name_normalized VARCHAR(300)
            """))
            logger.info("✅ Search columns added to stores")

            # Search trigger function
            await self.session.execute(text("""
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
            logger.info("✅ Search trigger function created")

            # Create trigger
            await self.session.execute(text("""
                DROP TRIGGER IF EXISTS trg_stores_search ON stores
            """))
            await self.session.execute(text("""
                CREATE TRIGGER trg_stores_search
                    BEFORE INSERT OR UPDATE ON stores
                    FOR EACH ROW
                    EXECUTE FUNCTION stores_search_trigger()
            """))
            logger.info("✅ Search trigger created")

            await self.session.commit()
            return True

        except Exception as e:
            logger.error(f"❌ Failed to create search functions: {e}")
            await self.session.rollback()
            return False

    async def create_indexes(self) -> bool:
        """
        Create spatial and search indexes for performance.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Spatial index for stores (critical for nearby search)
            await self.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_stores_location 
                ON stores USING GIST (location)
            """))
            logger.info("✅ Spatial index on stores.location created")

            # Full-text search index
            await self.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_stores_search_text 
                ON stores USING GIN (search_text)
            """))
            logger.info("✅ Full-text search index created")

            # Trigram index for fuzzy search
            await self.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_stores_name_trgm 
                ON stores USING GIN (name_normalized gin_trgm_ops)
            """))
            logger.info("✅ Trigram index for fuzzy search created")

            # Category filter index
            await self.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_stores_category 
                ON stores (category_id) WHERE is_active = TRUE
            """))
            logger.info("✅ Category filter index created")

            # Brand filter index
            await self.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_stores_brand 
                ON stores (brand_id) WHERE is_active = TRUE
            """))
            logger.info("✅ Brand filter index created")

            # Administrative area indexes
            await self.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_stores_province ON stores (province_code)
            """))
            await self.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_stores_district ON stores (district_code)
            """))
            await self.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_stores_ward ON stores (ward_code)
            """))
            logger.info("✅ Administrative area indexes created")

            # Rating index
            await self.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_stores_rating 
                ON stores (rating DESC) WHERE is_active = TRUE
            """))
            logger.info("✅ Rating index created")

            # Admin spatial indexes
            await self.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_provinces_geom ON provinces USING GIST (geom)
            """))
            await self.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_districts_geom ON districts USING GIST (geom)
            """))
            await self.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_wards_geom ON wards USING GIST (geom)
            """))
            logger.info("✅ Admin spatial indexes created")

            await self.session.commit()
            return True

        except Exception as e:
            logger.error(f"❌ Failed to create indexes: {e}")
            await self.session.rollback()
            return False

    async def create_stored_procedures(self) -> bool:
        """
        Create stored procedures for common geo operations.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find nearest stores procedure
            await self.session.execute(text("""
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
            logger.info("✅ find_nearest_stores procedure created")

            # Search stores procedure
            await self.session.execute(text("""
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
            logger.info("✅ search_stores procedure created")

            # Geocode procedure
            await self.session.execute(text("""
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
            logger.info("✅ geocode_address procedure created")

            await self.session.commit()
            return True

        except Exception as e:
            logger.error(f"❌ Failed to create stored procedures: {e}")
            await self.session.rollback()
            return False

    async def create_views(self) -> bool:
        """
        Create useful views for common queries.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Full store view
            await self.session.execute(text("""
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
            logger.info("✅ v_stores_full view created")

            await self.session.commit()
            return True

        except Exception as e:
            logger.error(f"❌ Failed to create views: {e}")
            await self.session.rollback()
            return False

    async def seed_initial_data(self) -> bool:
        """
        Seed initial data (categories, brands).
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Seed store categories
            categories = [
                ('Supermarket', 'Siêu thị', 'supermarket', '🛒'),
                ('Convenience Store', 'Cửa hàng tiện lợi', 'convenience', '🏪'),
                ('Cafe', 'Quán cà phê', 'cafe', '☕'),
                ('Restaurant', 'Nhà hàng', 'restaurant', '🍽️'),
                ('Pharmacy', 'Nhà thuốc', 'pharmacy', '💊'),
                ('Bank', 'Ngân hàng', 'bank', '🏦'),
                ('ATM', 'ATM', 'atm', '💳'),
                ('Gas Station', 'Cây xăng', 'fuel', '⛽'),
                ('Hospital', 'Bệnh viện', 'hospital', '🏥'),
                ('School', 'Trường học', 'school', '🏫'),
                ('Electronics', 'Điện tử/Điện thoại', 'electronics', '📱'),
                ('Fashion', 'Thời trang', 'fashion', '👕'),
                ('Bakery', 'Tiệm bánh', 'bakery', '🍞'),
                ('Fast Food', 'Đồ ăn nhanh', 'fast_food', '🍔'),
                ('Gym/Fitness', 'Phòng tập', 'gym', '💪'),
                ('Hotel', 'Khách sạn', 'hotel', '🏨'),
                ('Market', 'Chợ', 'market', '🏬'),
                ('Post Office', 'Bưu điện', 'post_office', '📮'),
            ]

            for name, name_vi, slug, icon in categories:
                await self.session.execute(text("""
                    INSERT INTO store_categories (name, name_vi, slug, icon)
                    VALUES (:name, :name_vi, :slug, :icon)
                    ON CONFLICT (slug) DO NOTHING
                """), {"name": name, "name_vi": name_vi, "slug": slug, "icon": icon})

            logger.info(f"✅ Seeded {len(categories)} store categories")

            # Seed popular Vietnamese brands
            brands = [
                # Supermarkets
                ('Co.op Mart', 'coop-mart', 1, 'https://cooponline.vn'),
                ('VinMart', 'vinmart', 1, 'https://vinmart.com'),
                ('Big C', 'big-c', 1, 'https://bigc.vn'),
                ('AEON Mall', 'aeon-mall', 1, 'https://aeon.com.vn'),
                ('Lotte Mart', 'lotte-mart', 1, 'https://lottemart.vn'),
                
                # Convenience stores
                ('Circle K', 'circle-k', 2, 'https://circlek.com.vn'),
                ('GS25', 'gs25', 2, 'https://gs25.com.vn'),
                ('Ministop', 'ministop', 2, None),
                ('7-Eleven', 'seven-eleven', 2, None),
                ('Bách Hóa Xanh', 'bach-hoa-xanh', 2, 'https://bachhoaxanh.com'),
                
                # Coffee
                ('Highlands Coffee', 'highlands-coffee', 3, 'https://highlands.vn'),
                ('Phúc Long', 'phuc-long', 3, 'https://phuclong.com.vn'),
                ('The Coffee House', 'the-coffee-house', 3, 'https://thecoffeehouse.com'),
                ('Trung Nguyên', 'trung-nguyen', 3, 'https://trungnguyenlegend.com'),
                ('Starbucks', 'starbucks', 3, 'https://starbucks.vn'),
                
                # Pharmacy
                ('Pharmacity', 'pharmacity', 5, 'https://pharmacity.vn'),
                ('Long Châu', 'long-chau', 5, 'https://longchau.vn'),
                ('An Khang', 'an-khang', 5, None),
                
                # Electronics
                ('Thế Giới Di Động', 'the-gioi-di-dong', 11, 'https://thegioididong.com'),
                ('FPT Shop', 'fpt-shop', 11, 'https://fptshop.com.vn'),
                ('CellphoneS', 'cellphones', 11, 'https://cellphones.com.vn'),
                ('Điện Máy Xanh', 'dien-may-xanh', 11, 'https://dienmayxanh.com'),
                
                # Fast food
                ('KFC', 'kfc', 14, 'https://kfc.vn'),
                ('Lotteria', 'lotteria', 14, 'https://lotteria.vn'),
                ('Jollibee', 'jollibee', 14, None),
                ('Pizza Hut', 'pizza-hut', 14, None),
            ]

            for name, slug, cat_id, website in brands:
                await self.session.execute(text("""
                    INSERT INTO brands (name, slug, category_id, website)
                    VALUES (:name, :slug, :cat_id, :website)
                    ON CONFLICT (slug) DO NOTHING
                """), {"name": name, "slug": slug, "cat_id": cat_id, "website": website})

            logger.info(f"✅ Seeded {len(brands)} brands")

            await self.session.commit()
            return True

        except Exception as e:
            logger.error(f"❌ Failed to seed initial data: {e}")
            await self.session.rollback()
            return False

    async def run_full_setup(self) -> bool:
        """
        Run complete PostGIS setup.
        
        Returns:
            True if all steps successful, False otherwise
        """
        logger.info("=" * 60)
        logger.info("  🚀 Starting PostGIS Setup for VietStore RAG")
        logger.info("=" * 60)

        steps = [
            ("Enable PostGIS Extensions", self.enable_postgis),
            ("Create Admin Schema", self.create_admin_schema),
            ("Create Store Schema", self.create_store_schema),
            ("Create Search Functions", self.create_search_functions),
            ("Create Indexes", self.create_indexes),
            ("Create Stored Procedures", self.create_stored_procedures),
            ("Create Views", self.create_views),
            ("Seed Initial Data", self.seed_initial_data),
        ]

        success_count = 0
        for step_name, step_func in steps:
            logger.info(f"\n📋 {step_name}...")
            if await step_func():
                success_count += 1
            else:
                logger.error(f"❌ {step_name} failed")

        logger.info("\n" + "=" * 60)
        logger.info(f"  ✅ Setup Complete: {success_count}/{len(steps)} steps successful")
        logger.info("=" * 60)

        return success_count == len(steps)


async def setup_postgis(session: AsyncSession) -> bool:
    """
    Convenience function to setup PostGIS.
    
    Args:
        session: SQLAlchemy async session
        
    Returns:
        True if successful, False otherwise
    """
    manager = PostGISManager(session)
    return await manager.run_full_setup()
