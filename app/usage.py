import json
from collections import defaultdict
from pathlib import Path


def usage_by_day(cost_log_path: str | Path) -> dict:
    """Aggregates calls, tokens, and cost per day (UTC) from the cost log."""
    path = Path(cost_log_path)
    if not path.exists():
        return {
            "days": {},
            "total_calls": 0,
            "total_cost_usd": 0.0,
            "total_tokens": 0,
        }

    daily_stats = defaultdict(
        lambda: {
            "calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "cost_usd": 0.0,
            "errors": 0,
            "fallback_used": 0,
        }
    )

    total_calls = 0
    total_cost_usd = 0.0
    total_tokens = 0

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            date_key = entry.get("timestamp", "")[:10] or "unknown"
            inp = entry.get("input_tokens", 0)
            out = entry.get("output_tokens", 0)
            cost = entry.get("cost_usd", 0.0)
            ok = entry.get("ok", True)
            fb = entry.get("fallback_used", False)

            day = daily_stats[date_key]
            day["calls"] += 1
            day["input_tokens"] += inp
            day["output_tokens"] += out
            day["total_tokens"] += inp + out
            day["cost_usd"] = round(day["cost_usd"] + cost, 6)
            if not ok:
                day["errors"] += 1
            if fb:
                day["fallback_used"] += 1

            total_calls += 1
            total_cost_usd += cost
            total_tokens += inp + out

    return {
        "days": dict(daily_stats),
        "total_calls": total_calls,
        "total_cost_usd": round(total_cost_usd, 6),
        "total_tokens": total_tokens,
    }
