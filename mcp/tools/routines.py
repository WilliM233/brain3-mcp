"""Routine CRUD, schedule, and completion tools."""

from validation import (
    validate_enum,
    validate_range,
    validate_required_str,
    validate_uuid,
    COMPLETION_STATUSES,
    DAYS_OF_WEEK,
    ROUTINE_FREQUENCIES,
    ROUTINE_STATUSES,
)
from tools._helpers import params, strip_nones


def register(mcp, api) -> None:
    """Register routine tools with the MCP server."""

    @mcp.tool()
    async def create_routine(
        domain_id: str,
        title: str,
        frequency: str,
        description: str | None = None,
        status: str = "active",
        energy_cost: int | None = None,
        activation_friction: int | None = None,
    ) -> dict:
        """Create a routine tied to a domain.

        Routines are recurring behaviors the user wants to build or maintain
        (e.g. "Morning meditation" under Health). Frequency options: daily,
        weekdays, weekends, weekly, custom.
        Energy cost & activation friction: 1-5 scale.
        Status: active, paused, retired.
        """
        validate_uuid(domain_id, "domain_id")
        validate_required_str(title, "title")
        validate_enum(frequency, "frequency", ROUTINE_FREQUENCIES)
        validate_enum(status, "status", ROUTINE_STATUSES)
        validate_range(energy_cost, "energy_cost")
        validate_range(activation_friction, "activation_friction")
        body = strip_nones({
            "domain_id": domain_id,
            "title": title,
            "description": description,
            "frequency": frequency,
            "status": status,
            "energy_cost": energy_cost,
            "activation_friction": activation_friction,
        })
        return await api.post("/api/routines/", json=body)

    @mcp.tool()
    async def list_routines(
        domain_id: str | None = None,
        status: str | None = None,
        frequency: str | None = None,
        streak_broken: bool | None = None,
    ) -> dict:
        """List routines with optional filters.

        Filter by domain, status (active, paused, retired), frequency,
        or streak_broken=true to find active routines that have lost their
        streak. All filters combine with AND logic.

        Returns a `RoutineListResponse` envelope: ``{"items": [...], "count": N}``.
        ``items`` is the routine list; ``count`` is the total matching the filters.
        """
        validate_uuid(domain_id, "domain_id")
        validate_enum(status, "status", ROUTINE_STATUSES)
        validate_enum(frequency, "frequency", ROUTINE_FREQUENCIES)
        return await api.get(
            "/api/routines/",
            params=params(
                domain_id=domain_id,
                status=status,
                frequency=frequency,
                streak_broken=streak_broken,
            ),
        )

    @mcp.tool()
    async def get_routine(routine_id: str) -> dict:
        """Get a routine with its schedules.

        Returns the routine details including current streak, best streak,
        last completion date, and all schedule entries.
        """
        validate_uuid(routine_id, "routine_id")
        return await api.get(f"/api/routines/{routine_id}")

    @mcp.tool()
    async def update_routine(
        routine_id: str,
        domain_id: str | None = None,
        title: str | None = None,
        description: str | None = None,
        frequency: str | None = None,
        status: str | None = None,
        energy_cost: int | None = None,
        activation_friction: int | None = None,
    ) -> dict:
        """Update a routine's details.

        Only provided fields are changed. Use this to pause/retire a routine,
        change its frequency, or update energy/friction ratings.
        """
        validate_uuid(routine_id, "routine_id")
        validate_uuid(domain_id, "domain_id")
        validate_enum(frequency, "frequency", ROUTINE_FREQUENCIES)
        validate_enum(status, "status", ROUTINE_STATUSES)
        validate_range(energy_cost, "energy_cost")
        validate_range(activation_friction, "activation_friction")
        body = strip_nones({
            "domain_id": domain_id,
            "title": title,
            "description": description,
            "frequency": frequency,
            "status": status,
            "energy_cost": energy_cost,
            "activation_friction": activation_friction,
        })
        return await api.patch(f"/api/routines/{routine_id}", json=body)

    @mcp.tool()
    async def delete_routine(routine_id: str) -> dict:
        """Delete a routine permanently.

        Removes the routine, its schedules, and completion history.
        Confirm with the user before deleting.
        """
        validate_uuid(routine_id, "routine_id")
        return await api.delete(f"/api/routines/{routine_id}")

    @mcp.tool()
    async def complete_routine(
        routine_id: str,
        completed_date: str | None = None,
        status: str = "all_done",
        freeform_note: str | None = None,
    ) -> dict:
        """Record a routine completion and evaluate the streak.

        Call this when the user completes a routine. Returns updated streak
        info including whether the streak was broken and recovered.

        Three completion modes:
        - all_done (default): routine fully completed.
        - partial: routine partially completed — use freeform_note to
          explain what was done.
        - skipped: routine intentionally skipped — use freeform_note to
          capture why.

        If completed_date is omitted, today's date is used.
        Date format: YYYY-MM-DD.
        """
        validate_uuid(routine_id, "routine_id")
        validate_enum(status, "status", COMPLETION_STATUSES)
        body = strip_nones({
            "completed_date": completed_date,
            "status": status,
            "freeform_note": freeform_note,
        })
        return await api.post(
            f"/api/routines/{routine_id}/complete", json=body or None
        )

    @mcp.tool()
    async def add_routine_schedule(
        routine_id: str,
        day_of_week: str,
        time_of_day: str,
        preferred_window: str | None = None,
    ) -> dict:
        """Add a schedule entry to a routine.

        Defines when a routine should happen. day_of_week: monday through
        sunday. time_of_day: 24h format (e.g. "08:30"). preferred_window:
        optional label like "morning", "afternoon", "evening".
        """
        validate_uuid(routine_id, "routine_id")
        validate_enum(day_of_week, "day_of_week", DAYS_OF_WEEK)
        validate_required_str(time_of_day, "time_of_day")
        body = strip_nones({
            "day_of_week": day_of_week,
            "time_of_day": time_of_day,
            "preferred_window": preferred_window,
        })
        return await api.post(
            f"/api/routines/{routine_id}/schedules", json=body
        )

    @mcp.tool()
    async def list_routine_schedules(routine_id: str) -> list:
        """List all schedule entries for a routine."""
        validate_uuid(routine_id, "routine_id")
        return await api.get(f"/api/routines/{routine_id}/schedules")

    @mcp.tool()
    async def delete_routine_schedule(
        routine_id: str, schedule_id: str
    ) -> dict:
        """Remove a schedule entry from a routine."""
        validate_uuid(routine_id, "routine_id")
        validate_uuid(schedule_id, "schedule_id")
        return await api.delete(
            f"/api/routines/{routine_id}/schedules/{schedule_id}"
        )
