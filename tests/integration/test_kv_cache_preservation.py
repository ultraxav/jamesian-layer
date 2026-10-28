"""KV-cache prefix invariance through the provider stream path."""

import json

import httpx

from jamesian_layer.core.biophysical_state import BiophysicalState
from jamesian_layer.kv_cache.prefix_verifier import prefix_hash, verify_suffix_only
from jamesian_layer.kv_cache.suffix_formatter import (
    check_token_budget,
    format_suffix,
    parse_telemetry,
)
from jamesian_layer.middleware.base_provider import collect_stream
from jamesian_layer.middleware.fireworks_client import FireworksClient

MESSAGES = [{"role": "user", "content": "advance"}]


def sse_transport(text: str):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=text.encode(),
            headers={"content-type": "text/event-stream"},
        )

    return httpx.MockTransport(handler)


def test_stream_prefix_preserved_and_suffix_parses():
    body = 'data: {"choices": [{"delta": {"content": "ok"}, "finish_reason": "stop"}]}\n\ndata: [DONE]\n\n'
    client = FireworksClient(api_key="test", transport=sse_transport(body))
    prefix = json.dumps(MESSAGES)
    message = _run(collect_stream(client.stream_chat(MESSAGES)))
    assert message["content"] == "ok"

    state = BiophysicalState(sigma=0.22, T_coil=28.1)
    suffix = format_suffix(state)
    after = prefix + suffix
    assert verify_suffix_only(prefix, after) == suffix
    assert prefix_hash(after[: len(prefix)]) == prefix_hash(prefix)

    comment = suffix.split("\n", 1)[1]
    assert parse_telemetry(comment)["T_coil"] == 28.1
    estimate, ok = check_token_budget(state)
    assert ok and estimate <= 45


def _run(coro):
    import asyncio

    return asyncio.run(coro)
