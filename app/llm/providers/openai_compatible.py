import json
from collections.abc import AsyncIterator

import httpx

from app.llm.errors import LLMConfigurationError, LLMUnavailable
from app.llm.providers.base import BaseLLMProvider
from app.llm.types import LLMChunk, LLMRequest, UsageData


class OpenAICompatibleProvider(BaseLLMProvider):
    """Provider for OpenAI-compatible APIs (OpenAI, Ollama, vLLM, LocalAI)."""

    def __init__(
        self,
        base_url: str,
        api_key: str = "",
        model: str = "gpt-4o-mini",
        timeout_seconds: float = 30.0,
        max_retries: int = 2,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout_seconds
        self.max_retries = max_retries

    async def stream(self, request: LLMRequest) -> AsyncIterator[LLMChunk]:
        endpoint = f"{self.base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        model = request.model or self.model
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "stream": True,
            "stream_options": {"include_usage": True},
        }

        attempts = 0
        while True:
            attempts += 1
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    async with client.stream("POST", endpoint, headers=headers, json=payload) as response:
                        if response.status_code in (401, 403):
                            raise LLMConfigurationError(f"Authentication failed ({response.status_code})")
                        if response.status_code >= 500 or response.status_code == 429:
                            raise LLMUnavailable(
                                f"Service unavailable from {endpoint}: status {response.status_code}"
                            )
                        if response.status_code != 200:
                            content = await response.aread()
                            content_str = content.decode("utf-8", errors="replace")
                            raise LLMUnavailable(
                                f"Unexpected HTTP status {response.status_code}: {content_str}"
                            )

                        async for line in response.aiter_lines():
                            line = line.strip()
                            if not line or not line.startswith("data:"):
                                continue
                            data_str = line[5:].strip()
                            if data_str == "[DONE]":
                                break

                            try:
                                parsed = json.loads(data_str)
                            except json.JSONDecodeError:
                                continue

                            delta_text = ""
                            choices = parsed.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                delta_text = delta.get("content") or ""

                            usage_data = None
                            if "usage" in parsed and parsed["usage"]:
                                u = parsed["usage"]
                                usage_data = UsageData(
                                    input_tokens=u.get("prompt_tokens", 0),
                                    output_tokens=u.get("completion_tokens", 0),
                                    estimated=False,
                                )

                            if delta_text or usage_data:
                                yield LLMChunk(text=delta_text, usage=usage_data)
                return

            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as err:
                if attempts <= self.max_retries:
                    continue
                raise LLMUnavailable(f"Failed to connect to LLM provider at {endpoint}: {err}") from err
            except LLMConfigurationError:
                raise
            except LLMUnavailable:
                if attempts <= self.max_retries:
                    continue
                raise
            except Exception as err:
                raise LLMUnavailable(f"Error calling LLM provider: {err}") from err
