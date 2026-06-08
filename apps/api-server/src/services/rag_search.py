"""
RAG Search Service

Provides fuzzy semantic search fallback when SQL ILIKE returns no results.
In production, this should be replaced with a true vector embedding pipeline
(e.g., sentence-transformers + Qdrant/pgvector).

Current implementation uses difflib.SequenceMatcher for lightweight fuzzy
matching across all product names.
"""

import difflib
import logging
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.database import async_session
from src.models.store import Product

logger = logging.getLogger(__name__)


def _tokenize(text: str) -> set[str]:
    """Simple Vietnamese-aware tokenization."""
    # Lowercase, split by spaces/punctuation
    return set(
        w.strip(".,!?;:\"'()[]{}")
        for w in text.lower().split()
        if w.strip()
    )


def _compute_similarity(query: str, target: str) -> float:
    """
    Compute a composite similarity score between query and target text.

    Combines:
    - SequenceMatcher ratio (character-level alignment)
    - Token overlap Jaccard (word-level overlap)
    """
    if not query or not target:
        return 0.0

    # Character-level similarity
    char_sim = difflib.SequenceMatcher(None, query.lower(), target.lower()).ratio()

    # Word-level Jaccard
    q_tokens = _tokenize(query)
    t_tokens = _tokenize(target)
    if q_tokens and t_tokens:
        intersection = len(q_tokens & t_tokens)
        union = len(q_tokens | t_tokens)
        word_sim = intersection / union if union > 0 else 0.0
    else:
        word_sim = 0.0

    # Weighted composite
    return char_sim * 0.6 + word_sim * 0.4


async def fuzzy_search_products(
    query: str,
    limit: int = 20,
    min_score: float = 0.15,
) -> List[Product]:
    """
    Fuzzy semantic search across all active products.

    Returns products ranked by composite similarity to the query.
    """
    async with async_session() as session:
        stmt = (
            select(Product)
            .where(Product.stock > 0)
            .where(Product.status == "active")
            .options(selectinload(Product.store))
        )
        result = await session.execute(stmt)
        all_products = result.scalars().all()

    if not all_products:
        return []

    # Score each product
    scored = []
    for p in all_products:
        # Search against name, description, and brand
        name_score = _compute_similarity(query, p.name)
        desc_score = _compute_similarity(query, p.description or "")
        brand_score = _compute_similarity(query, p.brand or "")

        best_score = max(name_score, desc_score * 0.7, brand_score * 0.8)

        if best_score >= min_score:
            scored.append((best_score, p))

    # Sort by score descending
    scored.sort(key=lambda x: x[0], reverse=True)

    logger.info(
        f"RAG fuzzy search for '{query[:50]}': {len(scored)} candidates, "
        f"top score={scored[0][0]:.3f if scored else 0}"
    )

    return [p for _, p in scored[:limit]]


async def hybrid_search_products(
    query: str,
    limit: int = 20,
    fuzzy_threshold: int = 3,
) -> List[Product]:
    """
    Hybrid search: SQL ILIKE first, fuzzy RAG fallback if too few results.

    Args:
        query: User search query
        limit: Max results to return
        fuzzy_threshold: Minimum ILIKE results before triggering fuzzy fallback

    Returns:
        List of Product objects, ranked by relevance.
    """
    # Phase 1: Exact-ish ILIKE search
    async with async_session() as session:
        search_term = f"%{query}%"
        stmt = (
            select(Product)
            .where(Product.name.ilike(search_term))
            .where(Product.stock > 0)
            .where(Product.status == "active")
            .options(selectinload(Product.store))
            .limit(limit * 2)
        )
        result = await session.execute(stmt)
        ilike_products = result.scalars().all()

    if len(ilike_products) >= fuzzy_threshold:
        logger.info(f"Hybrid search: ILIKE returned {len(ilike_products)} results, skipping fuzzy")
        return list(ilike_products)[:limit]

    # Phase 2: Fuzzy semantic fallback
    logger.info(f"Hybrid search: ILIKE only returned {len(ilike_products)}, triggering fuzzy fallback")
    fuzzy_products = await fuzzy_search_products(query, limit=limit)

    # Merge: ILIKE results first, then fuzzy (deduplicate by ID)
    seen_ids = {p.id for p in ilike_products}
    merged = list(ilike_products)
    for p in fuzzy_products:
        if p.id not in seen_ids:
            merged.append(p)
            seen_ids.add(p.id)

    return merged[:limit]
