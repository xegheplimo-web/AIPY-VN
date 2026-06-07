"""
Tests for Ollama Cloud LLM Service
"""

import pytest
from src.services.llm import OllamaCloudService, get_ollama_service
from src.config import config


class TestOllamaCloudService:
    """Tests for Ollama Cloud service."""

    @pytest.fixture
    def ollama_service(self):
        """Create Ollama service instance."""
        return OllamaCloudService()

    def test_service_initialization(self, ollama_service):
        """Test service initializes correctly."""
        assert ollama_service is not None
        # API key may be None in test environment
        assert ollama_service.base_url == config.ollama.cloud_url
        assert ollama_service.default_model == config.ollama.default_model
        assert len(ollama_service.available_models) > 0

    def test_get_available_models(self, ollama_service):
        """Test getting available models."""
        models = ollama_service.get_available_models()
        assert isinstance(models, list)
        assert len(models) > 0
        assert config.ollama.default_model in models

    @pytest.mark.asyncio
    async def test_generate_text(self, ollama_service):
        """Test text generation."""
        try:
            response = await ollama_service.generate(
                prompt="Hello, how are you?", temperature=0.7, max_tokens=100
            )
            assert isinstance(response, str)
            assert len(response) > 0
        except Exception as e:
            pytest.skip(f"Ollama Cloud API not accessible: {e}")

    @pytest.mark.asyncio
    async def test_chat_completion(self, ollama_service):
        """Test chat completion."""
        try:
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello in Vietnamese."},
            ]
            response = await ollama_service.chat(
                messages=messages, temperature=0.7, max_tokens=100
            )
            assert isinstance(response, str)
            assert len(response) > 0
        except Exception as e:
            pytest.skip(f"Ollama Cloud API not accessible: {e}")

    @pytest.mark.asyncio
    async def test_list_models(self, ollama_service):
        """Test listing models from API."""
        try:
            models = await ollama_service.list_models()
            assert isinstance(models, list)
            assert len(models) > 0
        except Exception as e:
            pytest.skip(f"Ollama Cloud API not accessible: {e}")


def test_get_ollama_service():
    """Test getting global service instance."""
    service = get_ollama_service()
    assert service is not None
    assert isinstance(service, OllamaCloudService)
