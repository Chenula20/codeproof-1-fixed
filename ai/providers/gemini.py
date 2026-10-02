import os
from typing import Any, Dict, List, Optional
import google.generativeai as genai
from .base import BaseAIProvider, AIProviderConfig


class GeminiProvider(BaseAIProvider):
    """Google Gemini AI provider implementation."""

    def __init__(self, config: AIProviderConfig):
        super().__init__(config)
        genai.configure(api_key=config.api_key)
        self.model = genai.GenerativeModel(config.model)

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a response from Gemini."""
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        response = await self.model.generate_content_async(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_tokens,
            ),
        )
        return response.text or ""

    async def generate_structured(
        self,
        prompt: str,
        response_model: type,
        system_prompt: Optional[str] = None
    ) -> Any:
        """Generate a structured response from Gemini."""
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        response = await self.model.generate_content_async(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_tokens,
                response_mime_type="application/json",
            ),
        )
        import json
        data = json.loads(response.text or "{}")
        return response_model(**data)

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Gemini."""
        result = await genai.embed_content_async(
            model="models/embedding-001",
            content=texts,
        )
        return result["embedding"]

    @property
    def provider_name(self) -> str:
        return "gemini"