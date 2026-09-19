from __future__ import annotations

from fastapi import FastAPI

from app.a2a.protocol import A2ATask, A2ATaskRequest, AgentCard, build_default_a2a_agent
from app.mcp.server import JsonRpcRequest, JsonRpcResponse, build_default_mcp_server

app = FastAPI(
    title="MCP / A2A Gateway",
    description=(
        "Model Context Protocol tool-server + Agent2Agent interop endpoints — "
        "ServiceNow Staff AI Engineer showcase."
    ),
    version="0.1.0",
)

_mcp = build_default_mcp_server()
_a2a = build_default_a2a_agent()


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "service": "mcp-a2a-gateway"}


@app.post("/mcp", response_model=JsonRpcResponse)
def mcp_rpc(request: JsonRpcRequest) -> JsonRpcResponse:
    return _mcp.handle(request)


@app.get("/.well-known/agent.json", response_model=AgentCard)
def agent_card() -> AgentCard:
    return _a2a.card


@app.post("/a2a/tasks", response_model=A2ATask)
def submit_a2a_task(request: A2ATaskRequest) -> A2ATask:
    return _a2a.submit_task(request)


@app.get("/a2a/tasks/{task_id}", response_model=A2ATask | None)
def get_a2a_task(task_id: str) -> A2ATask | None:
    return _a2a.get_task(task_id)
