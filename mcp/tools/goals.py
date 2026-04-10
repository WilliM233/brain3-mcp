"""Goal CRUD tools."""

from validation import (
    validate_enum,
    validate_required_str,
    validate_uuid,
    GOAL_STATUSES,
)
from tools._helpers import params, strip_nones


def register(mcp, api) -> None:
    """Register goal tools with the MCP server."""

    @mcp.tool()
    async def create_goal(
        domain_id: str,
        title: str,
        description: str | None = None,
        status: str = "active",
    ) -> dict:
        """Create a goal under a domain.

        Goals are enduring outcomes tied to a life domain (e.g. "Lose 20 lbs"
        under Health). Status options: active, paused, achieved, abandoned.
        """
        validate_uuid(domain_id, "domain_id")
        validate_required_str(title, "title")
        validate_enum(status, "status", GOAL_STATUSES)
        body = strip_nones({
            "domain_id": domain_id,
            "title": title,
            "description": description,
            "status": status,
        })
        return await api.post("/api/goals/", json=body)

    @mcp.tool()
    async def list_goals(
        domain_id: str | None = None,
        status: str | None = None,
    ) -> list:
        """List goals with optional filters.

        Filter by domain_id to see goals in one life area, or by status
        (active, paused, achieved, abandoned). Combine filters with AND logic.
        Use this to find goal IDs for creating projects.
        """
        validate_uuid(domain_id, "domain_id")
        validate_enum(status, "status", GOAL_STATUSES)
        return await api.get(
            "/api/goals/", params=params(domain_id=domain_id, status=status)
        )

    @mcp.tool()
    async def get_goal(goal_id: str) -> dict:
        """Get a goal with its nested projects.

        Returns the goal details and all projects underneath it. Use this to
        see the full breakdown of work under a goal.
        """
        validate_uuid(goal_id, "goal_id")
        return await api.get(f"/api/goals/{goal_id}")

    @mcp.tool()
    async def update_goal(
        goal_id: str,
        domain_id: str | None = None,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> dict:
        """Update a goal's details.

        Only provided fields are changed. Use this to change status (e.g.
        mark as achieved), move to a different domain, or update the title.
        Status options: active, paused, achieved, abandoned.
        """
        validate_uuid(goal_id, "goal_id")
        validate_uuid(domain_id, "domain_id")
        validate_enum(status, "status", GOAL_STATUSES)
        body = strip_nones({
            "domain_id": domain_id,
            "title": title,
            "description": description,
            "status": status,
        })
        return await api.patch(f"/api/goals/{goal_id}", json=body)

    @mcp.tool()
    async def delete_goal(goal_id: str) -> dict:
        """Delete a goal and cascade to its projects.

        Permanently removes the goal. Confirm with the user before deleting.
        """
        validate_uuid(goal_id, "goal_id")
        return await api.delete(f"/api/goals/{goal_id}")
