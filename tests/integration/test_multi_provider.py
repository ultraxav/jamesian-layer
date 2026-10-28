"""Multi-provider routing and transport contract (offline, via MockTransport)."""

import json

import httpx
import pytest

from jamesian_layer.config import Settings
from jamesian_layer.middleware.base_provider import ProviderError, collect_stream
from jamesian_layer.middleware.multi_provider import MultiProviderClient, list_providers

SETTINGS = Settings(
    meta_api_key="meta-test",
    baseten_api_key="baseten-test",
    fireworks_api_key="fireworks-test",
    modal_token_id="modal-id",
    modal_token_secret="modal-secret",
)

EXPECTED = {
    "meta": ("meta-test", "muse-spark-1.3"),
    "baseten": ("baseten-test", "meta-models/muse-spark-open-1026"),
    "fireworks": ("fireworks-test", Settings().default_model),
}

MESSAGES = [{"role": "user", "content": "advance"}]
TOOLS = [{"type": "function", "function": {"name": "robot_actuator"}}]


def completion_body():
    return {
        "id": "chatcmpl-x",
        "model": "test-model",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "ok",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {
                                "name": "robot_actuator",
                                "arguments": '{"velocity": 1.0}',
                            },
                        }
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ],
    }


def sse_response_body():
    chunks = [
        {
            "choices": [
                {
                    "delta": {
                        "tool_calls": [
                            {
                                "index": 0,
                                "id": "call_1",
                                "function": {"name": "robot_actuator", "arguments": '{"velo'},
                            }
                        ]
                    },
                    "finish_reason": None,
                }
            ]
        },
        {
            "choices": [
                {
                    "delta": {
                        "tool_calls": [{"index": 0, "function": {"arguments": 'city": 1.0}'}}]
                    },
                    "finish_reason": None,
                }
            ]
        },
        {"choices": [{"delta": {}, "finish_reason": "tool_calls"}]},
    ]
    text = "".join("data: " + json.dumps(c) + "\n\n" for c in chunks) + "data: [DONE]\n\n"
    return text.encode()


def make_transport(expected_key, seen, mode="completion", status=200):
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        assert request.headers["authorization"] == f"Bearer {expected_key}"
        body = json.loads(request.content.decode())
        if mode == "completion":
            return httpx.Response(status, json=completion_body())
        return httpx.Response(
            status, content=sse_response_body(), headers={"content-type": "text/event-stream"}
        )

    return httpx.MockTransport(handler)


def test_list_providers():
    assert set(list_providers()) == {"meta", "baseten", "modal", "fireworks"}


def test_unknown_provider_raises():
    with pytest.raises(ValueError):
        MultiProviderClient("unknown", SETTINGS)


@pytest.mark.parametrize("provider", ["meta", "baseten", "fireworks"])
def test_routing_auth_and_completion(provider):
    key, model = EXPECTED[provider]
    seen: list = []
    client = MultiProviderClient(provider, SETTINGS, transport=make_transport(key, seen))
    out = _run(client.chat_completion(MESSAGES, TOOLS))
    assert out["content"] == "ok"
    assert out["tool_calls"] == [
        {"id": "call_1", "name": "robot_actuator", "arguments": '{"velocity": 1.0}'}
    ]
    assert len(seen) == 1
    assert json.loads(seen[0].content.decode())["model"] == model


def test_stream_assembles_fragmented_tool_call():
    seen: list = []
    client = MultiProviderClient(
        "fireworks", SETTINGS, transport=make_transport("fireworks-test", seen, mode="stream")
    )
    message = _run(collect_stream(client.stream_chat(MESSAGES, TOOLS)))
    assert message["tool_calls"] == [
        {"id": "call_1", "name": "robot_actuator", "arguments": '{"velocity": 1.0}'}
    ]
    assert json.loads(message["tool_calls"][0]["arguments"]) == {"velocity": 1.0}


def test_provider_error_mapping():
    seen: list = []
    client = MultiProviderClient(
        "meta", SETTINGS, transport=make_transport("meta-test", seen, status=500)
    )
    with pytest.raises(ProviderError) as exc:
        _run(client.chat_completion(MESSAGES))
    assert exc.value.status == 500


def test_missing_key_raises():
    # Explicit Nones so ambient .env credentials cannot mask the failure.
    empty = Settings(
        meta_api_key=None,
        baseten_api_key=None,
        modal_token_id=None,
        modal_token_secret=None,
        fireworks_api_key=None,
    )
    client = MultiProviderClient("meta", empty)
    with pytest.raises(ValueError):
        _run(client.chat_completion(MESSAGES))


def test_modal_routing_with_stubbed_invoke():
    seen = {}

    def fake_invoke(payload):
        assert payload["messages"] == MESSAGES
        seen.update(payload)
        return {
            "content": "modal-ok",
            "tool_calls": [],
            "model": "modal-worker",
            "finish_reason": "stop",
        }

    client = MultiProviderClient(
        "modal", SETTINGS, invoke=fake_invoke, model="meta-models/muse-spark-open-1026"
    )
    out = _run(client.chat_completion(MESSAGES))
    assert out["content"] == "modal-ok"
    assert out["model"] == "modal-worker"
    assert seen["model"] == "meta-models/muse-spark-open-1026"


def test_modal_missing_tokens_raise():
    from jamesian_layer.middleware.modal_client import ModalClient

    with pytest.raises(ValueError):
        _run(ModalClient().chat_completion(MESSAGES))


def _run(coro):
    import asyncio

    return asyncio.run(coro)
