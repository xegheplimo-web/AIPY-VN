"""
Ollama Cloud LLM Service for VietStore RAG

Provides interface to Ollama cloud API for LLM inference.
"""

import httpx
import json
import logging
from typing import Optional, List, Dict, Any
from src.config import config

logger = logging.getLogger(__name__)


class OllamaCloudService:
    """Service for interacting with Ollama Cloud API."""

    def __init__(self):
        """Initialize Ollama Cloud service."""
        self.api_key = config.ollama.cloud_api_key
        self.base_url = config.ollama.cloud_url
        self.default_model = config.ollama.default_model
        self.timeout = config.ollama.timeout
        self.available_models = [
            model.strip() for model in config.ollama.cloud_models.split(",")
        ]

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate text using Ollama Cloud API.

        Args:
            prompt: The input prompt
            model: Model to use (defaults to configured default)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
            **kwargs: Additional parameters for the API

        Returns:
            Generated text response
        """
        model = model or self.default_model

        if model not in self.available_models:
            logger.warning(f"Model {model} not in available models, using default")
            model = self.default_model

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }

        if system_prompt:
            payload["system"] = system_prompt

        # Add any additional options
        if kwargs:
            payload["options"].update(kwargs)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

                # Extract the generated text from response
                if "message" in data and "content" in data["message"]:
                    return data["message"]["content"]
                elif "response" in data:
                    return data["response"]
                else:
                    logger.warning(f"Unexpected response format: {data}")
                    return str(data)

        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama Cloud API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error calling Ollama Cloud API: {e}")
            raise

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """
        Chat completion using Ollama Cloud API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to configured default)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for the API

        Returns:
            Generated text response
        """
        model = model or self.default_model

        if model not in self.available_models:
            logger.warning(f"Model {model} not in available models, using default")
            model = self.default_model

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }

        # Add any additional options
        if kwargs:
            payload["options"].update(kwargs)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

                # Extract the generated text from response
                if "message" in data and "content" in data["message"]:
                    return data["message"]["content"]
                elif "response" in data:
                    return data["response"]
                else:
                    logger.warning(f"Unexpected response format: {data}")
                    return str(data)

        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama Cloud API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error calling Ollama Cloud API: {e}")
            raise

    async def list_models(self) -> List[str]:
        """
        List available models from Ollama Cloud.

        Returns:
            List of available model names
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/v1/models",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                data = response.json()

                if "models" in data:
                    return [model["name"] for model in data["models"]]
                else:
                    return self.available_models

        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return self.available_models

    def get_available_models(self) -> List[str]:
        """
        Get list of available models (sync wrapper).

        Returns:
            List of available model names
        """
        return self.available_models


# Global service instance
ollama_service = OllamaCloudService()


def get_ollama_service() -> OllamaCloudService:
    """Get the global Ollama Cloud service instance."""
    return ollama_service
