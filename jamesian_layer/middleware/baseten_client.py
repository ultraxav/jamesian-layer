"""Baseten dedicated model client (meta-models/muse-spark-open-1026)."""

import httpx

from jamesian_layer.config import Settings
from jamesian_layer.middleware.base_provider import OpenAICompatibleClient

DEFAULT_MODEL = "meta-models/muse-spark-open-1026"
DEFAULT_BASE_URL = "https://inference.baseten.co/v1"


class BasetenClient(OpenAICompatibleClient):
    provider_name = "baseten"

    def __init__(
        self,
        api_key: str | None,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        super().__init__(api_key=api_key, base_url=base_url, model=model, transport=transport)

    @classmethod
    def from_settings(cls, settings: Settings, **kwargs) -> "BasetenClient":
        return cls(api_key=settings.baseten_api_key, **kwargs)
