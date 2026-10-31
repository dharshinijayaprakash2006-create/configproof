import json

import pytest

from app.cost import cost_usd, log_call
from app.schemas import Usage


def test_cost_formula():
    usage = Usage(input_tokens=1200, output_tokens=300)
    assert cost_usd(usage, 0.5, 1.5) == pytest.approx(0.00105)


def test_log_call_writes_one_json_line(tmp_path):
    path = tmp_path / "cost.jsonl"
    log_call(str(path), provider="fake", model="m",
             usage=Usage(input_tokens=1000, output_tokens=500), latency_ms=12.34,
             price_in_per_m=0.5, price_out_per_m=1.5, ok=True)
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["cost_usd"] == pytest.approx(0.00125)
    assert data["fallback_used"] is False
