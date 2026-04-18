"""Tests for rules engine MCP tools."""

import pytest
from unittest.mock import AsyncMock

from client import BrainAPIError
from mcp.server.fastmcp import FastMCP
from tools.rules import register
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
    """Register rules tools and return a dict of tool functions."""
    mcp = FastMCP("test")
    register(mcp, api)
    return {
        name: tool.fn
        for name, tool in mcp._tool_manager._tools.items()
    }


# ---------------------------------------------------------------------------
# create_rule
# ---------------------------------------------------------------------------

class TestCreateRule:

    @pytest.mark.anyio
    async def test_happy_path(self, tools, api):
        api.post.return_value = {"id": VALID_UUID, "name": "Skip alert"}
        result = await tools["create_rule"](
            name="Skip alert",
            entity_type="habit",
            metric="consecutive_skips",
            operator=">=",
            threshold=3,
            notification_type="habit_nudge",
            message_template="{entity_name} has been skipped {metric_value} times",
        )
        assert result["id"] == VALID_UUID
        api.post.assert_called_once()
        call_args = api.post.call_args
        assert call_args[0][0] == "/api/rules/"
        body = call_args[1]["json"]
        assert body["name"] == "Skip alert"
        assert body["entity_type"] == "habit"
        assert body["metric"] == "consecutive_skips"
        assert body["operator"] == ">="
        assert body["threshold"] == 3
        assert body["notification_type"] == "habit_nudge"
        assert body["enabled"] is True
        assert body["cooldown_hours"] == 24

    @pytest.mark.anyio
    async def test_with_entity_id(self, tools, api):
        api.post.return_value = {"id": VALID_UUID}
        await tools["create_rule"](
            name="Targeted rule",
            entity_type="habit",
            metric="consecutive_skips",
            operator=">=",
            threshold=2,
            notification_type="habit_nudge",
            message_template="test",
            entity_id=VALID_UUID_2,
            enabled=False,
            cooldown_hours=48,
        )
        body = api.post.call_args[1]["json"]
        assert body["entity_id"] == VALID_UUID_2
        assert body["enabled"] is False
        assert body["cooldown_hours"] == 48

    @pytest.mark.anyio
    async def test_invalid_entity_type(self, tools):
        with pytest.raises(InputValidationError, match="entity_type"):
            await tools["create_rule"](
                name="Bad rule",
                entity_type="widget",
                metric="consecutive_skips",
                operator=">=",
                threshold=3,
                notification_type="habit_nudge",
                message_template="test",
            )

    @pytest.mark.anyio
    async def test_invalid_metric(self, tools):
        with pytest.raises(InputValidationError, match="metric"):
            await tools["create_rule"](
                name="Bad rule",
                entity_type="habit",
                metric="invalid_metric",
                operator=">=",
                threshold=3,
                notification_type="habit_nudge",
                message_template="test",
            )

    @pytest.mark.anyio
    async def test_invalid_operator(self, tools):
        with pytest.raises(InputValidationError, match="operator"):
            await tools["create_rule"](
                name="Bad rule",
                entity_type="habit",
                metric="consecutive_skips",
                operator="gt",
                threshold=3,
                notification_type="habit_nudge",
                message_template="test",
            )

    @pytest.mark.anyio
    async def test_invalid_notification_type(self, tools):
        with pytest.raises(InputValidationError, match="notification_type"):
            await tools["create_rule"](
                name="Bad rule",
                entity_type="habit",
                metric="consecutive_skips",
                operator=">=",
                threshold=3,
                notification_type="invalid_type",
                message_template="test",
            )

    @pytest.mark.anyio
    async def test_negative_threshold(self, tools):
        with pytest.raises(InputValidationError, match="threshold"):
            await tools["create_rule"](
                name="Bad rule",
                entity_type="habit",
                metric="consecutive_skips",
                operator=">=",
                threshold=-1,
                notification_type="habit_nudge",
                message_template="test",
            )

    @pytest.mark.anyio
    async def test_negative_cooldown(self, tools):
        with pytest.raises(InputValidationError, match="cooldown_hours"):
            await tools["create_rule"](
                name="Bad rule",
                entity_type="habit",
                metric="consecutive_skips",
                operator=">=",
                threshold=3,
                notification_type="habit_nudge",
                message_template="test",
                cooldown_hours=-1,
            )

    @pytest.mark.anyio
    async def test_missing_name(self, tools):
        with pytest.raises(InputValidationError, match="name"):
            await tools["create_rule"](
                name="",
                entity_type="habit",
                metric="consecutive_skips",
                operator=">=",
                threshold=3,
                notification_type="habit_nudge",
                message_template="test",
            )

    @pytest.mark.anyio
    async def test_invalid_entity_id_uuid(self, tools):
        with pytest.raises(InputValidationError, match="entity_id"):
            await tools["create_rule"](
                name="Bad rule",
                entity_type="habit",
                metric="consecutive_skips",
                operator=">=",
                threshold=3,
                notification_type="habit_nudge",
                message_template="test",
                entity_id="not-a-uuid",
            )

    @pytest.mark.anyio
    async def test_checkin_entity_type_accepted(self, tools, api):
        api.post.return_value = {"id": VALID_UUID}
        await tools["create_rule"](
            name="Checkin rule",
            entity_type="checkin",
            metric="non_responses",
            operator=">=",
            threshold=3,
            notification_type="checkin_prompt",
            message_template="test",
        )
        body = api.post.call_args[1]["json"]
        assert body["entity_type"] == "checkin"

    @pytest.mark.anyio
    async def test_goal_entity_type_rejected(self, tools):
        with pytest.raises(InputValidationError, match="entity_type"):
            await tools["create_rule"](
                name="Bad rule",
                entity_type="goal",
                metric="consecutive_skips",
                operator=">=",
                threshold=3,
                notification_type="habit_nudge",
                message_template="test",
            )

    @pytest.mark.parametrize("symbol", [">=", "<=", "=="])
    @pytest.mark.anyio
    async def test_all_operator_symbols_accepted(self, tools, api, symbol):
        api.post.return_value = {"id": VALID_UUID}
        await tools["create_rule"](
            name=f"Rule {symbol}",
            entity_type="habit",
            metric="consecutive_skips",
            operator=symbol,
            threshold=3,
            notification_type="habit_nudge",
            message_template="test",
        )
        body = api.post.call_args[1]["json"]
        assert body["operator"] == symbol


