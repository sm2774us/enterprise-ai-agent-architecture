from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz() -> None:
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_list_skills_exposes_risk_tiers() -> None:
    resp = client.get("/skills")
    assert resp.status_code == 200
    tiers = {s["skill_id"]: s["risk_tier"] for s in resp.json()}
    assert tiers["create_change_request"] == "write_high_risk"


def test_run_workflow_unknown_agent_returns_404() -> None:
    resp = client.post(
        "/workflows/run",
        json={"workflow_id": "wf-1", "agent_id": "does-not-exist", "goal": "x"},
    )
    assert resp.status_code == 404


def test_run_workflow_happy_path() -> None:
    resp = client.post(
        "/workflows/run",
        json={
            "workflow_id": "wf-1",
            "agent_id": "readonly-reporting-agent",
            "goal": "summarize",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["final_status"] == "completed"
