"""Unit and integration tests for LM Studio and Strata providers."""

import pytest
from jamesian_layer.config import Settings
from jamesian_layer.middleware.base_provider import BaseProviderClient
from jamesian_layer.middleware.lmstudio_client import LMStudioClient
from jamesian_layer.middleware.lmstudio_manager import LMStudioVRAMManager
from jamesian_layer.middleware.models import discover_available_models
from jamesian_layer.middleware.multi_provider import MultiProviderClient
from jamesian_layer.middleware.strata_client import StrataClient
from jamesian_layer.middleware.strata_manager import StrataServerManager


def test_lmstudio_client_initialization():
    settings = Settings(lmstudio_base_url="http://localhost:1234/v1")
    client = MultiProviderClient("lmstudio", settings=settings, model="meta-llama_-_llama-3.2-3b")
    assert isinstance(client.raw_client, LMStudioClient)
    assert client.raw_client.model == "meta-llama_-_llama-3.2-3b"
    assert client.raw_client.base_url == "http://localhost:1234/v1"


def test_strata_client_initialization():
    settings = Settings(
        strata_base_url="http://127.0.0.1:8080/v1",
        strata_launch_script="/tmp/fake_strata.sh",
    )
    client = MultiProviderClient("strata", settings=settings, model="qwen3.8-flash-next-iq2_xs")
    assert isinstance(client.raw_client, StrataClient)
    assert client.raw_client.model == "qwen3.8-flash-next-iq2_xs"
    assert client.raw_client.base_url == "http://127.0.0.1:8080/v1"


def test_lmstudio_vram_manager_discovery():
    mgr = LMStudioVRAMManager("http://localhost:1234/v1")
    models = mgr.discover_models()
    # If LM Studio is running locally, models will be a list of non-embedding models
    assert isinstance(models, list)
    assert not any("embed" in m.lower() for m in models)


def test_strata_server_manager_is_running():
    mgr = StrataServerManager(base_url="http://127.0.0.1:8080/v1")
    # Initially strata should not be running
    status = mgr.is_running()
    assert isinstance(status, bool)

