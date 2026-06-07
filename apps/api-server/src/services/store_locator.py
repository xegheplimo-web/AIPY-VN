"""
Vietnam Store Locator Service

Lấy tọa độ & địa chỉ cửa hàng tại VN sử dụng OpenMap.vn (ưu tiên) và OpenStreetMap (fallback)
"""

import logging
import time
import math
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
import requests

from src.config import config

logger = logging.getLogger(__name__)


@dataclass
class Store:
    """Store data model."""

    name: str
    latitude: float
    longitude: float
    address: str
    city: str
    district: str
    ward: str
    phone: Optional[str] = None
    category: Optional[str] = None
    opening_hours: Optional[str] = None
    website: Optional[str] = None
    osm_id: Optional[int] = None


class VietnamStoreLocator:
    """
    Lấy tọa độ & địa chỉ cửa hàng tại VN
    sử dụng OpenStreetMap (MIỄN PHÍ, không cần API key)
    """

    # Nominatim API (miễn phí, giới hạn 1 req/s)
    NOMINATIM_URL = "https://nominatim.openstreetmap.org"

    # Overpass API (miễn phí, không giới hạn)
    OVERPASS_URL = "https://overpass-api.de/api/interpreter"

    def __init__(self):
        """Initialize store locator."""
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "AIPY-VN-StoreLocator/1.0 (contact@example.com)"}
        )

        # Try to import OpenMap service
        try:
            from src.services.openmap import get_openmap_service

            self.openmap = get_openmap_service()
            self.use_openmap = self.openmap.is_ready()
            if self.use_openmap:
                logger.info("OpenMap.vn service enabled (priority)")
        except Exception as e:
            logger.warning(f"OpenMap service not available: {e}")
            self.openmap = None
            self.use_openmap = False

    async def _try_openmap_nearby(
        self, lat: float, lon: float, category: str, radius_km: float
    ) -> List[Store]:
        """Try OpenMap.vn first (priority for Vietnam data)."""
        if not self.use_openmap:
            return []

        try:
            # Map category to OpenMap types
            type_map = {
                "supermarket": "supermarket",
                "convenience": "convenience_store",
                "cafe": "cafe",
                "restaurant": "restaurant",
                "pharmacy": "pharmacy",
                "bank": "bank",
                "fuel": "gas_station",
                "bakery": "bakery",
                "fast_food": "fast_food",
            }

            openmap_type = type_map.get(category, category)
            results = await self.openmap.place_nearby(
                lat=lat,
                lon=lon,
                radius=int(radius_km * 1000),
                types=openmap_type,
                limit=50,
            )

            # Convert OpenMap results to Store objects
            stores = []
            for r in results:
                stores.append(
                    Store(
                        name=r.get("name", "Không tên"),
                        latitude=r.get("lat", 0),
                        longitude=r.get("lon", 0),
                        address=r.get("address", ""),
                        city=r.get("city", ""),
                        district=r.get("district", ""),
                        ward=r.get("ward", ""),
                        phone=r.get("phone"),
                        category=category,
                        opening_hours=r.get("opening_hours"),
                        website=r.get("website"),
                    )
                )

            logger.info(f"OpenMap found {len(stores)} {category} stores")
            return stores

        except Exception as e:
            logger.error(f"OpenMap nearby search failed: {e}")
            return []

    async def search_stores_by_name(
        self, query: str, city: str = "Hồ Chí Minh", limit: int = 50
    ) -> List[Store]:
        """
        Tìm cửa hàng theo tên.

        Ví dụ:
            search_stores_by_name("Bách Hóa Xanh")
            search_stores_by_name("Circle K", city="Hà Nội")
            search_stores_by_name("Highland Coffee")
        """
        # Try OpenMap first if available
        if self.use_openmap:
            try:
                results = await self.openmap.search_text(
                    query, lat=None, lon=None, limit=limit
                )
                if results:
                    # Convert to Store objects
                    stores = []
                    for r in results:
                        stores.append(
                            Store(
                                name=r.get("name", query),
                                latitude=r.get("lat", 0),
                                longitude=r.get("lon", 0),
                                address=r.get("address", ""),
                                city=r.get("city", city),
                                district=r.get("district", ""),
                                ward=r.get("ward", ""),
                                phone=r.get("phone"),
                                category=r.get("type", ""),
                                opening_hours=r.get("opening_hours"),
                                website=r.get("website"),
                            )
                        )
                    logger.info(f"OpenMap found {len(stores)} stores for {query}")
                    return stores
            except Exception as e:
                logger.error(f"OpenMap search failed: {e}")

        # Fallback to Nominatim
        params = {
            "q": f"{query}, {city}, Vietnam",
            "format": "json",
            "addressdetails": 1,
            "limit": limit,
            "countrycodes": "vn",
            "accept-language": "vi",
        }

        try:
            response = self.session.get(f"{self.NOMINATIM_URL}/search", params=params)
            response.raise_for_status()
            results = response.json()

            stores = []
            for r in results:
                addr = r.get("address", {})
                store = Store(
                    name=r.get("display_name", "").split(",")[0],
                    latitude=float(r["lat"]),
                    longitude=float(r["lon"]),
                    address=r.get("display_name", ""),
                    city=addr.get("city", addr.get("town", city)),
                    district=addr.get("suburb", addr.get("district", "")),
                    ward=addr.get("quarter", addr.get("neighbourhood", "")),
                    category=r.get("type", ""),
                    osm_id=r.get("osm_id"),
                )
                stores.append(store)
                time.sleep(1)  # Nominatim rate limit: 1 req/s

            logger.info(f"Found {len(stores)} stores for query: {query}")
            return stores

        except Exception as e:
            logger.error(f"Error searching stores by name: {e}")
            return []

    def search_stores_by_area(
        self,
        category: str,
        city: str = "Hồ Chí Minh",
        radius_km: float = 10,
    ) -> List[Store]:
        """
        Tìm TẤT CẢ cửa hàng theo loại trong khu vực.

        Categories:
            "supermarket"   - Siêu thị
            "convenience"   - Cửa hàng tiện lợi (Circle K, GS25, 7-Eleven...)
            "cafe"          - Quán cà phê
            "restaurant"    - Nhà hàng
            "pharmacy"      - Nhà thuốc
            "bank"          - Ngân hàng
            "atm"           - ATM
            "hospital"      - Bệnh viện
            "school"        - Trường học
            "fuel"          - Cây xăng
            "bakery"        - Tiệm bánh
            "fast_food"     - Fast food
            "clothes"       - Cửa hàng quần áo
            "electronics"   - Cửa hàng điện tử
            "mobile_phone"  - Cửa hàng điện thoại
        """
        # Lấy tọa độ trung tâm thành phố
        center = self._geocode_city(city)
        if not center:
            logger.warning(f"City not found: {city}")
            return []

        lat, lon = center
        radius_m = radius_km * 1000

        # Map category to OSM tags
        tag_map = {
            "supermarket": 'node["shop"="supermarket"]',
            "convenience": 'node["shop"="convenience"]',
            "cafe": 'node["amenity"="cafe"]',
            "restaurant": 'node["amenity"="restaurant"]',
            "pharmacy": 'node["amenity"="pharmacy"]',
            "bank": 'node["amenity"="bank"]',
            "atm": 'node["amenity"="atm"]',
            "hospital": 'node["amenity"="hospital"]',
            "school": 'node["amenity"="school"]',
            "fuel": 'node["amenity"="fuel"]',
            "bakery": 'node["shop"="bakery"]',
            "fast_food": 'node["amenity"="fast_food"]',
            "clothes": 'node["shop"="clothes"]',
            "electronics": 'node["shop"="electronics"]',
            "mobile_phone": 'node["shop"="mobile_phone"]',
        }

        osm_tag = tag_map.get(category, f'node["shop"="{category}"]')

        # Overpass QL query
        query = f"""
        [out:json][timeout:60];
        (
            {osm_tag}(around:{radius_m},{lat},{lon});
            way["shop"="{category}"](around:{radius_m},{lat},{lon});
        );
        out body;
        >;
        out skel qt;
        """

        try:
            response = self.session.post(self.OVERPASS_URL, data={"data": query})
            response.raise_for_status()
            data = response.json()

            stores = []
            for element in data.get("elements", []):
                if element["type"] != "node":
                    continue

                tags = element.get("tags", {})

                store = Store(
                    name=tags.get("name", tags.get("name:vi", "Không tên")),
                    latitude=element["lat"],
                    longitude=element["lon"],
                    address=self._build_address(tags),
                    city=tags.get("addr:city", city),
                    district=tags.get("addr:district", ""),
                    ward=tags.get("addr:ward", ""),
                    phone=tags.get("phone", tags.get("contact:phone")),
                    category=category,
                    opening_hours=tags.get("opening_hours"),
                    website=tags.get("website", tags.get("contact:website")),
                    osm_id=element.get("id"),
                )
                stores.append(store)

            logger.info(f"Found {len(stores)} {category} stores in {city}")
            return stores

        except Exception as e:
            logger.error(f"Error searching stores by area: {e}")
            return []

    def search_chain_stores(
        self,
        brand: str,
        city: str = "",
    ) -> List[Store]:
        """
        Tìm tất cả cửa hàng của một chuỗi.

        Ví dụ:
            search_chain_stores("Circle K")
            search_chain_stores("Bách Hóa Xanh")
            search_chain_stores("Highland Coffee")
            search_chain_stores("Thế Giới Di Động")
            search_chain_stores("FPT Shop")
            search_chain_stores("Pharmacity")
            search_chain_stores("GS25")
            search_chain_stores("Ministop")
            search_chain_stores("VinMart")
            search_chain_stores("Co.op Mart")
        """
        area_filter = ""
        if city:
            center = self._geocode_city(city)
            if center:
                lat, lon = center
                area_filter = f"(around:50000,{lat},{lon})"

        if not area_filter:
            # Tìm trong toàn bộ Việt Nam
            area_filter = '(area["ISO3166-1"="VN"])'

        query = f"""
        [out:json][timeout:120];
        area["ISO3166-1"="VN"]->.vn;
        (
            node["name"~"{brand}",i](area.vn);
            node["brand"~"{brand}",i](area.vn);
            node["operator"~"{brand}",i](area.vn);
            way["name"~"{brand}",i](area.vn);
            way["brand"~"{brand}",i](area.vn);
        );
        out body;
        >;
        out skel qt;
        """

        try:
            response = self.session.post(self.OVERPASS_URL, data={"data": query})
            response.raise_for_status()
            data = response.json()

            stores = []
            seen_ids = set()

            for element in data.get("elements", []):
                if element.get("id") in seen_ids:
                    continue
                seen_ids.add(element.get("id"))

                if "lat" not in element or "lon" not in element:
                    continue

                tags = element.get("tags", {})

                store = Store(
                    name=tags.get("name", brand),
                    latitude=element["lat"],
                    longitude=element["lon"],
                    address=self._build_address(tags),
                    city=tags.get("addr:city", ""),
                    district=tags.get("addr:district", ""),
                    ward=tags.get("addr:ward", ""),
                    phone=tags.get("phone", tags.get("contact:phone")),
                    category=tags.get("shop", tags.get("amenity", "")),
                    opening_hours=tags.get("opening_hours"),
                    website=tags.get("website"),
                    osm_id=element.get("id"),
                )
                stores.append(store)

            logger.info(f"Found {len(stores)} {brand} stores")
            return stores

        except Exception as e:
            logger.error(f"Error searching chain stores: {e}")
            return []

    async def reverse_geocode(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Chuyển tọa độ thành địa chỉ đầy đủ.

        Priority: OpenMap.vn → Nominatim

        Ví dụ: reverse_geocode(10.7769, 106.7009)
        → "123 Nguyễn Huệ, Phường Bến Nghé, Quận 1, TP.HCM"
        """
        # Try OpenMap first
        if self.use_openmap:
            try:
                result = await self.openmap.reverse_geocode(lat, lon)
                if result:
                    return {
                        "full_address": result.get("address", ""),
                        "house_number": result.get("house_number", ""),
                        "road": result.get("road", ""),
                        "ward": result.get("ward", ""),
                        "district": result.get("district", ""),
                        "city": result.get("city", ""),
                        "state": result.get("state", ""),
                        "postcode": result.get("postcode", ""),
                        "country": result.get("country", "Việt Nam"),
                    }
            except Exception as e:
                logger.error(f"OpenMap reverse geocode failed: {e}")

        # Fallback to Nominatim
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "addressdetails": 1,
            "accept-language": "vi",
            "zoom": 18,
        }

        try:
            response = self.session.get(f"{self.NOMINATIM_URL}/reverse", params=params)
            response.raise_for_status()
            data = response.json()
            addr = data.get("address", {})

            return {
                "full_address": data.get("display_name", ""),
                "house_number": addr.get("house_number", ""),
                "road": addr.get("road", ""),
                "ward": addr.get("quarter", addr.get("neighbourhood", "")),
                "district": addr.get("suburb", addr.get("district", "")),
                "city": addr.get("city", addr.get("town", "")),
                "state": addr.get("state", ""),
                "postcode": addr.get("postcode", ""),
                "country": addr.get("country", "Việt Nam"),
            }

        except Exception as e:
            logger.error(f"Error reverse geocoding: {e}")
            return {}

    async def geocode_address(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Chuyển địa chỉ thành tọa độ.

        Priority: OpenMap.vn → Nominatim

        Ví dụ: geocode_address("123 Nguyễn Huệ, Quận 1, TP.HCM")
        → {"lat": 10.7769, "lon": 106.7009}
        """
        # Try OpenMap first
        if self.use_openmap:
            try:
                result = await self.openmap.geocode(address)
                if result:
                    return {
                        "latitude": result.get("lat", 0),
                        "longitude": result.get("lon", 0),
                        "full_address": result.get("address", ""),
                        "ward": result.get("ward", ""),
                        "district": result.get("district", ""),
                        "city": result.get("city", ""),
                        "confidence": 1.0,
                    }
            except Exception as e:
                logger.error(f"OpenMap geocode failed: {e}")

        # Fallback to Nominatim
        params = {
            "q": f"{address}, Vietnam",
            "format": "json",
            "addressdetails": 1,
            "limit": 1,
            "countrycodes": "vn",
            "accept-language": "vi",
        }

        try:
            response = self.session.get(f"{self.NOMINATIM_URL}/search", params=params)
            response.raise_for_status()
            results = response.json()

            if not results:
                return None

            r = results[0]
            addr = r.get("address", {})

            return {
                "latitude": float(r["lat"]),
                "longitude": float(r["lon"]),
                "full_address": r.get("display_name", ""),
                "ward": addr.get("quarter", ""),
                "district": addr.get("suburb", addr.get("district", "")),
                "city": addr.get("city", addr.get("town", "")),
                "confidence": float(r.get("importance", 0)),
            }

        except Exception as e:
            logger.error(f"Error geocoding address: {e}")
            return None

    async def find_nearest_stores(
        self,
        lat: float,
        lon: float,
        category: str = "convenience",
        radius_km: float = 2,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Tìm cửa hàng gần nhất từ vị trí hiện tại.

        Priority: OpenMap.vn → Overpass API
        """
        # Try OpenMap first (Vietnam-optimized)
        stores = []
        if self.use_openmap:
            stores = await self._try_openmap_nearby(lat, lon, category, radius_km)

        # Fallback to Overpass if OpenMap returns no results
        if not stores:
            stores = self._search_nearby(lat, lon, category, radius_km)

        # Tính khoảng cách
        results = []
        for store in stores:
            distance = self._haversine(lat, lon, store.latitude, store.longitude)
            results.append(
                {
                    **asdict(store),
                    "distance_km": round(distance, 2),
                    "distance_text": self._format_distance(distance),
                }
            )

        # Sắp xếp theo khoảng cách
        results.sort(key=lambda x: x["distance_km"])
        return results[:limit]

    def _search_nearby(
        self, lat: float, lon: float, category: str, radius_km: float
    ) -> List[Store]:
        """Tìm trực tiếp bằng tọa độ."""
        radius_m = radius_km * 1000

        tag_map = {
            "supermarket": '"shop"="supermarket"',
            "convenience": '"shop"="convenience"',
            "cafe": '"amenity"="cafe"',
            "restaurant": '"amenity"="restaurant"',
            "pharmacy": '"amenity"="pharmacy"',
            "bank": '"amenity"="bank"',
            "fuel": '"amenity"="fuel"',
        }

        osm_tag = tag_map.get(category, f'"shop"="{category}"')

        query = f"""
        [out:json][timeout:30];
        node[{osm_tag}](around:{radius_m},{lat},{lon});
        out body;
        """

        try:
            response = self.session.post(self.OVERPASS_URL, data={"data": query})
            response.raise_for_status()
            data = response.json()

            stores = []
            for el in data.get("elements", []):
                tags = el.get("tags", {})
                stores.append(
                    Store(
                        name=tags.get("name", "Không tên"),
                        latitude=el["lat"],
                        longitude=el["lon"],
                        address=self._build_address(tags),
                        city=tags.get("addr:city", ""),
                        district=tags.get("addr:district", ""),
                        ward=tags.get("addr:ward", ""),
                        phone=tags.get("phone"),
                        category=category,
                        opening_hours=tags.get("opening_hours"),
                        osm_id=el.get("id"),
                    )
                )

            return stores

        except Exception as e:
            logger.error(f"Error searching nearby: {e}")
            return []

    def _geocode_city(self, city: str) -> Optional[tuple[float, float]]:
        """Lấy tọa độ trung tâm thành phố."""
        city_coords = {
            "Hồ Chí Minh": (10.7769, 106.7009),
            "HCM": (10.7769, 106.7009),
            "TP.HCM": (10.7769, 106.7009),
            "Hà Nội": (21.0285, 105.8542),
            "Đà Nẵng": (16.0544, 108.2022),
            "Cần Thơ": (10.0452, 105.7469),
            "Hải Phòng": (20.8449, 106.6881),
            "Biên Hòa": (10.9574, 106.8426),
            "Nha Trang": (12.2388, 109.1967),
            "Huế": (16.4637, 107.5909),
            "Vũng Tàu": (10.3460, 107.0843),
            "Đà Lạt": (11.9404, 108.4583),
            "Buôn Ma Thuột": (12.6800, 108.0378),
            "Quy Nhon": (13.7830, 109.2197),
            "Thủ Đức": (10.8513, 106.7530),
            "Bình Dương": (11.0254, 106.6530),
            "Long An": (10.5360, 106.4110),
        }

        if city in city_coords:
            return city_coords[city]

        # Fallback: geocode
        params = {
            "q": f"{city}, Vietnam",
            "format": "json",
            "limit": 1,
            "countrycodes": "vn",
        }
        try:
            response = self.session.get(f"{self.NOMINATIM_URL}/search", params=params)
            results = response.json()

            if results:
                return (float(results[0]["lat"]), float(results[0]["lon"]))
        except Exception as e:
            logger.error(f"Error geocoding city: {e}")

        return None

    @staticmethod
    def _build_address(tags: dict) -> str:
        """Xây dựng địa chỉ từ OSM tags."""
        parts = []
        for key in [
            "addr:housenumber",
            "addr:street",
            "addr:ward",
            "addr:district",
            "addr:city",
        ]:
            if tags.get(key):
                parts.append(tags[key])

        return ", ".join(parts) if parts else tags.get("address", "")

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Tính khoảng cách giữa 2 điểm (km)."""
        R = 6371  # km

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    @staticmethod
    def _format_distance(km: float) -> str:
        """Format khoảng cách."""
        if km < 1:
            return f"{int(km * 1000)}m"
        return f"{km:.1f}km"


# Global service instance
store_locator = VietnamStoreLocator()


def get_store_locator() -> VietnamStoreLocator:
    """Get the global store locator instance."""
    return store_locator
