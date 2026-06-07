"""
Data Import Script

Run this script to import Vietnam admin data and OSM POI data.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_import():
    """Run complete data import process."""
    
    logger.info("=" * 60)
    logger.info("  🚀 Starting Data Import for VietStore RAG")
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
            # Step 1: Import Vietnam admin data
            logger.info("\n📍 Step 1/2: Importing Vietnam admin data...")
            from src.db.admin_importer import import_admin_data
            admin_success = await import_admin_data(session)
            
            if not admin_success:
                logger.warning("⚠️  Admin data import failed or incomplete")
            
            # Step 2: Import OSM POI data
            logger.info("\n📍 Step 2/2: Importing OSM POI data...")
            from src.db.osm_importer import import_osm_data
            osm_success = await import_osm_data(session)
            
            if not osm_success:
                logger.warning("⚠️  OSM data import failed or incomplete")
            
            # Final statistics
            logger.info("\n📊 Final Statistics:")
            stats = await session.execute(text("""
                SELECT
                    (SELECT COUNT(*) FROM provinces) as provinces,
                    (SELECT COUNT(*) FROM districts) as districts,
                    (SELECT COUNT(*) FROM wards) as wards,
                    (SELECT COUNT(*) FROM stores) as stores,
                    (SELECT COUNT(*) FROM brands) as brands,
                    (SELECT COUNT(*) FROM store_categories) as categories
            """))
            row = stats.fetchone()
            
            logger.info(f"""
╔══════════════════════════════════════╗
║       📊 FINAL STATISTICS           ║
╠══════════════════════════════════════╣
║  Tỉnh/TP:        {row['provinces']:>8,}          ║
║  Quận/Huyện:      {row['districts']:>8,}          ║
║  Phường/Xã:       {row['wards']:>8,}          ║
║  Cửa hàng:        {row['stores']:>8,}          ║
║  Thương hiệu:     {row['brands']:>8,}          ║
║  Danh mục:        {row['categories']:>8,}          ║
╚══════════════════════════════════════╝
            """)
            
            logger.info("\n✅ Data import complete!")
            
            if admin_success and osm_success:
                logger.info("🎉 All data imported successfully!")
            else:
                logger.warning("⚠️  Some data imports failed - check logs above")
            
            return admin_success and osm_success
            
    except Exception as e:
        logger.error(f"\n❌ Import failed: {e}")
        return False
    
    finally:
        await engine.dispose()


if __name__ == "__main__":
    success = asyncio.run(run_import())
    sys.exit(0 if success else 1)
