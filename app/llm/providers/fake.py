from collections.abc import AsyncIterator

from app.llm.errors import LLMUnavailable
from app.llm.providers.base import BaseLLMProvider
from app.llm.types import LLMChunk, LLMRequest, UsageData


class FakeLLMProvider(BaseLLMProvider):
    """Fake LLM provider for tests and local development without API keys."""

    def __init__(self, model_name: str = "examate-fake", should_fail: bool = False):
        self.model_name = model_name
        self.should_fail = should_fail

    async def stream(self, request: LLMRequest) -> AsyncIterator[LLMChunk]:
        if self.should_fail:
            raise LLMUnavailable(f"Simulated failure for fake provider model {self.model_name}")

        prompt_text = " ".join(msg.content for msg in request.messages)
        # Approximate 1 token ~= 4 characters
        input_tokens = max(1, len(prompt_text) // 4)

        response_text = (
            f"Simulated response from {self.model_name}: Fraud risk insights processed successfully."
        )
        output_tokens = max(1, len(response_text) // 4)

        # Stream words as chunks
        words = response_text.split(" ")
        for i, word in enumerate(words):
            chunk_text = word if i == 0 else " " + word
            yield LLMChunk(text=chunk_text)

        # Final chunk with token usage
        yield LLMChunk(
            text="",
            usage=UsageData(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated=True,
            ),
        )
