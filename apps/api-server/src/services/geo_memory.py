"""
GeoMemoryDB — Persistent SQLite cache for geocoding results.

Provides:
- Address normalization (Vietnamese)
- Lat/lng + metadata storage
- Access tracking
- API call logging
- Statistics

Usage:
    from src.services.geo_memory import geo_memory

    cached = geo_memory.lookup("227 Nguyễn Văn Cừ, Quận 5")
    if not cached:
        result = call_external_api(...)
        geo_memory.save("227 Nguyễn Văn Cừ", result.lat, result.lng, ...)
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any

from src.config import config

logger = logging.getLogger(__name__)

# Default DB path inside project data dir
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "geo_memory.db"


class GeoMemoryDB:
    """Persistent SQLite cache for geocoding with address normalization."""

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        logger.info(f"GeoMemoryDB initialized: {self.db_path}")

    # ─── Schema ──────────────────────────────────────────────────────────────

    def _init_database(self) -> None:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS geo_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    address_hash TEXT UNIQUE NOT NULL,
                    address_original TEXT NOT NULL,
                    address_normalized TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    full_response TEXT,
                    source_api TEXT DEFAULT 'unknown',
                    created_at REAL NOT NULL,
                    last_accessed REAL NOT NULL,
                    access_count INTEGER DEFAULT 1,
                    is_valid INTEGER DEFAULT 1,
                    country TEXT,
                    city TEXT,
                    district TEXT,
                    ward TEXT,
                    street TEXT,
                    postal_code TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_geo_hash
                    ON geo_cache(address_hash);
                CREATE INDEX IF NOT EXISTS idx_geo_lat_lng
                    ON geo_cache(latitude, longitude);
                CREATE INDEX IF NOT EXISTS idx_geo_city
                    ON geo_cache(city);
                CREATE INDEX IF NOT EXISTS idx_geo_district
                    ON geo_cache(district);

                CREATE TABLE IF NOT EXISTS api_call_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    api_name TEXT NOT NULL,
                    address_query TEXT NOT NULL,
                    cache_hit INTEGER NOT NULL,
                    response_time_ms REAL,
                    success INTEGER DEFAULT 1,
                    error_message TEXT
                );
                """
            )
            conn.commit()

    # ─── Helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _normalize_address(address: str) -> str:
        normalized = address.lower().strip()
        normalized = " ".join(normalized.split())
        replacements = {
            "tp.": "thanh pho",
            "tp ": "thanh pho ",
            "q.": "quan",
            "q ": "quan ",
            "p.": "phuong",
            "p ": "phuong ",
            "đ.": "duong",
            "tx.": "thi xa",
            "tt.": "thi tran",
            "h.": "huyen",
            "h ": "huyen ",
            "t.": "tinh",
            "t ": "tinh ",
        }
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        return normalized

    @staticmethod
    def _hash_address(address: str) -> str:
        normalized = GeoMemoryDB._normalize_address(address)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    # ─── Core: Lookup ────────────────────────────────────────────────────────

    def lookup(self, address: str) -> dict[str, Any] | None:
        """Find address in cache. Returns None on cache miss."""
        addr_hash = self._hash_address(address)

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT * FROM geo_cache
                WHERE address_hash = ? AND is_valid = 1
                """,
                (addr_hash,),
            ).fetchone()

            if row:
                conn.execute(
                    """
                    UPDATE geo_cache
                    SET last_accessed = ?, access_count = access_count + 1
                    WHERE address_hash = ?
                    """,
                    (time.time(), addr_hash),
                )
                conn.commit()
                logger.debug(f"GeoMemoryDB HIT: {address}")
                return dict(row)

        logger.debug(f"GeoMemoryDB MISS: {address}")
        return None

    def lookup_by_coords(self, lat: float, lng: float, tolerance: float = 0.0001) -> dict[str, Any] | None:
        """Reverse lookup by coordinates with tolerance (approx 10m)."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT * FROM geo_cache
                WHERE ABS(latitude - ?) < ? AND ABS(longitude - ?) < ?
                    AND is_valid = 1
                ORDER BY ABS(latitude - ?) + ABS(longitude - ?)
                LIMIT 1
                """,
                (lat, tolerance, lng, tolerance, lat, lng),
            ).fetchone()
            return dict(row) if row else None

    # ─── Core: Save ──────────────────────────────────────────────────────────

    def save(
        self,
        address: str,
        latitude: float,
        longitude: float,
        full_response: dict | None = None,
        source_api: str = "unknown",
        metadata: dict | None = None,
    ) -> bool:
        """Save geocoding result to persistent cache."""
        normalized = self._normalize_address(address)
        addr_hash = self._hash_address(address)
        now = time.time()
        meta = metadata or {}

        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    """
                    INSERT INTO geo_cache (
                        address_hash, address_original, address_normalized,
                        latitude, longitude, full_response, source_api,
                        created_at, last_accessed, access_count,
                        country, city, district, ward, street, postal_code
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(address_hash) DO UPDATE SET
                        latitude = excluded.latitude,
                        longitude = excluded.longitude,
                        full_response = excluded.full_response,
                        source_api = excluded.source_api,
                        last_accessed = excluded.last_accessed,
                        access_count = access_count + 1,
                        is_valid = 1
                    """,
                    (
                        addr_hash,
                        address,
                        normalized,
                        latitude,
                        longitude,
                        json.dumps(full_response or {}, ensure_ascii=False),
                        source_api,
                        now,
                        now,
                        meta.get("country", ""),
                        meta.get("city", ""),
                        meta.get("district", ""),
                        meta.get("ward", ""),
                        meta.get("street", ""),
                        meta.get("postal_code", ""),
                    ),
                )
                conn.commit()
            logger.debug(f"GeoMemoryDB SAVED: {address}")
            return True
        except Exception as e:
            logger.error(f"GeoMemoryDB save error: {e}")
            return False

    # ─── Logging ─────────────────────────────────────────────────────────────

    def log_api_call(
        self,
        api_name: str,
        address: str,
        cache_hit: bool,
        response_time_ms: float = 0.0,
        success: bool = True,
        error: str | None = None,
    ) -> None:
        """Log every API call for analytics."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    """
                    INSERT INTO api_call_log
                    (timestamp, api_name, address_query, cache_hit,
                     response_time_ms, success, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        time.time(),
                        api_name,
                        address,
                        1 if cache_hit else 0,
                        response_time_ms,
                        1 if success else 0,
                        error,
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"GeoMemoryDB log error: {e}")

    # ─── Statistics ──────────────────────────────────────────────────────────

    def get_stats(self) -> dict[str, Any]:
        """Return cache analytics."""
        with sqlite3.connect(str(self.db_path)) as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM geo_cache WHERE is_valid = 1"
            ).fetchone()[0]

            total_calls = conn.execute(
                "SELECT COUNT(*) FROM api_call_log"
            ).fetchone()[0]

            cache_hits = conn.execute(
                "SELECT COUNT(*) FROM api_call_log WHERE cache_hit = 1"
            ).fetchone()[0]

            most_accessed = conn.execute(
                """
                SELECT address_original, access_count
                FROM geo_cache
                WHERE is_valid = 1
                ORDER BY access_count DESC
                LIMIT 5
                """
            ).fetchall()

            avg_response = conn.execute(
                """
                SELECT AVG(response_time_ms) FROM api_call_log
                WHERE cache_hit = 0 AND success = 1
                """
            ).fetchone()[0]

            error_rate = conn.execute(
                """
                SELECT
                    CAST(SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) AS REAL)
                    / COUNT(*) * 100
                FROM api_call_log
                WHERE cache_hit = 0
                """
            ).fetchone()[0]

        hit_rate = (cache_hits / total_calls * 100) if total_calls > 0 else 0.0

        return {
            "total_cached_addresses": total,
            "total_api_calls": total_calls,
            "cache_hits": cache_hits,
            "cache_misses": total_calls - cache_hits,
            "cache_hit_rate_percent": round(hit_rate, 1),
            "avg_api_response_ms": round(avg_response or 0, 1),
            "api_error_rate_percent": round(error_rate or 0, 1),
            "most_accessed": [
                {"address": addr, "access_count": cnt}
                for addr, cnt in most_accessed
            ],
        }

    def invalidate(self, address: str) -> bool:
        """Soft-delete a cached address."""
        addr_hash = self._hash_address(address)
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "UPDATE geo_cache SET is_valid = 0 WHERE address_hash = ?",
                (addr_hash,),
            )
            conn.commit()
        return cursor.rowcount > 0


# ─── Singleton instance ──────────────────────────────────────────────────────

_geo_memory_instance: GeoMemoryDB | None = None


def get_geo_memory() -> GeoMemoryDB:
    """Get or create the singleton GeoMemoryDB instance."""
    global _geo_memory_instance
    if _geo_memory_instance is None:
        _geo_memory_instance = GeoMemoryDB()
    return _geo_memory_instance
