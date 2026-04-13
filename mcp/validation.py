"""Pre-request input validation for MCP tool parameters.

Implements CLAUDE.md error tier 3: catch invalid tool parameters before
making the HTTP request. Returns clear messages that help Claude
understand what went wrong and self-correct.
"""

import uuid as _uuid


class InputValidationError(Exception):
    """Raised when an MCP tool receives invalid parameters."""


# ---------------------------------------------------------------------------
# Enum value sets (sourced from brain3 API schema)
# ---------------------------------------------------------------------------

GOAL_STATUSES = {"active", "paused", "achieved", "abandoned"}
PROJECT_STATUSES = {"not_started", "active", "blocked", "completed", "abandoned"}
TASK_STATUSES = {"pending", "active", "completed", "skipped", "deferred"}
COGNITIVE_TYPES = {
    "hands_on", "communication", "decision", "errand", "admin", "focus_work",
}
ROUTINE_FREQUENCIES = {"daily", "weekdays", "weekends", "weekly", "custom"}
ROUTINE_STATUSES = {"active", "paused", "retired"}
HABIT_STATUSES = {"active", "paused", "graduated", "abandoned"}
HABIT_FREQUENCIES = {"daily", "weekdays", "weekends", "weekly", "custom"}
NOTIFICATION_FREQUENCIES = {
    "daily", "every_other_day", "twice_week", "weekly", "graduated", "none",
}
SCAFFOLDING_STATUSES = {"tracking", "accountable", "graduated"}
COMPLETION_STATUSES = {"all_done", "partial", "skipped"}
CHECKIN_TYPES = {"morning", "midday", "evening", "micro", "freeform"}
ACTION_TYPES = {
    "completed", "skipped", "deferred", "started", "reflected", "checked_in",
}
DAYS_OF_WEEK = {
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
}
ARTIFACT_TYPES = {
    "document", "protocol", "brief", "prompt", "template", "journal", "spec",
}
DIRECTIVE_SCOPES = {"global", "skill", "agent"}
NOTIFICATION_TYPES = {
    "habit_nudge", "routine_checklist", "checkin_prompt",
    "time_block_reminder", "deadline_event_alert", "pattern_observation",
    "stale_work_nudge",
}
NOTIFICATION_STATUSES = {"pending", "delivered", "responded", "expired"}
DELIVERY_TYPES = {"notification"}
SCHEDULED_BY_VALUES = {"system", "claude", "rule"}
TARGET_ENTITY_TYPES = {"habit", "routine", "task", "checkin", "goal", "project"}


# ---------------------------------------------------------------------------
# Validators — each is a no-op when value is None (for optional params)
# ---------------------------------------------------------------------------

def validate_uuid(value: str | None, name: str) -> None:
    """Validate that a string is a valid UUID, if provided."""
    if value is None:
        return
    try:
        _uuid.UUID(value)
    except (ValueError, AttributeError):
        raise InputValidationError(
            f"Invalid {name}: '{value}' is not a valid UUID. "
            "Expected format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        )


def validate_enum(
    value: str | None, name: str, allowed: set[str],
) -> None:
    """Validate that a string is one of the allowed values, if provided."""
    if value is None:
        return
    if value not in allowed:
        sorted_values = ", ".join(sorted(allowed))
        raise InputValidationError(
            f"Invalid {name}: '{value}'. Must be one of: {sorted_values}"
        )


def validate_range(
    value: int | None, name: str, min_val: int = 1, max_val: int = 5,
) -> None:
    """Validate that a numeric value is within the expected range, if provided."""
    if value is None:
        return
    if not isinstance(value, int):
        raise InputValidationError(
            f"Invalid {name}: expected an integer, got {type(value).__name__}"
        )
    if value < min_val or value > max_val:
        raise InputValidationError(
            f"Invalid {name}: {value} is out of range. "
            f"Must be between {min_val} and {max_val}."
        )


def validate_required_str(value: str | None, name: str) -> None:
    """Validate that a required string parameter is present and non-empty."""
    if value is None or (isinstance(value, str) and not value.strip()):
        raise InputValidationError(
            f"Missing required parameter: {name}. Must be a non-empty string."
        )
