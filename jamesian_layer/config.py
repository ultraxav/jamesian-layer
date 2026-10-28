"""Global configuration for the Jamesian Layer (spec section 8)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Provider API Keys
    meta_api_key: str | None = None
    baseten_api_key: str | None = None
    modal_token_id: str | None = None
    modal_token_secret: str | None = None
    fireworks_api_key: str | None = None

    # Middleware Defaults
    default_provider: str = "fireworks"
    default_model: str = "accounts/fireworks/models/llama-v3p3-70b-instruct"

    # Biophysical Daemon Defaults
    ode_frequency_hz: float = 20.0
    cpg_habit_frequency_hz: float = 10.0
    telemetry_token_budget: int = 40

    # Unified Threshold Hierarchy
    theta_habit: float = 0.15  # Maximum prediction error for 0-token CPG cruise
    theta_surprise: float = 0.25  # Prediction error triggering autonomic alarm
    theta_jaccard: float = 0.70  # Jaccard overlap triggering circuit-breaker
    jaccard_window_k: int = 3  # Consecutive turns required to trip breaker

    model_config = SettingsConfigDict(env_file=".env")
