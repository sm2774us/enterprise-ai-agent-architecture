"""AI Control Tower governance policy engine.

Centralizes the same allow/deny logic every agent-runtime should enforce
(see the LocalPolicyChecker mirror in services/agent-orchestrator), but as
an independently deployable, independently auditable service — the actual
posture ServiceNow's AI Control Tower is built to provide: one governed
control plane that many agent runtimes call into, rather than policy logic
copy-pasted and drifting across teams.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field

_RISK_ORDER = {"read_only": 0, "write_low_risk": 1, "write_high_risk": 2}


class PolicyDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


class PolicyCheckRequest(BaseModel):
    agent_id: str
    skill_id: str
    risk_tier: str
    requires_human_approval: bool = False
    max_autonomous_risk_tier: str = "write_low_risk"


class AuditRecord(BaseModel):
    record_id: str
    timestamp: str
    agent_id: str
    skill_id: str
    decision: PolicyDecision
    reason: str


class PolicyCheckResponse(BaseModel):
    decision: PolicyDecision
    reason: str
    audit: AuditRecord


class GovernanceEngine:
    """Evaluates a skill invocation against declared agent policy.

    Also appends an immutable, in-memory audit trail entry per decision —
    a stand-in for a durable, queryable audit log an examiner or platform
    owner could pull for any agent's history.
    """

    def __init__(self) -> None:
        self._audit_log: list[AuditRecord] = []
        self._sequence = 0

    def evaluate(self, request: PolicyCheckRequest) -> PolicyCheckResponse:
        self._sequence += 1
        record_id = f"audit-{self._sequence:06d}"
        timestamp = datetime.now(UTC).isoformat()

        if request.risk_tier not in _RISK_ORDER:
            decision, reason = PolicyDecision.DENY, f"Unknown risk tier '{request.risk_tier}'."
        elif request.requires_human_approval:
            decision, reason = (
                PolicyDecision.REQUIRE_APPROVAL,
                "Skill is configured for mandatory human-in-the-loop approval.",
            )
        elif _RISK_ORDER[request.risk_tier] > _RISK_ORDER[request.max_autonomous_risk_tier]:
            decision, reason = (
                PolicyDecision.DENY,
                (
                    f"Risk tier '{request.risk_tier}' exceeds agent's autonomous "
                    f"ceiling '{request.max_autonomous_risk_tier}'."
                ),
            )
        else:
            decision, reason = PolicyDecision.ALLOW, "Within agent's autonomous risk ceiling."

        audit = AuditRecord(
            record_id=record_id,
            timestamp=timestamp,
            agent_id=request.agent_id,
            skill_id=request.skill_id,
            decision=decision,
            reason=reason,
        )
        self._audit_log.append(audit)
        return PolicyCheckResponse(decision=decision, reason=reason, audit=audit)

    def audit_trail(self, agent_id: str | None = None) -> list[AuditRecord]:
        if agent_id is None:
            return list(self._audit_log)
        return [a for a in self._audit_log if a.agent_id == agent_id]


class GovernancePolicySummary(BaseModel):
    total_decisions: int
    allow: int
    deny: int
    require_approval: int
    deny_rate: float = Field(description="Fraction of decisions that were DENY, 0..1")
