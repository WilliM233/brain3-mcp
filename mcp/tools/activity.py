"""Activity log CRUD and tag tools."""

from validation import (
    validate_enum,
    validate_range,
    validate_uuid,
    ACTION_TYPES,
)
from tools._helpers import params, strip_nones


def register(mcp, api) -> None:
    """Register activity log tools with the MCP server."""

    @mcp.tool()
    async def log_activity(
        action_type: str,
        task_id: str | None = None,
        routine_id: str | None = None,
        checkin_id: str | None = None,
        notes: str | None = None,
        energy_before: int | None = None,
        energy_after: int | None = None,
        mood_rating: int | None = None,
        friction_actual: int | None = None,
        duration_minutes: int | None = None,
        tag_ids: list[str] | None = None,
    ) -> dict:
        """Create an activity log entry.

        Records what happened and how the user felt. At most one of task_id,
        routine_id, or checkin_id can be provided to link the entry.

        Action types: completed, skipped, deferred, started, reflected,
        checked_in.
        Energy before/after, mood, friction: 1-5 scale.

        Optionally pass tag_ids to tag the entry at creation time, saving
        separate tag_activity calls. Tags are returned in the response.
        """
        validate_enum(action_type, "action_type", ACTION_TYPES)
        validate_uuid(task_id, "task_id")
        validate_uuid(routine_id, "routine_id")
        validate_uuid(checkin_id, "checkin_id")
        validate_range(energy_before, "energy_before")
        validate_range(energy_after, "energy_after")
        validate_range(mood_rating, "mood_rating")
        validate_range(friction_actual, "friction_actual")
        if tag_ids is not None:
            for tid in tag_ids:
                validate_uuid(tid, "tag_ids element")
        body = strip_nones({
            "task_id": task_id,
            "routine_id": routine_id,
            "checkin_id": checkin_id,
            "action_type": action_type,
            "notes": notes,
            "energy_before": energy_before,
            "energy_after": energy_after,
            "mood_rating": mood_rating,
            "friction_actual": friction_actual,
            "duration_minutes": duration_minutes,
            "tag_ids": tag_ids,
        })
        return await api.post("/api/activity/", json=body)

    @mcp.tool()
    async def list_activity(
        action_type: str | None = None,
        task_id: str | None = None,
        routine_id: str | None = None,
        logged_after: str | None = None,
        logged_before: str | None = None,
        has_task: bool | None = None,
        has_routine: bool | None = None,
        tag: str | None = None,
    ) -> list:
        """List activity log entries with optional filters.

        Filter by action type, linked task or routine, date range, or whether
        entries have a task/routine attached. Results are ordered newest first.
        Use this to review what the user has been doing and how they felt.

        The tag parameter accepts comma-separated tag names with AND logic.
        Example: tag="session-handoff" or tag="movie,fluxnook" (entries must
        have ALL listed tags).
        """
        validate_enum(action_type, "action_type", ACTION_TYPES)
        validate_uuid(task_id, "task_id")
        validate_uuid(routine_id, "routine_id")
        return await api.get(
            "/api/activity/",
            params=params(
                action_type=action_type,
                task_id=task_id,
                routine_id=routine_id,
                logged_after=logged_after,
                logged_before=logged_before,
                has_task=has_task,
                has_routine=has_routine,
                tag=tag,
            ),
        )

    @mcp.tool()
    async def get_activity(entry_id: str) -> dict:
        """Get an activity log entry with resolved references.

        Returns the entry with full task, routine, or check-in details
        attached (not just IDs).
        """
        validate_uuid(entry_id, "entry_id")
        return await api.get(f"/api/activity/{entry_id}")

    @mcp.tool()
    async def update_activity(
        entry_id: str,
        task_id: str | None = None,
        routine_id: str | None = None,
        checkin_id: str | None = None,
        action_type: str | None = None,
        notes: str | None = None,
        energy_before: int | None = None,
        energy_after: int | None = None,
        mood_rating: int | None = None,
        friction_actual: int | None = None,
        duration_minutes: int | None = None,
    ) -> dict:
        """Update an activity log entry.

        Only provided fields are changed.
        """
        validate_uuid(entry_id, "entry_id")
        validate_uuid(task_id, "task_id")
        validate_uuid(routine_id, "routine_id")
        validate_uuid(checkin_id, "checkin_id")
        validate_enum(action_type, "action_type", ACTION_TYPES)
        validate_range(energy_before, "energy_before")
        validate_range(energy_after, "energy_after")
        validate_range(mood_rating, "mood_rating")
        validate_range(friction_actual, "friction_actual")
        body = strip_nones({
            "task_id": task_id,
            "routine_id": routine_id,
            "checkin_id": checkin_id,
            "action_type": action_type,
            "notes": notes,
            "energy_before": energy_before,
            "energy_after": energy_after,
            "mood_rating": mood_rating,
            "friction_actual": friction_actual,
            "duration_minutes": duration_minutes,
        })
        return await api.patch(f"/api/activity/{entry_id}", json=body)

    @mcp.tool()
    async def delete_activity(entry_id: str) -> dict:
        """Delete an activity log entry."""
        validate_uuid(entry_id, "entry_id")
        return await api.delete(f"/api/activity/{entry_id}")

    @mcp.tool()
    async def tag_activity(activity_id: str, tag_id: str) -> dict:
        """Attach a tag to an activity log entry.

        This is idempotent — calling it again with the same tag has no effect.
        Use this to categorize activity entries for filtering and discovery
        (e.g. session-handoff notes, media reviews, life logging themes).
        """
        validate_uuid(activity_id, "activity_id")
        validate_uuid(tag_id, "tag_id")
        return await api.post(f"/api/activity/{activity_id}/tags/{tag_id}")

    @mcp.tool()
    async def untag_activity(activity_id: str, tag_id: str) -> dict:
        """Remove a tag from an activity log entry."""
        validate_uuid(activity_id, "activity_id")
        validate_uuid(tag_id, "tag_id")
        return await api.delete(f"/api/activity/{activity_id}/tags/{tag_id}")

    @mcp.tool()
    async def list_activity_tags(activity_id: str) -> list:
        """List all tags attached to an activity log entry."""
        validate_uuid(activity_id, "activity_id")
        return await api.get(f"/api/activity/{activity_id}/tags")

    @mcp.tool()
    async def list_tagged_activities(tag_id: str) -> list:
        """List all activity log entries that have a specific tag.

        Use this to find all activities in a category (e.g. all entries tagged
        "session-handoff" for context recovery, or "fluxnook" for media reviews).
        """
        validate_uuid(tag_id, "tag_id")
        return await api.get(f"/api/tags/{tag_id}/activities")
