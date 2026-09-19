from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz() -> None:
    assert client.get("/healthz").json()["status"] == "ok"


def test_policy_check_and_audit_summary() -> None:
    payload = {
        "agent_id": "itsm-triage-agent",
        "skill_id": "create_change_request",
        "risk_tier": "write_high_risk",
        "requires_human_approval": True,
        "max_autonomous_risk_tier": "write_high_risk",
    }
    resp = client.post("/policy/check", json=payload)
    assert resp.status_code == 200
    assert resp.json()["decision"] == "require_approval"

    summary = client.get("/audit/summary").json()
    assert summary["total_decisions"] >= 1
    assert summary["require_approval"] >= 1


def test_audit_filter_by_agent() -> None:
    client.post(
        "/policy/check",
        json={"agent_id": "agent-x", "skill_id": "s", "risk_tier": "read_only"},
    )
    resp = client.get("/audit", params={"agent_id": "agent-x"})
    assert resp.status_code == 200
    assert all(r["agent_id"] == "agent-x" for r in resp.json())
