"""Multi-provider middleware and framework integrations (spec 5.6)."""

from jamesian_layer.middleware.base_provider import (
    BaseProviderClient,
    OpenAICompatibleClient,
    ProviderError,
    collect_stream,
)
from jamesian_layer.middleware.baseten_client import BasetenClient
from jamesian_layer.middleware.fastapi_middleware import FastAPIInteroceptiveMiddleware
from jamesian_layer.middleware.fireworks_client import FireworksClient
from jamesian_layer.middleware.lmstudio_client import LMStudioClient
from jamesian_layer.middleware.llama_stack_hook import LlamaStackInteroceptiveHook
from jamesian_layer.middleware.meta_client import MetaModelClient
from jamesian_layer.middleware.modal_client import ModalClient
from jamesian_layer.middleware.multi_provider import (
    PROVIDERS,
    MultiProviderClient,
    list_providers,
)
from jamesian_layer.middleware.strata_client import StrataClient

__all__ = [
    "PROVIDERS",
    "BaseProviderClient",
    "BasetenClient",
    "FastAPIInteroceptiveMiddleware",
    "FireworksClient",
    "LMStudioClient",
    "LlamaStackInteroceptiveHook",
    "MetaModelClient",
    "ModalClient",
    "MultiProviderClient",
    "OpenAICompatibleClient",
    "ProviderError",
    "StrataClient",
    "collect_stream",
    "list_providers",
]
