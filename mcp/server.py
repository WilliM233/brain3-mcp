"""BRAIN 3.0 MCP Server.

Exposes every BRAIN 3.0 API endpoint as an MCP tool that Claude can call.
Supports two transport modes:
- stdio (default): runs as a subprocess of the Claude client
- streamable HTTP: runs as a network-accessible server
"""

import os
import sys

from mcp.server.fastmcp import FastMCP

from client import BrainAPIClient
from tools import register_all

transport = os.environ.get("MCP_TRANSPORT", "stdio")
host = os.environ.get("MCP_HOST", "0.0.0.0")
port = int(os.environ.get("MCP_PORT", "8001"))

mcp = FastMCP("BRAIN 3.0", host=host, port=port)
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
    if transport == "http":
        token = os.environ.get("MCP_AUTH_TOKEN")
        if not token:
            print(
                "ERROR: MCP_AUTH_TOKEN must be set when running in HTTP transport mode",
                file=sys.stderr,
            )
            sys.exit(1)

        import uvicorn

        from auth import BearerAuthMiddleware

        app = mcp.streamable_http_app()
        app.add_middleware(BearerAuthMiddleware, token=token)

        print(
            f"Starting BRAIN 3.0 MCP server (streamable-http) on {host}:{port}",
            file=sys.stderr,
        )
        uvicorn.run(app, host=host, port=port)
    else:
        print("Starting BRAIN 3.0 MCP server (stdio)", file=sys.stderr)
        mcp.run(transport="stdio")
