"""Fireworks AI low-latency streaming client (OpenAI-compatible)."""

import httpx

from jamesian_layer.config import Settings
from jamesian_layer.middleware.base_provider import OpenAICompatibleClient

DEFAULT_MODEL = "accounts/fireworks/models/llama-v3p3-70b-instruct"
DEFAULT_BASE_URL = "https://api.fireworks.ai/inference/v1"


class FireworksClient(OpenAICompatibleClient):
    provider_name = "fireworks"

    def __init__(
        self,
        api_key: str | None,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        super().__init__(api_key=api_key, base_url=base_url, model=model, transport=transport)

    @classmethod
    def from_settings(cls, settings: Settings, **kwargs) -> "FireworksClient":
        kwargs.setdefault("model", settings.default_model)
        return cls(api_key=settings.fireworks_api_key, **kwargs)
