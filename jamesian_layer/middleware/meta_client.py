"""Meta Model API async client ($150 hackathon credit pool)."""

import httpx

from jamesian_layer.config import Settings
from jamesian_layer.middleware.base_provider import OpenAICompatibleClient

DEFAULT_MODEL = "meta-llama/Llama-3.3-70B-Instruct"
DEFAULT_BASE_URL = "https://api.meta.ai/v1"


class MetaModelClient(OpenAICompatibleClient):
    provider_name = "meta"

    def __init__(
        self,
        api_key: str | None,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        super().__init__(api_key=api_key, base_url=base_url, model=model, transport=transport)

    @classmethod
    def from_settings(cls, settings: Settings, **kwargs) -> "MetaModelClient":
        return cls(api_key=settings.meta_api_key, **kwargs)
