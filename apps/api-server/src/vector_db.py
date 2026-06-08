"""
Vector Database Client for VietStore RAG.

Supports Qdrant (recommended) or Typesense.
In production, configure via environment variables.
"""

import logging
import os

# Qdrant client (install via: uv add qdrant-client)
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, PointStruct, VectorParams

    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

logger = logging.getLogger(__name__)

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("VECTOR_COLLECTION", "vietstore_products")
VECTOR_SIZE = int(os.getenv("VECTOR_SIZE", "384"))  # all-MiniLM-L6-v2


class VectorDBClient:
    """Client for vector database operations."""

    def __init__(self):
        self.client = None
        self._init_client()

    def _init_client(self):
        if not QDRANT_AVAILABLE:
            logger.warning("qdrant-client not installed. Vector search disabled.")
            return
        try:
            self.client = QdrantClient(url=QDRANT_URL)
            self._ensure_collection()
        except Exception as e:
            logger.warning(f"Could not connect to Qdrant: {e}")
            self.client = None

    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        if not self.client:
            return
        try:
            collections = self.client.get_collections().collections
            names = [c.name for c in collections]
            if COLLECTION_NAME not in names:
                self.client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=VECTOR_SIZE,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(f"Created Qdrant collection: {COLLECTION_NAME}")
        except Exception as e:
            logger.error(f"Could not ensure collection: {e}", exc_info=True)

    def upsert_product(
        self,
        product_id: str,
        vector: list[float],
        payload: dict,
    ) -> bool:
        """Insert or update a product vector."""
        if not self.client:
            return False
        try:
            self.client.upsert(
                collection_name=COLLECTION_NAME,
                points=[PointStruct(id=product_id, vector=vector, payload=payload)],
            )
            return True
        except Exception as e:
            logger.error(f"Failed to upsert product {product_id}: {e}", exc_info=True)
            return False

    def search(
        self,
        query_vector: list[float],
        limit: int = 10,
        filters: dict | None = None,
    ) -> list[dict]:
        """Search products by vector similarity."""
        if not self.client:
            return []
        try:
            results = self.client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_vector,
                limit=limit,
                query_filter=filters,
            )
            return [
                {
                    "id": r.id,
                    "score": r.score,
                    "payload": r.payload,
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Vector search failed: {e}", exc_info=True)
            return []

    def delete_product(self, product_id: str) -> bool:
        """Remove a product from vector index."""
        if not self.client:
            return False
        try:
            self.client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=[product_id],
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete product {product_id}: {e}", exc_info=True)
            return False


# Singleton instance
vector_db = VectorDBClient()
