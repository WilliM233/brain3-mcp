"""Check-in CRUD tools."""

from validation import (
    validate_enum,
    validate_range,
    validate_uuid,
    CHECKIN_TYPES,
)
from tools._helpers import params, strip_nones


def register(mcp, api) -> None:
    """Register check-in tools with the MCP server."""

    @mcp.tool()
    async def create_checkin(
        checkin_type: str,
        energy_level: int | None = None,
        mood: int | None = None,
        focus_level: int | None = None,
        freeform_note: str | None = None,
        context: str | None = None,
    ) -> dict:
        """Log a state check-in.

        Check-ins capture the user's current energy, mood, and focus. Use
        these to understand capacity before suggesting tasks.

        Types: morning, midday, evening, micro, freeform.
        Energy, mood, focus: 1 (low) to 5 (high).
        Context: optional label for where/what the user is doing.
        """
        validate_enum(checkin_type, "checkin_type", CHECKIN_TYPES)
        validate_range(energy_level, "energy_level")
        validate_range(mood, "mood")
        validate_range(focus_level, "focus_level")
        body = strip_nones({
            "checkin_type": checkin_type,
            "energy_level": energy_level,
            "mood": mood,
            "focus_level": focus_level,
            "freeform_note": freeform_note,
            "context": context,
        })
        return await api.post("/api/checkins/", json=body)

    @mcp.tool()
    async def list_checkins(
        checkin_type: str | None = None,
        context: str | None = None,
        logged_after: str | None = None,
        logged_before: str | None = None,
    ) -> list:
        """List check-ins with optional filters.

        Filter by type (morning, midday, evening, micro, freeform), context,
        or date range (ISO datetime format). Use this to review the user's
        state history and identify patterns.
        """
        validate_enum(checkin_type, "checkin_type", CHECKIN_TYPES)
        return await api.get(
            "/api/checkins/",
            params=params(
                checkin_type=checkin_type,
                context=context,
                logged_after=logged_after,
                logged_before=logged_before,
            ),
        )

    @mcp.tool()
    async def get_checkin(checkin_id: str) -> dict:
        """Get a single check-in by ID."""
        validate_uuid(checkin_id, "checkin_id")
        return await api.get(f"/api/checkins/{checkin_id}")

    @mcp.tool()
    async def update_checkin(
        checkin_id: str,
        checkin_type: str | None = None,
        energy_level: int | None = None,
        mood: int | None = None,
        focus_level: int | None = None,
        freeform_note: str | None = None,
        context: str | None = None,
    ) -> dict:
        """Update a check-in's details.

        Only provided fields are changed.
        """
        validate_uuid(checkin_id, "checkin_id")
        validate_enum(checkin_type, "checkin_type", CHECKIN_TYPES)
        validate_range(energy_level, "energy_level")
        validate_range(mood, "mood")
        validate_range(focus_level, "focus_level")
        body = strip_nones({
            "checkin_type": checkin_type,
            "energy_level": energy_level,
            "mood": mood,
            "focus_level": focus_level,
            "freeform_note": freeform_note,
            "context": context,
        })
        return await api.patch(f"/api/checkins/{checkin_id}", json=body)

    @mcp.tool()
    async def delete_checkin(checkin_id: str) -> dict:
        """Delete a check-in."""
        validate_uuid(checkin_id, "checkin_id")
        return await api.delete(f"/api/checkins/{checkin_id}")
