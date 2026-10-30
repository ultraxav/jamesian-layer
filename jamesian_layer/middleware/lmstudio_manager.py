"""LM Studio VRAM management helper: load, unload, and discover models."""

import json
import logging
import time
import httpx

logger = logging.getLogger(__name__)

EMBEDDING_KEYWORDS = [
    "embed", "bge", "nomic", "gte", "e5",
    "minilm", "arctic-embed", "stella", "all-mini",
]


class LMStudioVRAMManager:
    """Manages explicit model loading and unloading in LM Studio to conserve VRAM."""

    def __init__(self, base_url: str = "http://localhost:1234/v1"):
        # base_url could be http://localhost:1234/v1 or http://localhost:1234
        self.host_url = base_url.replace("/v1", "").rstrip("/")

    def get_loaded_models(self) -> list[str]:
        """Return list of model IDs currently loaded in VRAM."""
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(f"{self.host_url}/api/v0/models")
                if res.status_code == 200:
                    data = res.json()
                    return [
                        item["id"]
                        for item in data.get("data", [])
                        if item.get("state") == "loaded" and item.get("id")
                    ]
        except Exception as e:
            logger.warning(f"Failed to query loaded models from LM Studio: {e}")
        return []

    def discover_models(self) -> list[str]:
        """Discover available (chat/completion) models in LM Studio."""
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(f"{self.host_url}/v1/models")
                if res.status_code == 200:
                    data = res.json()
                    models = [
                        m["id"]
                        for m in data.get("data", [])
                        if not any(k in m["id"].lower() for k in EMBEDDING_KEYWORDS)
                    ]
                    return sorted(models)
        except Exception as e:
            logger.warning(f"Failed to discover models from LM Studio: {e}")
        return []

    def unload_model(self, model_id: str, timeout_s: float = 15.0) -> bool:
        """Unload specific model instance from LM Studio VRAM."""
        try:
            with httpx.Client(timeout=timeout_s) as client:
                client.post(
                    f"{self.host_url}/api/v1/models/unload",
                    json={"instance_id": model_id},
                )
        except Exception as e:
            logger.info(f"Unload notice for {model_id}: {e}")

        # Poll until unloaded
        t0 = time.time()
        while time.time() - t0 < timeout_s:
            if model_id not in self.get_loaded_models():
                return True
            time.sleep(0.5)
        return False

    def unload_all_models(self) -> None:
        """Unload all currently loaded models from VRAM."""
        for model_id in self.get_loaded_models():
            logger.info(f"Unloading residual model from LM Studio VRAM: {model_id}...")
            self.unload_model(model_id)

    def load_model(self, model_id: str, context_length: int = 32768, timeout_s: float = 180.0) -> bool:
        """Unload prior models first, then load the target model."""
        self.unload_all_models()
        time.sleep(1.0)
        logger.info(f"Loading {model_id} into LM Studio VRAM...")
        try:
            with httpx.Client(timeout=timeout_s) as client:
                res = client.post(
                    f"{self.host_url}/api/v1/models/load",
                    json={"model": model_id, "context_length": context_length},
                )
                return res.status_code in (200, 204)
        except Exception as e:
            logger.error(f"Failed to load {model_id} into LM Studio: {e}")
            return False

