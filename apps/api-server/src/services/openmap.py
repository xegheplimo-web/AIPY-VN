"""
OpenMap.vn Service

Vietnam-specific location data service with daily updates.
Optimized for Vietnamese addresses and POI data.
"""

import logging
from typing import Any

import requests
from src.config import config

logger = logging.getLogger(__name__)


class OpenMapService:
    """
    OpenMap.vn - Dữ liệu bản địa VN, cập nhật hàng ngày.
    
    Tối ưu cho siêu ứng dụng/đặt hàng/giao hàng tại Việt Nam.
    """

    def __init__(self):
        """Initialize OpenMap service."""
        self.api_key = config.openmap.api_key
        self.base_url = config.openmap.base_url
        self.timeout = config.openmap.timeout

    def is_ready(self) -> bool:
        """Check if the service is ready."""
        return bool(self.api_key)

    async def place_nearby(
        self,
        lat: float,
        lon: float,
        radius: int = 1000,
        types: str = "restaurant,cafe,convenience_store,supermarket",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Tìm POI gần vị trí - tối ưu cho VN.

        Args:
            lat: Latitude
            lon: Longitude
            radius: Bán kính (mét)
            types: Loại POI (comma-separated)
            limit: Số lượng kết quả

        Returns:
            List of POI data
        """
        if not self.is_ready():
            logger.warning("OpenMap not configured, using fallback")
            return []

        try:
            params = {
                "lat": lat,
                "lon": lon,
                "radius": radius,
                "types": types,
                "limit": limit,
                "apikey": self.api_key,
            }

            response = requests.get(
                f"{self.base_url}/nearby",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            logger.info(f"OpenMap found {len(data.get('results', []))} places nearby")
            return data.get("results", [])

        except Exception as e:
            logger.error(f"OpenMap nearby search error: {e}")
            return []

    async def place_details(
        self,
        place_id: str,
    ) -> dict[str, Any] | None:
        """
        Lấy chi tiết POI theo ID.

        Args:
            place_id: ID của địa điểm

        Returns:
            POI details
        """
        if not self.is_ready():
            logger.warning("OpenMap not configured")
            return None

        try:
            params = {
                "place_id": place_id,
                "apikey": self.api_key,
            }

            response = requests.get(
                f"{self.base_url}/details",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            return data.get("result")

        except Exception as e:
            logger.error(f"OpenMap place details error: {e}")
            return None

    async def geocode(
        self,
        address: str,
    ) -> dict[str, Any] | None:
        """
        Chuyển địa chỉ thành tọa độ.

        Args:
            address: Địa chỉ cần tìm

        Returns:
            Geocoding result with lat, lon
        """
        if not self.is_ready():
            logger.warning("OpenMap not configured")
            return None

        try:
            params = {
                "address": address,
                "apikey": self.api_key,
            }

            response = requests.get(
                f"{self.base_url}/geocode",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            return data.get("result")

        except Exception as e:
            logger.error(f"OpenMap geocode error: {e}")
            return None

    async def reverse_geocode(
        self,
        lat: float,
        lon: float,
    ) -> dict[str, Any] | None:
        """
        Chuyển tọa độ thành địa chỉ.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Address details
        """
        if not self.is_ready():
            logger.warning("OpenMap not configured")
            return None

        try:
            params = {
                "lat": lat,
                "lon": lon,
                "apikey": self.api_key,
            }

            response = requests.get(
                f"{self.base_url}/reverse_geocode",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            return data.get("result")

        except Exception as e:
            logger.error(f"OpenMap reverse geocode error: {e}")
            return None

    async def autocomplete(
        self,
        input_text: str,
        lat: float | None = None,
        lon: float | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Gợi ý địa chỉ khi gõ.

        Args:
            input_text: Text người dùng đang gõ
            lat: Latitude (optional, để ưu tiên kết quả gần)
            lon: Longitude (optional)
            limit: Số lượng gợi ý

        Returns:
            List of autocomplete suggestions
        """
        if not self.is_ready():
            logger.warning("OpenMap not configured")
            return []

        try:
            params = {
                "input": input_text,
                "limit": limit,
                "apikey": self.api_key,
            }

            if lat and lon:
                params["location"] = f"{lat},{lon}"

            response = requests.get(
                f"{self.base_url}/autocomplete",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            return data.get("predictions", [])

        except Exception as e:
            logger.error(f"OpenMap autocomplete error: {e}")
            return []

    async def search_text(
        self,
        query: str,
        lat: float | None = None,
        lon: float | None = None,
        radius: int = 5000,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Tìm kiếm theo text query.

        Args:
            query: Từ khóa tìm kiếm
            lat: Latitude (optional)
            lon: Longitude (optional)
            radius: Bán kính tìm kiếm (mét)
            limit: Số lượng kết quả

        Returns:
            List of search results
        """
        if not self.is_ready():
            logger.warning("OpenMap not configured")
            return []

        try:
            params = {
                "query": query,
                "limit": limit,
                "apikey": self.api_key,
            }

            if lat and lon:
                params["location"] = f"{lat},{lon}"
                params["radius"] = radius

            response = requests.get(
                f"{self.base_url}/search",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            return data.get("results", [])

        except Exception as e:
            logger.error(f"OpenMap text search error: {e}")
            return []


# Global service instance
openmap_service = OpenMapService()


def get_openmap_service() -> OpenMapService:
    """Get the global OpenMap service instance."""
    return openmap_service
