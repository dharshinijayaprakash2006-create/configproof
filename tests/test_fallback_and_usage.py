"""Added for Session 5: fallback model and GET /usage."""

import asyncio
import json

import httpx
import pytest

from app.llm.base import LLMError, StreamResult
from app.llm.fake import FakeProvider
from app.llm.fallback import FallbackProvider
from app.llm.openai_compat import OpenAICompatProvider
from app.schemas import Message

MSGS = [Message(role="user", content="hello")]


def slow_main(handler):
    return OpenAICompatProvider(
        base_url="http://test/v1",
        api_key="k",
        model="main-model",
        max_retries=1,
        backoff_base_seconds=0.0,
        transport=httpx.MockTransport(handler),
    )


def collect(p):
    result = StreamResult()

    async def run():
        return "".join([piece async for piece in p.stream_chat(MSGS, 0.2, result)])

    return asyncio.run(run()), result


def test_fallback_answers_when_main_times_out():
    def handler(request):
        raise httpx.ReadTimeout("slow", request=request)

    text, result = collect(FallbackProvider(slow_main(handler), FakeProvider(model="backup-model")))
    assert text.startswith("You asked: hello")
    assert result.fallback_used is True and result.model == "backup-model"


def test_no_fallback_on_bad_key():
    def handler(request):
        return httpx.Response(401, json={"error": "bad key"})

    with pytest.raises(LLMError):
        collect(FallbackProvider(slow_main(handler), FakeProvider(model="backup-model")))


def test_main_answers_without_fallback():
    text, result = collect(FallbackProvider(FakeProvider(model="main-model"), FakeProvider(model="backup")))
    assert result.fallback_used is False and result.model == "main-model"


def test_usage_totals_per_day(client, tmp_path):
    log = [
        {"ts": 1792800000.0, "input_tokens": 1200, "output_tokens": 300, "cost_usd": 0.00105},  # 2026-10-24
        {"ts": 1792810000.0, "input_tokens": 800, "output_tokens": 200, "cost_usd": 0.0007},  # 2026-10-24
        {"ts": 1792900000.0, "input_tokens": 100, "output_tokens": 50, "cost_usd": 0.000125},  # 2026-10-25
    ]
    path = client.settings.cost_log_path
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(json.dumps(r) for r in log) + "\n{half-written line\n")
    r = client.get("/usage")
    assert r.status_code == 200
    assert r.json() == {
        "2026-10-24": {"calls": 2, "input_tokens": 2000, "output_tokens": 500, "cost_usd": 0.00175},
        "2026-10-25": {"calls": 1, "input_tokens": 100, "output_tokens": 50, "cost_usd": 0.000125},
    }