# ---------------------------------------------------------------------------
# list_rules
# ---------------------------------------------------------------------------

class TestListRules:

    @pytest.mark.anyio
    async def test_no_filters(self, tools, api):
        api.get.return_value = []
        result = await tools["list_rules"]()
        assert result == []
        api.get.assert_called_once_with("/api/rules/", params=None)

    @pytest.mark.anyio
    async def test_all_filters(self, tools, api):
        api.get.return_value = [{"id": VALID_UUID}]
        await tools["list_rules"](
            entity_type="habit",
            enabled=True,
            notification_type="habit_nudge",
            entity_id=VALID_UUID,
        )
        call_params = api.get.call_args[1]["params"]
        assert call_params["entity_type"] == "habit"
        assert call_params["enabled"] is True
        assert call_params["notification_type"] == "habit_nudge"
        assert call_params["entity_id"] == VALID_UUID

    @pytest.mark.anyio
    async def test_invalid_entity_type_filter(self, tools):
        with pytest.raises(InputValidationError, match="entity_type"):
            await tools["list_rules"](entity_type="invalid")

    @pytest.mark.anyio
    async def test_invalid_notification_type_filter(self, tools):
        with pytest.raises(InputValidationError, match="notification_type"):
            await tools["list_rules"](notification_type="bogus")

    @pytest.mark.anyio
    async def test_invalid_entity_id_filter(self, tools):
        with pytest.raises(InputValidationError, match="entity_id"):
            await tools["list_rules"](entity_id="bad-uuid")


