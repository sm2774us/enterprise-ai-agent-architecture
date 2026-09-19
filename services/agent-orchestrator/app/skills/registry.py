"""Skill Kit registry: a governed catalogue of callable agent capabilities.

Each skill declares its own risk tier up front, which is what lets the
Control Tower (see services/control-tower) enforce policy *before* a skill
executes rather than after — the same "govern by design" posture ServiceNow's
AI Control Tower promotes.
"""

from __future__ import annotations

from collections.abc import Callable

from app.models import SkillDefinition, SkillRiskTier

SkillHandler = Callable[[dict], dict]


class SkillRegistry:
    """In-memory Skill Kit catalogue with pluggable handlers."""

    def __init__(self) -> None:
        self._definitions: dict[str, SkillDefinition] = {}
        self._handlers: dict[str, SkillHandler] = {}

    def register(self, definition: SkillDefinition, handler: SkillHandler) -> None:
        self._definitions[definition.skill_id] = definition
        self._handlers[definition.skill_id] = handler

    def get_definition(self, skill_id: str) -> SkillDefinition:
        if skill_id not in self._definitions:
            raise KeyError(f"Unknown skill_id: {skill_id}")
        return self._definitions[skill_id]

    def invoke(self, skill_id: str, payload: dict) -> dict:
        handler = self._handlers[skill_id]
        return handler(payload)

    def list_skills(self) -> list[SkillDefinition]:
        return list(self._definitions.values())


def _lookup_incident_handler(payload: dict) -> dict:
    return {
        "incident_id": payload.get("incident_id", "INC0010042"),
        "short_description": "P1 - Payment gateway latency spike",
        "priority": "1",
        "assignment_group": "Platform-Reliability",
    }


def _summarize_change_risk_handler(payload: dict) -> dict:
    change_size = payload.get("lines_changed", 0)
    risk = "high" if change_size > 500 else "moderate" if change_size > 100 else "low"
    return {"change_id": payload.get("change_id", "CHG0004821"), "predicted_risk": risk}


def _create_change_request_handler(payload: dict) -> dict:
    # A write, high-risk action -- deliberately requires human approval;
    # see SkillRegistry definitions below and the Control Tower gate.
    return {
        "change_id": "CHG0004907",
        "state": "new",
        "requested_by": payload.get("requested_by", "agent:staff-ai-engineer-copilot"),
    }


def build_default_registry() -> SkillRegistry:
    """Wire up the demo Skill Kit used by the showcase workflows."""

    registry = SkillRegistry()
    registry.register(
        SkillDefinition(
            skill_id="lookup_incident",
            name="Lookup Incident",
            description="Read-only lookup of an incident record by sys_id/number.",
            risk_tier=SkillRiskTier.READ_ONLY,
            input_schema={"incident_id": "string"},
        ),
        _lookup_incident_handler,
    )
    registry.register(
        SkillDefinition(
            skill_id="summarize_change_risk",
            name="Summarize Change Risk",
            description="LLM-assisted risk scoring for a proposed change record (no write).",
            risk_tier=SkillRiskTier.READ_ONLY,
            input_schema={"change_id": "string", "lines_changed": "integer"},
        ),
        _summarize_change_risk_handler,
    )
    registry.register(
        SkillDefinition(
            skill_id="create_change_request",
            name="Create Change Request",
            description="Writes a new Change Request record. High-risk, human-gated.",
            risk_tier=SkillRiskTier.WRITE_HIGH_RISK,
            input_schema={"requested_by": "string"},
            requires_human_approval=True,
        ),
        _create_change_request_handler,
    )
    return registry
