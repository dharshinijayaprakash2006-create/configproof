def test_chat_streams_and_logs_cost(client):
    r = client.post("/chat", json={"messages": [{"role": "user", "content": "hello"}]})
    assert r.status_code == 200
    assert "text/event-stream" in r.headers["content-type"]
    assert 'data: {"delta": "You "}' in r.text
    assert "event: done" in r.text
    usage = client.get("/usage").json()
    assert sum(day["calls"] for day in usage.values()) == 1


def test_chat_rejects_bad_input(client):
    r = client.post("/chat", json={"messages": [{"role": "hacker", "content": "hi"}]})
    assert r.status_code == 422
