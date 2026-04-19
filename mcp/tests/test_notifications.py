"""Tests for notification queue MCP tools."""

import pytest
from unittest.mock import AsyncMock

from client import BrainAPIError
from mcp.server.fastmcp import FastMCP
from tools.notifications import register
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
    """Register notification tools and return a dict of tool functions."""
    mcp = FastMCP("test")
    register(mcp, api)
    # Access registered tool functions directly from the internal manager
    return {
        name: tool.fn
        for name, tool in mcp._tool_manager._tools.items()
    }


# ---------------------------------------------------------------------------
# create_notification
# ---------------------------------------------------------------------------

class TestCreateNotification:

    @pytest.mark.anyio
    async def test_happy_path(self, tools, api):
        api.post.return_value = {"id": VALID_UUID, "status": "pending"}
        result = await tools["create_notification"](
            notification_type="habit_nudge",
            scheduled_at="2026-04-14T09:00:00Z",
            target_entity_type="habit",
            target_entity_id=VALID_UUID,
            message="Time to check in on your morning routine!",
            scheduled_by="claude",
        )
        assert result["id"] == VALID_UUID
        api.post.assert_called_once()
        call_args = api.post.call_args
        assert call_args[0][0] == "/api/notifications/"
        body = call_args[1]["json"]
        assert body["notification_type"] == "habit_nudge"
        assert body["scheduled_by"] == "claude"
        assert body["delivery_type"] == "notification"

    @pytest.mark.anyio
    async def test_all_optional_params(self, tools, api):
        api.post.return_value = {"id": VALID_UUID}
        await tools["create_notification"](
            notification_type="routine_checklist",
            scheduled_at="2026-04-14T09:00:00Z",
            target_entity_type="routine",
            target_entity_id=VALID_UUID,
            message="Checklist time",
            scheduled_by="rule",
            delivery_type="notification",
            canned_responses=["done", "skip", "snooze"],
            expires_at="2026-04-14T10:00:00Z",
            rule_id=VALID_UUID_2,
        )
        body = api.post.call_args[1]["json"]
        assert body["canned_responses"] == ["done", "skip", "snooze"]
        assert body["expires_at"] == "2026-04-14T10:00:00Z"
        assert body["rule_id"] == VALID_UUID_2

    @pytest.mark.anyio
    async def test_invalid_notification_type(self, tools):
        with pytest.raises(InputValidationError, match="notification_type"):
            await tools["create_notification"](
                notification_type="invalid_type",
                scheduled_at="2026-04-14T09:00:00Z",
                target_entity_type="habit",
                target_entity_id=VALID_UUID,
                message="test",
                scheduled_by="claude",
            )

    @pytest.mark.anyio
    async def test_invalid_scheduled_by(self, tools):
        with pytest.raises(InputValidationError, match="scheduled_by"):
            await tools["create_notification"](
                notification_type="habit_nudge",
                scheduled_at="2026-04-14T09:00:00Z",
                target_entity_type="habit",
                target_entity_id=VALID_UUID,
                message="test",
                scheduled_by="user",
            )

    @pytest.mark.anyio
    async def test_invalid_target_entity_type(self, tools):
        with pytest.raises(InputValidationError, match="target_entity_type"):
            await tools["create_notification"](
                notification_type="habit_nudge",
                scheduled_at="2026-04-14T09:00:00Z",
                target_entity_type="widget",
                target_entity_id=VALID_UUID,
                message="test",
                scheduled_by="claude",
            )

    @pytest.mark.anyio
    async def test_invalid_uuid(self, tools):
        with pytest.raises(InputValidationError, match="target_entity_id"):
            await tools["create_notification"](
                notification_type="habit_nudge",
                scheduled_at="2026-04-14T09:00:00Z",
                target_entity_type="habit",
                target_entity_id="not-a-uuid",
                message="test",
                scheduled_by="claude",
            )

    @pytest.mark.anyio
    async def test_missing_required_message(self, tools):
        with pytest.raises(InputValidationError, match="message"):
            await tools["create_notification"](
                notification_type="habit_nudge",
                scheduled_at="2026-04-14T09:00:00Z",
                target_entity_type="habit",
                target_entity_id=VALID_UUID,
                message="",
                scheduled_by="claude",
            )

    @pytest.mark.anyio
    async def test_message_too_long(self, tools):
        with pytest.raises(InputValidationError, match="2000"):
            await tools["create_notification"](
                notification_type="habit_nudge",
                scheduled_at="2026-04-14T09:00:00Z",
                target_entity_type="habit",
                target_entity_id=VALID_UUID,
                message="x" * 2001,
                scheduled_by="claude",
            )


# ---------------------------------------------------------------------------
# get_notification
# ---------------------------------------------------------------------------

