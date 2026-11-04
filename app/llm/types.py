from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Message:
    role: str
    content: str


@dataclass(frozen=True)
class UsageData:
    input_tokens: int
    output_tokens: int
    estimated: bool = False


@dataclass(frozen=True)
class LLMRequest:
    messages: Sequence[Message]
    model: str | None = None


@dataclass(frozen=True)
class LLMChunk:
    text: str = ""
    usage: UsageData | None = None
