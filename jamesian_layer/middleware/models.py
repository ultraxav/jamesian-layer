"""Provider model registry for the automated campaign (spec section 6).

Only models verified live or explicitly spec-listed. Keys gate execution:
providers without credentials are skipped, never attempted.
"""

import os
from jamesian_layer.config import Settings
from jamesian_layer.middleware.lmstudio_manager import LMStudioVRAMManager

PROVIDER_MODELS: dict[str, list[str]] = {
    "baseten": ["meta-models/muse-spark-open-1026"],
    "meta": [
        "muse-spark-1.3",
        "muse-spark-1.2",
        "muse-spark-1.1",
        "muse-wonder-1.0",
    ],
    "fireworks": ["accounts/fireworks/models/llama-v3p3-70b-instruct"],
    "modal": ["meta-models/muse-spark-open-1026"],
    "lmstudio": [
        "google/gemma-4-31b",
        "google/gemma-4-26b-a4b",
        "google/gemma-4-12b",
        "google/gemma-4-e4b",
        "google/gemma-4-e2b",
        "prism-ml/bonsai-27b",
        "liquid/lfm2-24b-a2b",
        "liquid/lfm2.5-1.2b",
        "openai/gpt-oss-20b",
        "qwen/qwen3.5-9b",
        "zai-org/glm-4.7-flash",
        "nvidia/nemotron-3-nano-omni",
        "nvidia/nemotron-3-nano-4b",
        "qwen/qwen3.8-27b",
    ],
    "strata": ["qwen3.8-flash-next-iq2_xs"],
}


def configured_providers(settings: Settings) -> list[str]:
    """Providers with credentials or local availability."""
    available = []
    if settings.baseten_api_key:
        available.append("baseten")
    if settings.meta_api_key:
        available.append("meta")
    if settings.modal_token_id and settings.modal_token_secret:
        available.append("modal")
    if settings.fireworks_api_key:
        available.append("fireworks")

    # Local providers
    if settings.lmstudio_base_url:
        available.append("lmstudio")
    if settings.strata_launch_script and os.path.exists(settings.strata_launch_script):
        available.append("strata")
    return available


def discover_available_models(provider: str, settings: Settings | None = None) -> list[str]:
    """Dynamic model discovery for local and cloud providers with fallbacks."""
    settings = settings or Settings()
    if provider == "lmstudio":
        mgr = LMStudioVRAMManager(base_url=settings.lmstudio_base_url)
        discovered = mgr.discover_models()
        if discovered:
            return discovered
    return list(PROVIDER_MODELS.get(provider, []))

