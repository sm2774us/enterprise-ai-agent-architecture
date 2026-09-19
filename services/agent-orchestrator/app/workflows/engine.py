"""Workflow Data Fabric-style execution engine.

Executes a bounded plan of (agent, skill) steps against the Skill Kit
registry, enforcing the agent's declared autonomy ceiling before every
step -- and delegating to an injectable PolicyChecker so the same engine
can run fully offline in unit tests or call the real Control Tower service
over HTTP in an integration/deployed environment.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Protocol

from app.models import (
    AgentDefinition,
    SkillRiskTier,
    WorkflowRunRequest,
    WorkflowRunResult,
    WorkflowStepResult,
    WorkflowStepStatus,
)
from app.skills.registry import SkillRegistry
from app.telemetry.tracer import get_tracer

_RISK_ORDER = {
    SkillRiskTier.READ_ONLY: 0,
    SkillRiskTier.WRITE_LOW_RISK: 1,
    SkillRiskTier.WRITE_HIGH_RISK: 2,
}

tracer = get_tracer("agent-orchestrator")


class PolicyChecker(Protocol):
    def is_allowed(self, agent: AgentDefinition, risk_tier: SkillRiskTier) -> bool: ...


class LocalPolicyChecker:
    """Default, offline Control Tower policy mirror.

    Denies any step whose risk tier exceeds the agent's declared autonomy
    ceiling. This is intentionally the *same rule* the real Control Tower
    service enforces (see services/control-tower/app/governance/policy.py),
    kept in sync by the shared `docs/adr/0002-policy-parity.md` decision
    record, so a workflow behaves identically whether policy is checked
    in-process (fast path) or via the governance service (audited path).
    """

    def is_allowed(self, agent: AgentDefinition, risk_tier: SkillRiskTier) -> bool:
        return _RISK_ORDER[risk_tier] <= _RISK_ORDER[agent.max_autonomous_risk_tier]


def _default_plan(goal: str) -> list[str]:
    """A tiny deterministic planner stand-in for a real LLM planning call.

    Kept rule-based (not an LLM call) so unit tests are hermetic; the plug
    point for a genuine LLM-generated plan is `app.providers` in the
    llm-gateway service, which this engine can call over HTTP in production.
    """

    if "change" in goal.lower():
        return ["lookup_incident", "summarize_change_risk", "create_change_request"]
    return ["lookup_incident", "summarize_change_risk"]


class WorkflowEngine:
    def __init__(
        self,
        skill_registry: SkillRegistry,
        agents: dict[str, AgentDefinition],
        policy_checker: PolicyChecker | None = None,
        planner: Callable[[str], list[str]] | None = None,
    ) -> None:
        self._skills = skill_registry
        self._agents = agents
        self._policy = policy_checker or LocalPolicyChecker()
        self._planner = planner or _default_plan

    def run(self, request: WorkflowRunRequest) -> WorkflowRunResult:
        with tracer.start_as_current_span("workflow.run") as span:
            span.set_attribute("workflow.id", request.workflow_id)
            span.set_attribute("agent.id", request.agent_id)

            agent = self._agents[request.agent_id]
            plan = self._planner(request.goal)
            steps: list[WorkflowStepResult] = []
            run_id = str(uuid.uuid4())

            for skill_id in plan:
                step_id = str(uuid.uuid4())
                with tracer.start_as_current_span("workflow.step") as step_span:
                    step_span.set_attribute("skill.id", skill_id)

                    if skill_id not in agent.allowed_skill_ids:
                        steps.append(
                            WorkflowStepResult(
                                step_id=step_id,
                                agent_id=agent.agent_id,
                                skill_id=skill_id,
                                status=WorkflowStepStatus.BLOCKED_BY_POLICY,
                                reason="Skill not in agent's allow-list.",
                            )
                        )
                        break

                    definition = self._skills.get_definition(skill_id)

                    if not self._policy.is_allowed(agent, definition.risk_tier):
                        steps.append(
                            WorkflowStepResult(
                                step_id=step_id,
                                agent_id=agent.agent_id,
                                skill_id=skill_id,
                                status=WorkflowStepStatus.BLOCKED_BY_POLICY,
                                reason=(
                                    f"Skill risk tier {definition.risk_tier.value} exceeds "
                                    f"agent ceiling {agent.max_autonomous_risk_tier.value}."
                                ),
                            )
                        )
                        break

                    if definition.requires_human_approval:
                        steps.append(
                            WorkflowStepResult(
                                step_id=step_id,
                                agent_id=agent.agent_id,
                                skill_id=skill_id,
                                status=WorkflowStepStatus.AWAITING_APPROVAL,
                                reason="Skill requires mandatory human-in-the-loop approval.",
                            )
                        )
                        break

                    output = self._skills.invoke(skill_id, request.context)
                    steps.append(
                        WorkflowStepResult(
                            step_id=step_id,
                            agent_id=agent.agent_id,
                            skill_id=skill_id,
                            status=WorkflowStepStatus.COMPLETED,
                            output=output,
                            trace_id=format(step_span.get_span_context().trace_id, "032x"),
                        )
                    )

            final_status = steps[-1].status if steps else WorkflowStepStatus.FAILED
            return WorkflowRunResult(
                workflow_id=request.workflow_id,
                run_id=run_id,
                steps=steps,
                final_status=final_status,
            )