class TestGetNotification:

    @pytest.mark.anyio
    async def test_happy_path(self, tools, api):
        api.get.return_value = {"id": VALID_UUID, "status": "pending"}
        result = await tools["get_notification"](notification_id=VALID_UUID)
        assert result["id"] == VALID_UUID
        api.get.assert_called_once_with(f"/api/notifications/{VALID_UUID}")

    @pytest.mark.anyio
    async def test_invalid_uuid(self, tools):
        with pytest.raises(InputValidationError, match="notification_id"):
            await tools["get_notification"](notification_id="bad")

    @pytest.mark.anyio
    async def test_not_found(self, tools, api):
        api.get.side_effect = make_api_error(404, "Notification not found")
        with pytest.raises(BrainAPIError, match="404"):
            await tools["get_notification"](notification_id=VALID_UUID)


# ---------------------------------------------------------------------------
# list_notifications
# ---------------------------------------------------------------------------

class TestListNotifications:

    @pytest.mark.anyio
    async def test_no_filters_empty_envelope(self, tools, api):
        api.get.return_value = {"items": [], "count": 0}
        result = await tools["list_notifications"]()
        assert result == {"items": [], "count": 0}
        assert result["items"] == []
        assert result["count"] == 0
        api.get.assert_called_once_with("/api/notifications/", params=None)

    @pytest.mark.anyio
    async def test_envelope_items_passed_through(self, tools, api):
        api.get.return_value = {
            "items": [
                {"id": VALID_UUID, "status": "pending"},
                {"id": VALID_UUID_2, "status": "delivered"},
            ],
            "count": 2,
        }
        result = await tools["list_notifications"]()
        assert result["count"] == 2
        assert len(result["items"]) == 2
        assert result["items"][0]["status"] == "pending"

    @pytest.mark.anyio
    async def test_all_filters(self, tools, api):
        api.get.return_value = {"items": [{"id": VALID_UUID}], "count": 1}
        result = await tools["list_notifications"](
            notification_type="habit_nudge",
            status="pending",
            delivery_type="notification",
            target_entity_type="habit",
            target_entity_id=VALID_UUID,
            scheduled_by="claude",
            scheduled_after="2026-04-01T00:00:00Z",
            scheduled_before="2026-04-30T00:00:00Z",
            has_response=False,
            rule_id=VALID_UUID_2,
        )
        assert result["count"] == 1
        assert result["items"][0]["id"] == VALID_UUID
        call_params = api.get.call_args[1]["params"]
        assert call_params["notification_type"] == "habit_nudge"
        assert call_params["status"] == "pending"
        assert call_params["has_response"] is False
        assert call_params["rule_id"] == VALID_UUID_2

    @pytest.mark.anyio
    async def test_invalid_status_filter(self, tools):
        with pytest.raises(InputValidationError, match="status"):
            await tools["list_notifications"](status="invalid")

    @pytest.mark.anyio
    async def test_invalid_notification_type_filter(self, tools):
        with pytest.raises(InputValidationError, match="notification_type"):
            await tools["list_notifications"](notification_type="bogus")


# ---------------------------------------------------------------------------
# update_notification
# ---------------------------------------------------------------------------

class TestUpdateNotification:

    @pytest.mark.anyio
    async def test_happy_path(self, tools, api):
        api.patch.return_value = {"id": VALID_UUID, "message": "Updated"}
        result = await tools["update_notification"](
            notification_id=VALID_UUID,
            message="Updated",
        )
        assert result["message"] == "Updated"
        call_args = api.patch.call_args
        assert call_args[0][0] == f"/api/notifications/{VALID_UUID}"
        assert call_args[1]["json"]["message"] == "Updated"

    @pytest.mark.anyio
    async def test_status_transition(self, tools, api):
        api.patch.return_value = {"id": VALID_UUID, "status": "delivered"}
        await tools["update_notification"](
            notification_id=VALID_UUID,
            status="delivered",
        )
        body = api.patch.call_args[1]["json"]
        assert body["status"] == "delivered"

    @pytest.mark.anyio
    async def test_invalid_uuid(self, tools):
        with pytest.raises(InputValidationError, match="notification_id"):
            await tools["update_notification"](notification_id="bad")

    @pytest.mark.anyio
    async def test_invalid_status(self, tools):
        with pytest.raises(InputValidationError, match="status"):
            await tools["update_notification"](
                notification_id=VALID_UUID, status="invalid"
            )

    @pytest.mark.anyio
    async def test_message_too_long(self, tools):
        with pytest.raises(InputValidationError, match="2000"):
            await tools["update_notification"](
                notification_id=VALID_UUID, message="x" * 2001
            )

    @pytest.mark.anyio
    async def test_not_found(self, tools, api):
        api.patch.side_effect = make_api_error(404, "Notification not found")
        with pytest.raises(BrainAPIError, match="404"):
            await tools["update_notification"](
                notification_id=VALID_UUID, message="test"
            )


