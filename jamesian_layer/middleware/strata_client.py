"""Strata provider client with on-demand server lifecycle management."""

import httpx

from jamesian_layer.config import Settings
from jamesian_layer.middleware.base_provider import OpenAICompatibleClient
from jamesian_layer.middleware.strata_manager import StrataServerManager

DEFAULT_MODEL = "qwen3.8-flash-next-iq2_xs"
DEFAULT_BASE_URL = "http://127.0.0.1:8080/v1"


class StrataClient(OpenAICompatibleClient):
    provider_name = "strata"

    def __init__(
        self,
        api_key: str | None = "strata",
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        transport: httpx.AsyncBaseTransport | None = None,
        launch_script: str | None = None,
    ):
        super().__init__(api_key=api_key or "strata", base_url=base_url, model=model, transport=transport)
        self.server_manager = StrataServerManager(
            launch_script=launch_script or "/var/home/ultraxav/projects/strata/run-iq2_xs.sh",
            base_url=base_url,
        )

    def start_server(self) -> bool:
        """Start the Strata server process if not running."""
        return self.server_manager.start()

    def stop_server(self) -> None:
        """Stop the Strata server process."""
        self.server_manager.stop()

    @classmethod
    def from_settings(cls, settings: Settings, **kwargs) -> "StrataClient":
        kwargs.setdefault("base_url", settings.strata_base_url)
        kwargs.setdefault("api_key", settings.strata_api_key)
        kwargs.setdefault("model", DEFAULT_MODEL)
        kwargs.setdefault("launch_script", settings.strata_launch_script)
        return cls(**kwargs)

