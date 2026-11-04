import json


def test_chat_streams_fake_response(client):
    payload = {
        "messages": [{"role": "user", "content": "What are the latest bank fraud figures?"}],
        "model": "FraudPulse",
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")

    lines = [line.strip() for line in response.text.split("\n") if line.strip()]
    deltas = []
    done_payload = None

    for line in lines:
        if line.startswith("data:"):
            parsed = json.loads(line[5:].strip())
            if "delta" in parsed:
                deltas.append(parsed["delta"])
            if "cost_usd" in parsed:
                done_payload = parsed

    full_text = "".join(deltas)
    assert "Fraud risk insights processed successfully" in full_text
    assert done_payload is not None
    assert "usage" in done_payload
    assert done_payload["usage"]["input_tokens"] > 0
    assert done_payload["usage"]["output_tokens"] > 0
    assert "cost_usd" in done_payload
