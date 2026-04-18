"""Shared fixtures for MCP tool tests."""

import json
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


def make_api_error(
    status_code: int,
    detail: str | dict | list,
) -> BrainAPIError:
    """Create a BrainAPIError mimicking an HTTP error response.

    Accepts string detail (typical for HTTPException) or structured
    detail (dict/list, as produced by FastAPI's default
    RequestValidationError). Structured detail is JSON-encoded so the
    resulting message is JSON-parseable by MCP consumers — matching the
    production behavior of client._request after the MCP-BUG-01 fix.
    """
    if not isinstance(detail, str):
        detail = json.dumps(detail)
    return BrainAPIError(f"API error ({status_code}): {detail}")
