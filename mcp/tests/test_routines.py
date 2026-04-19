"""Tests for routine MCP tools."""

import pytest
from unittest.mock import AsyncMock

from mcp.server.fastmcp import FastMCP
from tools.routines import register
from validation import InputValidationError


VALID_UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
VALID_UUID_2 = "b2c3d4e5-f6a7-8901-bcde-f12345678901"


@pytest.fixture()
def api():
    return AsyncMock()


@pytest.fixture()
def tools(api):
    """Register routine tools and return a dict of tool functions."""
    mcp = FastMCP("test")
    register(mcp, api)
    return {
        name: tool.fn
        for name, tool in mcp._tool_manager._tools.items()
    }


# ---------------------------------------------------------------------------
# list_routines — envelope response shape
# ---------------------------------------------------------------------------

class TestListRoutines:
    """list_routines returns the {items, count} envelope from /api/routines/."""

    @pytest.mark.anyio
    async def test_no_filters_empty_envelope(self, tools, api):
        api.get.return_value = {"items": [], "count": 0}
        result = await tools["list_routines"]()
        assert result == {"items": [], "count": 0}
        assert result["items"] == []
        assert result["count"] == 0
        api.get.assert_called_once_with("/api/routines/", params=None)

    @pytest.mark.anyio
    async def test_envelope_items_passed_through(self, tools, api):
        api.get.return_value = {
            "items": [
                {"id": VALID_UUID, "title": "Morning meditation"},
                {"id": VALID_UUID_2, "title": "Evening journal"},
            ],
            "count": 2,
        }
        result = await tools["list_routines"]()
        assert result["count"] == 2
        assert len(result["items"]) == 2
        assert result["items"][0]["title"] == "Morning meditation"

    @pytest.mark.anyio
    async def test_all_filters_forwarded(self, tools, api):
        api.get.return_value = {"items": [], "count": 0}
        await tools["list_routines"](
            domain_id=VALID_UUID,
            status="active",
            frequency="daily",
            streak_broken=True,
        )
        call_params = api.get.call_args[1]["params"]
        assert call_params["domain_id"] == VALID_UUID
        assert call_params["status"] == "active"
        assert call_params["frequency"] == "daily"
        assert call_params["streak_broken"] is True

    @pytest.mark.anyio
    async def test_invalid_status_filter(self, tools):
        with pytest.raises(InputValidationError, match="status"):
            await tools["list_routines"](status="bogus")

    @pytest.mark.anyio
    async def test_invalid_frequency_filter(self, tools):
        with pytest.raises(InputValidationError, match="frequency"):
            await tools["list_routines"](frequency="bogus")
