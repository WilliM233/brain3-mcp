"""BRAIN 3.0 MCP Server.

Exposes every BRAIN 3.0 API endpoint as an MCP tool that Claude can call.
Runs via stdio transport as a subprocess of the Claude client.
"""

import os

from mcp.server.fastmcp import FastMCP

from client import BrainAPIClient, BrainAPIError
from validation import (
    InputValidationError,
    validate_enum,
    validate_range,
    validate_required_str,
    validate_uuid,
    ACTION_TYPES,
    CHECKIN_TYPES,
    COGNITIVE_TYPES,
    DAYS_OF_WEEK,
    GOAL_STATUSES,
    PROJECT_STATUSES,
    ROUTINE_FREQUENCIES,
    ROUTINE_STATUSES,
    TASK_STATUSES,
)

mcp = FastMCP("BRAIN 3.0")
api = BrainAPIClient()


def _strip_nones(d: dict) -> dict:
    """Remove keys with None values so PATCH only sends provided fields."""
    return {k: v for k, v in d.items() if v is not None}


def _params(**kwargs: object) -> dict | None:
    """Build query params dict, dropping None values. Returns None if empty."""
    filtered = {k: v for k, v in kwargs.items() if v is not None}
    return filtered or None


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------


@mcp.tool()
async def health_check() -> dict:
    """Check BRAIN 3.0 API connectivity.

    Use this first to verify the API is running and the database is connected.
    Returns status and database connection state.
    """
    return await api.get("/health")


# ---------------------------------------------------------------------------
# Domain Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def create_domain(
    name: str,
    description: str | None = None,
    color: str | None = None,
    sort_order: int = 0,
) -> dict:
    """Create a new life domain.

    Domains are top-level categories that organize goals (e.g. Health,
    Finances, Career, Relationships). Use this when the user wants to
    establish a new area of focus in their life.
    """
    validate_required_str(name, "name")
    body = _strip_nones({
        "name": name,
        "description": description,
        "color": color,
        "sort_order": sort_order,
    })
    return await api.post("/api/domains/", json=body)


@mcp.tool()
async def list_domains() -> list:
    """List all life domains.

    Returns every domain sorted by sort_order then name. Use this to see
    what areas of life are being tracked, or to find a domain_id for
    creating goals.
    """
    return await api.get("/api/domains/")


@mcp.tool()
async def get_domain(domain_id: str) -> dict:
    """Get a domain with its nested goals.

    Use this to see the full picture of a life domain — its details and
    all goals underneath it. The domain_id should be a UUID.
    """
    validate_uuid(domain_id, "domain_id")
    return await api.get(f"/api/domains/{domain_id}")


@mcp.tool()
async def update_domain(
    domain_id: str,
    name: str | None = None,
    description: str | None = None,
    color: str | None = None,
    sort_order: int | None = None,
) -> dict:
    """Update a domain's details.

    Only provided fields are changed — omit fields to leave them as-is.
    Use this to rename, recolor, or reorder domains.
    """
    validate_uuid(domain_id, "domain_id")
    body = _strip_nones({
        "name": name,
        "description": description,
        "color": color,
        "sort_order": sort_order,
    })
    return await api.patch(f"/api/domains/{domain_id}", json=body)


@mcp.tool()
async def delete_domain(domain_id: str) -> dict:
    """Delete a domain and cascade to its goals.

    This permanently removes the domain. Use with care — confirm with
    the user before deleting.
    """
    validate_uuid(domain_id, "domain_id")
    return await api.delete(f"/api/domains/{domain_id}")


