"""Added for Session 5: answer with a second model when the main one is unavailable."""

from collections.abc import AsyncIterator

from app.llm.base import LLMUnavailable, StreamResult
from app.schemas import Message


class FallbackProvider:
    def __init__(self, main, fallback) -> None:
        self.main = main
        self.fallback = fallback
        self.name = main.name
        self.model = main.model

    async def stream_chat(
        self, messages: list[Message], temperature: float, result: StreamResult
    ) -> AsyncIterator[str]:
        produced_any = False
        try:
            async for piece in self.main.stream_chat(messages, temperature, result):
                produced_any = True
                yield piece
            result.model = self.main.model
            return
        except LLMUnavailable:
            # No fallback once text reached the user: a second model would start a new,
            # different answer in the middle of the first one.
            if produced_any:
                raise
        result.fallback_used = True
        result.model = self.fallback.model
        async for piece in self.fallback.stream_chat(messages, temperature, result):
            yield piece
