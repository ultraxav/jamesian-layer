"""Unified multi-provider router (spec section 5.6)."""

from jamesian_layer.config import Settings
from jamesian_layer.middleware.base_provider import BaseProviderClient
from jamesian_layer.middleware.baseten_client import BasetenClient
from jamesian_layer.middleware.fireworks_client import FireworksClient
from jamesian_layer.middleware.meta_client import MetaModelClient
from jamesian_layer.middleware.modal_client import ModalClient

PROVIDERS = ("meta", "baseten", "modal", "fireworks")


def list_providers() -> tuple[str, ...]:
    return PROVIDERS


class MultiProviderClient(BaseProviderClient):
    def __init__(self, provider: str = "fireworks", settings: Settings | None = None, **kwargs):
        settings = settings or Settings()
        builders = {
            "meta": MetaModelClient.from_settings,
            "baseten": BasetenClient.from_settings,
            "modal": ModalClient.from_settings,
            "fireworks": FireworksClient.from_settings,
        }
        try:
            build = builders[provider]
        except KeyError:
            raise ValueError(f"unknown provider: {provider!r} (expected one of {PROVIDERS})")
        self.provider = provider
        self._client = build(settings, **kwargs)

    @property
    def model(self) -> str | None:
        return getattr(self._client, "model", None)

    async def chat_completion(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> dict:
        return await self._client.chat_completion(messages, tools)

    async def stream_chat(self, messages, tools=None):
        async for chunk in self._client.stream_chat(messages, tools):
            yield chunk
