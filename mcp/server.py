"""BRAIN 3.0 MCP Server.

Exposes every BRAIN 3.0 API endpoint as an MCP tool that Claude can call.
Runs via stdio transport as a subprocess of the Claude client.
"""

from mcp.server.fastmcp import FastMCP

from client import BrainAPIClient
from tools import register_all

mcp = FastMCP("BRAIN 3.0")
api = BrainAPIClient()

register_all(mcp, api)

# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------


@mcp.tool()
async def health_check() -> dict:
    """Check BRAIN 3.0 API connectivity.

    Use this first to verify the API is running and the database is connected.
    Returns status and database connection state.
    """
    return await api.get("/health")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
