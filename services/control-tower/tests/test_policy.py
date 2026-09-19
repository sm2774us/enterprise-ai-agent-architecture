from __future__ import annotations

from app.governance.policy import GovernanceEngine, PolicyCheckRequest, PolicyDecision


def test_allows_within_ceiling() -> None:
    engine = GovernanceEngine()
    resp = engine.evaluate(
        PolicyCheckRequest(
            agent_id="a1",
            skill_id="lookup_incident",
            risk_tier="read_only",
            max_autonomous_risk_tier="write_low_risk",
        )
    )
    assert resp.decision == PolicyDecision.ALLOW


def test_denies_above_ceiling() -> None:
    engine = GovernanceEngine()
    resp = engine.evaluate(
        PolicyCheckRequest(
            agent_id="a1",
            skill_id="delete_record",
            risk_tier="write_high_risk",
            max_autonomous_risk_tier="read_only",
        )
    )
    assert resp.decision == PolicyDecision.DENY


def test_requires_approval_flag_overrides_ceiling() -> None:
    engine = GovernanceEngine()
    resp = engine.evaluate(
        PolicyCheckRequest(
            agent_id="a1",
            skill_id="create_change_request",
            risk_tier="write_high_risk",
            requires_human_approval=True,
            max_autonomous_risk_tier="write_high_risk",
        )
    )
    assert resp.decision == PolicyDecision.REQUIRE_APPROVAL


def test_unknown_risk_tier_is_denied() -> None:
    engine = GovernanceEngine()
    resp = engine.evaluate(
        PolicyCheckRequest(agent_id="a1", skill_id="x", risk_tier="not_a_real_tier")
    )
    assert resp.decision == PolicyDecision.DENY


def test_audit_trail_accumulates_and_filters_by_agent() -> None:
    engine = GovernanceEngine()
    engine.evaluate(PolicyCheckRequest(agent_id="a1", skill_id="s1", risk_tier="read_only"))
    engine.evaluate(PolicyCheckRequest(agent_id="a2", skill_id="s2", risk_tier="read_only"))
    assert len(engine.audit_trail()) == 2
    assert len(engine.audit_trail(agent_id="a1")) == 1
    assert engine.audit_trail(agent_id="a1")[0].agent_id == "a1"


def test_audit_records_have_monotonic_ids() -> None:
    engine = GovernanceEngine()
    for _ in range(3):
        engine.evaluate(PolicyCheckRequest(agent_id="a1", skill_id="s1", risk_tier="read_only"))
    ids = [r.record_id for r in engine.audit_trail()]
    assert ids == sorted(ids)
