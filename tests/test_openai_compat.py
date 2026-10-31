import asyncio
import json

import httpx
import pytest

from app.llm.base import LLMError, LLMUnavailable, StreamResult
from app.llm.openai_compat import OpenAICompatProvider
from app.schemas import Message

MSGS = [Message(role="user", content="hello")]


def sse_body(pieces, usage=None):
    lines = []
    for p in pieces:
        lines.append("data: " + json.dumps({"choices": [{"delta": {"content": p}}]}))
        lines.append("")
    if usage:
        lines.append("data: " + json.dumps({"choices": [], "usage": usage}))
        lines.append("")
    lines.append("data: [DONE]")
    lines.append("")
    return "\n".join(lines)


def make_provider(handler, max_retries=3):
    return OpenAICompatProvider(
        base_url="http://test/v1", api_key="k", model="m",
        max_retries=max_retries, backoff_base_seconds=0.0,
        transport=httpx.MockTransport(handler),
    )


def collect(p):
    result = StreamResult()

    async def run():
        return "".join([piece async for piece in p.stream_chat(MSGS, 0.2, result)])

    return asyncio.run(run()), result


def test_streams_pieces_and_reports_usage():
    def handler(request):
        body = sse_body(["Hel", "lo"], usage={"prompt_tokens": 7, "completion_tokens": 2})
        return httpx.Response(200, text=body)

    text, result = collect(make_provider(handler))
    assert text == "Hello"
    assert result.usage.input_tokens == 7 and result.usage.output_tokens == 2
    assert result.usage.estimated is False


def test_estimates_usage_when_provider_sends_none():
    def handler(request):
        return httpx.Response(200, text=sse_body(["Hi"]))

    text, result = collect(make_provider(handler))
    assert text == "Hi"
    assert result.usage.estimated is True


def test_retries_503_then_succeeds():
    calls = []

    def handler(request):
        calls.append(1)
        if len(calls) < 3:
            return httpx.Response(503, text="busy")
        return httpx.Response(200, text=sse_body(["ok"]))

    text, _ = collect(make_provider(handler))
    assert text == "ok"
    assert len(calls) == 3


def test_does_not_retry_on_401():
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(401, json={"error": "bad key"})

    with pytest.raises(LLMError) as info:
        collect(make_provider(handler))
    assert not isinstance(info.value, LLMUnavailable)
    assert len(calls) == 1


def test_gives_up_after_timeouts():
    calls = []

    def handler(request):
        calls.append(1)
        raise httpx.ReadTimeout("slow", request=request)

    with pytest.raises(LLMUnavailable):
        collect(make_provider(handler, max_retries=2))
    assert len(calls) == 3
