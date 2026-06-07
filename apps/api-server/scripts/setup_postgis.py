"""
PostGIS Setup Script

This script sets up PostGIS extensions and creates the spatial schema
for Vietnam geographic data.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from src.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_postgis():
    """Setup PostGIS extensions and schema."""
    
    logger.info("=" * 60)
    logger.info("  🚀 Setting up PostGIS for VietStore RAG")
    logger.info("=" * 60)
    
    # Create async engine
    engine = create_async_engine(
        config.database.url,
        echo=False,
    )
    
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    try:
        async with async_session() as session:
            # Enable PostGIS extensions
            logger.info("\n📋 Step 1/8: Enabling PostGIS extensions...")
            try:
                await session.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
                await session.execute(text("CREATE EXTENSION IF NOT EXISTS postgis_topology"))
                await session.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
                await session.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent"))
                await session.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))
                await session.commit()
                logger.info("✅ PostGIS extensions enabled")
            except Exception as e:
                logger.error(f"❌ Failed to enable extensions: {e}")
                await session.rollback()
                return False
            
            # Check PostGIS version
            result = await session.execute(text("SELECT PostGIS_Version()"))
            version = result.scalar()
            logger.info(f"   PostGIS version: {version}")
            
            # Test vn_unaccent function
            result = await session.execute(
                text("SELECT vn_unaccent('Cà phê ngon quá')")
            )
            normalized = result.scalar()
            logger.info(f"   Vietnamese normalization test: 'Cà phê ngon quá' → '{normalized}'")
            
            # Check if tables already exist
            logger.info("\n📋 Step 2/8: Checking existing tables...")
            tables_to_check = [
                "provinces", "districts", "wards",
                "store_categories", "brands", "stores"
            ]
            
            existing_tables = []
            for table in tables_to_check:
                result = await session.execute(
                    text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')")
                )
                exists = result.scalar()
                if exists:
                    existing_tables.append(table)
                    logger.info(f"   ✓ {table} exists")
                else:
                    logger.info(f"   ✗ {table} not found")
            
            if existing_tables:
                logger.info(f"\n⚠️  {len(existing_tables)} tables already exist.")
                logger.info("   Run Alembic migration to update schema:")
                logger.info("   alembic upgrade head")
            else:
                logger.info("\n📋 Step 3/8: Creating spatial schema...")
                logger.info("   Run Alembic migration to create tables:")
                logger.info("   alembic upgrade head")
            
            # Check stored procedures
            logger.info("\n📋 Step 4/8: Checking stored procedures...")
            procedures = ["find_nearest_stores", "search_stores", "geocode_address"]
            for proc in procedures:
                result = await session.execute(
                    text(f"SELECT EXISTS (SELECT FROM pg_proc WHERE proname = '{proc}')")
                )
                exists = result.scalar()
                if exists:
                    logger.info(f"   ✓ {proc} exists")
                else:
                    logger.info(f"   ✗ {proc} not found")
            
            # Check indexes
            logger.info("\n📋 Step 5/8: Checking spatial indexes...")
            indexes = [
                "idx_stores_location", "idx_stores_search_text",
                "idx_stores_name_trgm", "idx_stores_category"
            ]
            for index in indexes:
                result = await session.execute(
                    text(f"SELECT EXISTS (SELECT FROM pg_indexes WHERE indexname = '{index}')")
                )
                exists = result.scalar()
                if exists:
                    logger.info(f"   ✓ {index} exists")
                else:
                    logger.info(f"   ✗ {index} not found")
            
            # Test sample query
            logger.info("\n📋 Step 6/8: Testing sample queries...")
            try:
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM store_categories
                """))
                count = result.scalar()
                logger.info(f"   Store categories: {count}")
            except Exception as e:
                logger.info(f"   Store categories not yet imported")
            
            try:
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM brands
                """))
                count = result.scalar()
                logger.info(f"   Brands: {count}")
            except Exception as e:
                logger.info(f"   Brands not yet imported")
            
            # Summary
            logger.info("\n" + "=" * 60)
            logger.info("  ✅ PostGIS Setup Check Complete")
            logger.info("=" * 60)
            logger.info("\n📝 Next Steps:")
            logger.info("   1. Run Alembic migration to create/update schema:")
            logger.info("      alembic upgrade head")
            logger.info("   2. Import Vietnam admin data (optional):")
            logger.info("      python -m src.db.postgis_importer")
            logger.info("   3. Import OSM data (optional):")
            logger.info("      python -m src.db.osm_importer")
            logger.info("   4. Test the API:")
            logger.info("      curl http://localhost:8000/api/geo/categories")
            
            return True
            
    except Exception as e:
        logger.error(f"\n❌ Setup failed: {e}")
        return False
    
    finally:
        await engine.dispose()


if __name__ == "__main__":
    success = asyncio.run(setup_postgis())
    sys.exit(0 if success else 1)