# ---------------------------------------------------------------------------
# get_rule
# ---------------------------------------------------------------------------

class TestGetRule:

    @pytest.mark.anyio
    async def test_happy_path(self, tools, api):
        api.get.return_value = {"id": VALID_UUID, "name": "Skip alert"}
        result = await tools["get_rule"](rule_id=VALID_UUID)
        assert result["id"] == VALID_UUID
        api.get.assert_called_once_with(f"/api/rules/{VALID_UUID}")

    @pytest.mark.anyio
    async def test_invalid_uuid(self, tools):
        with pytest.raises(InputValidationError, match="rule_id"):
            await tools["get_rule"](rule_id="bad")

    @pytest.mark.anyio
    async def test_not_found(self, tools, api):
        api.get.side_effect = make_api_error(404, "Rule not found")
        with pytest.raises(BrainAPIError, match="404"):
            await tools["get_rule"](rule_id=VALID_UUID)


# ---------------------------------------------------------------------------
# update_rule
# ---------------------------------------------------------------------------

class TestUpdateRule:

    @pytest.mark.anyio
    async def test_happy_path(self, tools, api):
        api.patch.return_value = {"id": VALID_UUID, "threshold": 5}
        result = await tools["update_rule"](
            rule_id=VALID_UUID,
            threshold=5,
        )
        assert result["threshold"] == 5
        call_args = api.patch.call_args
        assert call_args[0][0] == f"/api/rules/{VALID_UUID}"
        assert call_args[1]["json"]["threshold"] == 5

    @pytest.mark.anyio
    async def test_multiple_fields(self, tools, api):
        api.patch.return_value = {"id": VALID_UUID}
        await tools["update_rule"](
            rule_id=VALID_UUID,
            name="Updated name",
            enabled=False,
            cooldown_hours=48,
        )
        body = api.patch.call_args[1]["json"]
        assert body["name"] == "Updated name"
        assert body["enabled"] is False
        assert body["cooldown_hours"] == 48

    @pytest.mark.anyio
    async def test_invalid_uuid(self, tools):
        with pytest.raises(InputValidationError, match="rule_id"):
            await tools["update_rule"](rule_id="bad")

    @pytest.mark.anyio
    async def test_invalid_entity_type(self, tools):
        with pytest.raises(InputValidationError, match="entity_type"):
            await tools["update_rule"](
                rule_id=VALID_UUID, entity_type="invalid"
            )

    @pytest.mark.anyio
    async def test_invalid_metric(self, tools):
        with pytest.raises(InputValidationError, match="metric"):
            await tools["update_rule"](
                rule_id=VALID_UUID, metric="bad_metric"
            )

    @pytest.mark.anyio
    async def test_invalid_operator(self, tools):
        with pytest.raises(InputValidationError, match="operator"):
            await tools["update_rule"](
                rule_id=VALID_UUID, operator="neq"
            )

    @pytest.mark.anyio
    async def test_negative_threshold(self, tools):
        with pytest.raises(InputValidationError, match="threshold"):
            await tools["update_rule"](
                rule_id=VALID_UUID, threshold=-1
            )

    @pytest.mark.anyio
    async def test_negative_cooldown(self, tools):
        with pytest.raises(InputValidationError, match="cooldown_hours"):
            await tools["update_rule"](
                rule_id=VALID_UUID, cooldown_hours=-5
            )

    @pytest.mark.anyio
    async def test_not_found(self, tools, api):
        api.patch.side_effect = make_api_error(404, "Rule not found")
        with pytest.raises(BrainAPIError, match="404"):
            await tools["update_rule"](
                rule_id=VALID_UUID, threshold=5
            )


