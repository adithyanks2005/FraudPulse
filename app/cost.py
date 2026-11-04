import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def log_call(
    cost_log_path: str | Path,
    provider: str,
    model: str,
    usage: Any,
    latency_ms: float,
    price_in_per_m: float = 0.0,
    price_out_per_m: float = 0.0,
    ok: bool = True,
    fallback_used: bool = False,
) -> dict:
    """Appends an LLM call record with token usage and estimated cost to the JSONL log file."""
    if hasattr(usage, "__dict__"):
        input_tokens = getattr(usage, "input_tokens", 0)
        output_tokens = getattr(usage, "output_tokens", 0)
        estimated = getattr(usage, "estimated", False)
    elif isinstance(usage, dict):
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        estimated = usage.get("estimated", False)
    else:
        input_tokens = 0
        output_tokens = 0
        estimated = False

    cost_usd = round(
        (input_tokens / 1_000_000.0) * price_in_per_m + (output_tokens / 1_000_000.0) * price_out_per_m,
        6,
    )

    record = {
        "timestamp": datetime.now(UTC).isoformat(),
        "provider": provider,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "estimated": estimated,
        "latency_ms": round(latency_ms, 2),
        "cost_usd": cost_usd,
        "ok": ok,
        "fallback_used": fallback_used,
    }

    path = Path(cost_log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    return record
