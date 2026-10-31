from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "examate-rag"
    environment: str = "local"  # local | ci | production

    llm_provider: str = "fake"  # fake | openai_compat
    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = ""
    llm_model: str = "llama3.1:8b"

    llm_timeout_seconds: float = 30.0
    llm_max_retries: int = 3
    llm_backoff_base_seconds: float = 0.5

    # Added for Session 5: a second model that answers when the main one is unavailable.
    # Empty LLM_FALLBACK_MODEL = no fallback. Base URL and key default to the main ones.
    llm_fallback_model: str = ""
    llm_fallback_base_url: str = ""
    llm_fallback_api_key: str = ""

    price_input_per_million: float = 0.0
    price_output_per_million: float = 0.0
    cost_log_path: str = "logs/cost.jsonl"

    # Needed for /ready in Session 6
    database_url: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
