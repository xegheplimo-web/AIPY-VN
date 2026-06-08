"""
SQLite Backup Cache for Geo Service

Persistent offline cache for geocoding results when Redis is unavailable.
Works as a backup layer on top of Redis cache.
"""

import sqlite3
import json
import time
import hashlib
import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class GeoSQLiteCache:
    """
    SQLite-based persistent cache for geocoding results.
    Serves as backup when Redis is unavailable.
    """

    def __init__(self, db_path: str = "data/geo_cache.db"):
        self.db_path = db_path
        self._init_database()
        logger.info(f"Geo SQLite cache initialized: {db_path}")

    def _init_database(self):
        """Initialize SQLite database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
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
                    
                    -- Metadata
                    country TEXT,
                    city TEXT,
                    district TEXT,
                    ward TEXT,
                    street TEXT,
                    postal_code TEXT
                )
            """)

            # Indexes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_address_hash 
                ON geo_cache(address_hash)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_lat_lng 
                ON geo_cache(latitude, longitude)
            """)

            # API call log
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_call_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    api_name TEXT NOT NULL,
                    address_query TEXT NOT NULL,
                    cache_hit INTEGER NOT NULL,
                    response_time_ms REAL,
                    success INTEGER DEFAULT 1,
                    error_message TEXT
                )
            """)
            conn.commit()

    @staticmethod
    def _normalize_address(address: str) -> str:
        """Normalize address for comparison"""
        normalized = address.lower().strip()
        normalized = " ".join(normalized.split())
        
        # Vietnamese address normalization
        replacements = {
            "tp.": "thành phố",
            "tp ": "thành phố ",
            "q.": "quận",
            "q ": "quận ",
            "p.": "phường",
            "p ": "phường ",
            "đ.": "đường",
            "tx.": "thị xã",
            "tt.": "thị trấn",
        }
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        return normalized

    @staticmethod
    def _hash_address(address: str) -> str:
        """Create hash for normalized address"""
        return hashlib.sha256(address.encode("utf-8")).hexdigest()

    def lookup(self, address: str) -> Optional[Dict[str, Any]]:
        """Lookup address in cache"""
        normalized = self._normalize_address(address)
        addr_hash = self._hash_address(normalized)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM geo_cache 
                WHERE address_hash = ? AND is_valid = 1
                """,
                (addr_hash,),
            )
            row = cursor.fetchone()

            if row:
                # Update access stats
                conn.execute(
                    """
                    UPDATE geo_cache 
                    SET last_accessed = ?, access_count = access_count + 1
                    WHERE address_hash = ?
                    """,
                    (time.time(), addr_hash),
                )
                conn.commit()

                logger.debug(f"SQLite cache HIT: {address}")
                return dict(row)

        logger.debug(f"SQLite cache MISS: {address}")
        return None

    def save(
        self,
        address: str,
        latitude: float,
        longitude: float,
        full_response: dict = None,
        source_api: str = "unknown",
        metadata: dict = None,
    ) -> bool:
        """Save geocoding result to cache"""
        normalized = self._normalize_address(address)
        addr_hash = self._hash_address(normalized)
        now = time.time()

        meta = metadata or {}

        try:
            with sqlite3.connect(self.db_path) as conn:
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
                        last_accessed = excluded.last_accessed,
                        access_count = access_count + 1
                    """,
                    (
                        addr_hash, address, normalized,
                        latitude, longitude,
                        json.dumps(full_response or {}, ensure_ascii=False),
                        source_api, now, now,
                        meta.get("country", ""),
                        meta.get("city", ""),
                        meta.get("district", ""),
                        meta.get("ward", ""),
                        meta.get("street", ""),
                        meta.get("postal_code", ""),
                    ),
                )
                conn.commit()

            logger.debug(f"SQLite cache SAVED: {address}")
            return True

        except Exception as e:
            logger.error(f"Error saving to SQLite cache: {e}")
            return False

    def log_api_call(
        self,
        api_name: str,
        address: str,
        cache_hit: bool,
        response_time_ms: float = 0,
        success: bool = True,
        error: str = None,
    ):
        """Log API call"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO api_call_log 
                (timestamp, api_name, address_query, cache_hit, 
                 response_time_ms, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    time.time(), api_name, address,
                    1 if cache_hit else 0,
                    response_time_ms,
                    1 if success else 0,
                    error,
                ),
            )
            conn.commit()

    def get_stats(self) -> dict:
        """Get cache statistics"""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM geo_cache WHERE is_valid = 1"
            ).fetchone()[0]

            api_calls = conn.execute(
                "SELECT COUNT(*) FROM api_call_log"
            ).fetchone()[0]

            cache_hits = conn.execute(
                "SELECT COUNT(*) FROM api_call_log WHERE cache_hit = 1"
            ).fetchone()[0]

            most_accessed = conn.execute(
                """
                SELECT address_original, access_count 
                FROM geo_cache 
                ORDER BY access_count DESC LIMIT 5
                """
            ).fetchall()

        hit_rate = (
            (cache_hits / api_calls * 100) if api_calls > 0 else 0
        )

        return {
            "total_cached_addresses": total,
            "total_api_calls": api_calls,
            "cache_hits": cache_hits,
            "cache_hit_rate": f"{hit_rate:.1f}%",
            "most_accessed": most_accessed,
        }

    def clear_cache(self):
        """Clear all cache"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM geo_cache")
            conn.execute("DELETE FROM api_call_log")
            conn.commit()
        logger.info("SQLite cache cleared")


# Global instance
sqlite_cache = GeoSQLiteCache()
