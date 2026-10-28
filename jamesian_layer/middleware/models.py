"""Provider model registry for the automated campaign (spec section 6).

Only models verified live or explicitly spec-listed. Keys gate execution:
providers without credentials are skipped, never attempted.
"""

from jamesian_layer.config import Settings

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
}


def configured_providers(settings: Settings) -> list[str]:
    """Providers with credentials present (modal needs both token parts)."""
    available = []
    if settings.baseten_api_key:
        available.append("baseten")
    if settings.meta_api_key:
        available.append("meta")
    if settings.modal_token_id and settings.modal_token_secret:
        available.append("modal")
    if settings.fireworks_api_key:
        available.append("fireworks")
    return available
