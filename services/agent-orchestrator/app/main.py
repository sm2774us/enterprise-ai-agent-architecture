from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.agents.registry import build_default_agents
from app.models import SkillDefinition, WorkflowRunRequest, WorkflowRunResult
from app.skills.registry import build_default_registry
from app.workflows.engine import WorkflowEngine

app = FastAPI(
    title="Agent Orchestrator",
    description=(
        "AI Agent Studio / Workflow Data Fabric-style orchestration engine — "
        "ServiceNow Staff AI Engineer showcase."
    ),
    version="0.1.0",
)

_registry = build_default_registry()
_agents = build_default_agents()
_engine = WorkflowEngine(_registry, _agents)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "service": "agent-orchestrator"}


@app.get("/skills", response_model=list[SkillDefinition])
def list_skills() -> list[SkillDefinition]:
    return _registry.list_skills()


@app.get("/agents")
def list_agents() -> list[dict]:
    return [a.model_dump() for a in _agents.values()]


@app.post("/workflows/run", response_model=WorkflowRunResult)
def run_workflow(request: WorkflowRunRequest) -> WorkflowRunResult:
    if request.agent_id not in _agents:
        raise HTTPException(status_code=404, detail=f"Unknown agent_id: {request.agent_id}")
    return _engine.run(request)
