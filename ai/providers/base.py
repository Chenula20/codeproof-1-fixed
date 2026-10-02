from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AIProviderConfig(BaseModel):
    """Configuration for an AI provider."""
    api_key: str = Field(..., description="API key for the provider")
    model: str = Field(..., description="Model name to use")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(default=4096, gt=0, description="Maximum tokens in response")
    timeout: int = Field(default=60, gt=0, description="Request timeout in seconds")


class BaseAIProvider(ABC):
    """Abstract base class for AI providers."""

    def __init__(self, config: AIProviderConfig):
        self.config = config

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a response from the AI model."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_model: type,
        system_prompt: Optional[str] = None
    ) -> Any:
        """Generate a structured response parsed into the given model."""
        pass

    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for the given texts."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name."""
        pass