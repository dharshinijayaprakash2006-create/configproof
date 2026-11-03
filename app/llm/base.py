"""The provider abstraction: the rest of the app only knows this interface."""

from collections.abc import AsyncIterator
from typing import Protocol

from app.schemas import Message, Usage


class StreamResult:
    """Collects usage while a stream is consumed (filled in by the provider)."""

    def __init__(self) -> None:
        self.usage = Usage()
        self.model = ""  # added for Session 5: which model actually answered
        self.fallback_used = False  # added for Session 5


class LLMProvider(Protocol):
    name: str
    model: str

    def stream_chat(
        self, messages: list[Message], temperature: float, result: StreamResult
    ) -> AsyncIterator[str]:
        """Yield text pieces as they arrive; set result.usage before finishing."""
        ...


class LLMError(Exception):
    """Raised when the provider fails after all retries."""


class LLMUnavailable(LLMError):
    """Added for Session 5: the provider was down, slow or rate-limited after every retry.
    Only this error switches to the fallback model; a bad key (401) or wrong model (404)
    is a configuration bug that the fallback must not hide."""
