"""Streaming client for any OpenAI-compatible /chat/completions endpoint.

Reliability: per-call timeout, retries with exponential backoff and full jitter on
timeouts, connection errors, HTTP 429 and HTTP 5xx. Client errors (400, 401, 403, 404)
are not retried because retrying cannot fix them.
"""
import asyncio
import json
import random
from collections.abc import AsyncIterator

import httpx

from app.llm.base import LLMError, LLMUnavailable, StreamResult
from app.schemas import Message, Usage
from app.tokens import estimate_tokens

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def backoff_delay(attempt: int, base: float, cap: float = 8.0) -> float:
    """Full jitter: a random wait between 0 and base * 2**attempt (capped)."""
    return random.uniform(0, min(cap, base * (2**attempt)))


class OpenAICompatProvider:
    name = "openai_compat"

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 30.0,
        max_retries: int = 3,
        backoff_base_seconds: float = 0.5,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = httpx.Timeout(timeout_seconds, connect=5.0)
        self.max_retries = max_retries
        self.backoff_base = backoff_base_seconds
        self.transport = transport  # injected in tests

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def stream_chat(
        self, messages: list[Message], temperature: float, result: StreamResult
    ) -> AsyncIterator[str]:
        payload = {
            "model": self.model,
            "messages": [m.model_dump() for m in messages],
            "temperature": temperature,
            "stream": True,
            # Ask for a final usage chunk; providers that do not support it ignore or reject it.
            "stream_options": {"include_usage": True},
        }
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            produced_any = False
            try:
                async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport) as client:
                    async with client.stream(
                        "POST", f"{self.base_url}/chat/completions",
                        headers=self._headers(), json=payload,
                    ) as response:
                        if response.status_code in RETRYABLE_STATUS:
                            raise httpx.HTTPStatusError(
                                f"retryable status {response.status_code}",
                                request=response.request, response=response,
                            )
                        if response.status_code >= 400:
                            body = (await response.aread()).decode(errors="replace")[:300]
                            raise LLMError(f"provider returned {response.status_code}: {body}")
                        text_parts: list[str] = []
                        async for line in response.aiter_lines():
                            if not line.startswith("data:"):
                                continue
                            data = line[len("data:"):].strip()
                            if data == "[DONE]":
                                break
                            chunk = json.loads(data)
                            if chunk.get("usage"):
                                u = chunk["usage"]
                                result.usage = Usage(
                                    input_tokens=u.get("prompt_tokens", 0),
                                    output_tokens=u.get("completion_tokens", 0),
                                )
                            for choice in chunk.get("choices", []):
                                piece = (choice.get("delta") or {}).get("content")
                                if piece:
                                    produced_any = True
                                    text_parts.append(piece)
                                    yield piece
                        if result.usage.input_tokens == 0 and result.usage.output_tokens == 0:
                            result.usage = Usage(
                                input_tokens=sum(estimate_tokens(m.content) for m in messages),
                                output_tokens=estimate_tokens("".join(text_parts)),
                                estimated=True,
                            )
                        return
            except LLMError:
                raise
            except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as exc:
                # Never retry after text has already been streamed to the user:
                # a retry would repeat or duplicate the answer.
                if produced_any:
                    raise LLMError(f"stream broke mid-answer: {exc}") from exc
                last_error = exc
                if attempt < self.max_retries:
                    await asyncio.sleep(backoff_delay(attempt, self.backoff_base))
        # Session 5: LLMUnavailable (a kind of LLMError) so the fallback knows it may step in.
        raise LLMUnavailable(f"LLM call failed after {self.max_retries + 1} attempts: {last_error}")
