"""Minimal Model Context Protocol (MCP) server surface.

Implements the three JSON-RPC methods every MCP client needs to discover and
invoke tools -- `initialize`, `tools/list`, `tools/call` -- over plain HTTP so
the showcase has zero heavyweight SDK dependency and stays hermetic in CI.
The message shapes follow the MCP spec's JSON-RPC 2.0 envelope so a real MCP
client (Claude, an IDE agent, a ServiceNow AI Agent Studio tool connector)
could speak to this server with only a transport shim.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class McpTool(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]


class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: int | str
    method: str
    params: dict[str, Any] = {}


class JsonRpcResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: int | str
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None


ToolHandler = Any  # Callable[[dict], dict] -- kept loose to avoid a mypy generic tangle


class McpServer:
    """A tiny, protocol-correct MCP server: capability negotiation + tool calls."""

    PROTOCOL_VERSION = "2025-06-18"

    def __init__(self, server_name: str) -> None:
        self._server_name = server_name
        self._tools: dict[str, McpTool] = {}
        self._handlers: dict[str, ToolHandler] = {}

    def register_tool(self, tool: McpTool, handler: ToolHandler) -> None:
        self._tools[tool.name] = tool
        self._handlers[tool.name] = handler

    def handle(self, request: JsonRpcRequest) -> JsonRpcResponse:
        try:
            if request.method == "initialize":
                return JsonRpcResponse(
                    id=request.id,
                    result={
                        "protocolVersion": self.PROTOCOL_VERSION,
                        "serverInfo": {"name": self._server_name, "version": "0.1.0"},
                        "capabilities": {"tools": {"listChanged": False}},
                    },
                )
            if request.method == "tools/list":
                return JsonRpcResponse(
                    id=request.id,
                    result={"tools": [t.model_dump() for t in self._tools.values()]},
                )
            if request.method == "tools/call":
                tool_name = request.params.get("name")
                arguments = request.params.get("arguments", {})
                if tool_name not in self._handlers:
                    return JsonRpcResponse(
                        id=request.id,
                        error={"code": -32601, "message": f"Unknown tool: {tool_name}"},
                    )
                output = self._handlers[tool_name](arguments)
                return JsonRpcResponse(
                    id=request.id,
                    result={"content": [{"type": "text", "text": str(output)}], "isError": False},
                )
            return JsonRpcResponse(
                id=request.id,
                error={"code": -32601, "message": f"Unknown method: {request.method}"},
            )
        except Exception as exc:  # defensive: never let a tool crash the transport
            return JsonRpcResponse(id=request.id, error={"code": -32000, "message": str(exc)})


def _get_incident_metrics(_: dict[str, Any]) -> dict[str, Any]:
    return {"open_p1": 3, "open_p2": 11, "mttr_hours": 4.2}


def build_default_mcp_server() -> McpServer:
    server = McpServer(server_name="servicenow-itsm-mcp")
    server.register_tool(
        McpTool(
            name="get_incident_metrics",
            description="Return current open-incident volume and MTTR metrics.",
            input_schema={"type": "object", "properties": {}},
        ),
        _get_incident_metrics,
    )
    return server
