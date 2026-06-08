"""
Vietnam Admin Data Importer

Imports Vietnam administrative data (63 provinces, 713 districts, 11,162 wards)
from provinces.open-api.vn API.
"""

import logging

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class VietnamAdminImporter:
    """
    Import Vietnam administrative data into PostGIS.
    
    Sources:
    - provinces.open-api.vn API (free, no API key required)
    """

    ADMIN_API = "https://provinces.open-api.vn/api"

    def __init__(self, session: AsyncSession):
        self.session = session
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def import_provinces(self) -> int:
        """
        Import 63 provinces/cities.
        
        Returns:
            Number of provinces imported
        """
        logger.info("📍 Importing provinces...")
        
        try:
            resp = await self.client.get(f"{self.ADMIN_API}/p/")
            resp.raise_for_status()
            provinces = resp.json()

            imported = 0
            for p in provinces:
                # Get detailed info with coordinates
                detail_resp = await self.client.get(
                    f"{self.ADMIN_API}/p/{p['code']}",
                    params={"depth": 2}  # Get districts
                )
                detail = detail_resp.json()

                # Geocode center coordinates
                center = await self._geocode_nominatim(detail['name'])

                await self.session.execute(text("""
                    INSERT INTO provinces (code, name, name_en, full_name, slug, type, center)
                    VALUES ($1, $2, $3, $4, $5, $6,
                        CASE WHEN $7 IS NOT NULL AND $8 IS NOT NULL
                            THEN ST_SetSRID(ST_MakePoint($8, $7), 4326)
                            ELSE NULL
                        END
                    )
                    ON CONFLICT (code) DO UPDATE SET
                        name = EXCLUDED.name,
                        center = EXCLUDED.center
                """), {
                    "code": p['code'],
                    "name": detail.get('name', ''),
                    "name_en": detail.get('name_en', ''),
                    "full_name": detail.get('name', ''),
                    "slug": self._slugify(detail.get('name', '')),
                    "type": self._get_admin_type(detail.get('division_type', '')),
                    "lat": center[0] if center else None,
                    "lng": center[1] if center else None,
                })

                imported += 1
                logger.info(f"  ✅ {detail['name']}")

            await self.session.commit()
            logger.info(f"✅ Imported {imported} provinces")
            return imported

        except Exception as e:
            logger.error(f"❌ Failed to import provinces: {e}")
            await self.session.rollback()
            return 0

    async def import_districts(self) -> int:
        """
        Import 713 districts/counties.
        
        Returns:
            Number of districts imported
        """
        logger.info("📍 Importing districts...")
        
        try:
            # Get all provinces first
            provinces_resp = await self.client.get(f"{self.ADMIN_API}/p/")
            provinces = provinces_resp.json()

            imported = 0
            for p in provinces:
                # Get districts for this province
                detail_resp = await self.client.get(
                    f"{self.ADMIN_API}/p/{p['code']}",
                    params={"depth": 2}
                )
                detail = detail_resp.json()

                for d in detail.get('districts', []):
                    # Geocode center
                    center = await self._geocode_nominatim(
                        f"{d['name']}, {detail['name']}"
                    )

                    await self.session.execute(text("""
                        INSERT INTO districts 
                            (code, name, name_en, full_name, slug, type, 
                             province_code, center)
                        VALUES ($1,$2,$3,$4,$5,$6,$7,
                            CASE WHEN $8 IS NOT NULL AND $9 IS NOT NULL
                                THEN ST_SetSRID(ST_MakePoint($9,$8), 4326)
                                ELSE NULL
                            END
                        )
                        ON CONFLICT (code) DO UPDATE SET
                            name = EXCLUDED.name,
                            center = EXCLUDED.center
                    """), {
                        "code": d['code'],
                        "name": d.get('name', ''),
                        "name_en": d.get('name_en', ''),
                        "full_name": d.get('name', ''),
                        "slug": self._slugify(d.get('name', '')),
                        "type": self._get_admin_type(d.get('division_type', '')),
                        "province_code": p['code'],
                        "lat": center[0] if center else None,
                        "lng": center[1] if center else None,
                    })

                    imported += 1

                logger.info(f"  ✅ {detail['name']}: {len(detail.get('districts', []))} districts")

            await self.session.commit()
            logger.info(f"✅ Imported {imported} districts")
            return imported

        except Exception as e:
            logger.error(f"❌ Failed to import districts: {e}")
            await self.session.rollback()
            return 0

    async def import_wards(self) -> int:
        """
        Import 11,162 wards/communes.
        
        Returns:
            Number of wards imported
        """
        logger.info("📍 Importing wards...")
        
        try:
            # Get all provinces
            provinces_resp = await self.client.get(f"{self.ADMIN_API}/p/")
            provinces = provinces_resp.json()

            imported = 0
            for p in provinces:
                # Get districts
                detail_resp = await self.client.get(
                    f"{self.ADMIN_API}/p/{p['code']}",
                    params={"depth": 3}  # Get wards
                )
                detail = detail_resp.json()

                for d in detail.get('districts', []):
                    for w in d.get('wards', []):
                        await self.session.execute(text("""
                            INSERT INTO wards 
                                (code, name, name_en, full_name, slug, 
                                 type, district_code)
                            VALUES ($1,$2,$3,$4,$5,$6,$7)
                            ON CONFLICT (code) DO UPDATE SET
                                name = EXCLUDED.name
                        """), {
                            "code": w['code'],
                            "name": w.get('name', ''),
                            "name_en": w.get('name_en', ''),
                            "full_name": w.get('name', ''),
                            "slug": self._slugify(w.get('name', '')),
                            "type": self._get_admin_type(w.get('division_type', '')),
                            "district_code": d['code'],
                        })

                        imported += 1

                logger.info(f"  ✅ {detail['name']}: imported wards")

            await self.session.commit()
            logger.info(f"✅ Imported {imported} wards")
            return imported

        except Exception as e:
            logger.error(f"❌ Failed to import wards: {e}")
            await self.session.rollback()
            return 0

    async def _geocode_nominatim(self, query: str) -> tuple[float, float] | None:
        """
        Geocode using Nominatim (fallback).
        
        Args:
            query: Address to geocode
            
        Returns:
            (lat, lng) tuple or None
        """
        try:
            params = {
                "q": f"{query}, Vietnam",
                "format": "json",
                "limit": 1,
                "countrycodes": "vn",
            }
            resp = await self.client.get(
                "https://nominatim.openstreetmap.org/search",
                params=params,
                headers={"User-Agent": "AIPY-VN-Importer/1.0"}
            )
            resp.raise_for_status()
            results = resp.json()

            if results:
                return (
                    float(results[0]['lat']),
                    float(results[0]['lon'])
                )
        except Exception as e:
            logger.debug(f"Geocode failed for {query}: {e}")

        return None

    @staticmethod
    def _slugify(text: str) -> str:
        """Create slug from Vietnamese text."""
        import re
        import unicodedata
        text = unicodedata.normalize('NFD', text)
        text = ''.join(
            c for c in text 
            if unicodedata.category(c) != 'Mn'
        )
        text = text.replace('đ', 'd').replace('Đ', 'D')
        text = re.sub(r'[^\w\s-]', '', text.lower())
        text = re.sub(r'[-\s]+', '-', text).strip('-')
        return text

    @staticmethod
    def _get_admin_type(division_type: str) -> str:
        """Normalize admin division type."""
        type_map = {
            'thành phố trung ương': 'thành phố trung ương',
            'tỉnh': 'tỉnh',
            'quận': 'quận',
            'huyện': 'huyện',
            'thị xã': 'thị xã',
            'thành phố': 'thành phố',
            'phường': 'phường',
            'xã': 'xã',
            'thị trấn': 'thị trấn',
        }
        return type_map.get(division_type, division_type)

    async def run_full_import(self) -> bool:
        """
        Run complete admin data import.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("=" * 60)
        logger.info("  🚀 Starting Vietnam Admin Data Import")
        logger.info("=" * 60)

        try:
            # Import provinces
            provinces = await self.import_provinces()
            if provinces == 0:
                logger.warning("No provinces imported")

            # Import districts
            districts = await self.import_districts()
            if districts == 0:
                logger.warning("No districts imported")

            # Import wards
            wards = await self.import_wards()
            if wards == 0:
                logger.warning("No wards imported")

            # Print statistics
            await self._print_stats()

            logger.info("\n✅ Admin data import complete!")
            return True

        except Exception as e:
            logger.error(f"\n❌ Import failed: {e}")
            return False

        finally:
            await self.close()

    async def _print_stats(self):
        """Print import statistics."""
        stats = await self.session.execute(text("""
            SELECT
                (SELECT COUNT(*) FROM provinces) as provinces,
                (SELECT COUNT(*) FROM districts) as districts,
                (SELECT COUNT(*) FROM wards) as wards
        """))
        row = stats.fetchone()

        logger.info(f"""
╔══════════════════════════════════════╗
║       📊 IMPORT STATISTICS          ║
╠══════════════════════════════════════╣
║  Tỉnh/TP:        {row['provinces']:>8,}          ║
║  Quận/Huyện:      {row['districts']:>8,}          ║
║  Phường/Xã:       {row['wards']:>8,}          ║
╚══════════════════════════════════════╝
        """)


async def import_admin_data(session: AsyncSession) -> bool:
    """
    Convenience function to import admin data.
    
    Args:
        session: SQLAlchemy async session
        
    Returns:
        True if successful, False otherwise
    """
    importer = VietnamAdminImporter(session)
    return await importer.run_full_import()
