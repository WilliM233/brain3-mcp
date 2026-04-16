"""Habit CRUD and completion tools."""

from validation import (
    InputValidationError,
    validate_enum,
    validate_range,
    validate_uuid,
    validate_required_str,
    HABIT_STATUSES,
    HABIT_FREQUENCIES,
    NOTIFICATION_FREQUENCIES,
    SCAFFOLDING_STATUSES,
)
from tools._helpers import params, strip_nones


def register(mcp, api) -> None:
    """Register habit tools with the MCP server."""

    @mcp.tool()
    async def create_habit(
        title: str,
        routine_id: str | None = None,
        description: str | None = None,
        status: str = "active",
        frequency: str | None = None,
        notification_frequency: str = "none",
        scaffolding_status: str = "tracking",
        introduced_at: str | None = None,
        graduation_window: int | None = None,
        graduation_target: float | None = None,
        graduation_threshold: int | None = None,
        friction_score: int | None = None,
    ) -> dict:
        """Create a new habit, standalone or under a routine.

        Habits are specific behaviors the user is building. Standalone habits
        require a frequency (daily, weekdays, weekends, weekly, custom).
        Routine-linked habits inherit frequency from their parent routine.

        Scaffolding starts at "tracking" — the user just logs completions.
        Later stages add accountability and graduation criteria.

        friction_score (1–5) captures how hard this habit feels to the user
        and drives graduation defaults: higher friction = longer window and
        more lenient targets.
        """
        validate_required_str(title, "title")
        validate_uuid(routine_id, "routine_id")
        validate_enum(status, "status", HABIT_STATUSES)
        validate_enum(frequency, "frequency", HABIT_FREQUENCIES)
        validate_enum(notification_frequency, "notification_frequency", NOTIFICATION_FREQUENCIES)
        validate_enum(scaffolding_status, "scaffolding_status", SCAFFOLDING_STATUSES)
        validate_range(friction_score, "friction_score", 1, 5)
        if routine_id is None and frequency is None:
            raise InputValidationError(
                "Missing required parameter: frequency. "
                "Standalone habits (no routine_id) must specify a frequency."
            )
        if graduation_target is not None and not (0.0 <= graduation_target <= 1.0):
            raise InputValidationError(
                f"Invalid graduation_target: {graduation_target}. "
                "Must be between 0.0 and 1.0."
            )
        body = strip_nones({
            "title": title,
            "routine_id": routine_id,
            "description": description,
            "status": status,
            "frequency": frequency,
            "notification_frequency": notification_frequency,
            "scaffolding_status": scaffolding_status,
            "introduced_at": introduced_at,
            "graduation_window": graduation_window,
            "graduation_target": graduation_target,
            "graduation_threshold": graduation_threshold,
            "friction_score": friction_score,
        })
        return await api.post("/api/habits/", json=body)

    @mcp.tool()
    async def get_habit(habit_id: str) -> dict:
        """Get a habit with its parent routine info.

        Returns habit details including scaffolding status, completion stats,
        and the parent routine (if linked). Use this to check on a specific
        habit's progress or configuration.
        """
        validate_uuid(habit_id, "habit_id")
        return await api.get(f"/api/habits/{habit_id}")

    @mcp.tool()
    async def list_habits(
        routine_id: str | None = None,
        status: str | None = None,
        scaffolding_status: str | None = None,
    ) -> list:
        """List habits with optional filters.

        Use this to see what habits the user is building, check on scaffolding
        progress, or find habits linked to a specific routine. All filters
        combine with AND logic.
        """
        validate_uuid(routine_id, "routine_id")
        validate_enum(status, "status", HABIT_STATUSES)
        validate_enum(scaffolding_status, "scaffolding_status", SCAFFOLDING_STATUSES)
        return await api.get(
            "/api/habits/",
            params=params(
                routine_id=routine_id,
                status=status,
                scaffolding_status=scaffolding_status,
            ),
        )

    @mcp.tool()
    async def update_habit(
        habit_id: str,
        title: str | None = None,
        routine_id: str | None = None,
        description: str | None = None,
        status: str | None = None,
        frequency: str | None = None,
        notification_frequency: str | None = None,
        scaffolding_status: str | None = None,
        introduced_at: str | None = None,
        graduation_window: int | None = None,
        graduation_target: float | None = None,
        graduation_threshold: int | None = None,
        friction_score: int | None = None,
    ) -> dict:
        """Update a habit's details.

        Only provided fields are changed. Use this to advance scaffolding
        status, pause/resume a habit, adjust graduation criteria, or change
        notification frequency.

        friction_score (1–5) captures how hard this habit feels to the user
        and drives graduation defaults: higher friction = longer window and
        more lenient targets.
        """
        validate_uuid(habit_id, "habit_id")
        validate_uuid(routine_id, "routine_id")
        validate_enum(status, "status", HABIT_STATUSES)
        validate_enum(frequency, "frequency", HABIT_FREQUENCIES)
        validate_enum(notification_frequency, "notification_frequency", NOTIFICATION_FREQUENCIES)
        validate_enum(scaffolding_status, "scaffolding_status", SCAFFOLDING_STATUSES)
        validate_range(friction_score, "friction_score", 1, 5)
        if graduation_target is not None and not (0.0 <= graduation_target <= 1.0):
            raise InputValidationError(
                f"Invalid graduation_target: {graduation_target}. "
                "Must be between 0.0 and 1.0."
            )
        body = strip_nones({
            "title": title,
            "routine_id": routine_id,
            "description": description,
            "status": status,
            "frequency": frequency,
            "notification_frequency": notification_frequency,
            "scaffolding_status": scaffolding_status,
            "introduced_at": introduced_at,
            "graduation_window": graduation_window,
            "graduation_target": graduation_target,
            "graduation_threshold": graduation_threshold,
            "friction_score": friction_score,
        })
        return await api.patch(f"/api/habits/{habit_id}", json=body)

    @mcp.tool()
    async def delete_habit(habit_id: str) -> dict:
        """Delete a habit permanently.

        Removes the habit and its completion history. Confirm with the user
        before deleting.
        """
        validate_uuid(habit_id, "habit_id")
        return await api.delete(f"/api/habits/{habit_id}")

    @mcp.tool()
    async def complete_habit(
        habit_id: str,
        completed_date: str | None = None,
        notes: str | None = None,
    ) -> dict:
        """Record an individual habit completion.

        Idempotent — completing the same habit on the same date returns the
        existing record. Only active habits can be completed. Does NOT
        auto-complete the parent routine.

        If completed_date is omitted, today's date is used.
        Date format: YYYY-MM-DD.
        """
        validate_uuid(habit_id, "habit_id")
        body = strip_nones({
            "completed_date": completed_date,
            "notes": notes,
        })
        return await api.post(
            f"/api/habits/{habit_id}/complete", json=body or None
        )
