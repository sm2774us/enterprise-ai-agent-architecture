# ADR 0002: Policy logic must be identical in-process and in the Control Tower

## Status
Accepted

## Context
`agent-orchestrator.LocalPolicyChecker` and
`control-tower.governance.policy.GovernanceEngine` both implement
"deny anything above the agent's declared risk ceiling, unless it requires
mandatory human approval." Two implementations of the same rule is a classic
drift risk: a change to one without the other silently reopens a governance
gap.

## Decision
Both implementations are kept intentionally tiny (one risk-order comparison
+ one boolean flag check) and are unit-tested against the same table of
cases. Any change to the policy semantics must update both call sites and
both test suites in the same PR — enforced today by code review /
CODEOWNERS, not by tooling, since a shared library would reintroduce a
network dependency the orchestrator's offline-first design is meant to
avoid.

## Consequences
- A future iteration could extract a shared `policy-core` package published
  to an internal registry; deferred here to keep the demo's dependency
  graph simple.
- Until then, `agent-orchestrator`'s fast path (in-process) and its audited
  path (calling `control-tower` over HTTP) behave identically by
  construction, not by coincidence.
