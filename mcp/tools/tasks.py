"""Task CRUD and tag tools."""

from validation import (
    validate_enum,
    validate_range,
    validate_required_str,
    validate_uuid,
    COGNITIVE_TYPES,
    TASK_STATUSES,
)
from tools._helpers import params, strip_nones


def register(mcp, api) -> None:
    """Register task tools with the MCP server."""

    @mcp.tool()
    async def create_task(
        title: str,
        project_id: str | None = None,
        description: str | None = None,
        status: str = "pending",
        cognitive_type: str | None = None,
        energy_cost: int | None = None,
        activation_friction: int | None = None,
        context_required: str | None = None,
        due_date: str | None = None,
        recurrence_rule: str | None = None,
    ) -> dict:
        """Create a task, optionally under a project.

        Tasks are the atomic unit of work. They can be standalone or belong to
        a project. ADHD-aware metadata helps match tasks to the user's current
        state.

        Status: pending, active, completed, skipped, deferred.
        Cognitive types: hands_on, communication, decision, errand, admin,
        focus_work.
        Energy cost & activation friction: 1 (low) to 5 (high).
        Due date format: YYYY-MM-DD.
        Recurrence rule: RRULE format (e.g. "FREQ=DAILY").
        """
        validate_required_str(title, "title")
        validate_uuid(project_id, "project_id")
        validate_enum(status, "status", TASK_STATUSES)
        validate_enum(cognitive_type, "cognitive_type", COGNITIVE_TYPES)
        validate_range(energy_cost, "energy_cost")
        validate_range(activation_friction, "activation_friction")
        body = strip_nones({
            "project_id": project_id,
            "title": title,
            "description": description,
            "status": status,
            "cognitive_type": cognitive_type,
            "energy_cost": energy_cost,
            "activation_friction": activation_friction,
            "context_required": context_required,
            "due_date": due_date,
            "recurrence_rule": recurrence_rule,
        })
        return await api.post("/api/tasks/", json=body)

    @mcp.tool()
    async def list_tasks(
        project_id: str | None = None,
        standalone: bool | None = None,
        status: str | None = None,
        cognitive_type: str | None = None,
        energy_cost_min: int | None = None,
        energy_cost_max: int | None = None,
        friction_min: int | None = None,
        friction_max: int | None = None,
        context_required: str | None = None,
        due_before: str | None = None,
        due_after: str | None = None,
        overdue: bool | None = None,
    ) -> list:
        """List tasks with composable filters.

        Use to find tasks matching the user's current energy, context, or
        cognitive capacity. All filter parameters are optional and combine
        with AND logic.

        - standalone=true: only tasks not assigned to a project
        - energy_cost_min/max: filter by energy cost (1-5 scale)
        - friction_min/max: filter by activation friction (1-5 scale)
        - cognitive_type: hands_on, communication, decision, errand, admin,
          focus_work
        - due_before/due_after: date range (YYYY-MM-DD)
        - overdue=true: tasks past due that aren't completed/skipped
        """
        validate_uuid(project_id, "project_id")
        validate_enum(status, "status", TASK_STATUSES)
        validate_enum(cognitive_type, "cognitive_type", COGNITIVE_TYPES)
        validate_range(energy_cost_min, "energy_cost_min")
        validate_range(energy_cost_max, "energy_cost_max")
        validate_range(friction_min, "friction_min")
        validate_range(friction_max, "friction_max")
        return await api.get(
            "/api/tasks/",
            params=params(
                project_id=project_id,
                standalone=standalone,
                status=status,
                cognitive_type=cognitive_type,
                energy_cost_min=energy_cost_min,
                energy_cost_max=energy_cost_max,
                friction_min=friction_min,
                friction_max=friction_max,
                context_required=context_required,
                due_before=due_before,
                due_after=due_after,
                overdue=overdue,
            ),
        )

    @mcp.tool()
    async def get_task(task_id: str) -> dict:
        """Get a task with its tags.

        Returns the full task details including any attached tags. Use this
        to see everything about a specific task.
        """
        validate_uuid(task_id, "task_id")
        return await api.get(f"/api/tasks/{task_id}")

    @mcp.tool()
    async def update_task(
        task_id: str,
        project_id: str | None = None,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
        cognitive_type: str | None = None,
        energy_cost: int | None = None,
        activation_friction: int | None = None,
        context_required: str | None = None,
        due_date: str | None = None,
        recurrence_rule: str | None = None,
    ) -> dict:
        """Update a task's details.

        Only provided fields are changed. Use this to change status (e.g.
        mark as completed), reassign to a project, update energy cost, etc.

        Status: pending, active, completed, skipped, deferred.
        Energy cost & activation friction: 1-5 scale.
        """
        validate_uuid(task_id, "task_id")
        validate_uuid(project_id, "project_id")
        validate_enum(status, "status", TASK_STATUSES)
        validate_enum(cognitive_type, "cognitive_type", COGNITIVE_TYPES)
        validate_range(energy_cost, "energy_cost")
        validate_range(activation_friction, "activation_friction")
        body = strip_nones({
            "project_id": project_id,
            "title": title,
            "description": description,
            "status": status,
            "cognitive_type": cognitive_type,
            "energy_cost": energy_cost,
            "activation_friction": activation_friction,
            "context_required": context_required,
            "due_date": due_date,
            "recurrence_rule": recurrence_rule,
        })
        return await api.patch(f"/api/tasks/{task_id}", json=body)

    @mcp.tool()
    async def delete_task(task_id: str) -> dict:
        """Delete a task permanently.

        Removes the task and its tag associations. Confirm with the user
        before deleting.
        """
        validate_uuid(task_id, "task_id")
        return await api.delete(f"/api/tasks/{task_id}")

    @mcp.tool()
    async def tag_task(task_id: str, tag_id: str) -> dict:
        """Attach a tag to a task.

        This is idempotent — calling it again with the same tag has no effect.
        Use this to categorize tasks for flexible filtering and grouping.
        """
        validate_uuid(task_id, "task_id")
        validate_uuid(tag_id, "tag_id")
        return await api.post(f"/api/tasks/{task_id}/tags/{tag_id}")

    @mcp.tool()
    async def untag_task(task_id: str, tag_id: str) -> dict:
        """Remove a tag from a task."""
        validate_uuid(task_id, "task_id")
        validate_uuid(tag_id, "tag_id")
        return await api.delete(f"/api/tasks/{task_id}/tags/{tag_id}")

    @mcp.tool()
    async def list_task_tags(task_id: str) -> list:
        """List all tags attached to a task."""
        validate_uuid(task_id, "task_id")
        return await api.get(f"/api/tasks/{task_id}/tags")

    @mcp.tool()
    async def list_tagged_tasks(tag_id: str) -> list:
        """List all tasks that have a specific tag.

        Use this to find all tasks in a category (e.g. all "quick-win" tasks).
        """
        validate_uuid(tag_id, "tag_id")
        return await api.get(f"/api/tags/{tag_id}/tasks")
