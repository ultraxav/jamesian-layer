"""LM Studio provider client with automated VRAM lifecycle management."""

import httpx

from jamesian_layer.config import Settings
from jamesian_layer.middleware.base_provider import OpenAICompatibleClient
from jamesian_layer.middleware.lmstudio_manager import LMStudioVRAMManager

DEFAULT_MODEL = "meta-llama_-_llama-3.2-3b"
DEFAULT_BASE_URL = "http://localhost:1234/v1"


class LMStudioClient(OpenAICompatibleClient):
    provider_name = "lmstudio"

    def __init__(
        self,
        api_key: str | None = "lm-studio",
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        transport: httpx.AsyncBaseTransport | None = None,
        auto_manage_vram: bool = True,
    ):
        super().__init__(api_key=api_key or "lm-studio", base_url=base_url, model=model, transport=transport)
        self.auto_manage_vram = auto_manage_vram
        self.vram_manager = LMStudioVRAMManager(base_url=base_url)

    def load(self, context_length: int = 32768) -> bool:
        """Explicitly load the client's model into VRAM."""
        if self.auto_manage_vram:
            return self.vram_manager.load_model(self.model, context_length=context_length)
        return True

    def unload(self) -> bool:
        """Explicitly unload the client's model from VRAM."""
        if self.auto_manage_vram:
            return self.vram_manager.unload_model(self.model)
        return True

    @classmethod
    def from_settings(cls, settings: Settings, **kwargs) -> "LMStudioClient":
        kwargs.setdefault("base_url", settings.lmstudio_base_url)
        kwargs.setdefault("api_key", settings.lmstudio_api_key)
        kwargs.setdefault("model", DEFAULT_MODEL)
        return cls(**kwargs)

