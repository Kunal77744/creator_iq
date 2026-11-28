"""Model Context Protocol (MCP) server exposing CreatorIQ agent tools over stdio/MCP."""

from mcp.server.fastmcp import FastMCP

from ...database import SessionLocal
from ..agents import tools as agent_tools

mcp = FastMCP("CreatorIQ")


@mcp.tool()
def get_channel_kpis(user_id: int) -> dict:
    """Get live channel KPIs (followers, total views, posts, avg engagement) for a creator user_id."""
    with SessionLocal() as db:
        return agent_tools.get_channel_kpis(db, user_id)


@mcp.tool()
def get_revenue_summary(user_id: int) -> dict:
    """Get revenue & sponsorship payout summary (total, paid, pending) for a creator user_id."""
    with SessionLocal() as db:
        return agent_tools.get_revenue_summary(db, user_id)


@mcp.tool()
def search_creator_content_rag(user_id: int, query: str) -> list[dict]:
    """Search a creator's indexed content using pgvector cosine similarity."""
    with SessionLocal() as db:
        return agent_tools.search_creator_content_rag(db, user_id, query)


@mcp.tool()
def calculate_sponsorship_rate(user_id: int) -> dict:
    """Calculate recommended sponsorship deal pricing in INR from live channel metrics."""
    with SessionLocal() as db:
        return agent_tools.calculate_sponsorship_rate(db, user_id)


if __name__ == "__main__":
    mcp.run()
