"""Cost logging: one JSON line per LLM call."""
import json
import time
from pathlib import Path

from app.schemas import Usage


def cost_usd(usage: Usage, price_in_per_m: float, price_out_per_m: float) -> float:
    return (usage.input_tokens * price_in_per_m + usage.output_tokens * price_out_per_m) / 1_000_000


def log_call(path: str, *, provider: str, model: str, usage: Usage, latency_ms: float,
             price_in_per_m: float, price_out_per_m: float, ok: bool,
             fallback_used: bool = False) -> dict:
    record = {
        "ts": round(time.time(), 3),
        "provider": provider,
        "model": model,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "usage_estimated": usage.estimated,
        "latency_ms": round(latency_ms, 1),
        "cost_usd": round(cost_usd(usage, price_in_per_m, price_out_per_m), 8),
        "ok": ok,
        "fallback_used": fallback_used,  # added for Session 5
    }
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return record
