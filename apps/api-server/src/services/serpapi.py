"""
SerpAPI Service for Web Search

Provides web search functionality using SerpAPI for Google search results.
Uses httpx for async HTTP requests to the SerpAPI REST API.
"""

import logging
from typing import Any

import httpx

from src.config import config

logger = logging.getLogger(__name__)

# SerpAPI base URL
_SERPAPI_BASE_URL = "https://serpapi.com/search"


class SerpAPIService:
    """Service for web search using SerpAPI."""

    def __init__(self) -> None:
        """Initialize SerpAPI service."""
        self.api_key: str = config.serpapi.api_key
        self.engine: str = config.serpapi.engine
        self.timeout: int = config.serpapi.timeout

    def is_ready(self) -> bool:
        """Check if the service is ready (API key configured)."""
        return bool(self.api_key)

    async def _make_request(
        self, params: dict[str, Any]
    ) -> dict[str, Any] | None:
        """
        Make an async request to the SerpAPI REST endpoint.

        Args:
            params: Query parameters for the SerpAPI request (without api_key).

        Returns:
            Parsed JSON response as dict, or None on error.
        """
        if not self.is_ready():
            logger.warning("SerpAPI not configured — API key is empty")
            return None

        params["api_key"] = self.api_key

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(_SERPAPI_BASE_URL, params=params)

            if response.status_code == 429:
                logger.error(
                    "SerpAPI rate limit exceeded. Consider upgrading your plan."
                )
                return None

            if response.status_code == 401:
                logger.error(
                    "SerpAPI authentication failed — invalid API key"
                )
                return None

            if response.status_code == 403:
                logger.error(
                    "SerpAPI forbidden — account may be depleted or blocked"
                )
                return None

            response.raise_for_status()
            return response.json()

        except httpx.TimeoutException:
            logger.error(
                f"SerpAPI request timed out after {self.timeout}s "
                f"for params: {params.get('engine', 'unknown')}"
            )
            return None
        except httpx.HTTPStatusError as exc:
            logger.error(
                f"SerpAPI HTTP error {exc.response.status_code}: {exc}"
            )
            return None
        except httpx.RequestError as exc:
            logger.error(f"SerpAPI network error: {exc}")
            return None
        except Exception as exc:
            logger.error(f"SerpAPI unexpected error: {exc}")
            return None

    @staticmethod
    def _build_common_params(
        engine: str,
        query: str,
        num_results: int = 10,
        location: str | None = None,
        language: str = "vi",
    ) -> dict[str, Any]:
        """
        Build common SerpAPI query parameters with Vietnamese location bias.

        Args:
            engine: SerpAPI engine name (google, google_shopping, etc.)
            query: Search query string
            num_results: Number of results to request
            location: Optional location string for localized results
            language: Language code (default: Vietnamese)

        Returns:
            Dict of query parameters ready for the SerpAPI request.
        """
        params: dict[str, Any] = {
            "engine": engine,
            "q": query,
            "num": num_results,
            "hl": language,
            "gl": "vn",  # Geographic location bias — Vietnam
        }

        if location:
            params["location"] = location

        return params

    # ------------------------------------------------------------------ #
    #  Public search methods                                               #
    # ------------------------------------------------------------------ #

    async def search(
        self,
        query: str,
        num_results: int = 10,
        location: str | None = None,
        language: str = "vi",
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """
        Perform web search using SerpAPI (Google).

        Args:
            query: Search query
            num_results: Number of results to return
            location: Location for localized search (e.g., "Vietnam")
            language: Language code (default: Vietnamese)
            **kwargs: Additional SerpAPI parameters

        Returns:
            List of search results with title, link, snippet, etc.
        """
        if not self.is_ready():
            logger.warning("SerpAPI not configured, web search disabled")
            return []

        params = self._build_common_params(
            engine=self.engine,  # defaults to "google"
            query=query,
            num_results=num_results,
            location=location,
            language=language,
        )
        params.update(kwargs)

        data = await self._make_request(params)
        if data is None:
            return []

        organic_results = data.get("organic_results", [])
        if not organic_results:
            logger.info(f"No organic results found for query: {query}")
            return []

        results: list[dict[str, Any]] = []
        for item in organic_results:
            results.append(
                {
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "position": item.get("position"),
                    "date": item.get("date", ""),
                }
            )

        logger.info(
            f"Web search returned {len(results)} results for: {query}"
        )
        return results

    async def search_shopping(
        self,
        query: str,
        num_results: int = 10,
        location: str | None = None,
        language: str = "vi",
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """
        Perform shopping search using SerpAPI (Google Shopping).

        Args:
            query: Search query
            num_results: Number of results
            location: Optional location for localized results
            language: Language code (default: Vietnamese)
            **kwargs: Additional parameters

        Returns:
            List of shopping results with title, link, price, etc.
        """
        if not self.is_ready():
            logger.warning("SerpAPI not configured, shopping search disabled")
            return []

        params = self._build_common_params(
            engine="google_shopping",
            query=query,
            num_results=num_results,
            location=location,
            language=language,
        )
        params.update(kwargs)

        data = await self._make_request(params)
        if data is None:
            return []

        shopping_results = data.get("shopping_results", [])
        if not shopping_results:
            logger.info(f"No shopping results found for query: {query}")
            return []

        results: list[dict[str, Any]] = []
        for item in shopping_results:
            # Extract price information
            extracted_price = item.get("extracted_price")
            price_str = item.get("price", "")

            results.append(
                {
                    "title": item.get("title", ""),
                    "link": item.get("link", item.get("product_link", "")),
                    "snippet": item.get("snippet", ""),
                    "price": price_str,
                    "extracted_price": extracted_price,
                    "store": item.get("store", item.get("seller", "")),
                    "rating": item.get("rating"),
                    "reviews": item.get("reviews"),
                    "thumbnail": item.get("thumbnail", ""),
                    "position": item.get("position"),
                }
            )

        logger.info(
            f"Shopping search returned {len(results)} results for: {query}"
        )
        return results

    async def search_images(
        self,
        query: str,
        num_results: int = 10,
        location: str | None = None,
        language: str = "vi",
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """
        Perform image search using SerpAPI (Google Images).

        Args:
            query: Search query
            num_results: Number of results
            location: Optional location for localized results
            language: Language code (default: Vietnamese)
            **kwargs: Additional parameters

        Returns:
            List of image results with title, link, thumbnail, etc.
        """
        if not self.is_ready():
            logger.warning("SerpAPI not configured, image search disabled")
            return []

        params = self._build_common_params(
            engine="google_images",
            query=query,
            num_results=num_results,
            location=location,
            language=language,
        )
        params.update(kwargs)

        data = await self._make_request(params)
        if data is None:
            return []

        image_results = data.get("images_results", [])
        if not image_results:
            logger.info(f"No image results found for query: {query}")
            return []

        results: list[dict[str, Any]] = []
        for item in image_results:
            results.append(
                {
                    "title": item.get("title", ""),
                    "link": item.get("link", item.get("original", "")),
                    "snippet": item.get("snippet", ""),
                    "thumbnail": item.get("thumbnail", ""),
                    "original": item.get("original", ""),
                    "source": item.get("source", ""),
                    "position": item.get("position"),
                }
            )

        logger.info(
            f"Image search returned {len(results)} results for: {query}"
        )
        return results

    async def get_search_suggestions(
        self,
        query: str,
        num_suggestions: int = 5,
        language: str = "vi",
    ) -> list[str]:
        """
        Get search suggestions for a query using Google Autocomplete.

        Args:
            query: Search query prefix
            num_suggestions: Maximum number of suggestions to return
            language: Language code (default: Vietnamese)

        Returns:
            List of suggested query strings
        """
        if not self.is_ready():
            logger.warning("SerpAPI not configured, suggestions disabled")
            return []

        params: dict[str, Any] = {
            "engine": "google_autocomplete",
            "q": query,
            "hl": language,
            "gl": "vn",
        }

        data = await self._make_request(params)
        if data is None:
            return []

        suggestions_data = data.get("suggestions", [])
        if not suggestions_data:
            logger.info(f"No autocomplete suggestions found for: {query}")
            return []

        suggestions: list[str] = []
        for item in suggestions_data[:num_suggestions]:
            value = item.get("value", "")
            if value:
                suggestions.append(value)

        logger.info(
            f"Autocomplete returned {len(suggestions)} suggestions for: {query}"
        )
        return suggestions


# Global service instance
serpapi_service = SerpAPIService()


def get_serpapi_service() -> SerpAPIService:
    """Get the global SerpAPI service instance."""
    return serpapi_service
