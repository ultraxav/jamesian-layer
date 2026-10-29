"""Meta Model API async client ($150 hackathon credit pool)."""

import httpx

from jamesian_layer.config import Settings
from jamesian_layer.middleware.base_provider import OpenAICompatibleClient

DEFAULT_MODEL = "muse-spark-1.3"
DEFAULT_BASE_URL = "https://api.meta.ai/v1"


class MetaModelClient(OpenAICompatibleClient):
    provider_name = "meta"

    def __init__(
        self,
        api_key: str | None,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        transport: httpx.AsyncBaseTransport | None = None,
        reasoning_effort: str = "minimal",
    ):
        super().__init__(api_key=api_key, base_url=base_url, model=model, transport=transport)
        self.reasoning_effort = reasoning_effort

    def _payload(self, messages: list[dict], tools: list[dict] | None) -> dict:
        payload = super()._payload(messages, tools)
        if self.reasoning_effort:
            payload["reasoning_effort"] = self.reasoning_effort
        return payload

    @classmethod
    def from_settings(cls, settings: Settings, **kwargs) -> "MetaModelClient":
        return cls(api_key=settings.meta_api_key, **kwargs)
