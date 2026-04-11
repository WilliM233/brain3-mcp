"""Project CRUD tools."""

from validation import (
    validate_enum,
    validate_required_str,
    validate_uuid,
    PROJECT_STATUSES,
)
from tools._helpers import params, strip_nones


def register(mcp, api) -> None:
    """Register project tools with the MCP server."""

    @mcp.tool()
    async def create_project(
        goal_id: str,
        title: str,
        description: str | None = None,
        status: str = "not_started",
        deadline: str | None = None,
    ) -> dict:
        """Create a project under a goal.

        Projects are bounded initiatives with a clear finish line (e.g.
        "Complete C25K program" under a fitness goal). Status options:
        not_started, active, blocked, completed, abandoned.
        Deadline format: YYYY-MM-DD.
        """
        validate_uuid(goal_id, "goal_id")
        validate_required_str(title, "title")
        validate_enum(status, "status", PROJECT_STATUSES)
        body = strip_nones({
            "goal_id": goal_id,
            "title": title,
            "description": description,
            "status": status,
            "deadline": deadline,
        })
        return await api.post("/api/projects/", json=body)

    @mcp.tool()
    async def list_projects(
        goal_id: str | None = None,
        status: str | None = None,
        has_deadline: bool | None = None,
        overdue: bool | None = None,
    ) -> list:
        """List projects with optional filters.

        Filter by goal_id, status (not_started, active, blocked, completed,
        abandoned), whether they have a deadline, or whether they're overdue.
        All filters combine with AND logic.
        """
        validate_uuid(goal_id, "goal_id")
        validate_enum(status, "status", PROJECT_STATUSES)
        return await api.get(
            "/api/projects/",
            params=params(
                goal_id=goal_id,
                status=status,
                has_deadline=has_deadline,
                overdue=overdue,
            ),
        )

    @mcp.tool()
    async def get_project(project_id: str) -> dict:
        """Get a project with its nested tasks.

        Returns the project details, progress percentage, and all tasks
        underneath it. Use this to see the full task breakdown.
        """
        validate_uuid(project_id, "project_id")
        return await api.get(f"/api/projects/{project_id}")

    @mcp.tool()
    async def update_project(
        project_id: str,
        goal_id: str | None = None,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
        deadline: str | None = None,
    ) -> dict:
        """Update a project's details.

        Only provided fields are changed. Use this to change status, move to
        a different goal, update the deadline, etc. Status options: not_started,
        active, blocked, completed, abandoned. Deadline format: YYYY-MM-DD.
        """
        validate_uuid(project_id, "project_id")
        validate_uuid(goal_id, "goal_id")
        validate_enum(status, "status", PROJECT_STATUSES)
        body = strip_nones({
            "goal_id": goal_id,
            "title": title,
            "description": description,
            "status": status,
            "deadline": deadline,
        })
        return await api.patch(f"/api/projects/{project_id}", json=body)

    @mcp.tool()
    async def delete_project(project_id: str) -> dict:
        """Delete a project and cascade to its tasks.

        Permanently removes the project. Confirm with the user before deleting.
        """
        validate_uuid(project_id, "project_id")
        return await api.delete(f"/api/projects/{project_id}")
