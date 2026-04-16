"""Tests for habit CRUD MCP tools."""

import pytest
from unittest.mock import AsyncMock

from mcp.server.fastmcp import FastMCP
from tools.habits import register
from validation import InputValidationError


VALID_UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


@pytest.fixture()
def api():
    return AsyncMock()


@pytest.fixture()
def tools(api):
    """Register habit tools and return a dict of tool functions."""
    mcp = FastMCP("test")
    register(mcp, api)
    return {
        name: tool.fn
        for name, tool in mcp._tool_manager._tools.items()
    }


# ---------------------------------------------------------------------------
# create_habit — friction_score
# ---------------------------------------------------------------------------

class TestCreateHabitFrictionScore:

    @pytest.mark.anyio
    async def test_friction_score_passed_through(self, tools, api):
        api.post.return_value = {"id": VALID_UUID}
        await tools["create_habit"](
            title="Floss", frequency="daily", friction_score=3,
        )
        call_args = api.post.call_args
        assert call_args[1]["json"]["friction_score"] == 3

    @pytest.mark.anyio
    async def test_friction_score_omitted_when_none(self, tools, api):
        api.post.return_value = {"id": VALID_UUID}
        await tools["create_habit"](title="Floss", frequency="daily")
        call_args = api.post.call_args
        assert "friction_score" not in call_args[1]["json"]

    @pytest.mark.anyio
    async def test_friction_score_boundary_low(self, tools, api):
        api.post.return_value = {"id": VALID_UUID}
        await tools["create_habit"](
            title="Floss", frequency="daily", friction_score=1,
        )
        assert api.post.call_args[1]["json"]["friction_score"] == 1

    @pytest.mark.anyio
    async def test_friction_score_boundary_high(self, tools, api):
        api.post.return_value = {"id": VALID_UUID}
        await tools["create_habit"](
            title="Floss", frequency="daily", friction_score=5,
        )
        assert api.post.call_args[1]["json"]["friction_score"] == 5

    @pytest.mark.anyio
    async def test_friction_score_below_range(self, tools, api):
        with pytest.raises(InputValidationError, match="friction_score"):
            await tools["create_habit"](
                title="Floss", frequency="daily", friction_score=0,
            )

    @pytest.mark.anyio
    async def test_friction_score_above_range(self, tools, api):
        with pytest.raises(InputValidationError, match="friction_score"):
            await tools["create_habit"](
                title="Floss", frequency="daily", friction_score=6,
            )


# ---------------------------------------------------------------------------
# update_habit — friction_score
# ---------------------------------------------------------------------------

class TestUpdateHabitFrictionScore:

    @pytest.mark.anyio
    async def test_friction_score_passed_through(self, tools, api):
        api.patch.return_value = {"id": VALID_UUID}
        await tools["update_habit"](habit_id=VALID_UUID, friction_score=4)
        call_args = api.patch.call_args
        assert call_args[1]["json"]["friction_score"] == 4

    @pytest.mark.anyio
    async def test_friction_score_omitted_when_none(self, tools, api):
        api.patch.return_value = {"id": VALID_UUID}
        await tools["update_habit"](habit_id=VALID_UUID, title="New title")
        call_args = api.patch.call_args
        assert "friction_score" not in call_args[1]["json"]

    @pytest.mark.anyio
    async def test_friction_score_below_range(self, tools, api):
        with pytest.raises(InputValidationError, match="friction_score"):
            await tools["update_habit"](
                habit_id=VALID_UUID, friction_score=0,
            )

    @pytest.mark.anyio
    async def test_friction_score_above_range(self, tools, api):
        with pytest.raises(InputValidationError, match="friction_score"):
            await tools["update_habit"](
                habit_id=VALID_UUID, friction_score=10,
            )
