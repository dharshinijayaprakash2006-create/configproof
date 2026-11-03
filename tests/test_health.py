def test_health_is_fast_and_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "app": "examate-rag", "environment": "test"}


def test_ready_without_database(client):
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json()["database"] == "not configured"


def test_usage_returns_json(client):
    r = client.get("/usage")
    assert r.status_code == 200
    assert isinstance(r.json(), dict)


def test_health_has_expected_keys(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert "app" in body
    assert "environment" in body


def test_ready_returns_status_field(client):
    body = client.get("/ready").json()
    assert body["status"] == "ready"
    assert "database" in body