# ---------------------------------------------------------------------------
# delete_rule
# ---------------------------------------------------------------------------

class TestDeleteRule:

    @pytest.mark.anyio
    async def test_happy_path(self, tools, api):
        api.delete.return_value = {"deleted": True}
        result = await tools["delete_rule"](rule_id=VALID_UUID)
        assert result["deleted"] is True
        api.delete.assert_called_once_with(f"/api/rules/{VALID_UUID}")

    @pytest.mark.anyio
    async def test_invalid_uuid(self, tools):
        with pytest.raises(InputValidationError, match="rule_id"):
            await tools["delete_rule"](rule_id="bad")

    @pytest.mark.anyio
    async def test_not_found(self, tools, api):
        api.delete.side_effect = make_api_error(404, "Rule not found")
        with pytest.raises(BrainAPIError, match="404"):
            await tools["delete_rule"](rule_id=VALID_UUID)


# ---------------------------------------------------------------------------
# evaluate_rules
# ---------------------------------------------------------------------------

class TestEvaluateRules:

    @pytest.mark.anyio
    async def test_happy_path(self, tools, api):
        api.post.return_value = {
            "evaluated": 5, "fired": 2, "skipped": 3, "results": [],
        }
        result = await tools["evaluate_rules"]()
        assert result["evaluated"] == 5
        assert result["fired"] == 2
        api.post.assert_called_once_with("/api/rules/evaluate")


# ---------------------------------------------------------------------------
# evaluate_rule
# ---------------------------------------------------------------------------

class TestEvaluateRule:

    @pytest.mark.anyio
    async def test_happy_path(self, tools, api):
        api.post.return_value = {"rule_id": VALID_UUID, "fired": True}
        result = await tools["evaluate_rule"](rule_id=VALID_UUID)
        assert result["fired"] is True
        call_args = api.post.call_args
        assert call_args[0][0] == f"/api/rules/{VALID_UUID}/evaluate"
        assert call_args[1]["params"]["respect_cooldown"] is True

    @pytest.mark.anyio
    async def test_bypass_cooldown(self, tools, api):
        api.post.return_value = {"rule_id": VALID_UUID, "fired": True}
        await tools["evaluate_rule"](
            rule_id=VALID_UUID,
            respect_cooldown=False,
        )
        call_params = api.post.call_args[1]["params"]
        assert call_params["respect_cooldown"] is False

    @pytest.mark.anyio
    async def test_invalid_uuid(self, tools):
        with pytest.raises(InputValidationError, match="rule_id"):
            await tools["evaluate_rule"](rule_id="bad")

    @pytest.mark.anyio
    async def test_not_found(self, tools, api):
        api.post.side_effect = make_api_error(404, "Rule not found")
        with pytest.raises(BrainAPIError, match="404"):
            await tools["evaluate_rule"](rule_id=VALID_UUID)


# ---------------------------------------------------------------------------
# [MCP-BUG-01] Structured-detail error envelope — regression coverage
# ---------------------------------------------------------------------------

class TestStructuredDetailErrorEnvelope:
    """Tool-level error path receives FastAPI-shaped list-of-dicts detail."""

    @pytest.mark.anyio
    async def test_evaluate_rule_422_list_detail_is_json_parseable(
        self, tools, api,
    ):
        import json

        validation_detail = [
            {
                "type": "uuid_parsing",
                "loc": ["path", "rule_id"],
                "msg": "Input should be a valid UUID",
                "input": "bogus",
            },
        ]
        api.post.side_effect = make_api_error(422, validation_detail)

        with pytest.raises(BrainAPIError) as exc_info:
            await tools["evaluate_rule"](rule_id=VALID_UUID)

        message = str(exc_info.value)
        assert message.startswith("API error (422): ")
        payload = message.removeprefix("API error (422): ")
        assert json.loads(payload) == validation_detail
        assert '"msg"' in message
