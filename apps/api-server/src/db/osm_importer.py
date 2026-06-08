"""
OpenStreetMap Data Importer

Imports POI data from OpenStreetMap for Vietnam using Overpass API.
"""

import asyncio
import logging
from typing import Optional, Dict
import httpx

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)


class OSMImporter:
    """
    Import OpenStreetMap POI data for Vietnam.
    
    Sources:
    - Overpass API (free, no API key required)
    - Geofabrik (optional, for bulk import)
    """

    OVERPASS_URL = "https://overpass-api.de/api/interpreter"

    # OSM tag mappings to our categories
    CATEGORY_MAP = {
        'supermarket': 'shop=supermarket',
        'convenience': 'shop=convenience',
        'cafe': 'amenity=cafe',
        'restaurant': 'amenity=restaurant',
        'pharmacy': 'amenity=pharmacy',
        'bank': 'amenity=bank',
        'atm': 'amenity=atm',
        'hospital': 'amenity=hospital',
        'school': 'amenity=school',
        'fuel': 'amenity=fuel',
        'bakery': 'shop=bakery',
        'fast_food': 'amenity=fast_food',
        'clothes': 'shop=clothes',
        'electronics': 'shop=electronics',
        'mobile_phone': 'shop=mobile_phone',
    }

    # Popular Vietnamese brands for detection
    BRAND_PATTERNS = {
        'circle k': ['circle k', 'circle-k'],
        'bach hoa xanh': ['bách hóa xanh', 'bach hoa xanh'],
        'highlands': ['highlands', 'highlands coffee'],
        'phuc long': ['phúc long', 'phuclong'],
        'the coffee house': ['the coffee house', 'coffee house'],
        'trung nguyen': ['trung nguyên', 'trungnguyen'],
        'starbucks': ['starbucks'],
        'pharmacity': ['pharmacity'],
        'long chau': ['long châu', 'longchau'],
        'the gioi di dong': ['thế giới di động', 'thegioididong'],
        'fpt shop': ['fpt shop'],
        'cellphones': ['cellphones', 'cellphone s'],
        'dien may xanh': ['điện máy xanh', 'dienmayxanh'],
        'kfc': ['kfc'],
        'lotteria': ['lotteria'],
        'jollibee': ['jollibee'],
        'pizza hut': ['pizza hut'],
        'gs25': ['gs25'],
        'ministop': ['ministop'],
        '7-eleven': ['7-eleven', 'seven-eleven'],
        'vinmart': ['vinmart'],
        'coop mart': ['co.op mart', 'coopmart'],
        'aeon': ['aeon', 'aeon mall'],
        'big c': ['big c', 'bigc'],
        'lotte mart': ['lotte mart', 'lottemart'],
    }

    def __init__(self, session: AsyncSession):
        self.session = session
        self.client = httpx.AsyncClient(timeout=120.0)

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def get_category_map(self) -> Dict[str, int]:
        """Get mapping from category slug to database ID."""
        result = await self.session.execute(
            text("SELECT id, slug FROM store_categories")
        )
        return {row['slug']: row['id'] for row in result}

    async def get_brand_map(self) -> Dict[str, int]:
        """Get mapping from brand name to database ID."""
        result = await self.session.execute(
            text("SELECT id, name, slug FROM brands")
        )
        brand_map = {}
        for row in result:
            brand_map[row['name'].lower()] = row['id']
            brand_map[row['slug']] = row['id']
        return brand_map

    async def import_poi_by_category(
        self,
        category: str,
        limit: int = 1000
    ) -> int:
        """
        Import POI by category using Overpass API.
        
        Args:
            category: Category name (e.g., 'supermarket', 'cafe')
            limit: Maximum number of POI to import
            
        Returns:
            Number of POI imported
        """
        logger.info(f"📍 Importing {category} POI...")
        
        try:
            osm_tag = self.CATEGORY_MAP.get(category)
            if not osm_tag:
                logger.warning(f"Unknown category: {category}")
                return 0

            # Build Overpass query
            query = f"""
            [out:json][timeout:120];
            area["ISO3166-1"="VN"]->.vn;
            (
                node[{osm_tag}](area.vn);
                way[{osm_tag}](area.vn);
            );
            out body;
            >;
            out skel qt;
            """

            resp = await self.client.post(
                self.OVERPASS_URL,
                data={"data": query}
            )
            resp.raise_for_status()
            data = resp.json()

            # Get mappings
            category_map = await self.get_category_map()
            brand_map = await self.get_brand_map()
            cat_id = category_map.get(category)

            imported = 0
            seen_ids = set()

            for element in data.get('elements', []):
                if element.get('id') in seen_ids:
                    continue
                seen_ids.add(element.get('id'))

                # Only process nodes (ways need center calculation)
                if element['type'] != 'node':
                    continue

                tags = element.get('tags', {})
                name = tags.get('name', tags.get('name:vi', ''))
                if not name:
                    continue

                # Detect brand
                brand_id = self._detect_brand(name, tags, brand_map)

                # Build address
                address_parts = []
                for addr_key in ['addr:housenumber', 'addr:street',
                                 'addr:ward', 'addr:district', 'addr:city']:
                    if tags.get(addr_key):
                        address_parts.append(tags[addr_key])
                full_address = ', '.join(address_parts) if address_parts else ''

                # Parse opening hours
                opening_hours = None
                if tags.get('opening_hours'):
                    opening_hours = {'raw': tags['opening_hours']}

                await self.session.execute(text("""
                    INSERT INTO stores (
                        name, brand_id, category_id,
                        house_number, street, full_address,
                        location, phone, website,
                        opening_hours, source, source_id
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6,
                        ST_SetSRID(ST_MakePoint($7, $8), 4326),
                        $9, $10, $11::jsonb, 'osm', $12
                    )
                    ON CONFLICT DO NOTHING
                """), {
                    "name": name,
                    "brand_id": brand_id,
                    "category_id": cat_id,
                    "house_number": tags.get('addr:housenumber'),
                    "street": tags.get('addr:street'),
                    "full_address": full_address,
                    "lng": element['lon'],
                    "lat": element['lat'],
                    "phone": tags.get('phone', tags.get('contact:phone')),
                    "website": tags.get('website', tags.get('contact:website')),
                    "opening_hours": opening_hours,
                    "source_id": str(element['id']),
                })

                imported += 1

            await self.session.commit()
            logger.info(f"  ✅ {category}: {imported} POI imported")
            return imported

        except Exception as e:
            logger.error(f"❌ Failed to import {category}: {e}")
            await self.session.rollback()
            return 0

    def _detect_brand(
        self, name: str, tags: dict, brand_map: dict
    ) -> Optional[int]:
        """Detect brand from name or OSM tags."""
        # Check OSM brand tag
        brand_tag = tags.get('brand', '').lower()
        if brand_tag and brand_tag in brand_map:
            return brand_map[brand_tag]

        # Check name against patterns
        name_lower = name.lower()
        for brand_name, patterns in self.BRAND_PATTERNS.items():
            for pattern in patterns:
                if pattern in name_lower:
                    return brand_map.get(brand_name)

        return None

    async def import_all_categories(self) -> int:
        """
        Import POI for all categories.
        
        Returns:
            Total number of POI imported
        """
        logger.info("=" * 60)
        logger.info("  🚀 Starting OSM POI Import")
        logger.info("=" * 60)

        total_imported = 0
        
        for category in self.CATEGORY_MAP.keys():
            imported = await self.import_poi_by_category(category)
            total_imported += imported
            
            # Rate limiting
            await asyncio.sleep(5)

        await self._print_stats()
        
        logger.info(f"\n✅ Total POI imported: {total_imported}")
        return total_imported

    async def _print_stats(self):
        """Print import statistics."""
        stats = await self.session.execute(text("""
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
║       📊 IMPORT STATISTICS          ║
╠══════════════════════════════════════╣
║  Tỉnh/TP:        {row['provinces']:>8,}          ║
║  Quận/Huyện:      {row['districts']:>8,}          ║
║  Phường/Xã:       {row['wards']:>8,}          ║
║  Cửa hàng:        {row['stores']:>8,}          ║
║  Thương hiệu:     {row['brands']:>8,}          ║
║  Danh mục:        {row['categories']:>8,}          ║
╚══════════════════════════════════════╝
        """)


async def import_osm_data(session: AsyncSession) -> bool:
    """
    Convenience function to import OSM data.
    
    Args:
        session: SQLAlchemy async session
        
    Returns:
        True if successful, False otherwise
    """
    importer = OSMImporter(session)
    return await importer.import_all_categories()
