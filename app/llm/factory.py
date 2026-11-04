from app.config import Settings
from app.llm.errors import LLMConfigurationError
from app.llm.providers.base import BaseLLMProvider
from app.llm.providers.fake import FakeLLMProvider
from app.llm.providers.fallback import FallbackLLMProvider
from app.llm.providers.openai_compatible import OpenAICompatibleProvider


def create_provider(settings: Settings) -> BaseLLMProvider:
    """Builds and returns the configured LLM provider, optionally wrapped in a fallback provider."""
    provider_type = (settings.llm_provider or "").lower().strip()

    if provider_type == "fake":
        primary: BaseLLMProvider = FakeLLMProvider(model_name=settings.llm_model)
        if settings.llm_fallback_model:
            fallback: BaseLLMProvider = FakeLLMProvider(model_name=settings.llm_fallback_model)
            return FallbackLLMProvider(primary, fallback)
        return primary

    if provider_type in ("openai", "ollama", "compatible"):
        primary = OpenAICompatibleProvider(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            timeout_seconds=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
        )

        if settings.llm_fallback_model:
            fallback_base_url = settings.llm_fallback_base_url or settings.llm_base_url
            fallback_api_key = (
                settings.llm_fallback_api_key if settings.llm_fallback_api_key else settings.llm_api_key
            )
            fallback = OpenAICompatibleProvider(
                base_url=fallback_base_url,
                api_key=fallback_api_key,
                model=settings.llm_fallback_model,
                timeout_seconds=settings.llm_timeout_seconds,
                max_retries=settings.llm_max_retries,
            )
            return FallbackLLMProvider(primary, fallback)

        return primary

    raise LLMConfigurationError(f"Unknown or unsupported LLM provider: {settings.llm_provider}")
