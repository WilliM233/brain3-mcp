"""Tests for graduation, frequency, and stacking MCP tools."""

import pytest
from unittest.mock import AsyncMock

from client import BrainAPIError
from mcp.server.fastmcp import FastMCP
from tools.graduation import register
from validation import InputValidationError
from tests.conftest import make_api_error


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
VALID_UUID_2 = "b2c3d4e5-f6a7-8901-bcde-f12345678901"


@pytest.fixture()
def api():
    return AsyncMock()


@pytest.fixture()
def tools(api):
    """Register graduation tools and return a dict of tool functions."""
    mcp = FastMCP("test")
    register(mcp, api)
    return {
        name: tool.fn
        for name, tool in mcp._tool_manager._tools.items()
    }


# ---------------------------------------------------------------------------
# evaluate_graduation
# ---------------------------------------------------------------------------

class TestEvaluateGraduation:

    @pytest.mark.anyio
    async def test_happy_path(self, tools, api):
        api.post.return_value = {
            "eligible": True,
            "current_rate": 0.85,
            "target_rate": 0.80,
            "days_since_introduction": 30,
            "blocking_reasons": [],
        }
        result = await tools["evaluate_graduation"](habit_id=VALID_UUID)
        assert result["eligible"] is True
        assert result["current_rate"] == 0.85
        api.post.assert_called_once_with(
            f"/api/habits/{VALID_UUID}/evaluate-graduation"
        )

    @pytest.mark.anyio
    async def test_invalid_uuid(self, tools, api):
        with pytest.raises(InputValidationError, match="not a valid UUID"):
            await tools["evaluate_graduation"](habit_id="not-a-uuid")

    @pytest.mark.anyio
    async def test_not_found(self, tools, api):
        api.post.side_effect = make_api_error(404, "Habit not found")
        with pytest.raises(BrainAPIError, match="404"):
            await tools["evaluate_graduation"](habit_id=VALID_UUID)


# ---------------------------------------------------------------------------
# graduate_habit
# ---------------------------------------------------------------------------

class TestGraduateHabit:

    @pytest.mark.anyio
    async def test_happy_path(self, tools, api):
        api.post.return_value = {
            "success": True,
            "previous_state": "accountable",
            "new_state": "graduated",
        }
        result = await tools["graduate_habit"](habit_id=VALID_UUID)
        assert result["success"] is True
        api.post.assert_called_once_with(
            f"/api/habits/{VALID_UUID}/graduate", json=None
        )

    @pytest.mark.anyio
    async def test_with_force(self, tools, api):
        api.post.return_value = {"success": True}
        await tools["graduate_habit"](habit_id=VALID_UUID, force=True)
        call_args = api.post.call_args
        assert call_args[1]["json"]["force"] is True

    @pytest.mark.anyio
    async def test_invalid_uuid(self, tools, api):
        with pytest.raises(InputValidationError, match="not a valid UUID"):
            await tools["graduate_habit"](habit_id="bad")

    @pytest.mark.anyio
    async def test_not_eligible(self, tools, api):
        api.post.side_effect = make_api_error(
            400, "Habit does not meet graduation criteria"
        )
        with pytest.raises(BrainAPIError, match="400"):
            await tools["graduate_habit"](habit_id=VALID_UUID)


# ---------------------------------------------------------------------------
# evaluate_frequency
# ---------------------------------------------------------------------------

class TestEvaluateFrequency:

    @pytest.mark.anyio
    async def test_happy_path(self, tools, api):
        api.post.return_value = {
            "recommendation": "step_down",
            "current_frequency": "daily",
            "recommended_frequency": "every_other_day",
            "rate": 0.90,
            "cooldown_active": False,
        }
        result = await tools["evaluate_frequency"](habit_id=VALID_UUID)
        assert result["recommendation"] == "step_down"
        api.post.assert_called_once_with(
            f"/api/habits/{VALID_UUID}/evaluate-frequency"
        )

    @pytest.mark.anyio
    async def test_invalid_uuid(self, tools, api):
        with pytest.raises(InputValidationError, match="not a valid UUID"):
            await tools["evaluate_frequency"](habit_id="nope")

    @pytest.mark.anyio
    async def test_not_found(self, tools, api):
        api.post.side_effect = make_api_error(404, "Habit not found")
        with pytest.raises(BrainAPIError, match="404"):
            await tools["evaluate_frequency"](habit_id=VALID_UUID)