# ---------------------------------------------------------------------------
# Goal Tools
# ---------------------------------------------------------------------------


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
    body = _strip_nones({
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
        "/api/goals/", params=_params(domain_id=domain_id, status=status)
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
    body = _strip_nones({
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


# ---------------------------------------------------------------------------
# Project Tools
# ---------------------------------------------------------------------------


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
    body = _strip_nones({
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
        params=_params(
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
    body = _strip_nones({
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


# ---------------------------------------------------------------------------
# Task Tools
# ---------------------------------------------------------------------------


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
    body = _strip_nones({
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
        params=_params(
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
    body = _strip_nones({
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


# ---------------------------------------------------------------------------
# Tag Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def create_tag(
    name: str,
    color: str | None = None,
) -> dict:
    """Create a tag, or return the existing one if the name already exists.

    Tags are labels that can be attached to tasks for flexible grouping
    (e.g. "quick-win", "deep-focus", "waiting-on"). This uses get-or-create
    semantics — if a tag with this name exists (case-insensitive), it's
    returned instead of creating a duplicate.
    """
    validate_required_str(name, "name")
    body = _strip_nones({"name": name, "color": color})
    return await api.post("/api/tags/", json=body)


@mcp.tool()
async def list_tags(
    search: str | None = None,
) -> list:
    """List all tags, optionally filtered by name search.

    The search parameter does a case-insensitive partial match on tag
    names. Use this to find existing tags before creating new ones.
    """
    return await api.get("/api/tags/", params=_params(search=search))


@mcp.tool()
async def get_tag(tag_id: str) -> dict:
    """Get a single tag by ID."""
    validate_uuid(tag_id, "tag_id")
    return await api.get(f"/api/tags/{tag_id}")


@mcp.tool()
async def update_tag(
    tag_id: str,
    name: str | None = None,
    color: str | None = None,
) -> dict:
    """Update a tag's name or color.

    Only provided fields are changed.
    """
    validate_uuid(tag_id, "tag_id")
    body = _strip_nones({"name": name, "color": color})
    return await api.patch(f"/api/tags/{tag_id}", json=body)


@mcp.tool()
async def delete_tag(tag_id: str) -> dict:
    """Delete a tag. Removes it from all tasks that use it."""
    validate_uuid(tag_id, "tag_id")
    return await api.delete(f"/api/tags/{tag_id}")


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


# ---------------------------------------------------------------------------
# Routine Tools
# ---------------------------------------------------------------------------


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
    body = _strip_nones({
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
) -> list:
    """List routines with optional filters.

    Filter by domain, status (active, paused, retired), frequency,
    or streak_broken=true to find active routines that have lost their
    streak. All filters combine with AND logic.
    """
    validate_uuid(domain_id, "domain_id")
    validate_enum(status, "status", ROUTINE_STATUSES)
    validate_enum(frequency, "frequency", ROUTINE_FREQUENCIES)
    return await api.get(
        "/api/routines/",
        params=_params(
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
    body = _strip_nones({
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
) -> dict:
    """Record a routine completion and evaluate the streak.

    Call this when the user completes a routine. Returns updated streak
    info including whether the streak was broken and recovered.
    If completed_date is omitted, today's date is used.
    Date format: YYYY-MM-DD.
    """
    validate_uuid(routine_id, "routine_id")
    body = _strip_nones({"completed_date": completed_date})
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
    body = _strip_nones({
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


# ---------------------------------------------------------------------------
# Check-in Tools
# ---------------------------------------------------------------------------


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
    body = _strip_nones({
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
        params=_params(
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
    body = _strip_nones({
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


# ---------------------------------------------------------------------------
# Activity Log Tools
# ---------------------------------------------------------------------------


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
) -> dict:
    """Create an activity log entry.

    Records what happened and how the user felt. At most one of task_id,
    routine_id, or checkin_id can be provided to link the entry.

    Action types: completed, skipped, deferred, started, reflected,
    checked_in.
    Energy before/after, mood, friction: 1-5 scale.
    """
    validate_enum(action_type, "action_type", ACTION_TYPES)
    validate_uuid(task_id, "task_id")
    validate_uuid(routine_id, "routine_id")
    validate_uuid(checkin_id, "checkin_id")
    validate_range(energy_before, "energy_before")
    validate_range(energy_after, "energy_after")
    validate_range(mood_rating, "mood_rating")
    validate_range(friction_actual, "friction_actual")
    body = _strip_nones({
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
) -> list:
    """List activity log entries with optional filters.

    Filter by action type, linked task or routine, date range, or whether
    entries have a task/routine attached. Results are ordered newest first.
    Use this to review what the user has been doing and how they felt.
    """
    validate_enum(action_type, "action_type", ACTION_TYPES)
    validate_uuid(task_id, "task_id")
    validate_uuid(routine_id, "routine_id")
    return await api.get(
        "/api/activity/",
        params=_params(
            action_type=action_type,
            task_id=task_id,
            routine_id=routine_id,
            logged_after=logged_after,
            logged_before=logged_before,
            has_task=has_task,
            has_routine=has_routine,
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
    body = _strip_nones({
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


# ---------------------------------------------------------------------------
# Reporting Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_activity_summary(after: str, before: str) -> dict:
    """Get aggregated activity statistics for a date range.

    Returns totals for completed, skipped, and deferred actions, total
    duration, average energy delta, and average mood. Use this for
    daily/weekly/monthly reviews.

    Date format: ISO datetime (e.g. "2025-03-01T00:00:00").
    Both after and before are required.
    """
    validate_required_str(after, "after")
    validate_required_str(before, "before")
    return await api.get(
        "/api/reports/activity-summary",
        params={"after": after, "before": before},
    )


@mcp.tool()
async def get_domain_balance() -> list:
    """Get per-domain item counts and recency.

    Returns each domain with counts of active goals, projects, pending
    tasks, overdue tasks, and days since last activity. Use this to
    identify neglected life areas or domains that need attention.
    """
    return await api.get("/api/reports/domain-balance")


@mcp.tool()
async def get_routine_adherence(after: str, before: str) -> list:
    """Get per-routine completion rates and streak health.

    Returns each routine with completions in period, expected completions,
    adherence percentage, and streak status. Use this for routine reviews
    and identifying habits that need reinforcement.

    Date format: ISO datetime. Both after and before are required.
    """
    validate_required_str(after, "after")
    validate_required_str(before, "before")
    return await api.get(
        "/api/reports/routine-adherence",
        params={"after": after, "before": before},
    )


@mcp.tool()
async def get_friction_analysis(
    after: str | None = None,
    before: str | None = None,
) -> list:
    """Get predicted vs actual friction analysis by cognitive type.

    Shows how the user's predicted activation friction compares to what
    they actually experienced, grouped by cognitive type. Reveals
    patterns like "I always overestimate friction for errand tasks."

    Defaults to the last 30 days if no dates are provided.
    Date format: ISO datetime.
    """
    return await api.get(
        "/api/reports/friction-analysis",
        params=_params(after=after, before=before),
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
