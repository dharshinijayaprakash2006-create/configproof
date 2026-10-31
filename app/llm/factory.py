"""Builds the provider chosen in .env. The rest of the app never imports a vendor."""
from app.config import Settings
from app.llm.fake import FakeProvider
from app.llm.fallback import FallbackProvider
from app.llm.openai_compat import OpenAICompatProvider


def build_provider(settings: Settings):
    if settings.llm_provider == "fake":
        return FakeProvider()
    if settings.llm_provider == "openai_compat":
        main = OpenAICompatProvider(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            timeout_seconds=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
            backoff_base_seconds=settings.llm_backoff_base_seconds,
        )
        if not settings.llm_fallback_model:  # added for Session 5
            return main
        backup = OpenAICompatProvider(
            base_url=settings.llm_fallback_base_url or settings.llm_base_url,
            api_key=settings.llm_fallback_api_key or settings.llm_api_key,
            model=settings.llm_fallback_model,
            timeout_seconds=settings.llm_timeout_seconds,
            max_retries=1,  # the user has already waited for the main model
            backoff_base_seconds=settings.llm_backoff_base_seconds,
        )
        return FallbackProvider(main, backup)
    raise ValueError(f"unknown LLM_PROVIDER: {settings.llm_provider}")
