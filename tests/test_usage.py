import json
from pathlib import Path

from app.cost import log_call
from app.usage import usage_by_day


def test_log_call_and_usage_by_day(tmp_path: Path):
    log_file = tmp_path / "logs" / "cost.jsonl"

    record1 = log_call(
        cost_log_path=log_file,
        provider="fake",
        model="examate-fake",
        usage={"input_tokens": 1000, "output_tokens": 500, "estimated": True},
        latency_ms=120.5,
        price_in_per_m=2.0,
        price_out_per_m=4.0,
        ok=True,
        fallback_used=False,
    )
    # Expected cost: (1000/1M)*2 + (500/1M)*4 = 0.002 + 0.002 = 0.004
    assert record1["cost_usd"] == 0.004

    record2 = log_call(
        cost_log_path=log_file,
        provider="fake",
        model="examate-fake-fallback",
        usage={"input_tokens": 500, "output_tokens": 250, "estimated": True},
        latency_ms=85.0,
        price_in_per_m=2.0,
        price_out_per_m=4.0,
        ok=True,
        fallback_used=True,
    )
    assert record2["cost_usd"] == 0.002

    summary = usage_by_day(log_file)
    assert summary["total_calls"] == 2
    assert summary["total_tokens"] == 2250
    assert summary["total_cost_usd"] == 0.006

    date_key = record1["timestamp"][:10]
    assert date_key in summary["days"]
    assert summary["days"][date_key]["calls"] == 2
    assert summary["days"][date_key]["fallback_used"] == 1


def test_usage_endpoint(client, tmp_path: Path, monkeypatch):
    from app.config import Settings, get_settings
    from app.main import app

    log_file = tmp_path / "cost_test.jsonl"
    log_file.write_text(
        json.dumps(
            {
                "timestamp": "2026-11-04T12:00:00+00:00",
                "provider": "fake",
                "model": "m",
                "input_tokens": 100,
                "output_tokens": 50,
                "cost_usd": 0.0001,
                "ok": True,
                "fallback_used": False,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    app.dependency_overrides[get_settings] = lambda: Settings(
        app_name="examate-rag",
        environment="test",
        cost_log_path=str(log_file),
    )

    resp = client.get("/usage")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_calls"] == 1
    assert data["total_tokens"] == 150
    assert "2026-11-04" in data["days"]
