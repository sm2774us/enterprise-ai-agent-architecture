from __future__ import annotations

from app.mcp.server import JsonRpcRequest, build_default_mcp_server


def test_initialize_returns_protocol_version() -> None:
    server = build_default_mcp_server()
    resp = server.handle(JsonRpcRequest(id=1, method="initialize"))
    assert resp.error is None
    assert resp.result is not None
    assert "protocolVersion" in resp.result


def test_tools_list_includes_registered_tool() -> None:
    server = build_default_mcp_server()
    resp = server.handle(JsonRpcRequest(id=2, method="tools/list"))
    names = [t["name"] for t in resp.result["tools"]]
    assert "get_incident_metrics" in names


def test_tools_call_invokes_handler() -> None:
    server = build_default_mcp_server()
    resp = server.handle(
        JsonRpcRequest(
            id=3, method="tools/call", params={"name": "get_incident_metrics", "arguments": {}}
        )
    )
    assert resp.error is None
    assert resp.result["isError"] is False


def test_tools_call_unknown_tool_returns_json_rpc_error() -> None:
    server = build_default_mcp_server()
    resp = server.handle(JsonRpcRequest(id=4, method="tools/call", params={"name": "not_a_tool"}))
    assert resp.error is not None
    assert resp.error["code"] == -32601


def test_unknown_method_returns_error() -> None:
    server = build_default_mcp_server()
    resp = server.handle(JsonRpcRequest(id=5, method="not/a_method"))
    assert resp.error is not None
