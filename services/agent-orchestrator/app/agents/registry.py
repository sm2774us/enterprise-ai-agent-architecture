"""AI Agent Studio-style agent catalogue."""

from __future__ import annotations

from app.models import AgentDefinition, SkillRiskTier


def build_default_agents() -> dict[str, AgentDefinition]:
    agents = [
        AgentDefinition(
            agent_id="itsm-triage-agent",
            name="ITSM Triage Agent",
            persona=(
                "Tier-1 triage specialist. Reads incidents, summarizes risk, "
                "and drafts change requests for human approval."
            ),
            allowed_skill_ids=[
                "lookup_incident",
                "summarize_change_risk",
                "create_change_request",
            ],
            max_autonomous_risk_tier=SkillRiskTier.WRITE_HIGH_RISK,
        ),
        AgentDefinition(
            agent_id="readonly-reporting-agent",
            name="Read-Only Reporting Agent",
            persona="Reports on incidents and changes. Never writes.",
            allowed_skill_ids=["lookup_incident", "summarize_change_risk"],
            max_autonomous_risk_tier=SkillRiskTier.READ_ONLY,
        ),
    ]
    return {agent.agent_id: agent for agent in agents}
