# ADR 0001: Four independently deployable services, not one monolith

## Status
Accepted

## Context
The JD asks for a Staff AI Engineer who can architect agents/workflows
(AI Agent Studio), own governance (AI Control Tower), integrate LLM
capabilities, and support governed multi-agent interoperability (MCP/A2A).
Those are four different concerns with different scaling, security, and
release-cadence needs in a real ServiceNow deployment.

## Decision
Split into four services:
- `agent-orchestrator` — executes agent/skill/workflow plans.
- `control-tower` — the single source of truth for governance policy and
  the audit trail.
- `mcp-a2a-gateway` — protocol-facing edge for external tools/agents.
- `llm-gateway` — the only service that talks to an LLM provider or holds
  embeddings, so a provider swap or a security review touches one service.

## Consequences
- `agent-orchestrator` calls `control-tower` for policy in a real
  deployment, but ships a `LocalPolicyChecker` fallback so it runs fully
  offline in unit tests and in this demo — see ADR 0002.
- Four Dockerfiles / CI matrix legs instead of one, which is the honest
  cost of the separation and is worth it for independent scaling and
  blast-radius containment.
