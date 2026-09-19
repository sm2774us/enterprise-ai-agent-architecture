from __future__ import annotations

from app.agents.registry import build_default_agents
from app.models import WorkflowRunRequest, WorkflowStepStatus
from app.skills.registry import build_default_registry
from app.workflows.engine import WorkflowEngine


def _engine() -> WorkflowEngine:
    return WorkflowEngine(build_default_registry(), build_default_agents())


def test_low_risk_agent_completes_read_only_plan() -> None:
    engine = _engine()
    result = engine.run(
        WorkflowRunRequest(
            workflow_id="wf-report",
            agent_id="readonly-reporting-agent",
            goal="summarize incident volume",
        )
    )
    assert result.final_status == WorkflowStepStatus.COMPLETED
    assert [s.skill_id for s in result.steps] == ["lookup_incident", "summarize_change_risk"]
    assert all(s.status == WorkflowStepStatus.COMPLETED for s in result.steps)


def test_high_risk_skill_requires_human_approval() -> None:
    engine = _engine()
    result = engine.run(
        WorkflowRunRequest(
            workflow_id="wf-change",
            agent_id="itsm-triage-agent",
            goal="draft a change request",
        )
    )
    assert result.final_status == WorkflowStepStatus.AWAITING_APPROVAL
    assert result.steps[-1].skill_id == "create_change_request"


def test_readonly_agent_is_blocked_from_write_skill() -> None:
    engine = _engine()
    result = engine.run(
        WorkflowRunRequest(
            workflow_id="wf-change",
            agent_id="readonly-reporting-agent",
            goal="draft a change request",
        )
    )
    # The planner includes create_change_request for a "change" goal, but
    # readonly-reporting-agent's allow-list never includes it, so the run
    # halts at that step rather than silently skipping or auto-executing it.
    assert result.final_status == WorkflowStepStatus.BLOCKED_BY_POLICY
    assert result.steps[-1].skill_id == "create_change_request"


def test_unknown_skill_is_blocked_by_allowlist() -> None:
    engine = _engine()
    agent = build_default_agents()["readonly-reporting-agent"]
    result = engine.run(
        WorkflowRunRequest(workflow_id="wf-x", agent_id=agent.agent_id, goal="noop")
    )
    assert all(s.skill_id in agent.allowed_skill_ids for s in result.steps)


def test_every_completed_step_carries_a_trace_id() -> None:
    engine = _engine()
    result = engine.run(
        WorkflowRunRequest(
            workflow_id="wf-report",
            agent_id="readonly-reporting-agent",
            goal="report",
        )
    )
    for step in result.steps:
        if step.status == WorkflowStepStatus.COMPLETED:
            assert step.trace_id is not None
            assert len(step.trace_id) == 32
