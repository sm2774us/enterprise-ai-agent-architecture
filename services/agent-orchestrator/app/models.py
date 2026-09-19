"""Domain models for the AI Agent Studio-style orchestration engine.

Mirrors the core objects a ServiceNow "AI Agent Studio" definition graph is
built from: a Skill (a governed, callable capability — the "Skill Kit"), an
Agent (a role + a bounded set of skills + an LLM policy), and a Workflow
(an explicit, auditable plan that chains agents/skills with a state machine,
analogous to Workflow Data Fabric orchestration records).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class SkillRiskTier(str, Enum):
    """Governance tier used by the Control Tower to gate execution."""

    READ_ONLY = "read_only"
    WRITE_LOW_RISK = "write_low_risk"
    WRITE_HIGH_RISK = "write_high_risk"


class SkillDefinition(BaseModel):
    """A single Skill Kit capability an agent may invoke."""

    skill_id: str
    name: str
    description: str
    risk_tier: SkillRiskTier
    input_schema: dict = Field(default_factory=dict)
    requires_human_approval: bool = False


class AgentDefinition(BaseModel):
    """An AI Agent Studio agent: a role bound to a skill allow-list and policy."""

    agent_id: str
    name: str
    persona: str
    allowed_skill_ids: list[str] = Field(default_factory=list)
    model_id: str = "enterprise-llm-default"
    max_autonomous_risk_tier: SkillRiskTier = SkillRiskTier.WRITE_LOW_RISK


class WorkflowStepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED_BY_POLICY = "blocked_by_policy"


class WorkflowStepResult(BaseModel):
    step_id: str
    agent_id: str
    skill_id: str
    status: WorkflowStepStatus
    output: dict = Field(default_factory=dict)
    trace_id: str | None = None
    reason: str | None = None


class WorkflowRunRequest(BaseModel):
    workflow_id: str
    agent_id: str
    goal: str
    context: dict = Field(default_factory=dict)


class WorkflowRunResult(BaseModel):
    workflow_id: str
    run_id: str
    steps: list[WorkflowStepResult]
    final_status: WorkflowStepStatus
