"""Abstract provider client and shared OpenAI-compatible transport (spec 5.6)."""

import json
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator

import httpx

TIMEOUT_S = 30.0


class ProviderError(RuntimeError):
    def __init__(self, provider: str, status: int, body: str):
        super().__init__(f"{provider} request failed (status {status}): {body[:200]}")
        self.provider = provider
        self.status = status
        self.body = body


class BaseProviderClient(ABC):
    @abstractmethod
    async def chat_completion(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> dict:
        pass

    @abstractmethod
    async def stream_chat(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> AsyncGenerator[dict, None]:
        pass


def _normalize_message(data: dict) -> dict:
    choice = (data.get("choices") or [{}])[0]
    message = choice.get("message", {})
    tool_calls = [
        {
            "id": tc.get("id"),
            "name": (tc.get("function") or {}).get("name"),
            "arguments": (tc.get("function") or {}).get("arguments", ""),
        }
        for tc in message.get("tool_calls") or []
    ]
    return {
        "content": message.get("content"),
        "tool_calls": tool_calls,
        "model": data.get("model"),
        "finish_reason": choice.get("finish_reason"),
        "raw": data,
    }


class OpenAICompatibleClient(BaseProviderClient):
    """Shared POST + SSE transport; subclasses set endpoint, auth, and model."""

    provider_name = "openai-compatible"

    def __init__(
        self,
        *,
        api_key: str | None,
        base_url: str,
        model: str,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout_s: float = TIMEOUT_S,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._transport = transport
        self._timeout = httpx.Timeout(timeout_s)

    def _require_key(self) -> str:
        if not self.api_key:
            raise ValueError(f"{self.provider_name} API key is not set")
        return self.api_key

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=self._transport, timeout=self._timeout)

    def _payload(self, messages: list[dict], tools: list[dict] | None) -> dict:
        payload: dict = {"model": self.model, "messages": messages}
        if tools:
            payload["tools"] = tools
        return payload

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._require_key()}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _raise_for_status(provider: str, response: httpx.Response) -> None:
        if response.status_code >= 400:
            raise ProviderError(provider, response.status_code, response.text)

    async def chat_completion(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> dict:
        async with self._client() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=self._payload(messages, tools),
                headers=self._headers(),
            )
        self._raise_for_status(self.provider_name, response)
        return _normalize_message(response.json())

    async def stream_chat(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> AsyncGenerator[dict, None]:
        payload = self._payload(messages, tools)
        payload["stream"] = True
        async with self._client() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={**self._headers(), "Accept": "text/event-stream"},
            ) as response:
                self._raise_for_status(self.provider_name, response)
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[len("data:"):].strip()
                    if data == "[DONE]":
                        return
                    yield _normalize_chunk(json.loads(data))


def _normalize_chunk(data: dict) -> dict:
    choice = (data.get("choices") or [{}])[0]
    delta = choice.get("delta", {})
    fragments = []
    for tc in delta.get("tool_calls") or []:
        fn = tc.get("function") or {}
        fragments.append(
            {
                "index": tc.get("index", 0),
                "id": tc.get("id"),
                "name": fn.get("name"),
                "arguments_fragment": fn.get("arguments", ""),
            }
        )
    return {
        "content_delta": delta.get("content") or "",
        "tool_call_deltas": fragments,
        "finish_reason": choice.get("finish_reason"),
    }


async def collect_stream(chunks: AsyncGenerator[dict, None]) -> dict:
    """Assemble streamed chunks into one normalized message dict."""
    content_parts: list[str] = []
    calls: dict[int, dict] = {}
    finish_reason = None
    async for chunk in chunks:
        content_parts.append(chunk.get("content_delta") or "")
        for frag in chunk.get("tool_call_deltas") or []:
            entry = calls.setdefault(
                frag["index"], {"id": frag["id"], "name": frag["name"], "arguments": ""}
            )
            if frag["id"]:
                entry["id"] = frag["id"]
            if frag["name"]:
                entry["name"] = frag["name"]
            entry["arguments"] += frag["arguments_fragment"] or ""
        finish_reason = chunk.get("finish_reason") or finish_reason
    return {
        "content": "".join(content_parts) or None,
        "tool_calls": [calls[i] for i in sorted(calls)],
        "model": None,
        "finish_reason": finish_reason,
        "raw": None,
    }


def parse_streamed_json_arg(arguments: str) -> Any:
    return json.loads(arguments)
