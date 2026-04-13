"""Shared fixtures for MCP tool tests."""

from unittest.mock import AsyncMock

import pytest

from client import BrainAPIClient, BrainAPIError
from mcp.server.fastmcp import FastMCP


@pytest.fixture()
def api():
    """Mock BrainAPIClient with async methods."""
    mock = AsyncMock(spec=BrainAPIClient)
    return mock


@pytest.fixture()
def mcp_server():
    """Fresh FastMCP instance for registering tools."""
    return FastMCP("BRAIN 3.0 Test")


def make_api_error(status_code: int, detail: str) -> BrainAPIError:
    """Create a BrainAPIError mimicking an HTTP error response."""
    return BrainAPIError(f"API error ({status_code}): {detail}")