# ---------------------------------------------------------------------------
# step_down_frequency
# ---------------------------------------------------------------------------

class TestStepDownFrequency:

    @pytest.mark.anyio
    async def test_happy_path(self, tools, api):
        api.post.return_value = {
            "success": True,
            "previous_frequency": "daily",
            "new_frequency": "every_other_day",
        }
        result = await tools["step_down_frequency"](habit_id=VALID_UUID)
        assert result["success"] is True
        assert result["new_frequency"] == "every_other_day"
        api.post.assert_called_once_with(
            f"/api/habits/{VALID_UUID}/step-down-frequency"
        )

    @pytest.mark.anyio
    async def test_invalid_uuid(self, tools, api):
        with pytest.raises(InputValidationError, match="not a valid UUID"):
            await tools["step_down_frequency"](habit_id="bad-id")

    @pytest.mark.anyio
    async def test_not_recommended(self, tools, api):
        api.post.side_effect = make_api_error(
            400, "Step-down not recommended"
        )
        with pytest.raises(BrainAPIError, match="400"):
            await tools["step_down_frequency"](habit_id=VALID_UUID)


# ---------------------------------------------------------------------------
# evaluate_slip
# ---------------------------------------------------------------------------

class TestEvaluateSlip:

    @pytest.mark.anyio
    async def test_happy_path(self, tools, api):
        api.post.return_value = {
            "slip_signals": [],
            "recommendation": "no_action",
            "days_since_graduation": 14,
        }
        result = await tools["evaluate_slip"](habit_id=VALID_UUID)
        assert result["recommendation"] == "no_action"
        api.post.assert_called_once_with(
            f"/api/habits/{VALID_UUID}/evaluate-slip"
        )

    @pytest.mark.anyio
    async def test_with_slip_detected(self, tools, api):
        api.post.return_value = {
            "slip_signals": [
                {"type": "checklist_gap", "severity": "moderate"},
            ],
            "recommendation": "re_scaffold",
            "days_since_graduation": 7,
        }
        result = await tools["evaluate_slip"](habit_id=VALID_UUID)
        assert result["recommendation"] == "re_scaffold"
        assert len(result["slip_signals"]) == 1

    @pytest.mark.anyio
    async def test_invalid_uuid(self, tools, api):
        with pytest.raises(InputValidationError, match="not a valid UUID"):
            await tools["evaluate_slip"](habit_id="x")

    @pytest.mark.anyio
    async def test_not_graduated(self, tools, api):
        api.post.side_effect = make_api_error(
            400, "Habit is not graduated"
        )
        with pytest.raises(BrainAPIError, match="400"):
            await tools["evaluate_slip"](habit_id=VALID_UUID)


# ---------------------------------------------------------------------------
# re_scaffold_habit
# ---------------------------------------------------------------------------

class TestReScaffoldHabit:

    @pytest.mark.anyio
    async def test_happy_path(self, tools, api):
        api.post.return_value = {
            "new_scaffolding_state": "accountable",
            "re_scaffold_count": 1,
            "tightened_criteria": {
                "graduation_target": 0.90,
                "graduation_window": 21,
            },
        }
        result = await tools["re_scaffold_habit"](habit_id=VALID_UUID)
        assert result["new_scaffolding_state"] == "accountable"
        assert result["re_scaffold_count"] == 1
        api.post.assert_called_once_with(
            f"/api/habits/{VALID_UUID}/re-scaffold"
        )

    @pytest.mark.anyio
    async def test_invalid_uuid(self, tools, api):
        with pytest.raises(InputValidationError, match="not a valid UUID"):
            await tools["re_scaffold_habit"](habit_id="nah")

    @pytest.mark.anyio
    async def test_not_graduated(self, tools, api):
        api.post.side_effect = make_api_error(
            400, "Habit is not graduated"
        )
        with pytest.raises(BrainAPIError, match="400"):
            await tools["re_scaffold_habit"](habit_id=VALID_UUID)


