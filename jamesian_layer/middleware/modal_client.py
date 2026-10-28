"""Modal serverless GPU runner client (spec section 5.6).

Wraps the `run_agent_worker` deployment (app "jamesian-layer", A10G,
timeout 300). The remote call goes through the injectable `_invoke` hook so
unit tests can stub it without Modal credentials or network access.
"""

from collections.abc import AsyncGenerator
from typing import Any

from jamesian_layer.config import Settings
from jamesian_layer.middleware.base_provider import BaseProviderClient

APP_NAME = "jamesian-layer"
FUNCTION_NAME = "run_agent_worker"


class ModalClient(BaseProviderClient):
    provider_name = "modal"

    def __init__(
        self,
        token_id: str | None = None,
        token_secret: str | None = None,
        invoke: Any | None = None,
        model: str | None = None,
    ):
        self.token_id = token_id
        self.token_secret = token_secret
        self._invoke = invoke or self._remote_invoke
        self.model = model

    @classmethod
    def from_settings(cls, settings: Settings, **kwargs) -> "ModalClient":
        return cls(
            token_id=settings.modal_token_id,
            token_secret=settings.modal_token_secret,
            **kwargs,
        )

    def _require_tokens(self) -> None:
        if not self.token_id or not self.token_secret:
            raise ValueError("modal token id/secret are not set")

    def _remote_invoke(self, payload: dict) -> dict:
        import modal

        self._require_tokens()
        fn = modal.Function.from_name(APP_NAME, FUNCTION_NAME)
        return fn.remote(payload)

    async def chat_completion(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> dict:
        self._require_tokens()
        result = self._invoke(
            {"messages": messages, "tools": tools or [], "model": self.model}
        )
        return {
            "content": result.get("content"),
            "tool_calls": result.get("tool_calls", []),
            "model": result.get("model"),
            "finish_reason": result.get("finish_reason"),
            "raw": result,
        }

    async def stream_chat(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> AsyncGenerator[dict, None]:
        message = await self.chat_completion(messages, tools)
        yield {
            "content_delta": message.get("content") or "",
            "tool_call_deltas": [],
            "finish_reason": message.get("finish_reason"),
        }
