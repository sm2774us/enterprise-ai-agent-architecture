from __future__ import annotations

from fastapi import FastAPI

from app.governance.policy import (
    AuditRecord,
    GovernanceEngine,
    GovernancePolicySummary,
    PolicyCheckRequest,
    PolicyCheckResponse,
    PolicyDecision,
)
from app.observability.metrics import record_decision

app = FastAPI(
    title="AI Control Tower",
    description=(
        "Governance policy engine, audit trail, and observability endpoints — "
        "ServiceNow Staff AI Engineer showcase."
    ),
    version="0.1.0",
)

_engine = GovernanceEngine()


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "service": "control-tower"}


@app.post("/policy/check", response_model=PolicyCheckResponse)
def check_policy(request: PolicyCheckRequest) -> PolicyCheckResponse:
    response = _engine.evaluate(request)
    record_decision(response.decision.value, request.agent_id)
    return response


@app.get("/audit", response_model=list[AuditRecord])
def audit_trail(agent_id: str | None = None) -> list[AuditRecord]:
    return _engine.audit_trail(agent_id)


@app.get("/audit/summary", response_model=GovernancePolicySummary)
def audit_summary() -> GovernancePolicySummary:
    records = _engine.audit_trail()
    total = len(records)
    allow = sum(1 for r in records if r.decision == PolicyDecision.ALLOW)
    deny = sum(1 for r in records if r.decision == PolicyDecision.DENY)
    require_approval = sum(1 for r in records if r.decision == PolicyDecision.REQUIRE_APPROVAL)
    return GovernancePolicySummary(
        total_decisions=total,
        allow=allow,
        deny=deny,
        require_approval=require_approval,
        deny_rate=(deny / total) if total else 0.0,
    )