# ---------------------------------------------------------------------------
# get_graduation_status
# ---------------------------------------------------------------------------

class TestGetGraduationStatus:

    @pytest.mark.anyio
    async def test_happy_path(self, tools, api):
        api.get.return_value = {
            "habit_id": VALID_UUID,
            "scaffolding_status": "accountable",
            "notification_frequency": "daily",
            "graduation_progress": {
                "current_rate": 0.75,
                "target_rate": 0.80,
                "eligible": False,
            },
            "frequency_step_down": {
                "eligible": False,
                "cooldown_active": True,
            },
            "re_scaffold_count": 0,
        }
        result = await tools["get_graduation_status"](habit_id=VALID_UUID)
        assert result["scaffolding_status"] == "accountable"
        assert result["graduation_progress"]["current_rate"] == 0.75
        api.get.assert_called_once_with(
            f"/api/habits/{VALID_UUID}/graduation-status"
        )

    @pytest.mark.anyio
    async def test_invalid_uuid(self, tools, api):
        with pytest.raises(InputValidationError, match="not a valid UUID"):
            await tools["get_graduation_status"](habit_id="bad")

    @pytest.mark.anyio
    async def test_not_found(self, tools, api):
        api.get.side_effect = make_api_error(404, "Habit not found")
        with pytest.raises(BrainAPIError, match="404"):
            await tools["get_graduation_status"](habit_id=VALID_UUID)


# ---------------------------------------------------------------------------
# get_stacking_recommendation
# ---------------------------------------------------------------------------

class TestGetStackingRecommendation:

    @pytest.mark.anyio
    async def test_happy_path(self, tools, api):
        api.get.return_value = {
            "ready": True,
            "blocking_habits": [],
            "suggested_habit": {
                "id": VALID_UUID_2,
                "title": "Flossing",
                "reason": "paused_retry",
            },
            "message": "You've been solid -- ready to add flossing?",
        }
        result = await tools["get_stacking_recommendation"](
            routine_id=VALID_UUID
        )
        assert result["ready"] is True
        assert result["suggested_habit"]["title"] == "Flossing"
        api.get.assert_called_once_with(
            "/api/graduation/suggest-next",
            params={"routine_id": VALID_UUID},
        )

    @pytest.mark.anyio
    async def test_not_ready(self, tools, api):
        api.get.return_value = {
            "ready": False,
            "blocking_habits": [
                {"id": VALID_UUID_2, "title": "Brushing teeth"},
            ],
            "suggested_habit": None,
            "message": "Hold steady -- brushing teeth needs more time.",
        }
        result = await tools["get_stacking_recommendation"](
            routine_id=VALID_UUID
        )
        assert result["ready"] is False
        assert len(result["blocking_habits"]) == 1

    @pytest.mark.anyio
    async def test_invalid_uuid(self, tools, api):
        with pytest.raises(InputValidationError, match="not a valid UUID"):
            await tools["get_stacking_recommendation"](
                routine_id="not-uuid"
            )

    @pytest.mark.anyio
    async def test_not_found(self, tools, api):
        api.get.side_effect = make_api_error(404, "Routine not found")
        with pytest.raises(BrainAPIError, match="404"):
            await tools["get_stacking_recommendation"](
                routine_id=VALID_UUID
            )


