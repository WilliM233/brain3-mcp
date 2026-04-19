"""Tests for habit CRUD MCP tools."""

import pytest
from unittest.mock import AsyncMock

from client import BrainAPIError
from mcp.server.fastmcp import FastMCP
from tools.habits import register
from validation import InputValidationError
from tests.conftest import make_api_error


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


# ---------------------------------------------------------------------------
# list_habits — envelope response shape
# ---------------------------------------------------------------------------

class TestListHabits:
    """list_habits returns the {items, count} envelope from /api/habits/."""

    @pytest.mark.anyio
    async def test_no_filters_empty_envelope(self, tools, api):
        api.get.return_value = {"items": [], "count": 0}
        result = await tools["list_habits"]()
        assert result == {"items": [], "count": 0}
        assert result["items"] == []
        assert result["count"] == 0
        api.get.assert_called_once_with("/api/habits/", params=None)

    @pytest.mark.anyio
    async def test_envelope_items_passed_through(self, tools, api):
        api.get.return_value = {
            "items": [
                {"id": VALID_UUID, "title": "Floss"},
                {"id": "b2c3d4e5-f6a7-8901-bcde-f12345678901", "title": "Walk"},
            ],
            "count": 2,
        }
        result = await tools["list_habits"]()
        assert result["count"] == 2
        assert len(result["items"]) == 2
        assert result["items"][0]["title"] == "Floss"

    @pytest.mark.anyio
    async def test_all_filters_forwarded(self, tools, api):
        api.get.return_value = {"items": [], "count": 0}
        await tools["list_habits"](
            routine_id=VALID_UUID,
            status="active",
            scaffolding_status="tracking",
        )
        call_params = api.get.call_args[1]["params"]
        assert call_params["routine_id"] == VALID_UUID
        assert call_params["status"] == "active"
        assert call_params["scaffolding_status"] == "tracking"

    @pytest.mark.anyio
    async def test_invalid_status_filter(self, tools):
        with pytest.raises(InputValidationError, match="status"):
            await tools["list_habits"](status="bogus")

    @pytest.mark.anyio
    async def test_invalid_scaffolding_status_filter(self, tools):
        with pytest.raises(InputValidationError, match="scaffolding_status"):
            await tools["list_habits"](scaffolding_status="bogus")


# ---------------------------------------------------------------------------
# get_habit — effective_graduation_params pass-through
# ---------------------------------------------------------------------------


class TestGetHabitEffectiveGraduationParams:
    """[2A-Enh-01] get_habit must pass ``effective_graduation_params`` through.

    The MCP shim is a pass-through over GET /api/habits/{id}, so these tests
    assert the shim forwards the nested composite field intact — matching the
    real API contract surfaced by HabitDetailResponse in brain3.
    """

    @pytest.mark.anyio
    async def test_get_habit_returns_effective_graduation_params_friction_default(
        self, tools, api,
    ):
        api.get.return_value = {
            "id": VALID_UUID,
            "title": "Floss",
            "graduation_window": None,
            "graduation_target": None,
            "graduation_threshold": None,
            "friction_score": 3,
            "effective_graduation_params": {
                "window_days": 45,
                "target_rate": 0.85,
                "threshold_days": 45,
                "source": "friction_default",
            },
        }
        result = await tools["get_habit"](habit_id=VALID_UUID)
        api.get.assert_called_once_with(f"/api/habits/{VALID_UUID}")
        assert result["effective_graduation_params"] == {
            "window_days": 45,
            "target_rate": 0.85,
            "threshold_days": 45,
            "source": "friction_default",
        }

    @pytest.mark.anyio
    async def test_get_habit_returns_effective_graduation_params_override(
        self, tools, api,
    ):
        api.get.return_value = {
            "id": VALID_UUID,
            "title": "Floss",
            "graduation_window": 100,
            "graduation_target": 0.70,
            "graduation_threshold": 100,
            "friction_score": 1,
            "effective_graduation_params": {
                "window_days": 100,
                "target_rate": 0.70,
                "threshold_days": 100,
                "source": "override",
            },
        }
        result = await tools["get_habit"](habit_id=VALID_UUID)
        assert result["effective_graduation_params"]["source"] == "override"
        assert result["effective_graduation_params"]["window_days"] == 100


# ---------------------------------------------------------------------------
# [A-9-accountable-since] accountable_since rename — pass-through coverage
# ---------------------------------------------------------------------------

class TestAccountableSinceRename:
    """D2 rename: MCP tools accept ``accountable_since`` and forward it verbatim."""

    @pytest.mark.anyio
    async def test_create_habit_accountable_since_passed_through(
        self, tools, api,
    ):
        api.post.return_value = {"id": VALID_UUID}
        await tools["create_habit"](
            title="Floss", frequency="daily", accountable_since="2026-04-10",
        )
        body = api.post.call_args[1]["json"]
        assert body["accountable_since"] == "2026-04-10"

    @pytest.mark.anyio
    async def test_create_habit_accountable_since_omitted_when_none(
        self, tools, api,
    ):
        api.post.return_value = {"id": VALID_UUID}
        await tools["create_habit"](title="Floss", frequency="daily")
        body = api.post.call_args[1]["json"]
        assert "accountable_since" not in body

    @pytest.mark.anyio
    async def test_update_habit_accountable_since_passed_through(
        self, tools, api,
    ):
        api.patch.return_value = {"id": VALID_UUID}
        await tools["update_habit"](
            habit_id=VALID_UUID, accountable_since="2026-04-10",
        )
        body = api.patch.call_args[1]["json"]
        assert body["accountable_since"] == "2026-04-10"


# ---------------------------------------------------------------------------
# [MCP-BUG-01] Structured-detail error envelope — regression coverage
# ---------------------------------------------------------------------------

class TestStructuredDetailErrorEnvelope:
    """Tool-level error path receives FastAPI-shaped list-of-dicts detail."""

    @pytest.mark.anyio
    async def test_create_habit_422_list_detail_is_json_parseable(
        self, tools, api,
    ):
        import json

        validation_detail = [
            {
                "type": "missing",
                "loc": ["body", "title"],
                "msg": "Field required",
                "input": {"frequency": "daily"},
            },
        ]
        api.post.side_effect = make_api_error(422, validation_detail)

        with pytest.raises(BrainAPIError) as exc_info:
            await tools["create_habit"](title="Floss", frequency="daily")

        message = str(exc_info.value)
        assert message.startswith("API error (422): ")
        payload = message.removeprefix("API error (422): ")
        assert json.loads(payload) == validation_detail
        assert '"msg"' in message
