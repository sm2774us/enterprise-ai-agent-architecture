from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz() -> None:
    assert client.get("/healthz").json()["status"] == "ok"


def test_complete_endpoint() -> None:
    resp = client.post("/complete", json={"prompt": "hello"})
    assert resp.status_code == 200
    assert resp.json()["text"]


def test_ingest_and_search_roundtrip() -> None:
    client.post(
        "/vector/ingest",
        json={"doc_id": "kb-1", "text": "Reset your VPN client cache", "metadata": {"kb": "1"}},
    )
    resp = client.post("/vector/search", json={"query": "Reset your VPN client cache", "top_k": 1})
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert results
    assert results[0]["doc_id"] == "kb-1"
