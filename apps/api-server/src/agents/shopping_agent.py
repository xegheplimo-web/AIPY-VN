"""
VietStore Shopping AI Agent

Simple AI agent for helping users find products and stores using Ollama Cloud.
"""

import logging
from typing import Any

from src.config import config
from src.services.llm import get_ollama_service

logger = logging.getLogger(__name__)


class ShoppingAgent:
    """AI agent for VietStore shopping assistance."""

    def __init__(self):
        self.ollama_service = get_ollama_service()
        self.system_prompt = """You are a helpful shopping assistant for VietStore, a Vietnamese e-commerce platform.
You help users find products and stores near their location.
Provide concise, helpful responses in Vietnamese.
Focus on product availability, store information, and practical shopping advice.
When users ask about products, provide helpful suggestions.
When users ask about stores, mention location and availability.
Always be friendly and helpful."""

    async def chat(
        self, user_message: str, context: dict[str, Any] | None = None
    ) -> str:
        """
        Chat with the user using Ollama Cloud.

        Args:
            user_message: The user's message
            context: Optional context (location, search results, etc.)

        Returns:
            AI response
        """
        try:
            # Build prompt with context
            prompt = user_message
            if context:
                if context.get("location"):
                    prompt += f"\nUser location: {context['location']}"
                if context.get("search_results"):
                    prompt += f"\nSearch results: {context['search_results']}"
                if context.get("cart_items"):
                    prompt += f"\nCart items: {context['cart_items']}"

            # Use Ollama Cloud for inference
            response = await self.ollama_service.generate(
                prompt=prompt,
                model=config.ollama.default_model,
                system_prompt=self.system_prompt,
                temperature=0.7,
                max_tokens=500,
            )
            return response
        except Exception as e:
            logger.error(f"Agent error: {e}")
            return "Xin lỗi, tôi không thể xử lý yêu cầu của bạn lúc này. Vui lòng thử lại sau."

    async def search_products(
        self, query: str, location: dict[str, float] | None = None
    ) -> str:
        """
        Search for products based on user query.

        Args:
            query: Search query
            location: Optional user location {lat, lng}

        Returns:
            AI response with product suggestions
        """
        context = {"location": location, "search_type": "product_search"}
        return await self.chat(f"Tìm kiếm sản phẩm: {query}", context)

    async def search_stores(
        self, query: str, location: dict[str, float] | None = None
    ) -> str:
        """
        Search for stores based on user query.

        Args:
            query: Search query
            location: Optional user location {lat, lng}

        Returns:
            AI response with store suggestions
        """
        context = {"location": location, "search_type": "store_search"}
        return await self.chat(f"Tìm kiếm cửa hàng: {query}", context)

    async def get_recommendations(self, user_preferences: dict[str, Any]) -> str:
        """
        Get product recommendations based on user preferences.

        Args:
            user_preferences: User preferences (category, price range, etc.)

        Returns:
            AI response with recommendations
        """
        context = {
            "user_preferences": user_preferences,
            "search_type": "recommendations",
        }
        return await self.chat("Gợi ý sản phẩm dựa trên sở thích của tôi", context)


# Global agent instance
shopping_agent = ShoppingAgent()


def get_shopping_agent() -> ShoppingAgent:
    """Get the global shopping agent instance."""
    return shopping_agent
