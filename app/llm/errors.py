class LLMError(Exception):
    """Base exception for LLM operations."""


class LLMConfigurationError(LLMError):
    """Raised when an LLM provider or credential configuration is invalid."""


class LLMUnavailable(LLMError):
    """Raised when an LLM provider is unreachable, times out, or returns a 5xx response."""