# ---------------------------------------------------------------------------
# delete_notification
# ---------------------------------------------------------------------------

class TestDeleteNotification:

    @pytest.mark.anyio
    async def test_happy_path(self, tools, api):
        api.delete.return_value = {"deleted": True}
        result = await tools["delete_notification"](notification_id=VALID_UUID)
        assert result["deleted"] is True
        api.delete.assert_called_once_with(f"/api/notifications/{VALID_UUID}")

    @pytest.mark.anyio
    async def test_invalid_uuid(self, tools):
        with pytest.raises(InputValidationError, match="notification_id"):
            await tools["delete_notification"](notification_id="bad")

    @pytest.mark.anyio
    async def test_not_found(self, tools, api):
        api.delete.side_effect = make_api_error(404, "Notification not found")
        with pytest.raises(BrainAPIError, match="404"):
            await tools["delete_notification"](notification_id=VALID_UUID)


# ---------------------------------------------------------------------------
# respond_to_notification
# ---------------------------------------------------------------------------

class TestRespondToNotification:

    @pytest.mark.anyio
    async def test_happy_path(self, tools, api):
        api.post.return_value = {
            "id": VALID_UUID, "status": "responded", "response": "done",
        }
        result = await tools["respond_to_notification"](
            notification_id=VALID_UUID,
            response="done",
        )
        assert result["status"] == "responded"
        call_args = api.post.call_args
        assert call_args[0][0] == f"/api/notifications/{VALID_UUID}/respond"
        assert call_args[1]["json"]["response"] == "done"

    @pytest.mark.anyio
    async def test_with_response_note(self, tools, api):
        api.post.return_value = {"id": VALID_UUID, "status": "responded"}
        await tools["respond_to_notification"](
            notification_id=VALID_UUID,
            response="partial",
            response_note="Did two out of three items",
        )
        body = api.post.call_args[1]["json"]
        assert body["response_note"] == "Did two out of three items"

    @pytest.mark.anyio
    async def test_invalid_uuid(self, tools):
        with pytest.raises(InputValidationError, match="notification_id"):
            await tools["respond_to_notification"](
                notification_id="bad", response="done"
            )

    @pytest.mark.anyio
    async def test_missing_response(self, tools):
        with pytest.raises(InputValidationError, match="response"):
            await tools["respond_to_notification"](
                notification_id=VALID_UUID, response=""
            )

    @pytest.mark.anyio
    async def test_409_pending(self, tools, api):
        api.post.side_effect = make_api_error(
            409, "Notification has not been delivered yet"
        )
        with pytest.raises(BrainAPIError, match="409"):
            await tools["respond_to_notification"](
                notification_id=VALID_UUID, response="done"
            )

    @pytest.mark.anyio
    async def test_409_already_responded(self, tools, api):
        api.post.side_effect = make_api_error(
            409, "Notification has already been responded to"
        )
        with pytest.raises(BrainAPIError, match="409"):
            await tools["respond_to_notification"](
                notification_id=VALID_UUID, response="done"
            )

    @pytest.mark.anyio
    async def test_410_expired(self, tools, api):
        api.post.side_effect = make_api_error(
            410, "Notification has expired"
        )
        with pytest.raises(BrainAPIError, match="410"):
            await tools["respond_to_notification"](
                notification_id=VALID_UUID, response="done"
            )

    @pytest.mark.anyio
    async def test_not_found(self, tools, api):
        api.post.side_effect = make_api_error(404, "Notification not found")
        with pytest.raises(BrainAPIError, match="404"):
            await tools["respond_to_notification"](
                notification_id=VALID_UUID, response="done"
            )


# ---------------------------------------------------------------------------
# [MCP-BUG-01] Structured-detail error envelope — regression coverage
# ---------------------------------------------------------------------------

class TestStructuredDetailErrorEnvelope:
    """Tool-level error path receives FastAPI-shaped list-of-dicts detail."""

    @pytest.mark.anyio
    async def test_create_notification_422_list_detail_is_json_parseable(
        self, tools, api,
    ):
        import json

        validation_detail = [
            {
                "type": "missing",
                "loc": ["body", "notification_type"],
                "msg": "Field required",
                "input": {},
            },
        ]
        api.post.side_effect = make_api_error(422, validation_detail)

        with pytest.raises(BrainAPIError) as exc_info:
            await tools["create_notification"](
                notification_type="habit_nudge",
                scheduled_at="2026-04-14T09:00:00Z",
                target_entity_type="habit",
                target_entity_id=VALID_UUID,
                message="Time",
                scheduled_by="claude",
            )

        message = str(exc_info.value)
        assert message.startswith("API error (422): ")
        payload = message.removeprefix("API error (422): ")
        # Full round-trip: message body is valid JSON.
        assert json.loads(payload) == validation_detail
        # Double-quoted keys — distinguishes from Python repr's single quotes.
        assert '"msg"' in message
