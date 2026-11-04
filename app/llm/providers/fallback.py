import logging
from collections.abc import AsyncIterator

from app.llm.errors import LLMUnavailable
from app.llm.providers.base import BaseLLMProvider
from app.llm.types import LLMChunk, LLMRequest

logger = logging.getLogger(__name__)


class FallbackLLMProvider(BaseLLMProvider):
    """Wraps primary and secondary providers to handle failover seamlessly."""

    def __init__(self, primary: BaseLLMProvider, fallback: BaseLLMProvider):
        self.primary = primary
        self.fallback = fallback
        self.last_fallback_used = False

    async def stream(self, request: LLMRequest) -> AsyncIterator[LLMChunk]:
        self.last_fallback_used = False
        yielded_any = False

        try:
            async for chunk in self.primary.stream(request):
                yielded_any = True
                yield chunk
            return
        except (LLMUnavailable, Exception) as err:
            if yielded_any:
                # If primary already yielded chunks to the client, we cannot cleanly restart
                logger.error("Primary LLM failed mid-stream after yielding output: %s", err)
                raise LLMUnavailable(f"Primary LLM streaming failed mid-response: {err}") from err

            logger.warning("Primary LLM unavailable (%s). Switching to fallback provider.", err)
            self.last_fallback_used = True

        async for chunk in self.fallback.stream(request):
            yield chunk