# ---------------------------------------------------------------------------
# Integration flow: evaluate_graduation -> graduate_habit
# ---------------------------------------------------------------------------

class TestGraduationFlow:

    @pytest.mark.anyio
    async def test_evaluate_then_graduate(self, tools, api):
        """End-to-end flow: evaluate graduation, then graduate."""
        api.post.side_effect = [
            {
                "eligible": True,
                "current_rate": 0.85,
                "target_rate": 0.80,
                "days_since_introduction": 30,
                "blocking_reasons": [],
            },
            {
                "success": True,
                "previous_state": "accountable",
                "new_state": "graduated",
            },
        ]
        eval_result = await tools["evaluate_graduation"](
            habit_id=VALID_UUID
        )
        assert eval_result["eligible"] is True

        grad_result = await tools["graduate_habit"](habit_id=VALID_UUID)
        assert grad_result["success"] is True
        assert api.post.call_count == 2


# ---------------------------------------------------------------------------
# Integration flow: evaluate_frequency -> step_down_frequency
# ---------------------------------------------------------------------------

class TestFrequencyFlow:

    @pytest.mark.anyio
    async def test_evaluate_then_step_down(self, tools, api):
        """End-to-end flow: evaluate frequency, then step down."""
        api.post.side_effect = [
            {
                "recommendation": "step_down",
                "current_frequency": "daily",
                "recommended_frequency": "every_other_day",
                "rate": 0.90,
                "cooldown_active": False,
            },
            {
                "success": True,
                "previous_frequency": "daily",
                "new_frequency": "every_other_day",
            },
        ]
        eval_result = await tools["evaluate_frequency"](
            habit_id=VALID_UUID
        )
        assert eval_result["recommendation"] == "step_down"

        step_result = await tools["step_down_frequency"](
            habit_id=VALID_UUID
        )
        assert step_result["success"] is True
        assert api.post.call_count == 2


# ---------------------------------------------------------------------------
# Integration flow: get_stacking_recommendation with mixed states
# ---------------------------------------------------------------------------

class TestStackingFlow:

    @pytest.mark.anyio
    async def test_mixed_habit_states(self, tools, api):
        """Stacking recommendation with mixed habit states in routine."""
        api.get.return_value = {
            "ready": False,
            "blocking_habits": [
                {
                    "id": VALID_UUID,
                    "title": "Brushing teeth",
                    "scaffolding_status": "accountable",
                    "stability": "unstable",
                },
            ],
            "suggested_habit": {
                "id": VALID_UUID_2,
                "title": "Flossing",
                "reason": "paused_retry",
            },
            "message": "Brushing teeth isn't stable yet. "
                       "Hold off on adding flossing.",
        }
        result = await tools["get_stacking_recommendation"](
            routine_id=VALID_UUID
        )
        assert result["ready"] is False
        assert result["blocking_habits"][0]["stability"] == "unstable"
        assert result["suggested_habit"]["title"] == "Flossing"


# ---------------------------------------------------------------------------
# [MCP-BUG-01] Structured-detail error envelope — regression coverage
# ---------------------------------------------------------------------------

class TestStructuredDetailErrorEnvelope:
    """Tool-level error path receives FastAPI-shaped list-of-dicts detail."""

    @pytest.mark.anyio
    async def test_graduate_habit_422_list_detail_is_json_parseable(
        self, tools, api,
    ):
        import json

        validation_detail = [
            {
                "type": "bool_parsing",
                "loc": ["body", "force"],
                "msg": "Input should be a valid boolean",
                "input": "not-a-bool",
            },
        ]
        api.post.side_effect = make_api_error(422, validation_detail)

        with pytest.raises(BrainAPIError) as exc_info:
            await tools["graduate_habit"](habit_id=VALID_UUID)

        message = str(exc_info.value)
        assert message.startswith("API error (422): ")
        payload = message.removeprefix("API error (422): ")
        assert json.loads(payload) == validation_detail
        assert '"msg"' in message
