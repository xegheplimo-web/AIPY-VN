"""
Text Embedding Service for VietStore RAG.

Uses SentenceTransformers for local embedding generation.
Model: all-MiniLM-L6-v2 (384 dimensions, fast, good for English + Vietnamese)
For production Vietnamese: paraphrase-multilingual-MiniLM-L12-v2
"""

import os
from typing import List

# SentenceTransformers (install via: uv add sentence-transformers)
try:
    from sentence_transformers import SentenceTransformer
    ST_AVAILABLE = True
except ImportError:
    ST_AVAILABLE = False

MODEL_NAME = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")


class EmbeddingService:
    """Service for generating text embeddings."""

    def __init__(self):
        self.model = None
        self._load_model()

    def _load_model(self):
        if not ST_AVAILABLE:
            print("WARNING: sentence-transformers not installed. Embeddings disabled.")
            return
        try:
            print(f"Loading embedding model: {MODEL_NAME}")
            self.model = SentenceTransformer(MODEL_NAME)
            print("Embedding model loaded successfully.")
        except Exception as e:
            print(f"WARNING: Could not load embedding model: {e}")
            self.model = None

    def encode(self, text: str) -> List[float]:
        """Generate embedding vector for a single text."""
        if not self.model:
            return []
        try:
            vector = self.model.encode(text, convert_to_numpy=True)
            return vector.tolist()
        except Exception as e:
            print(f"ERROR: Embedding failed: {e}")
            return []

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if not self.model:
            return []
        try:
            vectors = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            return vectors.tolist()
        except Exception as e:
            print(f"ERROR: Batch embedding failed: {e}")
            return []

    @property
    def is_available(self) -> bool:
        return self.model is not None

    @property
    def vector_size(self) -> int:
        return 384


# Singleton instance
embeddings = EmbeddingService()
