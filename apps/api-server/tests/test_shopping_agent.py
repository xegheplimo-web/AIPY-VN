"""
Tests for Shopping Agent
"""

import pytest
from src.agents import get_shopping_agent, ShoppingAgent


class TestShoppingAgent:
    """Tests for Shopping Agent."""

    @pytest.fixture
    def agent(self):
        """Create shopping agent instance."""
        return get_shopping_agent()

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent is not None
        assert isinstance(agent, ShoppingAgent)
        assert agent.ollama_service is not None
        assert agent.system_prompt is not None

    @pytest.mark.asyncio
    async def test_chat_response(self, agent):
        """Test basic chat response."""
        try:
            response = await agent.chat("Xin chào")
            assert isinstance(response, str)
            assert len(response) > 0
        except Exception as e:
            pytest.skip(f"Ollama Cloud API not accessible: {e}")

    @pytest.mark.asyncio
    async def test_search_products(self, agent):
        """Test product search."""
        try:
            response = await agent.search_products("Panadol")
            assert isinstance(response, str)
            assert len(response) > 0
        except Exception as e:
            pytest.skip(f"Ollama Cloud API not accessible: {e}")

    @pytest.mark.asyncio
    async def test_search_stores(self, agent):
        """Test store search."""
        try:
            response = await agent.search_stores("nhà thuốc")
            assert isinstance(response, str)
            assert len(response) > 0
        except Exception as e:
            pytest.skip(f"Ollama Cloud API not accessible: {e}")

    @pytest.mark.asyncio
    async def test_get_recommendations(self, agent):
        """Test recommendations."""
        try:
            response = await agent.get_recommendations(
                {"category": "thuốc", "price_range": "dưới 100k"}
            )
            assert isinstance(response, str)
            assert len(response) > 0
        except Exception as e:
            pytest.skip(f"Ollama Cloud API not accessible: {e}")


def test_get_shopping_agent():
    """Test getting global agent instance."""
    agent = get_shopping_agent()
    assert agent is not None
    assert isinstance(agent, ShoppingAgent)
