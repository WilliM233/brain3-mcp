"""Notification queue CRUD and response recording tools."""

from validation import (
    InputValidationError,
    validate_enum,
    validate_uuid,
    validate_required_str,
    NOTIFICATION_TYPES,
    NOTIFICATION_STATUSES,
    DELIVERY_TYPES,
    SCHEDULED_BY_VALUES,
    TARGET_ENTITY_TYPES,
)
from tools._helpers import params, strip_nones


def register(mcp, api) -> None:
    """Register notification queue tools with the MCP server."""

    @mcp.tool()
    async def create_notification(
        notification_type: str,
        scheduled_at: str,
        target_entity_type: str,
        target_entity_id: str,
        message: str,
        scheduled_by: str,
        delivery_type: str = "notification",
        canned_responses: list[str] | None = None,
        expires_at: str | None = None,
        rule_id: str | None = None,
    ) -> dict:
        """Schedule a notification for delivery to the user.

        This is how you write to the notification queue during sessions.
        Use this to nudge the user about habits, remind them of routines,
        prompt check-ins, flag upcoming deadlines, or share pattern
        observations.

        notification_type controls default canned_responses and expiry
        windows — omit canned_responses to use the type's defaults.

        scheduled_by should be "claude" when you create notifications
        directly, "system" for automated processes, or "rule" when
        triggered by a notification rule (pair with rule_id).

        Types: habit_nudge, routine_checklist, checkin_prompt,
        time_block_reminder, deadline_event_alert, pattern_observation,
        stale_work_nudge.
        """
        validate_required_str(notification_type, "notification_type")
        validate_required_str(scheduled_at, "scheduled_at")
        validate_required_str(target_entity_type, "target_entity_type")
        validate_required_str(target_entity_id, "target_entity_id")
        validate_required_str(message, "message")
        validate_required_str(scheduled_by, "scheduled_by")
        validate_enum(notification_type, "notification_type", NOTIFICATION_TYPES)
        validate_enum(delivery_type, "delivery_type", DELIVERY_TYPES)
        validate_enum(scheduled_by, "scheduled_by", SCHEDULED_BY_VALUES)
        validate_enum(target_entity_type, "target_entity_type", TARGET_ENTITY_TYPES)
        validate_uuid(target_entity_id, "target_entity_id")
        validate_uuid(rule_id, "rule_id")
        if len(message) > 2000:
            raise InputValidationError(
                "Invalid message: exceeds 2000 character limit."
            )
        body = strip_nones({
            "notification_type": notification_type,
            "scheduled_at": scheduled_at,
            "target_entity_type": target_entity_type,
            "target_entity_id": target_entity_id,
            "message": message,
            "scheduled_by": scheduled_by,
            "delivery_type": delivery_type,
            "canned_responses": canned_responses,
            "expires_at": expires_at,
            "rule_id": rule_id,
        })
        return await api.post("/api/notifications/", json=body)

    @mcp.tool()
    async def get_notification(notification_id: str) -> dict:
        """Retrieve a specific notification by ID.

        Returns the full notification including status, message,
        canned_responses, response (if any), and timestamps. Use this
        to check whether a notification has been delivered or responded to.
        """
        validate_uuid(notification_id, "notification_id")
        return await api.get(f"/api/notifications/{notification_id}")

    @mcp.tool()
    async def list_notifications(
        notification_type: str | None = None,
        status: str | None = None,
        delivery_type: str | None = None,
        target_entity_type: str | None = None,
        target_entity_id: str | None = None,
        scheduled_by: str | None = None,
        scheduled_after: str | None = None,
        scheduled_before: str | None = None,
        has_response: bool | None = None,
        rule_id: str | None = None,
    ) -> list:
        """Browse notifications with composable filters.

        All filter parameters are optional and combine with AND logic.
        Results are ordered by scheduled_at descending (newest first).

        Common patterns:
        - Pending queue: status="pending"
        - Delivered but unanswered: status="delivered"
        - Silence tracking: has_response=false with a scheduled_after window
        - By origin: scheduled_by="claude" or scheduled_by="rule"
        - By target: target_entity_type + target_entity_id
        """
        validate_enum(notification_type, "notification_type", NOTIFICATION_TYPES)
        validate_enum(status, "status", NOTIFICATION_STATUSES)
        validate_enum(delivery_type, "delivery_type", DELIVERY_TYPES)
        validate_enum(target_entity_type, "target_entity_type", TARGET_ENTITY_TYPES)
        validate_uuid(target_entity_id, "target_entity_id")
        validate_enum(scheduled_by, "scheduled_by", SCHEDULED_BY_VALUES)
        validate_uuid(rule_id, "rule_id")
        return await api.get(
            "/api/notifications/",
            params=params(
                notification_type=notification_type,
                status=status,
                delivery_type=delivery_type,
                target_entity_type=target_entity_type,
                target_entity_id=target_entity_id,
                scheduled_by=scheduled_by,
                scheduled_after=scheduled_after,
                scheduled_before=scheduled_before,
                has_response=has_response,
                rule_id=rule_id,
            ),
        )

    @mcp.tool()
    async def update_notification(
        notification_id: str,
        scheduled_at: str | None = None,
        message: str | None = None,
        canned_responses: list[str] | None = None,
        expires_at: str | None = None,
        status: str | None = None,
    ) -> dict:
        """Modify a notification's mutable fields.

        Only provided fields are changed. Status transitions follow a
        state machine: pending -> delivered -> responded, and
        pending/delivered -> expired. The API rejects invalid transitions.

        Immutable fields (notification_type, target_entity_type,
        target_entity_id, scheduled_by, response, responded_at) cannot
        be changed — delete and recreate instead.

        Use this to reschedule a pending notification, update its message,
        or transition its status (e.g., mark as delivered).
        """
        validate_uuid(notification_id, "notification_id")
        validate_enum(status, "status", NOTIFICATION_STATUSES)
        if message is not None and len(message) > 2000:
            raise InputValidationError(
                "Invalid message: exceeds 2000 character limit."
            )
        body = strip_nones({
            "scheduled_at": scheduled_at,
            "message": message,
            "canned_responses": canned_responses,
            "expires_at": expires_at,
            "status": status,
        })
        return await api.patch(
            f"/api/notifications/{notification_id}", json=body
        )

    @mcp.tool()
    async def delete_notification(notification_id: str) -> dict:
        """Remove a notification from the queue permanently.

        Use this to cancel a pending notification that is no longer
        relevant, or to clean up expired/responded notifications.
        Confirm with the user before deleting.
        """
        validate_uuid(notification_id, "notification_id")
        return await api.delete(f"/api/notifications/{notification_id}")

    @mcp.tool()
    async def respond_to_notification(
        notification_id: str,
        response: str,
        response_note: str | None = None,
    ) -> dict:
        """Record a user response to a delivered notification.

        The notification must be in "delivered" status. Responding to a
        pending notification returns 409, responding to an already-responded
        notification returns 409, and responding to an expired notification
        returns 410.

        The response must match one of the notification's canned_responses
        or be "partial". Use response_note for freeform context from the
        user (up to 1000 chars).

        This closes the feedback loop — the response data feeds into
        pattern analysis and future notification tuning.
        """
        validate_uuid(notification_id, "notification_id")
        validate_required_str(response, "response")
        body = strip_nones({
            "response": response,
            "response_note": response_note,
        })
        return await api.post(
            f"/api/notifications/{notification_id}/respond", json=body
        )
