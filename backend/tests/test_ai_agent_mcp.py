"""TDD RED Phase: Tests for Tool-Calling Growth Agent and MCP Server."""


def test_agent_chat_requires_auth(client):
    r = client.post("/api/v1/ai/agent-chat", json={"message": "What is my sponsorship rate?"})
    assert r.status_code == 401


def test_agent_chat_invokes_real_tools(client, h):
    # Ensure creator has posts + revenue in DB
    client.get("/api/v1/analytics/posts", headers=h["creator"])
    client.get("/api/v1/revenue", headers=h["creator"])
    client.post("/api/v1/ai/index", headers=h["creator"])

    r = client.post(
        "/api/v1/ai/agent-chat",
        json={"message": "Give me my channel KPIs, revenue summary, and recommended sponsorship rate"},
        headers=h["creator"],
    )
    assert r.status_code == 200
    body = r.json()
    assert "reply" in body and len(body["reply"]) > 0
    assert isinstance(body["tools_used"], list)
    assert "get_channel_kpis" in body["tools_used"]
    assert "get_revenue_summary" in body["tools_used"]
    assert "calculate_sponsorship_rate" in body["tools_used"]


def test_agent_chat_validation_rejects_empty_message(client, h):
    r = client.post("/api/v1/ai/agent-chat", json={"message": "   "}, headers=h["creator"])
    assert r.status_code == 422


def test_mcp_server_exposes_creatoriq_tools():
    from app.ai.mcp.server import mcp

    assert mcp is not None
    # FastMCP registers tools internally; verify all 4 tools are registered
    tool_names = set(mcp._tool_manager._tools.keys())
    expected = {
        "get_channel_kpis",
        "get_revenue_summary",
        "search_creator_content_rag",
        "calculate_sponsorship_rate",
    }
    assert expected.issubset(tool_names)
