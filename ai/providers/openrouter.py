import os
from typing import Any, Dict, List, Optional
import httpx
from .base import BaseAIProvider, AIProviderConfig


class OpenRouterProvider(BaseAIProvider):
    """OpenRouter AI provider implementation."""

    def __init__(self, config: AIProviderConfig):
        super().__init__(config)
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://codeproof.app",
            "X-Title": "CodeProof",
        }
        self.client = httpx.AsyncClient(timeout=config.timeout)

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a response from OpenRouter."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json={
                "model": self.config.model,
                "messages": messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"] or ""

    async def generate_structured(
        self,
        prompt: str,
        response_model: type,
        system_prompt: Optional[str] = None
    ) -> Any:
        """Generate a structured response from OpenRouter."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        schema = response_model.model_json_schema()
        messages.append({
            "role": "user",
            "content": f"{prompt}\n\nRespond with valid JSON matching this schema:\n{schema}"
        })

        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json={
                "model": self.config.model,
                "messages": messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "response_format": {"type": "json_object"},
            },
        )
        response.raise_for_status()
        data = response.json()
        import json
        content = data["choices"][0]["message"]["content"] or "{}"
        parsed = json.loads(content)
        return response_model(**parsed)

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenRouter."""
        response = await self.client.post(
            f"{self.base_url}/embeddings",
            headers=self.headers,
            json={
                "model": "text-embedding-3-small",
                "input": texts,
            },
        )
        response.raise_for_status()
        data = response.json()
        return [item["embedding"] for item in data["data"]]

    @property
    def provider_name(self) -> str:
        return "openrouter"

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()