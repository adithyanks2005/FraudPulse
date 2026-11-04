import asyncio

import pytest

from app.llm.errors import LLMUnavailable
from app.llm.providers.fake import FakeLLMProvider
from app.llm.providers.fallback import FallbackLLMProvider
from app.llm.types import LLMRequest, Message


def test_fallback_provider_switches_on_primary_failure():
    async def run():
        primary = FakeLLMProvider(model_name="failing-primary", should_fail=True)
        fallback = FakeLLMProvider(model_name="working-backup", should_fail=False)

        provider = FallbackLLMProvider(primary=primary, fallback=fallback)
        request = LLMRequest(
            messages=[Message(role="user", content="Hello test")],
            model="test-model",
        )

        chunks = []
        async for chunk in provider.stream(request):
            chunks.append(chunk)

        assert provider.last_fallback_used is True
        combined_text = "".join(c.text for c in chunks)
        assert "working-backup" in combined_text

    asyncio.run(run())


def test_fallback_provider_uses_primary_when_available():
    async def run():
        primary = FakeLLMProvider(model_name="healthy-primary", should_fail=False)
        fallback = FakeLLMProvider(model_name="backup", should_fail=False)

        provider = FallbackLLMProvider(primary=primary, fallback=fallback)
        request = LLMRequest(
            messages=[Message(role="user", content="Hello test")],
            model="test-model",
        )

        chunks = []
        async for chunk in provider.stream(request):
            chunks.append(chunk)

        assert provider.last_fallback_used is False
        combined_text = "".join(c.text for c in chunks)
        assert "healthy-primary" in combined_text

    asyncio.run(run())


def test_fallback_provider_raises_if_both_fail():
    async def run():
        primary = FakeLLMProvider(model_name="failing-1", should_fail=True)
        fallback = FakeLLMProvider(model_name="failing-2", should_fail=True)

        provider = FallbackLLMProvider(primary=primary, fallback=fallback)
        request = LLMRequest(
            messages=[Message(role="user", content="Hello test")],
            model="test-model",
        )

        with pytest.raises(LLMUnavailable):
            async for _ in provider.stream(request):
                pass

    asyncio.run(run())
