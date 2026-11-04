from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.llm.types import LLMChunk, LLMRequest


class BaseLLMProvider(ABC):
    """Abstract interface for LLM streaming providers."""

    @abstractmethod
    async def stream(self, request: LLMRequest) -> AsyncIterator[LLMChunk]:
        """Stream chunks and token usage for the given prompt request."""
        yield  # pragma: no cover
