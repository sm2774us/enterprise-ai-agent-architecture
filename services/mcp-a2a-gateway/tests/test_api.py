from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz() -> None:
    assert client.get("/healthz").json()["status"] == "ok"


def test_agent_card_endpoint() -> None:
    resp = client.get("/.well-known/agent.json")
    assert resp.status_code == 200
    assert resp.json()["name"] == "itsm-triage-agent-remote"


def test_mcp_endpoint_tools_list() -> None:
    resp = client.post("/mcp", json={"id": 1, "method": "tools/list"})
    assert resp.status_code == 200
    assert resp.json()["result"]["tools"]


def test_a2a_task_roundtrip() -> None:
    submit = client.post("/a2a/tasks", json={"skill_id": "lookup_incident", "message": "status?"})
    assert submit.status_code == 200
    task_id = submit.json()["task_id"]
    fetched = client.get(f"/a2a/tasks/{task_id}")
    assert fetched.status_code == 200
    assert fetched.json()["task_id"] == task_id
