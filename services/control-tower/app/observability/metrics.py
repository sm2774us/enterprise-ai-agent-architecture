"""OpenTelemetry metrics for AI Control Tower monitoring/dashboards.

Emits counters an "AI Control Tower" adoption/health dashboard would surface:
decisions by outcome, and per-agent invocation counts — the metrics backbone
behind ServiceNow's real Control Tower usage and governance dashboards.
"""

from __future__ import annotations

from opentelemetry import metrics

_meter = metrics.get_meter("control-tower")

decision_counter = _meter.create_counter(
    name="control_tower.policy_decisions",
    description="Count of policy decisions issued, by outcome.",
    unit="1",
)

agent_invocation_counter = _meter.create_counter(
    name="control_tower.agent_invocations",
    description="Count of skill invocations evaluated, by agent.",
    unit="1",
)


def record_decision(decision: str, agent_id: str) -> None:
    decision_counter.add(1, attributes={"decision": decision})
    agent_invocation_counter.add(1, attributes={"agent_id": agent_id})
