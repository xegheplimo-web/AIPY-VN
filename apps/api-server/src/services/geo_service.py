"""GeoService — Smart geocoding with L1 (Redis) + L2 (SQLite) cache."""
from __future__ import annotations
import asyncio, logging, time
from typing import Any
import httpx
from src.config import config
from src.services.geo_cache import GeoCacheService, get_geo_cache
from src.services.geo_memory import GeoMemoryDB, get_geo_memory

logger = logging.getLogger(__name__)
DEFAULT_API = getattr(config, "geo_api", "nominatim")
API_TIMEOUT = 10.0
RATE_LIMIT_MS = 1000
_HEADERS = {"User-Agent": "VietStore-RAG/1.0 (contact@aipy.vn)"}

class GeoService:
    def __init__(self, l1_cache=None, l2_memory=None, default_api="nominatim") -> None:
        self.l1 = l1_cache or get_geo_cache()
        self.l2 = l2_memory or get_geo_memory()
        self.default_api = default_api
        self._last_request_time = 0.0
        self._lock = asyncio.Lock()

    async def geocode(self, address: str, api=None, force_refresh=False) -> Any:
        api = api or self.default_api
        t0 = time.perf_counter()
        if not force_refresh:
            try:
                l1_data = await self.l1.get_geocode(address)
                if l1_data:
                    elapsed = (time.perf_counter() - t0) * 1000
                    self.l2.log_api_call(api, address, True, elapsed)
                    return {**l1_data, "source": "redis", "response_time_ms": round(elapsed, 2)}
            except Exception:
                pass
            l2_data = self.l2.lookup(address)
            if l2_data:
                elapsed = (time.perf_counter() - t0) * 1000
                self.l2.log_api_call(api, address, True, elapsed)
                try:
                    await self.l1.set_geocode(address, {"latitude": l2_data["latitude"], "longitude": l2_data["longitude"], "address": l2_data["address_original"]})
                except Exception:
                    pass
                return {"latitude": l2_data["latitude"], "longitude": l2_data["longitude"], "address": l2_data["address_original"], "source": "memory", "response_time_ms": round(elapsed, 2), "metadata": {"city": l2_data.get("city"), "district": l2_data.get("district"), "ward": l2_data.get("ward"), "street": l2_data.get("street")}}
        try:
            result = await self._call_api(address, api)
            elapsed = (time.perf_counter() - t0) * 1000
            if result:
                try:
                    await self.l1.set_geocode(address, result)
                except Exception:
                    pass
                self.l2.save(address, result["latitude"], result["longitude"], result.get("raw"), result.get("source_api", "unknown"), result.get("metadata"))
                self.l2.log_api_call(api, address, False, elapsed)
                return {**result, "source": f"api:{api}", "response_time_ms": round(elapsed, 2)}
        except Exception as e:
            elapsed = (time.perf_counter() - t0) * 1000
            self.l2.log_api_call(api, address, False, elapsed, success=False, error=str(e))
            logger.error(f"Geocode API error: {e}")
        return None

    async def reverse_geocode(self, lat: float, lng: float, api=None) -> Any:
        api = api or self.default_api
        coord_key = f"@reverse:{lat:.6f},{lng:.6f}"
        t0 = time.perf_counter()
        try:
            l1_data = await self.l1.get_reverse_geocode(lat, lng)
            if l1_data:
                elapsed = (time.perf_counter() - t0) * 1000
                return {**l1_data, "source": "redis", "response_time_ms": round(elapsed, 2)}
        except Exception:
            pass
        l2_data = self.l2.lookup_by_coords(lat, lng)
        if l2_data:
            elapsed = (time.perf_counter() - t0) * 1000
            try:
                await self.l1.set_reverse_geocode(lat, lng, {"address": l2_data["address_original"], "latitude": lat, "longitude": lng})
            except Exception:
                pass
            return {"address": l2_data["address_original"], "latitude": lat, "longitude": lng, "source": "memory", "response_time_ms": round(elapsed, 2)}
        result = await self._call_reverse_api(lat, lng, api)
        if result:
            elapsed = (time.perf_counter() - t0) * 1000
            try:
                await self.l1.set_reverse_geocode(lat, lng, result)
            except Exception:
                pass
            self.l2.save(coord_key, lat, lng, result.get("raw"), api)
            return {**result, "source": f"api:{api}", "response_time_ms": round(elapsed, 2)}
        return None

    async def batch_geocode(self, addresses: list[str], api=None) -> list[Any]:
        results, api_calls = [], 0
        for addr in addresses:
            result = await self.geocode(addr, api=api)
            if result:
                if result["source"].startswith("api:"): api_calls += 1
                results.append(result)
            else:
                results.append({"address": addr, "error": "Geocode failed"})
        logger.info(f"Batch: {len(addresses)} items, {api_calls} API calls, {len(addresses) - api_calls} cached")
        return results

    def get_stats(self) -> Any:
        l2_stats = self.l2.get_stats()
        return {**l2_stats, "l1_cache_enabled": getattr(self.l1, "enabled", False), "db_path": str(self.l2.db_path)}

    async def _rate_limit(self, min_interval_ms=RATE_LIMIT_MS) -> None:
        async with self._lock:
            elapsed = (time.perf_counter() - self._last_request_time) * 1000
            if elapsed < min_interval_ms:
                await asyncio.sleep((min_interval_ms - elapsed) / 1000)
            self._last_request_time = time.perf_counter()

    async def _call_api(self, address: str, api: str) -> Any:
        match api:
            case "nominatim": return await self._call_nominatim(address)
            case "google": return await self._call_google(address)
            case "goong": return await self._call_goong(address)
            case _: raise ValueError(f"Unsupported API: {api}")

    async def _call_nominatim(self, address: str) -> Any:
        await self._rate_limit(1000)
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": address, "format": "json", "limit": 1, "addressdetails": 1, "accept-language": "vi"}
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            resp = await client.get(url, params=params, headers=_HEADERS)
            resp.raise_for_status()
            data = resp.json()
        if not data: return None
        result = data[0]
        addr = result.get("address", {})
        return {"latitude": float(result["lat"]), "longitude": float(result["lon"]), "display_name": result.get("display_name", ""), "raw": result, "source_api": "nominatim", "metadata": {"country": addr.get("country", ""), "city": addr.get("city") or addr.get("town") or addr.get("province", ""), "district": addr.get("suburb", addr.get("district", "")), "ward": addr.get("quarter", ""), "street": addr.get("road", ""), "postal_code": addr.get("postcode", "")}}

    async def _call_google(self, address: str) -> Any:
        key = getattr(config, "google_maps_api_key", "")
        if not key: raise ValueError("GOOGLE_MAPS_API_KEY not configured")
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {"address": address, "key": key, "language": "vi", "region": "vn"}
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
        if data.get("status") != "OK" or not data.get("results"): return None
        result = data["results"][0]
        loc = result["geometry"]["location"]
        comps = {t: c["long_name"] for c in result.get("address_components", []) for t in c["types"]}
        return {"latitude": loc["lat"], "longitude": loc["lng"], "display_name": result["formatted_address"], "raw": result, "source_api": "google", "metadata": {"country": comps.get("country", ""), "city": comps.get("administrative_area_level_1", ""), "district": comps.get("administrative_area_level_2", ""), "ward": comps.get("sublocality_level_1", ""), "street": comps.get("route", ""), "postal_code": comps.get("postal_code", "")}}

    async def _call_goong(self, address: str) -> Any:
        key = getattr(config, "goong_api_key", "")
        if not key: raise ValueError("GOONG_API_KEY not configured")
        url = "https://rsapi.goong.io/geocode"
        params = {"address": address, "api_key": key}
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
        if data.get("status") != "OK" or not data.get("results"): return None
        result = data["results"][0]
        loc = result["geometry"]["location"]
        compound = result.get("compound", {})
        return {"latitude": loc["lat"], "longitude": loc["lng"], "display_name": result.get("formatted_address", ""), "raw": result, "source_api": "goong", "metadata": {"country": "Viet Nam", "city": compound.get("province", ""), "district": compound.get("district", ""), "ward": compound.get("commune", "")}}

    async def _call_reverse_api(self, lat: float, lng: float, api: str) -> Any:
        if api == "nominatim":
            await self._rate_limit(1000)
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {"lat": lat, "lon": lng, "format": "json", "addressdetails": 1, "accept-language": "vi"}
            async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
                resp = await client.get(url, params=params, headers=_HEADERS)
                resp.raise_for_status()
                data = resp.json()
            return {"address": data.get("display_name", ""), "latitude": lat, "longitude": lng, "raw": data}
        return None


_geo_service_instance = None
def get_geo_service():
    global _geo_service_instance
    if _geo_service_instance is None:
        _geo_service_instance = GeoService()
    return _geo_service_instance
