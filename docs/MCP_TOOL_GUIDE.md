# MCP Tool Guide — BRAIN 3.0 v1.2.0

**Version:** 1.2.0
**Date:** 2026-04-10
**Writer:** Apollo Swagger (API Documentation Agent)
**Audience:** Claude (primary), developers building on or maintaining the MCP layer

---

## Overview

The BRAIN 3.0 MCP server exposes **109 tools** that map 1:1 to the BRAIN 3.0 REST API. Every API endpoint has exactly one corresponding MCP tool. Claude uses these tools to read and write the user's task, routine, goal, activity, artifact, protocol, directive, and skill data through natural conversation.

**Architecture:**

```
Claude Desktop / Claude Code
        | stdio
   brain3-mcp (this server)
        | HTTP
   brain3 FastAPI (localhost or network)
        |
   PostgreSQL
```

The MCP server is **stateless** — all state lives in the BRAIN 3.0 database. The server makes HTTP requests and returns responses. Nothing is stored locally.

**Design philosophy:** Phase 1 tools are thin wrappers. One tool per endpoint. Claude's intelligence handles composition — the MCP just provides access. See [Composable Query Patterns](#composable-query-patterns--cookbook) for multi-tool workflows.

---

## Table of Contents

- [Tool Inventory](#tool-inventory)
  - [Health Check](#health-check)
  - [Domains](#domains)
  - [Goals](#goals)
  - [Projects](#projects)
  - [Tasks](#tasks)
  - [Tags](#tags)
  - [Routines](#routines)
  - [Check-ins](#check-ins)
  - [Activity Log](#activity-log)
  - [Reports](#reports)
  - [Artifacts](#artifacts)
  - [Protocols](#protocols)
  - [Directives](#directives)
  - [Skills](#skills)
  - [Batch Operations](#batch-operations)
- [Tool-to-Endpoint Mapping](#tool-to-endpoint-mapping)
- [Composable Query Patterns — Cookbook](#composable-query-patterns--cookbook)
- [Integration Guide](#integration-guide)
- [Error Reference](#error-reference)

---

## Tool Inventory

### Health Check

#### `health_check`

| | |
|---|---|
| **Maps to** | `GET /health` |
| **Description** | Check BRAIN 3.0 API connectivity. Use this first to verify the API is running and the database is connected. |
| **Parameters** | None |
| **Returns** | Status object with API and database connection state |

**Example call:**

```json
health_check()
```

**Example response:**

```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

### Domains

Domains are top-level life categories that organize goals (e.g., Health, Finances, Career, Relationships). They are the broadest organizational unit in the hierarchy: Domain > Goal > Project > Task.

#### `create_domain`

| | |
|---|---|
| **Maps to** | `POST /api/domains` |
| **Description** | Create a new life domain. Use when the user wants to establish a new area of focus. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | string | **Yes** | — | Domain name (e.g., "Health", "Career") |
| `description` | string | No | `null` | What this domain covers |
| `color` | string | No | `null` | Hex color for UI display |
| `sort_order` | integer | No | `0` | Display ordering |

**Example call:**

```json
create_domain(name="Health", description="Physical and mental wellbeing", color="#4CAF50")
```

**Example response:**

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "Health",
  "description": "Physical and mental wellbeing",
  "color": "#4CAF50",
  "sort_order": 0,
  "created_at": "2026-03-29T10:00:00",
  "updated_at": "2026-03-29T10:00:00"
}
```

#### `list_domains`

| | |
|---|---|
| **Maps to** | `GET /api/domains` |
| **Description** | List all life domains, sorted by sort_order then name. Use to see what areas of life are being tracked, or to find a domain_id for creating goals. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| — | — | — | — | No parameters |

**Example call:**

```json
list_domains()
```

**Example response:**

```json
[
  {
    "id": "a1b2c3d4-...",
    "name": "Career",
    "description": "Professional growth",
    "color": "#2196F3",
    "sort_order": 0
  },
  {
    "id": "b2c3d4e5-...",
    "name": "Health",
    "description": "Physical and mental wellbeing",
    "color": "#4CAF50",
    "sort_order": 1
  }
]
```

#### `get_domain`

| | |
|---|---|
| **Maps to** | `GET /api/domains/{domain_id}` |
| **Description** | Get a domain with its nested goals. Use to see the full picture of a life domain. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `domain_id` | string (UUID) | **Yes** | — | The domain to retrieve |

**Example call:**

```json
get_domain(domain_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890")
```

**Example response:**

```json
{
  "id": "a1b2c3d4-...",
  "name": "Health",
  "description": "Physical and mental wellbeing",
  "color": "#4CAF50",
  "sort_order": 1,
  "goals": [
    {
      "id": "c3d4e5f6-...",
      "title": "Lose 20 lbs",
      "status": "active"
    }
  ]
}
```

#### `update_domain`

| | |
|---|---|
| **Maps to** | `PATCH /api/domains/{domain_id}` |
| **Description** | Update a domain's details. Only provided fields are changed — omit fields to leave them as-is. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `domain_id` | string (UUID) | **Yes** | — | The domain to update |
| `name` | string | No | `null` | New name |
| `description` | string | No | `null` | New description |
| `color` | string | No | `null` | New hex color |
| `sort_order` | integer | No | `null` | New sort order |

**Example call:**

```json
update_domain(domain_id="a1b2c3d4-...", color="#66BB6A")
```

#### `delete_domain`

| | |
|---|---|
| **Maps to** | `DELETE /api/domains/{domain_id}` |
| **Description** | Delete a domain and cascade to its goals. **Destructive** — confirm with the user before calling. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `domain_id` | string (UUID) | **Yes** | — | The domain to delete |

**Example call:**

```json
delete_domain(domain_id="a1b2c3d4-...")
```

**Example response:**

```json
{"deleted": true}
```

---

### Goals

Goals are enduring outcomes tied to a life domain (e.g., "Lose 20 lbs" under Health). They sit between domains and projects in the hierarchy.

#### `create_goal`

| | |
|---|---|
| **Maps to** | `POST /api/goals` |
| **Description** | Create a goal under a domain. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `domain_id` | string (UUID) | **Yes** | — | Parent domain |
| `title` | string | **Yes** | — | Goal title |
| `description` | string | No | `null` | Goal description |
| `status` | string | No | `"active"` | One of: `active`, `paused`, `achieved`, `abandoned` |

**Example call:**

```json
create_goal(domain_id="a1b2c3d4-...", title="Lose 20 lbs", status="active")
```

#### `list_goals`

| | |
|---|---|
| **Maps to** | `GET /api/goals` |
| **Description** | List goals with optional filters. Use to find goal IDs for creating projects. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `domain_id` | string (UUID) | No | `null` | Filter by domain |
| `status` | string | No | `null` | Filter by status: `active`, `paused`, `achieved`, `abandoned` |

Filters combine with AND logic.

**Example call:**

```json
list_goals(domain_id="a1b2c3d4-...", status="active")
```

#### `get_goal`

| | |
|---|---|
| **Maps to** | `GET /api/goals/{goal_id}` |
| **Description** | Get a goal with its nested projects. Use to see the full breakdown of work under a goal. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `goal_id` | string (UUID) | **Yes** | — | The goal to retrieve |

#### `update_goal`

| | |
|---|---|
| **Maps to** | `PATCH /api/goals/{goal_id}` |
| **Description** | Update a goal's details. Only provided fields are changed. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `goal_id` | string (UUID) | **Yes** | — | The goal to update |
| `domain_id` | string (UUID) | No | `null` | Move to a different domain |
| `title` | string | No | `null` | New title |
| `description` | string | No | `null` | New description |
| `status` | string | No | `null` | New status: `active`, `paused`, `achieved`, `abandoned` |

#### `delete_goal`

| | |
|---|---|
| **Maps to** | `DELETE /api/goals/{goal_id}` |
| **Description** | Delete a goal and cascade to its projects. **Destructive** — confirm with the user. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `goal_id` | string (UUID) | **Yes** | — | The goal to delete |

---

### Projects

Projects are bounded initiatives with a clear finish line (e.g., "Complete C25K program" under a fitness goal). They contain tasks.

#### `create_project`

| | |
|---|---|
| **Maps to** | `POST /api/projects` |
| **Description** | Create a project under a goal. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `goal_id` | string (UUID) | **Yes** | — | Parent goal |
| `title` | string | **Yes** | — | Project title |
| `description` | string | No | `null` | Project description |
| `status` | string | No | `"not_started"` | One of: `not_started`, `active`, `blocked`, `completed`, `abandoned` |
| `deadline` | string | No | `null` | Deadline in `YYYY-MM-DD` format |

**Example call:**

```json
create_project(goal_id="c3d4e5f6-...", title="Complete C25K program", deadline="2026-06-01")
```

#### `list_projects`

| | |
|---|---|
| **Maps to** | `GET /api/projects` |
| **Description** | List projects with optional filters. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `goal_id` | string (UUID) | No | `null` | Filter by goal |
| `status` | string | No | `null` | Filter by status: `not_started`, `active`, `blocked`, `completed`, `abandoned` |
| `has_deadline` | boolean | No | `null` | `true` = only projects with deadlines, `false` = only without |
| `overdue` | boolean | No | `null` | `true` = only projects past their deadline that aren't completed/abandoned |

Filters combine with AND logic.

**Example call:**

```json
list_projects(status="active", overdue=true)
```

#### `get_project`

| | |
|---|---|
| **Maps to** | `GET /api/projects/{project_id}` |
| **Description** | Get a project with its nested tasks and progress percentage. Use to see the full task breakdown. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `project_id` | string (UUID) | **Yes** | — | The project to retrieve |

#### `update_project`

| | |
|---|---|
| **Maps to** | `PATCH /api/projects/{project_id}` |
| **Description** | Update a project's details. Only provided fields are changed. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `project_id` | string (UUID) | **Yes** | — | The project to update |
| `goal_id` | string (UUID) | No | `null` | Move to a different goal |
| `title` | string | No | `null` | New title |
| `description` | string | No | `null` | New description |
| `status` | string | No | `null` | New status |
| `deadline` | string | No | `null` | New deadline (`YYYY-MM-DD`) |

#### `delete_project`

| | |
|---|---|
| **Maps to** | `DELETE /api/projects/{project_id}` |
| **Description** | Delete a project and cascade to its tasks. **Destructive** — confirm with the user. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `project_id` | string (UUID) | **Yes** | — | The project to delete |

---

### Tasks

Tasks are the atomic unit of work. They can be standalone or belong to a project. ADHD-aware metadata (energy cost, activation friction, cognitive type) helps match tasks to the user's current state.

#### `create_task`

| | |
|---|---|
| **Maps to** | `POST /api/tasks` |
| **Description** | Create a task with ADHD-aware metadata. Tasks can be standalone or under a project. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `title` | string | **Yes** | — | Task title |
| `project_id` | string (UUID) | No | `null` | Parent project (omit for standalone task) |
| `description` | string | No | `null` | Task description |
| `status` | string | No | `"pending"` | One of: `pending`, `active`, `completed`, `skipped`, `deferred` |
| `cognitive_type` | string | No | `null` | One of: `hands_on`, `communication`, `decision`, `errand`, `admin`, `focus_work` |
| `energy_cost` | integer | No | `null` | 1 (low) to 5 (high) — how much energy this task requires |
| `activation_friction` | integer | No | `null` | 1 (low) to 5 (high) — how hard it is to start |
| `context_required` | string | No | `null` | Where/what is needed (e.g., "at computer", "at gym", "phone available") |
| `due_date` | string | No | `null` | Due date in `YYYY-MM-DD` format |
| `recurrence_rule` | string | No | `null` | iCalendar RRULE (e.g., `"FREQ=DAILY"`, `"FREQ=WEEKLY;BYDAY=MO,WE,FR"`) |

**Example call:**

```json
create_task(
  title="Review quarterly budget",
  cognitive_type="focus_work",
  energy_cost=4,
  activation_friction=3,
  context_required="at computer",
  due_date="2026-04-01"
)
```

**Example response:**

```json
{
  "id": "d4e5f6a7-...",
  "title": "Review quarterly budget",
  "project_id": null,
  "status": "pending",
  "cognitive_type": "focus_work",
  "energy_cost": 4,
  "activation_friction": 3,
  "context_required": "at computer",
  "due_date": "2026-04-01",
  "recurrence_rule": null,
  "created_at": "2026-03-29T10:30:00",
  "updated_at": "2026-03-29T10:30:00"
}
```

#### `list_tasks`

| | |
|---|---|
| **Maps to** | `GET /api/tasks` |
| **Description** | List tasks with composable filters. This is the most powerful query tool — use it to find tasks matching the user's current energy, context, or cognitive capacity. All filters are optional and combine with AND logic. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `project_id` | string (UUID) | No | `null` | Only tasks in this project |
| `standalone` | boolean | No | `null` | `true` = only tasks **not** assigned to any project |
| `status` | string | No | `null` | Filter by status: `pending`, `active`, `completed`, `skipped`, `deferred` |
| `cognitive_type` | string | No | `null` | Filter by cognitive type |
| `energy_cost_min` | integer | No | `null` | Minimum energy cost (1-5) |
| `energy_cost_max` | integer | No | `null` | Maximum energy cost (1-5) |
| `friction_min` | integer | No | `null` | Minimum activation friction (1-5) |
| `friction_max` | integer | No | `null` | Maximum activation friction (1-5) |
| `context_required` | string | No | `null` | Partial match on context string |
| `due_before` | string | No | `null` | Tasks due before this date (`YYYY-MM-DD`) |
| `due_after` | string | No | `null` | Tasks due after this date (`YYYY-MM-DD`) |
| `overdue` | boolean | No | `null` | `true` = tasks past due that aren't completed/skipped |

**Example — low-energy tasks the user can do right now:**

```json
list_tasks(status="pending", energy_cost_max=2, friction_max=2)
```

**Example — overdue errands:**

```json
list_tasks(status="pending", cognitive_type="errand", overdue=true)
```

**Example — tasks due this week at the computer:**

```json
list_tasks(status="pending", due_before="2026-04-04", context_required="at computer")
```

#### `get_task`

| | |
|---|---|
| **Maps to** | `GET /api/tasks/{task_id}` |
| **Description** | Get a task with its tags. Returns the full task details including any attached tags. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `task_id` | string (UUID) | **Yes** | — | The task to retrieve |

#### `update_task`

| | |
|---|---|
| **Maps to** | `PATCH /api/tasks/{task_id}` |
| **Description** | Update a task's details. Only provided fields are changed. Use to change status, reassign to a project, update energy cost, etc. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `task_id` | string (UUID) | **Yes** | — | The task to update |
| `project_id` | string (UUID) | No | `null` | Reassign to a project |
| `title` | string | No | `null` | New title |
| `description` | string | No | `null` | New description |
| `status` | string | No | `null` | New status: `pending`, `active`, `completed`, `skipped`, `deferred` |
| `cognitive_type` | string | No | `null` | New cognitive type |
| `energy_cost` | integer | No | `null` | New energy cost (1-5) |
| `activation_friction` | integer | No | `null` | New activation friction (1-5) |
| `context_required` | string | No | `null` | New context requirement |
| `due_date` | string | No | `null` | New due date (`YYYY-MM-DD`) |
| `recurrence_rule` | string | No | `null` | New recurrence rule (RRULE) |

**Example — mark a task complete:**

```json
update_task(task_id="d4e5f6a7-...", status="completed")
```

#### `delete_task`

| | |
|---|---|
| **Maps to** | `DELETE /api/tasks/{task_id}` |
| **Description** | Delete a task permanently. Removes the task and its tag associations. Confirm with the user. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `task_id` | string (UUID) | **Yes** | — | The task to delete |

---

### Tags

Tags are labels that can be attached to tasks for flexible grouping (e.g., "quick-win", "deep-focus", "waiting-on"). They exist independently of the domain/goal/project hierarchy, enabling cross-cutting categorization.

#### `create_tag`

| | |
|---|---|
| **Maps to** | `POST /api/tags` |
| **Description** | Create a tag, or return the existing one if the name already exists (get-or-create semantics, case-insensitive). |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | string | **Yes** | — | Tag name |
| `color` | string | No | `null` | Hex color |

**Example call:**

```json
create_tag(name="quick-win", color="#FFC107")
```

#### `list_tags`

| | |
|---|---|
| **Maps to** | `GET /api/tags` |
| **Description** | List all tags, optionally filtered by name search (case-insensitive partial match). Use to find existing tags before creating new ones. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `search` | string | No | `null` | Partial match on tag name |

#### `get_tag`

| | |
|---|---|
| **Maps to** | `GET /api/tags/{tag_id}` |
| **Description** | Get a single tag by ID. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `tag_id` | string (UUID) | **Yes** | — | The tag to retrieve |

#### `update_tag`

| | |
|---|---|
| **Maps to** | `PATCH /api/tags/{tag_id}` |
| **Description** | Update a tag's name or color. Only provided fields are changed. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `tag_id` | string (UUID) | **Yes** | — | The tag to update |
| `name` | string | No | `null` | New name |
| `color` | string | No | `null` | New color |

#### `delete_tag`

| | |
|---|---|
| **Maps to** | `DELETE /api/tags/{tag_id}` |
| **Description** | Delete a tag. Removes it from all tasks that use it. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `tag_id` | string (UUID) | **Yes** | — | The tag to delete |

#### `tag_task`

| | |
|---|---|
| **Maps to** | `POST /api/tasks/{task_id}/tags/{tag_id}` |
| **Description** | Attach a tag to a task. Idempotent — calling again with the same tag has no effect. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `task_id` | string (UUID) | **Yes** | — | The task |
| `tag_id` | string (UUID) | **Yes** | — | The tag to attach |

#### `untag_task`

| | |
|---|---|
| **Maps to** | `DELETE /api/tasks/{task_id}/tags/{tag_id}` |
| **Description** | Remove a tag from a task. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `task_id` | string (UUID) | **Yes** | — | The task |
| `tag_id` | string (UUID) | **Yes** | — | The tag to remove |

#### `list_task_tags`

| | |
|---|---|
| **Maps to** | `GET /api/tasks/{task_id}/tags` |
| **Description** | List all tags attached to a task. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `task_id` | string (UUID) | **Yes** | — | The task |

#### `list_tagged_tasks`

| | |
|---|---|
| **Maps to** | `GET /api/tags/{tag_id}/tasks` |
| **Description** | List all tasks that have a specific tag. Use to find all tasks in a category (e.g., all "quick-win" tasks). |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `tag_id` | string (UUID) | **Yes** | — | The tag to look up |

---

### Routines

Routines are recurring behaviors the user wants to build or maintain (e.g., "Morning meditation" under Health). They have schedules, completion tracking, and streak management. Routines live under domains (not goals or projects).

#### `create_routine`

| | |
|---|---|
| **Maps to** | `POST /api/routines` |
| **Description** | Create a routine tied to a domain. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `domain_id` | string (UUID) | **Yes** | — | Parent domain |
| `title` | string | **Yes** | — | Routine title |
| `frequency` | string | **Yes** | — | One of: `daily`, `weekdays`, `weekends`, `weekly`, `custom` |
| `description` | string | No | `null` | What this routine involves |
| `status` | string | No | `"active"` | One of: `active`, `paused`, `retired` |
| `energy_cost` | integer | No | `null` | 1 (low) to 5 (high) |
| `activation_friction` | integer | No | `null` | 1 (low) to 5 (high) |

**Example call:**

```json
create_routine(
  domain_id="b2c3d4e5-...",
  title="Morning meditation",
  frequency="daily",
  energy_cost=2,
  activation_friction=3
)
```

#### `list_routines`

| | |
|---|---|
| **Maps to** | `GET /api/routines` |
| **Description** | List routines with optional filters. Use `streak_broken=true` to find active routines that have lost their streak. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `domain_id` | string (UUID) | No | `null` | Filter by domain |
| `status` | string | No | `null` | Filter by status: `active`, `paused`, `retired` |
| `frequency` | string | No | `null` | Filter by frequency |
| `streak_broken` | boolean | No | `null` | `true` = active routines whose streak is broken |

Filters combine with AND logic.

**Example — broken streaks:**

```json
list_routines(status="active", streak_broken=true)
```

#### `get_routine`

| | |
|---|---|
| **Maps to** | `GET /api/routines/{routine_id}` |
| **Description** | Get a routine with its schedules. Returns current streak, best streak, last completion date, and all schedule entries. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `routine_id` | string (UUID) | **Yes** | — | The routine to retrieve |

**Example response:**

```json
{
  "id": "e5f6a7b8-...",
  "title": "Morning meditation",
  "domain_id": "b2c3d4e5-...",
  "frequency": "daily",
  "status": "active",
  "energy_cost": 2,
  "activation_friction": 3,
  "current_streak": 12,
  "best_streak": 30,
  "last_completed_date": "2026-03-28",
  "schedules": [
    {
      "id": "f6a7b8c9-...",
      "day_of_week": "monday",
      "time_of_day": "07:00",
      "preferred_window": "morning"
    }
  ]
}
```

#### `update_routine`

| | |
|---|---|
| **Maps to** | `PATCH /api/routines/{routine_id}` |
| **Description** | Update a routine's details. Only provided fields are changed. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `routine_id` | string (UUID) | **Yes** | — | The routine to update |
| `domain_id` | string (UUID) | No | `null` | Move to a different domain |
| `title` | string | No | `null` | New title |
| `description` | string | No | `null` | New description |
| `frequency` | string | No | `null` | New frequency |
| `status` | string | No | `null` | New status: `active`, `paused`, `retired` |
| `energy_cost` | integer | No | `null` | New energy cost (1-5) |
| `activation_friction` | integer | No | `null` | New activation friction (1-5) |

#### `delete_routine`

| | |
|---|---|
| **Maps to** | `DELETE /api/routines/{routine_id}` |
| **Description** | Delete a routine permanently. Removes the routine, its schedules, and completion history. Confirm with the user. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `routine_id` | string (UUID) | **Yes** | — | The routine to delete |

#### `complete_routine`

| | |
|---|---|
| **Maps to** | `POST /api/routines/{routine_id}/complete` |
| **Description** | Record a routine completion and evaluate the streak. Call when the user completes a routine. Returns updated streak info. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `routine_id` | string (UUID) | **Yes** | — | The routine that was completed |
| `completed_date` | string | No | Today's date | Completion date in `YYYY-MM-DD` format |

**Important:** This does **not** automatically create an activity log entry. Activity logging is explicit — call `log_activity` separately if you want to record how the user felt about it.

**Example call:**

```json
complete_routine(routine_id="e5f6a7b8-...")
```

**Example response:**

```json
{
  "routine_id": "e5f6a7b8-...",
  "completed_date": "2026-03-29",
  "current_streak": 13,
  "best_streak": 30,
  "streak_broken": false
}
```

#### `add_routine_schedule`

| | |
|---|---|
| **Maps to** | `POST /api/routines/{routine_id}/schedules` |
| **Description** | Add a schedule entry to a routine. Defines when a routine should happen. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `routine_id` | string (UUID) | **Yes** | — | The routine |
| `day_of_week` | string | **Yes** | — | One of: `monday`, `tuesday`, `wednesday`, `thursday`, `friday`, `saturday`, `sunday` |
| `time_of_day` | string | **Yes** | — | 24-hour format (e.g., `"08:30"`) |
| `preferred_window` | string | No | `null` | Optional label: `"morning"`, `"afternoon"`, `"evening"` |

**Example — schedule meditation for weekday mornings:**

```json
add_routine_schedule(routine_id="e5f6a7b8-...", day_of_week="monday", time_of_day="07:00", preferred_window="morning")
add_routine_schedule(routine_id="e5f6a7b8-...", day_of_week="tuesday", time_of_day="07:00", preferred_window="morning")
# ... repeat for each day
```

#### `list_routine_schedules`

| | |
|---|---|
| **Maps to** | `GET /api/routines/{routine_id}/schedules` |
| **Description** | List all schedule entries for a routine. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `routine_id` | string (UUID) | **Yes** | — | The routine |

#### `delete_routine_schedule`

| | |
|---|---|
| **Maps to** | `DELETE /api/routines/{routine_id}/schedules/{schedule_id}` |
| **Description** | Remove a schedule entry from a routine. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `routine_id` | string (UUID) | **Yes** | — | The routine |
| `schedule_id` | string (UUID) | **Yes** | — | The schedule entry to remove |

---

### Check-ins

Check-ins capture the user's current state — energy, mood, and focus. They are the input signal that drives energy-matched task selection and pattern detection.

#### `create_checkin`

| | |
|---|---|
| **Maps to** | `POST /api/checkins` |
| **Description** | Log a state check-in. Use to understand the user's capacity before suggesting tasks. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `checkin_type` | string | **Yes** | — | One of: `morning`, `midday`, `evening`, `micro`, `freeform` |
| `energy_level` | integer | No | `null` | 1 (low) to 5 (high) |
| `mood` | integer | No | `null` | 1 (low) to 5 (high) |
| `focus_level` | integer | No | `null` | 1 (low) to 5 (high) |
| `freeform_note` | string | No | `null` | Free-text note about current state |
| `context` | string | No | `null` | Where/what the user is doing (e.g., "at home", "at office") |

**Example call:**

```json
create_checkin(
  checkin_type="morning",
  energy_level=3,
  mood=4,
  focus_level=2,
  context="at home"
)
```

**Example response:**

```json
{
  "id": "f6a7b8c9-...",
  "checkin_type": "morning",
  "energy_level": 3,
  "mood": 4,
  "focus_level": 2,
  "freeform_note": null,
  "context": "at home",
  "logged_at": "2026-03-29T08:15:00"
}
```

#### `list_checkins`

| | |
|---|---|
| **Maps to** | `GET /api/checkins` |
| **Description** | List check-ins with optional filters. Use to review state history and identify patterns. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `checkin_type` | string | No | `null` | Filter by type |
| `context` | string | No | `null` | Filter by context |
| `logged_after` | string | No | `null` | ISO datetime (e.g., `"2026-03-01T00:00:00"`) |
| `logged_before` | string | No | `null` | ISO datetime |

#### `get_checkin`

| | |
|---|---|
| **Maps to** | `GET /api/checkins/{checkin_id}` |
| **Description** | Get a single check-in by ID. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `checkin_id` | string (UUID) | **Yes** | — | The check-in to retrieve |

#### `update_checkin`

| | |
|---|---|
| **Maps to** | `PATCH /api/checkins/{checkin_id}` |
| **Description** | Update a check-in's details. Only provided fields are changed. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `checkin_id` | string (UUID) | **Yes** | — | The check-in to update |
| `checkin_type` | string | No | `null` | New type |
| `energy_level` | integer | No | `null` | New energy level (1-5) |
| `mood` | integer | No | `null` | New mood (1-5) |
| `focus_level` | integer | No | `null` | New focus level (1-5) |
| `freeform_note` | string | No | `null` | New note |
| `context` | string | No | `null` | New context |

#### `delete_checkin`

| | |
|---|---|
| **Maps to** | `DELETE /api/checkins/{checkin_id}` |
| **Description** | Delete a check-in. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `checkin_id` | string (UUID) | **Yes** | — | The check-in to delete |

---

### Activity Log

The activity log records what happened and how the user felt about it. Each entry can link to a task, routine, or check-in (at most one). Activity logging is **explicit only** — no automatic side effects from other operations.

#### `log_activity`

| | |
|---|---|
| **Maps to** | `POST /api/activity` |
| **Description** | Create an activity log entry. Records what happened and how the user felt. At most one of task_id, routine_id, or checkin_id can be provided. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `action_type` | string | **Yes** | — | One of: `completed`, `skipped`, `deferred`, `started`, `reflected`, `checked_in` |
| `task_id` | string (UUID) | No | `null` | Link to a task |
| `routine_id` | string (UUID) | No | `null` | Link to a routine |
| `checkin_id` | string (UUID) | No | `null` | Link to a check-in |
| `notes` | string | No | `null` | Free-text notes about the experience |
| `energy_before` | integer | No | `null` | Energy before the activity (1-5) |
| `energy_after` | integer | No | `null` | Energy after the activity (1-5) |
| `mood_rating` | integer | No | `null` | Mood during the activity (1-5) |
| `friction_actual` | integer | No | `null` | Actual friction experienced (1-5) — compare with predicted `activation_friction` |
| `duration_minutes` | integer | No | `null` | How long it took |
| `tag_ids` | list[string] | No | `null` | Tag IDs to attach at creation. Saves separate `tag_activity` calls. |

**Example — log completing a task:**

```json
log_activity(
  action_type="completed",
  task_id="d4e5f6a7-...",
  energy_before=3,
  energy_after=4,
  friction_actual=2,
  duration_minutes=25,
  notes="Easier than expected once I started"
)
```

**Example response:**

```json
{
  "id": "a7b8c9d0-...",
  "action_type": "completed",
  "task_id": "d4e5f6a7-...",
  "routine_id": null,
  "checkin_id": null,
  "notes": "Easier than expected once I started",
  "energy_before": 3,
  "energy_after": 4,
  "mood_rating": null,
  "friction_actual": 2,
  "duration_minutes": 25,
  "logged_at": "2026-03-29T11:00:00"
}
```

#### `list_activity`

| | |
|---|---|
| **Maps to** | `GET /api/activity` |
| **Description** | List activity log entries with optional filters. Results are ordered newest first. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `action_type` | string | No | `null` | Filter by action type |
| `task_id` | string (UUID) | No | `null` | Filter by linked task |
| `routine_id` | string (UUID) | No | `null` | Filter by linked routine |
| `logged_after` | string | No | `null` | ISO datetime |
| `logged_before` | string | No | `null` | ISO datetime |
| `has_task` | boolean | No | `null` | `true` = only entries linked to a task |
| `has_routine` | boolean | No | `null` | `true` = only entries linked to a routine |
| `tag` | string | No | `null` | Comma-separated tag names. Entries must have **all** listed tags (AND logic). |

**Example — today's completed activities:**

```json
list_activity(action_type="completed", logged_after="2026-03-29T00:00:00")
```

#### `get_activity`

| | |
|---|---|
| **Maps to** | `GET /api/activity/{entry_id}` |
| **Description** | Get an activity log entry with resolved references. Returns the entry with full task, routine, or check-in details attached (not just IDs). |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `entry_id` | string (UUID) | **Yes** | — | The entry to retrieve |

#### `update_activity`

| | |
|---|---|
| **Maps to** | `PATCH /api/activity/{entry_id}` |
| **Description** | Update an activity log entry. Only provided fields are changed. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `entry_id` | string (UUID) | **Yes** | — | The entry to update |
| `task_id` | string (UUID) | No | `null` | Change linked task |
| `routine_id` | string (UUID) | No | `null` | Change linked routine |
| `checkin_id` | string (UUID) | No | `null` | Change linked check-in |
| `action_type` | string | No | `null` | Change action type |
| `notes` | string | No | `null` | Update notes |
| `energy_before` | integer | No | `null` | Update energy before (1-5) |
| `energy_after` | integer | No | `null` | Update energy after (1-5) |
| `mood_rating` | integer | No | `null` | Update mood (1-5) |
| `friction_actual` | integer | No | `null` | Update actual friction (1-5) |
| `duration_minutes` | integer | No | `null` | Update duration |

#### `delete_activity`

| | |
|---|---|
| **Maps to** | `DELETE /api/activity/{entry_id}` |
| **Description** | Delete an activity log entry. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `entry_id` | string (UUID) | **Yes** | — | The entry to delete |

#### `tag_activity`

| | |
|---|---|
| **Maps to** | `POST /api/activity/{activity_id}/tags/{tag_id}` |
| **Description** | Attach a tag to an activity log entry. Idempotent — calling again with the same tag has no effect. Use to categorize entries for filtering and discovery (e.g., session-handoff notes, media reviews). |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `activity_id` | string (UUID) | **Yes** | — | The activity entry to tag |
| `tag_id` | string (UUID) | **Yes** | — | The tag to attach |

#### `untag_activity`

| | |
|---|---|
| **Maps to** | `DELETE /api/activity/{activity_id}/tags/{tag_id}` |
| **Description** | Remove a tag from an activity log entry. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `activity_id` | string (UUID) | **Yes** | — | The activity entry |
| `tag_id` | string (UUID) | **Yes** | — | The tag to remove |

#### `list_activity_tags`

| | |
|---|---|
| **Maps to** | `GET /api/activity/{activity_id}/tags` |
| **Description** | List all tags attached to an activity log entry. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `activity_id` | string (UUID) | **Yes** | — | The activity entry |

#### `list_tagged_activities`

| | |
|---|---|
| **Maps to** | `GET /api/tags/{tag_id}/activities` |
| **Description** | List all activity log entries that have a specific tag. Use to find all entries in a category (e.g., all entries tagged "session-handoff" for context recovery, or "fluxnook" for media reviews). |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `tag_id` | string (UUID) | **Yes** | — | The tag to search by |

**Example — find session handoff notes:**

```json
tag = list_tags(search="session-handoff")
entries = list_tagged_activities(tag_id=tag[0]["id"])
```

---

### Reports

Report tools return aggregated data from cross-table queries. They are read-only and do not modify state. Use them for reviews, pattern detection, and coaching conversations.

#### `get_activity_summary`

| | |
|---|---|
| **Maps to** | `GET /api/reports/activity-summary` |
| **Description** | Get aggregated activity statistics for a date range. Use for daily, weekly, or monthly reviews. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `after` | string | **Yes** | — | Start of range, ISO datetime (e.g., `"2026-03-22T00:00:00"`) |
| `before` | string | **Yes** | — | End of range, ISO datetime (e.g., `"2026-03-29T00:00:00"`) |

**Example call:**

```json
get_activity_summary(after="2026-03-22T00:00:00", before="2026-03-29T00:00:00")
```

**Example response:**

```json
{
  "total_entries": 23,
  "completed": 15,
  "skipped": 3,
  "deferred": 5,
  "total_duration_minutes": 480,
  "avg_energy_delta": 0.3,
  "avg_mood": 3.8
}
```

**How to interpret:**
- `total_entries` — Total activity log entries in the period.
- `completed` / `skipped` / `deferred` — Counts by action type. A high skip rate may indicate overcommitment or energy mismatch.
- `total_duration_minutes` — Sum of all `duration_minutes` values. Shows total time invested.
- `avg_energy_delta` — Average of (`energy_after` - `energy_before`) across entries that have both values. Positive means activities are generally energizing. Negative means activities are draining. A value near zero is neutral.
- `avg_mood` — Average mood rating across entries that have mood values. Track trends over time rather than individual readings.

#### `get_domain_balance`

| | |
|---|---|
| **Maps to** | `GET /api/reports/domain-balance` |
| **Description** | Get per-domain item counts and recency. Use to identify neglected life areas or domains that need attention. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| — | — | — | — | No parameters |

**Example call:**

```json
get_domain_balance()
```

**Example response:**

```json
[
  {
    "domain_id": "a1b2c3d4-...",
    "domain_name": "Health",
    "active_goals": 2,
    "active_projects": 3,
    "pending_tasks": 8,
    "overdue_tasks": 1,
    "days_since_last_activity": 0
  },
  {
    "domain_id": "b2c3d4e5-...",
    "domain_name": "Finances",
    "active_goals": 1,
    "active_projects": 1,
    "pending_tasks": 4,
    "overdue_tasks": 3,
    "days_since_last_activity": 12
  }
]
```

**How to interpret:**
- `days_since_last_activity` — Days since the last activity log entry linked to anything in this domain. A high number signals neglect. Compare across domains to identify imbalance.
- `overdue_tasks` — Tasks past their due date. Domains with growing overdue counts may need reprioritization.
- A domain with many pending tasks but no recent activity is a potential attention gap.

#### `get_routine_adherence`

| | |
|---|---|
| **Maps to** | `GET /api/reports/routine-adherence` |
| **Description** | Get per-routine completion rates and streak health for a date range. Use for routine reviews and identifying habits that need reinforcement. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `after` | string | **Yes** | — | Start of range, ISO datetime |
| `before` | string | **Yes** | — | End of range, ISO datetime |

**Example call:**

```json
get_routine_adherence(after="2026-03-01T00:00:00", before="2026-03-29T00:00:00")
```

**Example response:**

```json
[
  {
    "routine_id": "e5f6a7b8-...",
    "routine_title": "Morning meditation",
    "completions": 25,
    "expected": 28,
    "adherence_pct": 89.3,
    "current_streak": 12,
    "streak_broken": false
  },
  {
    "routine_id": "f6a7b8c9-...",
    "routine_title": "Evening journaling",
    "completions": 10,
    "expected": 28,
    "adherence_pct": 35.7,
    "current_streak": 0,
    "streak_broken": true
  }
]
```

**How to interpret:**
- `adherence_pct` — Completions divided by expected completions. Above 80% is strong. Below 50% may indicate the routine needs adjustment (different time, lower frequency, or retirement).
- `streak_broken` — Whether the routine's streak is currently broken. A broken streak on a routine the user cares about is a coaching opportunity.
- `expected` — Based on the routine's frequency and the date range. A `daily` routine over 28 days expects 28 completions.

#### `get_friction_analysis`

| | |
|---|---|
| **Maps to** | `GET /api/reports/friction-analysis` |
| **Description** | Get predicted vs actual friction analysis by cognitive type. Reveals patterns in how the user predicts versus experiences task difficulty. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `after` | string | No | 30 days ago | Start of range, ISO datetime |
| `before` | string | No | Now | End of range, ISO datetime |

**Example call:**

```json
get_friction_analysis()
```

**Example response:**

```json
[
  {
    "cognitive_type": "focus_work",
    "avg_predicted_friction": 4.2,
    "avg_actual_friction": 3.1,
    "sample_count": 12,
    "delta": -1.1
  },
  {
    "cognitive_type": "errand",
    "avg_predicted_friction": 2.5,
    "avg_actual_friction": 3.8,
    "sample_count": 8,
    "delta": 1.3
  }
]
```

**How to interpret:**
- `delta` — Actual minus predicted. **Negative delta** means the user overestimates friction (tasks are easier than expected). **Positive delta** means the user underestimates friction (tasks are harder than expected).
- Use this to calibrate future task suggestions: if the user consistently overestimates friction for `focus_work`, Claude can encourage them to start despite hesitation.
- `sample_count` — How many data points inform this average. Low counts (< 5) mean the pattern is not yet reliable.

---

### Artifacts

Persistent documents stored in BRAIN -- CLAUDE.md files, design docs, briefs, prompts, templates, journals, specs. Artifacts support hierarchical organization via `parent_id`, tagging, and automatic versioning on content changes.

#### `create_artifact`

| | |
|---|---|
| **Maps to** | `POST /api/artifacts` |
| **Description** | Store a reference document in BRAIN. Use for CLAUDE.md files, design docs, briefs, templates, prompts -- anything that needs to persist beyond a conversation. Supports inline tagging via tag_ids. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `title` | string | **Yes** | — | Artifact title (max 200 chars) |
| `artifact_type` | string | **Yes** | — | One of: `document`, `protocol`, `brief`, `prompt`, `template`, `journal`, `spec` |
| `content` | string | No | `null` | Document body (max 500,000 chars / 512 KB UTF-8) |
| `parent_id` | string (UUID) | No | `null` | Parent artifact for hierarchy |
| `is_seedable` | boolean | No | `false` | Whether usable in seed scripts |
| `tag_ids` | list[string] | No | `null` | Tag IDs to attach at creation |

**Example call:**

```json
create_artifact(
  title="Session Startup Protocol",
  artifact_type="protocol",
  content="1. Load skill context\n2. Check pending tasks\n3. Review recent activity",
  is_seedable=true
)
```

**Example response:**

```json
{
  "id": "b2c3d4e5-...",
  "title": "Session Startup Protocol",
  "artifact_type": "protocol",
  "content_size": 78,
  "version": 1,
  "parent_id": null,
  "is_seedable": true,
  "created_at": "2026-04-01T12:00:00",
  "updated_at": "2026-04-01T12:00:00",
  "tags": []
}
```

#### `get_artifact`

| | |
|---|---|
| **Maps to** | `GET /api/artifacts/{artifact_id}` |
| **Description** | Retrieve a stored document with full content and resolved parent. Use when you need to read a specific artifact's content. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `artifact_id` | string (UUID) | **Yes** | — | The artifact to retrieve |

#### `list_artifacts`

| | |
|---|---|
| **Maps to** | `GET /api/artifacts` |
| **Description** | Browse stored documents by type, tags, seedability, or search. Returns metadata only (no content) -- use `get_artifact` to read specific ones. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `artifact_type` | string | No | `null` | Filter by type |
| `is_seedable` | boolean | No | `null` | Filter by seedable status |
| `search` | string | No | `null` | Case-insensitive title search |
| `parent_id` | string (UUID) | No | `null` | Filter to children of a specific artifact |
| `tag` | string | No | `null` | Comma-separated tag names (AND logic) |

**Example — find CLAUDE.md files:**

```json
list_artifacts(tag="claude-md")
```

#### `update_artifact`

| | |
|---|---|
| **Maps to** | `PATCH /api/artifacts/{artifact_id}` |
| **Description** | Update a stored document. Content changes auto-increment the version number and recompute content_size. Only provided fields are changed. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `artifact_id` | string (UUID) | **Yes** | — | The artifact to update |
| `title` | string | No | `null` | New title (max 200) |
| `artifact_type` | string | No | `null` | New type |
| `content` | string | No | `null` | New content (max 500,000 chars / 512 KB) |
| `parent_id` | string (UUID) | No | `null` | New parent |
| `is_seedable` | boolean | No | `null` | New seedable flag |

#### `delete_artifact`

| | |
|---|---|
| **Maps to** | `DELETE /api/artifacts/{artifact_id}` |
| **Description** | Remove a stored document from BRAIN. Children get `parent_id` set to NULL (not cascade deleted). |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `artifact_id` | string (UUID) | **Yes** | — | The artifact to delete |

#### `tag_artifact`

| | |
|---|---|
| **Maps to** | `POST /api/artifacts/{artifact_id}/tags/{tag_id}` |
| **Description** | Tag a document for categorization. Idempotent. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `artifact_id` | string (UUID) | **Yes** | — | The artifact to tag |
| `tag_id` | string (UUID) | **Yes** | — | The tag to attach |

#### `untag_artifact`

| | |
|---|---|
| **Maps to** | `DELETE /api/artifacts/{artifact_id}/tags/{tag_id}` |
| **Description** | Remove a tag from a document. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `artifact_id` | string (UUID) | **Yes** | — | The artifact |
| `tag_id` | string (UUID) | **Yes** | — | The tag to remove |

#### `list_artifact_tags`

| | |
|---|---|
| **Maps to** | `GET /api/artifacts/{artifact_id}/tags` |
| **Description** | See which tags are on a document. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `artifact_id` | string (UUID) | **Yes** | — | The artifact |

#### `list_tagged_artifacts`

| | |
|---|---|
| **Maps to** | `GET /api/tags/{tag_id}/artifacts` |
| **Description** | Find all artifacts with a specific tag. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `tag_id` | string (UUID) | **Yes** | — | The tag to search by |

---

### Protocols

Step-by-step procedures for repeatable workflows -- session startup sequences, bug triage flows, release processes. Protocols have ordered steps, optional artifact links, and automatic versioning.

#### `create_protocol`

| | |
|---|---|
| **Maps to** | `POST /api/protocols` |
| **Description** | Define a new step-by-step procedure. Use for repeatable workflows like session startup, bug handling, release processes. Name must be unique. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | string | **Yes** | — | Protocol name (max 100, unique) |
| `description` | string | No | `null` | What this protocol is for (max 5000) |
| `steps` | list[dict] | No | `null` | Ordered steps (max 50). Each: `{order: int, title: str, instruction: str, is_optional: bool}` |
| `artifact_id` | string (UUID) | No | `null` | Linked reference document |
| `is_seedable` | boolean | No | `true` | Whether usable in seed scripts |
| `tag_ids` | list[string] | No | `null` | Tag IDs to attach at creation |

**Example call:**

```json
create_protocol(
  name="session-startup",
  description="Standard agent initialization sequence",
  steps=[
    {"order": 1, "title": "Load skill", "instruction": "Call get_skill_full with the assigned skill ID", "is_optional": false},
    {"order": 2, "title": "Check context", "instruction": "Review recent activity for session continuity", "is_optional": false},
    {"order": 3, "title": "Greet user", "instruction": "Acknowledge what was last worked on", "is_optional": true}
  ]
)
```

**Example response:**

```json
{
  "id": "c3d4e5f6-...",
  "name": "session-startup",
  "description": "Standard agent initialization sequence",
  "steps": [
    {"order": 1, "title": "Load skill", "instruction": "Call get_skill_full with the assigned skill ID", "is_optional": false},
    {"order": 2, "title": "Check context", "instruction": "Review recent activity for session continuity", "is_optional": false},
    {"order": 3, "title": "Greet user", "instruction": "Acknowledge what was last worked on", "is_optional": true}
  ],
  "artifact_id": null,
  "is_seedable": true,
  "version": 1,
  "tags": []
}
```

#### `get_protocol`

| | |
|---|---|
| **Maps to** | `GET /api/protocols/{protocol_id}` |
| **Description** | Load a specific protocol with its steps and linked artifact details. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `protocol_id` | string (UUID) | **Yes** | — | The protocol to retrieve |

#### `list_protocols`

| | |
|---|---|
| **Maps to** | `GET /api/protocols` |
| **Description** | Browse available protocols. Use at session start to see what procedures are defined. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `search` | string | No | `null` | Case-insensitive name search |
| `is_seedable` | boolean | No | `null` | Filter by seedable status |
| `has_artifact` | boolean | No | `null` | Filter by whether artifact is linked |
| `tag` | string | No | `null` | Comma-separated tag names (AND logic) |

#### `update_protocol`

| | |
|---|---|
| **Maps to** | `PATCH /api/protocols/{protocol_id}` |
| **Description** | Modify a protocol -- update steps, description, or linked artifact. Version auto-increments on steps or description changes. Name uniqueness enforced. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `protocol_id` | string (UUID) | **Yes** | — | The protocol to update |
| `name` | string | No | `null` | New name (max 100, unique) |
| `description` | string | No | `null` | New description (max 5000) |
| `steps` | list[dict] | No | `null` | New steps (max 50) |
| `artifact_id` | string (UUID) | No | `null` | New linked artifact |
| `is_seedable` | boolean | No | `null` | New seedable flag |

#### `delete_protocol`

| | |
|---|---|
| **Maps to** | `DELETE /api/protocols/{protocol_id}` |
| **Description** | Remove a protocol from BRAIN. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `protocol_id` | string (UUID) | **Yes** | — | The protocol to delete |

#### `tag_protocol`

| | |
|---|---|
| **Maps to** | `POST /api/protocols/{protocol_id}/tags/{tag_id}` |
| **Description** | Tag a protocol. Idempotent. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `protocol_id` | string (UUID) | **Yes** | — | The protocol to tag |
| `tag_id` | string (UUID) | **Yes** | — | The tag to attach |

#### `untag_protocol`

| | |
|---|---|
| **Maps to** | `DELETE /api/protocols/{protocol_id}/tags/{tag_id}` |
| **Description** | Remove a tag from a protocol. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `protocol_id` | string (UUID) | **Yes** | — | The protocol |
| `tag_id` | string (UUID) | **Yes** | — | The tag to remove |

#### `list_protocol_tags`

| | |
|---|---|
| **Maps to** | `GET /api/protocols/{protocol_id}/tags` |
| **Description** | List tags on a protocol. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `protocol_id` | string (UUID) | **Yes** | — | The protocol |

#### `list_tagged_protocols`

| | |
|---|---|
| **Maps to** | `GET /api/tags/{tag_id}/protocols` |
| **Description** | Find all protocols with a specific tag. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `tag_id` | string (UUID) | **Yes** | — | The tag to search by |

---

### Directives

Behavioral rules and guardrails scoped to global, skill, or agent contexts. Directives carry a priority (1-10) and are resolved at session start to build the agent's operating constraints.

**Scope model:**
- `global` — applies to all agents, all contexts. `scope_ref` must be null.
- `skill` — applies when a specific skill is loaded. `scope_ref` is the skill ID.
- `agent` — applies to a specific agent identity. `scope_ref` is the agent project ID.

#### `create_directive`

| | |
|---|---|
| **Maps to** | `POST /api/directives` |
| **Description** | Define a behavioral rule or guardrail. Scope it as global (always applies), skill-specific, or agent-specific. Global directives must NOT have a scope_ref. Skill/agent directives require one. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | string | **Yes** | — | Directive name (max 200) |
| `content` | string | **Yes** | — | The rule or guardrail text (max 10,000) |
| `scope` | string | **Yes** | — | One of: `global`, `skill`, `agent` |
| `scope_ref` | string (UUID) | Conditional | `null` | Required for skill/agent scope. Must be null for global. |
| `priority` | integer | No | `5` | Importance (1-10, higher = more important) |
| `is_seedable` | boolean | No | `true` | Whether usable in seed scripts |
| `tag_ids` | list[string] | No | `null` | Tag IDs to attach at creation |

**Example call:**

```json
create_directive(
  name="No silent assumptions",
  content="When a spec is ambiguous, stop and ask a focused question. Do not guess and proceed.",
  scope="global",
  priority=9
)
```

**Example response:**

```json
{
  "id": "d4e5f6a7-...",
  "name": "No silent assumptions",
  "content": "When a spec is ambiguous, stop and ask a focused question...",
  "scope": "global",
  "scope_ref": null,
  "priority": 9,
  "is_seedable": true,
  "tags": []
}
```

#### `get_directive`

| | |
|---|---|
| **Maps to** | `GET /api/directives/{directive_id}` |
| **Description** | Read a specific directive. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `directive_id` | string (UUID) | **Yes** | — | The directive to retrieve |

#### `list_directives`

| | |
|---|---|
| **Maps to** | `GET /api/directives` |
| **Description** | Browse directives with scope, priority, and tag filters. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `scope` | string | No | `null` | Filter: `global`, `skill`, `agent` |
| `scope_ref` | string (UUID) | No | `null` | Filter by scope reference |
| `is_seedable` | boolean | No | `null` | Filter by seedable status |
| `priority_min` | integer | No | `null` | Minimum priority (1-10) |
| `priority_max` | integer | No | `null` | Maximum priority (1-10) |
| `search` | string | No | `null` | Case-insensitive name search |
| `tag` | string | No | `null` | Comma-separated tag names (AND logic) |

**Example — high-priority global rules:**

```json
list_directives(scope="global", priority_min=8)
```

#### `update_directive`

| | |
|---|---|
| **Maps to** | `PATCH /api/directives/{directive_id}` |
| **Description** | Modify a directive. API validates scope/scope_ref constraints after merge. Only provided fields are changed. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `directive_id` | string (UUID) | **Yes** | — | The directive to update |
| `name` | string | No | `null` | New name (max 200) |
| `content` | string | No | `null` | New content (max 10,000) |
| `scope` | string | No | `null` | New scope |
| `scope_ref` | string (UUID) | No | `null` | New scope reference |
| `priority` | integer | No | `null` | New priority (1-10) |
| `is_seedable` | boolean | No | `null` | New seedable flag |

#### `delete_directive`

| | |
|---|---|
| **Maps to** | `DELETE /api/directives/{directive_id}` |
| **Description** | Remove a directive. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `directive_id` | string (UUID) | **Yes** | — | The directive to delete |

#### `resolve_directives`

| | |
|---|---|
| **Maps to** | `GET /api/directives/resolve` |
| **Description** | Get the merged directive set for a skill + optional agent context. Returns global + skill + agent directives grouped and sorted by priority. **Use this at session start to load behavioral rules.** |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skill_id` | string (UUID) | No | `null` | Include directives scoped to this skill |
| `scope_ref` | string (UUID) | No | `null` | Include directives scoped to this agent |

**Example — load all rules for core-protocol skill:**

```json
resolve_directives(skill_id="c3d4e5f6-...")
```

**Example response:**

```json
{
  "global_directives": [
    {"name": "No silent assumptions", "priority": 9, "...": "..."},
    {"name": "Log issues, don't fix inline", "priority": 7, "...": "..."}
  ],
  "skill_directives": [
    {"name": "Document reality not intent", "priority": 8, "...": "..."}
  ],
  "agent_directives": []
}
```

#### `tag_directive`

| | |
|---|---|
| **Maps to** | `POST /api/directives/{directive_id}/tags/{tag_id}` |
| **Description** | Tag a directive. Idempotent. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `directive_id` | string (UUID) | **Yes** | — | The directive to tag |
| `tag_id` | string (UUID) | **Yes** | — | The tag to attach |

#### `untag_directive`

| | |
|---|---|
| **Maps to** | `DELETE /api/directives/{directive_id}/tags/{tag_id}` |
| **Description** | Remove a tag from a directive. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `directive_id` | string (UUID) | **Yes** | — | The directive |
| `tag_id` | string (UUID) | **Yes** | — | The tag to remove |

#### `list_directive_tags`

| | |
|---|---|
| **Maps to** | `GET /api/directives/{directive_id}/tags` |
| **Description** | List tags on a directive. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `directive_id` | string (UUID) | **Yes** | — | The directive |

#### `list_tagged_directives`

| | |
|---|---|
| **Maps to** | `GET /api/tags/{tag_id}/directives` |
| **Description** | Find all directives with a specific tag. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `tag_id` | string (UUID) | **Yes** | — | The tag to search by |

---

### Skills

Operating modes that bundle domains, protocols, and directives into loadable contexts. A skill defines how an agent behaves -- which life areas it works with, what procedures it follows, and what rules constrain it.

#### `create_skill`

| | |
|---|---|
| **Maps to** | `POST /api/skills` |
| **Description** | Define a new operating mode with linked domains, protocols, and directives. Supports bulk linking at creation. Name must be unique. At most one skill can be the default. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | string | **Yes** | — | Skill name (max 100, unique) |
| `description` | string | No | `null` | What this skill is for (max 5000) |
| `adhd_patterns` | string | No | `null` | ADHD-specific behavioral guidance (max 10,000) |
| `artifact_id` | string (UUID) | No | `null` | Linked reference document |
| `is_seedable` | boolean | No | `true` | Whether usable in seed scripts |
| `is_default` | boolean | No | `false` | Whether this is the default skill (at most one) |
| `domain_ids` | list[string] | No | `null` | Domain UUIDs to link at creation |
| `protocol_ids` | list[string] | No | `null` | Protocol UUIDs to link at creation |
| `directive_ids` | list[string] | No | `null` | Directive UUIDs to link at creation |

**Example call:**

```json
create_skill(
  name="core-protocol",
  description="Default operating mode for all BRAIN agents",
  is_default=true,
  domain_ids=["a1b2c3d4-..."],
  protocol_ids=["c3d4e5f6-..."]
)
```

#### `get_skill`

| | |
|---|---|
| **Maps to** | `GET /api/skills/{skill_id}` |
| **Description** | Get a skill with its linked relationships (domains, protocols, directives). |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skill_id` | string (UUID) | **Yes** | — | The skill to retrieve |

#### `get_skill_full`

| | |
|---|---|
| **Maps to** | `GET /api/skills/{skill_id}/full` |
| **Description** | **Primary bootstrap tool.** Load complete skill context. Returns resolved protocols, grouped directives (global + skill-scoped sorted by priority), domains, and linked artifact. Call this at session start to load your operating context. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skill_id` | string (UUID) | **Yes** | — | The skill to bootstrap |

**Example call:**

```json
get_skill_full(skill_id="c3d4e5f6-...")
```

**Example response:**

```json
{
  "id": "c3d4e5f6-...",
  "name": "core-protocol",
  "description": "Default operating mode for all BRAIN agents",
  "adhd_patterns": null,
  "is_seedable": true,
  "is_default": true,
  "artifact": null,
  "domains": [{"id": "...", "name": "Engineering"}],
  "protocols": [{"id": "...", "name": "session-startup", "steps": [...]}],
  "directives": {
    "global_directives": [
      {"name": "No silent assumptions", "priority": 9},
      {"name": "Log issues, don't fix inline", "priority": 7}
    ],
    "skill": [
      {"name": "Document reality not intent", "priority": 8}
    ]
  }
}
```

#### `list_skills`

| | |
|---|---|
| **Maps to** | `GET /api/skills` |
| **Description** | Browse available operating modes. Filter by name, seedability, default status, or linked domain. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `search` | string | No | `null` | Case-insensitive name search |
| `is_seedable` | boolean | No | `null` | Filter by seedable status |
| `is_default` | boolean | No | `null` | Filter by default status |
| `domain_id` | string (UUID) | No | `null` | Filter to skills linked to this domain |

#### `update_skill`

| | |
|---|---|
| **Maps to** | `PATCH /api/skills/{skill_id}` |
| **Description** | Modify a skill's properties. Use link/unlink tools for relationship changes. Only provided fields are changed. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skill_id` | string (UUID) | **Yes** | — | The skill to update |
| `name` | string | No | `null` | New name (max 100, unique) |
| `description` | string | No | `null` | New description (max 5000) |
| `adhd_patterns` | string | No | `null` | New ADHD guidance (max 10,000) |
| `artifact_id` | string (UUID) | No | `null` | New linked artifact |
| `is_seedable` | boolean | No | `null` | New seedable flag |
| `is_default` | boolean | No | `null` | New default flag (at most one skill) |

#### `delete_skill`

| | |
|---|---|
| **Maps to** | `DELETE /api/skills/{skill_id}` |
| **Description** | Remove a skill and its join-table entries. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skill_id` | string (UUID) | **Yes** | — | The skill to delete |

#### `list_skill_domains`

| | |
|---|---|
| **Maps to** | `GET /api/skills/{skill_id}/domains` |
| **Description** | List all domains linked to a skill. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skill_id` | string (UUID) | **Yes** | — | The skill |

#### `link_skill_domain`

| | |
|---|---|
| **Maps to** | `POST /api/skills/{skill_id}/domains/{domain_id}` |
| **Description** | Associate a domain with a skill. Idempotent. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skill_id` | string (UUID) | **Yes** | — | The skill |
| `domain_id` | string (UUID) | **Yes** | — | The domain to link |

#### `unlink_skill_domain`

| | |
|---|---|
| **Maps to** | `DELETE /api/skills/{skill_id}/domains/{domain_id}` |
| **Description** | Remove domain association. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skill_id` | string (UUID) | **Yes** | — | The skill |
| `domain_id` | string (UUID) | **Yes** | — | The domain to unlink |

#### `list_skill_protocols`

| | |
|---|---|
| **Maps to** | `GET /api/skills/{skill_id}/protocols` |
| **Description** | List all protocols linked to a skill. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skill_id` | string (UUID) | **Yes** | — | The skill |

#### `link_skill_protocol`

| | |
|---|---|
| **Maps to** | `POST /api/skills/{skill_id}/protocols/{protocol_id}` |
| **Description** | Associate a protocol with a skill. Idempotent. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skill_id` | string (UUID) | **Yes** | — | The skill |
| `protocol_id` | string (UUID) | **Yes** | — | The protocol to link |

#### `unlink_skill_protocol`

| | |
|---|---|
| **Maps to** | `DELETE /api/skills/{skill_id}/protocols/{protocol_id}` |
| **Description** | Remove protocol association. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skill_id` | string (UUID) | **Yes** | — | The skill |
| `protocol_id` | string (UUID) | **Yes** | — | The protocol to unlink |

#### `list_skill_directives`

| | |
|---|---|
| **Maps to** | `GET /api/skills/{skill_id}/directives` |
| **Description** | List all directives linked to a skill. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skill_id` | string (UUID) | **Yes** | — | The skill |

#### `link_skill_directive`

| | |
|---|---|
| **Maps to** | `POST /api/skills/{skill_id}/directives/{directive_id}` |
| **Description** | Associate a directive with a skill. Idempotent. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skill_id` | string (UUID) | **Yes** | — | The skill |
| `directive_id` | string (UUID) | **Yes** | — | The directive to link |

#### `unlink_skill_directive`

| | |
|---|---|
| **Maps to** | `DELETE /api/skills/{skill_id}/directives/{directive_id}` |
| **Description** | Remove directive association. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skill_id` | string (UUID) | **Yes** | — | The skill |
| `directive_id` | string (UUID) | **Yes** | — | The directive to unlink |

---

### Batch Operations

Bulk creation and tagging tools. All batch create operations are **atomic** -- all items succeed or all fail with rollback. Batch tag operations are idempotent.

#### `batch_create_tasks`

| | |
|---|---|
| **Maps to** | `POST /api/tasks/batch` |
| **Description** | Create multiple tasks in one atomic operation. Max 100. Each item follows the `create_task` schema. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `items` | list[dict] | **Yes** | — | Task objects (max 100). Each follows `create_task` schema. |

**Example call:**

```json
batch_create_tasks(items=[
  {"title": "Buy groceries", "cognitive_type": "errand", "energy_cost": 2},
  {"title": "Review PR #42", "cognitive_type": "focus_work", "energy_cost": 4}
])
```

**Example response:**

```json
{
  "created": [{"id": "...", "title": "Buy groceries", "..."}, {"id": "...", "title": "Review PR #42", "..."}],
  "count": 2
}
```

#### `batch_create_activity`

| | |
|---|---|
| **Maps to** | `POST /api/activity/batch` |
| **Description** | Log multiple activities at once. Max 100. Use for session recaps or batch imports. Each item follows the `log_activity` schema. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `items` | list[dict] | **Yes** | — | Activity objects (max 100). Each follows `log_activity` schema. |

#### `batch_create_artifacts`

| | |
|---|---|
| **Maps to** | `POST /api/artifacts/batch` |
| **Description** | Store multiple documents at once. **Max 25** (lower limit due to potentially large content). Each item follows the `create_artifact` schema. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `items` | list[dict] | **Yes** | — | Artifact objects (**max 25**). Each follows `create_artifact` schema. |

#### `batch_create_protocols`

| | |
|---|---|
| **Maps to** | `POST /api/protocols/batch` |
| **Description** | Create multiple protocols at once. Max 100. Each item follows the `create_protocol` schema. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `items` | list[dict] | **Yes** | — | Protocol objects (max 100). Each follows `create_protocol` schema. |

#### `batch_create_directives`

| | |
|---|---|
| **Maps to** | `POST /api/directives/batch` |
| **Description** | Create multiple directives at once. Max 100. Each item follows the `create_directive` schema. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `items` | list[dict] | **Yes** | — | Directive objects (max 100). Each follows `create_directive` schema. |

#### `batch_create_skills`

| | |
|---|---|
| **Maps to** | `POST /api/skills/batch` |
| **Description** | Create multiple skills at once. Max 100. Returns with resolved relationships. Each item follows the `create_skill` schema. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `items` | list[dict] | **Yes** | — | Skill objects (max 100). Each follows `create_skill` schema. |

#### `batch_tag_task`

| | |
|---|---|
| **Maps to** | `POST /api/tasks/{task_id}/tags/batch` |
| **Description** | Attach multiple tags to a task at once. Idempotent. Max 100 tags. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `task_id` | string (UUID) | **Yes** | — | The task to tag |
| `tag_ids` | list[string] | **Yes** | — | Tag UUIDs to attach (max 100) |

#### `batch_tag_activity`

| | |
|---|---|
| **Maps to** | `POST /api/activity/{activity_id}/tags/batch` |
| **Description** | Attach multiple tags to an activity at once. Idempotent. Max 100 tags. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `activity_id` | string (UUID) | **Yes** | — | The activity entry to tag |
| `tag_ids` | list[string] | **Yes** | — | Tag UUIDs to attach (max 100) |

#### `batch_tag_artifact`

| | |
|---|---|
| **Maps to** | `POST /api/artifacts/{artifact_id}/tags/batch` |
| **Description** | Attach multiple tags to an artifact at once. Idempotent. Max 100 tags. |

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `artifact_id` | string (UUID) | **Yes** | — | The artifact to tag |
| `tag_ids` | list[string] | **Yes** | — | Tag UUIDs to attach (max 100) |

---

## Tool-to-Endpoint Mapping

The following table confirms the complete 1:1 mapping between all 109 MCP tools and their API endpoints. This mapping was verified against both `mcp/server.py` and the brain3 router implementations.

| # | MCP Tool | HTTP Method | API Endpoint |
|---|----------|-------------|--------------|
| 1 | `health_check` | GET | `/health` |
| **Domains** | | | |
| 2 | `create_domain` | POST | `/api/domains` |
| 3 | `list_domains` | GET | `/api/domains` |
| 4 | `get_domain` | GET | `/api/domains/{domain_id}` |
| 5 | `update_domain` | PATCH | `/api/domains/{domain_id}` |
| 6 | `delete_domain` | DELETE | `/api/domains/{domain_id}` |
| **Goals** | | | |
| 7 | `create_goal` | POST | `/api/goals` |
| 8 | `list_goals` | GET | `/api/goals` |
| 9 | `get_goal` | GET | `/api/goals/{goal_id}` |
| 10 | `update_goal` | PATCH | `/api/goals/{goal_id}` |
| 11 | `delete_goal` | DELETE | `/api/goals/{goal_id}` |
| **Projects** | | | |
| 12 | `create_project` | POST | `/api/projects` |
| 13 | `list_projects` | GET | `/api/projects` |
| 14 | `get_project` | GET | `/api/projects/{project_id}` |
| 15 | `update_project` | PATCH | `/api/projects/{project_id}` |
| 16 | `delete_project` | DELETE | `/api/projects/{project_id}` |
| **Tasks** | | | |
| 17 | `create_task` | POST | `/api/tasks` |
| 18 | `list_tasks` | GET | `/api/tasks` |
| 19 | `get_task` | GET | `/api/tasks/{task_id}` |
| 20 | `update_task` | PATCH | `/api/tasks/{task_id}` |
| 21 | `delete_task` | DELETE | `/api/tasks/{task_id}` |
| **Tags** | | | |
| 22 | `create_tag` | POST | `/api/tags` |
| 23 | `list_tags` | GET | `/api/tags` |
| 24 | `get_tag` | GET | `/api/tags/{tag_id}` |
| 25 | `update_tag` | PATCH | `/api/tags/{tag_id}` |
| 26 | `delete_tag` | DELETE | `/api/tags/{tag_id}` |
| 27 | `tag_task` | POST | `/api/tasks/{task_id}/tags/{tag_id}` |
| 28 | `untag_task` | DELETE | `/api/tasks/{task_id}/tags/{tag_id}` |
| 29 | `list_task_tags` | GET | `/api/tasks/{task_id}/tags` |
| 30 | `list_tagged_tasks` | GET | `/api/tags/{tag_id}/tasks` |
| **Routines** | | | |
| 31 | `create_routine` | POST | `/api/routines` |
| 32 | `list_routines` | GET | `/api/routines` |
| 33 | `get_routine` | GET | `/api/routines/{routine_id}` |
| 34 | `update_routine` | PATCH | `/api/routines/{routine_id}` |
| 35 | `delete_routine` | DELETE | `/api/routines/{routine_id}` |
| 36 | `complete_routine` | POST | `/api/routines/{routine_id}/complete` |
| 37 | `add_routine_schedule` | POST | `/api/routines/{routine_id}/schedules` |
| 38 | `list_routine_schedules` | GET | `/api/routines/{routine_id}/schedules` |
| 39 | `delete_routine_schedule` | DELETE | `/api/routines/{routine_id}/schedules/{schedule_id}` |
| **Check-ins** | | | |
| 40 | `create_checkin` | POST | `/api/checkins` |
| 41 | `list_checkins` | GET | `/api/checkins` |
| 42 | `get_checkin` | GET | `/api/checkins/{checkin_id}` |
| 43 | `update_checkin` | PATCH | `/api/checkins/{checkin_id}` |
| 44 | `delete_checkin` | DELETE | `/api/checkins/{checkin_id}` |
| **Activity Log** | | | |
| 45 | `log_activity` | POST | `/api/activity` |
| 46 | `list_activity` | GET | `/api/activity` |
| 47 | `get_activity` | GET | `/api/activity/{entry_id}` |
| 48 | `update_activity` | PATCH | `/api/activity/{entry_id}` |
| 49 | `delete_activity` | DELETE | `/api/activity/{entry_id}` |
| 50 | `tag_activity` | POST | `/api/activity/{activity_id}/tags/{tag_id}` |
| 51 | `untag_activity` | DELETE | `/api/activity/{activity_id}/tags/{tag_id}` |
| 52 | `list_activity_tags` | GET | `/api/activity/{activity_id}/tags` |
| 53 | `list_tagged_activities` | GET | `/api/tags/{tag_id}/activities` |
| **Reports** | | | |
| 54 | `get_activity_summary` | GET | `/api/reports/activity-summary` |
| 55 | `get_domain_balance` | GET | `/api/reports/domain-balance` |
| 56 | `get_routine_adherence` | GET | `/api/reports/routine-adherence` |
| 57 | `get_friction_analysis` | GET | `/api/reports/friction-analysis` |
| **Artifacts** | | | |
| 58 | `create_artifact` | POST | `/api/artifacts` |
| 59 | `get_artifact` | GET | `/api/artifacts/{artifact_id}` |
| 60 | `list_artifacts` | GET | `/api/artifacts` |
| 61 | `update_artifact` | PATCH | `/api/artifacts/{artifact_id}` |
| 62 | `delete_artifact` | DELETE | `/api/artifacts/{artifact_id}` |
| 63 | `tag_artifact` | POST | `/api/artifacts/{artifact_id}/tags/{tag_id}` |
| 64 | `untag_artifact` | DELETE | `/api/artifacts/{artifact_id}/tags/{tag_id}` |
| 65 | `list_artifact_tags` | GET | `/api/artifacts/{artifact_id}/tags` |
| 66 | `list_tagged_artifacts` | GET | `/api/tags/{tag_id}/artifacts` |
| **Protocols** | | | |
| 67 | `create_protocol` | POST | `/api/protocols` |
| 68 | `get_protocol` | GET | `/api/protocols/{protocol_id}` |
| 69 | `list_protocols` | GET | `/api/protocols` |
| 70 | `update_protocol` | PATCH | `/api/protocols/{protocol_id}` |
| 71 | `delete_protocol` | DELETE | `/api/protocols/{protocol_id}` |
| 72 | `tag_protocol` | POST | `/api/protocols/{protocol_id}/tags/{tag_id}` |
| 73 | `untag_protocol` | DELETE | `/api/protocols/{protocol_id}/tags/{tag_id}` |
| 74 | `list_protocol_tags` | GET | `/api/protocols/{protocol_id}/tags` |
| 75 | `list_tagged_protocols` | GET | `/api/tags/{tag_id}/protocols` |
| **Directives** | | | |
| 76 | `create_directive` | POST | `/api/directives` |
| 77 | `get_directive` | GET | `/api/directives/{directive_id}` |
| 78 | `list_directives` | GET | `/api/directives` |
| 79 | `update_directive` | PATCH | `/api/directives/{directive_id}` |
| 80 | `delete_directive` | DELETE | `/api/directives/{directive_id}` |
| 81 | `resolve_directives` | GET | `/api/directives/resolve` |
| 82 | `tag_directive` | POST | `/api/directives/{directive_id}/tags/{tag_id}` |
| 83 | `untag_directive` | DELETE | `/api/directives/{directive_id}/tags/{tag_id}` |
| 84 | `list_directive_tags` | GET | `/api/directives/{directive_id}/tags` |
| 85 | `list_tagged_directives` | GET | `/api/tags/{tag_id}/directives` |
| **Skills** | | | |
| 86 | `create_skill` | POST | `/api/skills` |
| 87 | `get_skill` | GET | `/api/skills/{skill_id}` |
| 88 | `get_skill_full` | GET | `/api/skills/{skill_id}/full` |
| 89 | `list_skills` | GET | `/api/skills` |
| 90 | `update_skill` | PATCH | `/api/skills/{skill_id}` |
| 91 | `delete_skill` | DELETE | `/api/skills/{skill_id}` |
| 92 | `list_skill_domains` | GET | `/api/skills/{skill_id}/domains` |
| 93 | `link_skill_domain` | POST | `/api/skills/{skill_id}/domains/{domain_id}` |
| 94 | `unlink_skill_domain` | DELETE | `/api/skills/{skill_id}/domains/{domain_id}` |
| 95 | `list_skill_protocols` | GET | `/api/skills/{skill_id}/protocols` |
| 96 | `link_skill_protocol` | POST | `/api/skills/{skill_id}/protocols/{protocol_id}` |
| 97 | `unlink_skill_protocol` | DELETE | `/api/skills/{skill_id}/protocols/{protocol_id}` |
| 98 | `list_skill_directives` | GET | `/api/skills/{skill_id}/directives` |
| 99 | `link_skill_directive` | POST | `/api/skills/{skill_id}/directives/{directive_id}` |
| 100 | `unlink_skill_directive` | DELETE | `/api/skills/{skill_id}/directives/{directive_id}` |
| **Batch Operations** | | | |
| 101 | `batch_create_tasks` | POST | `/api/tasks/batch` |
| 102 | `batch_create_activity` | POST | `/api/activity/batch` |
| 103 | `batch_create_artifacts` | POST | `/api/artifacts/batch` |
| 104 | `batch_create_protocols` | POST | `/api/protocols/batch` |
| 105 | `batch_create_directives` | POST | `/api/directives/batch` |
| 106 | `batch_create_skills` | POST | `/api/skills/batch` |
| 107 | `batch_tag_task` | POST | `/api/tasks/{task_id}/tags/batch` |
| 108 | `batch_tag_activity` | POST | `/api/activity/{activity_id}/tags/batch` |
| 109 | `batch_tag_artifact` | POST | `/api/artifacts/{artifact_id}/tags/batch` |

### Mapping Verification Results

**Status:** All 109 tools verified. Complete 1:1 correspondence confirmed.

- Every API endpoint has exactly one MCP tool.
- Every MCP tool calls a real, existing API endpoint.
- Parameter names match between tool definitions and API endpoints.
- Tool descriptions accurately reflect endpoint behavior.
- No orphaned tools (tools calling nonexistent endpoints).
- No missing tools (endpoints without corresponding tools).

---

## Composable Query Patterns — Cookbook

These patterns show how Claude composes multiple tool calls into workflows that serve the user's real needs. Each pattern is a multi-step interaction where Claude uses tool results to inform subsequent calls.

**Key principle:** The MCP tools are intentionally simple (1:1 with endpoints). The intelligence is in Claude's reasoning between calls. These patterns document that reasoning.

---

### Pattern 1: Energy-Matched Task Selection

**When to use:** The user checks in (explicitly or conversationally) and wants to know what to work on. The user's current energy and context determine which tasks are appropriate.

**Tool sequence:**

1. `create_checkin` — Record the user's current state
2. `list_tasks` — Filter tasks by energy ceiling and context
3. *(Present options to user)*
4. `update_task` — Mark selected task as active
5. `log_activity` — Record starting the task (with `energy_before`)

**What Claude does between calls:**

- After Step 1: Use the `energy_level` from the check-in to set `energy_cost_max` on the task query. If energy is 2, don't show energy-cost-4 tasks. Also use `context` to set the `context_required` filter.
- After Step 2: Rank the results by activation friction (lowest first) — the user has limited energy, so minimize startup cost. Present 3-5 options with a brief description of each.
- After Step 4: Optionally suggest a Pomodoro-style time box based on the task's typical duration.

**Example conversation flow:**

> **User:** I just woke up, feeling pretty groggy. Energy maybe a 2. I'm at home.
>
> **Claude:** *Calls `create_checkin(checkin_type="morning", energy_level=2, mood=null, focus_level=null, context="at home")`*
>
> **Claude:** *Calls `list_tasks(status="pending", energy_cost_max=2, friction_max=2, context_required="at home")`*
>
> **Claude:** Good morning! Given your energy level, here are some gentle tasks you can ease into:
> 1. **Sort mail on the counter** — errand, ~5 min, very low friction
> 2. **Review today's calendar** — admin, ~10 min, low friction
> 3. **Water the plants** — hands_on, ~5 min, very low friction
>
> Want to start one of these, or would you rather just ease into the morning?
>
> **User:** I'll sort the mail.
>
> **Claude:** *Calls `update_task(task_id="...", status="active")`*
> *Calls `log_activity(action_type="started", task_id="...", energy_before=2)`*

---

### Pattern 2: Context Batching

**When to use:** The user mentions a location or context, and Claude surfaces all available tasks for that context — across all domains and projects.

**Tool sequence:**

1. `list_tasks` — Filter by `context_required` and `status="pending"`
2. *(Present grouped results)*

**What Claude does between calls:**

- Match the user's stated context to the `context_required` field. The field is a string with partial matching, so "at computer" matches tasks tagged "at computer" or similar.
- Group results by project or domain for readability.
- Highlight overdue items first.

**Example conversation flow:**

> **User:** I'm heading to the store in 20 minutes. Anything I should handle while I'm out?
>
> **Claude:** *Calls `list_tasks(status="pending", cognitive_type="errand", context_required="store")`*
>
> **Claude:** You've got 3 errands that need a store trip:
> 1. **Buy new running shoes** (Health > C25K project) — due Friday
> 2. **Pick up printer ink** (Career) — overdue by 2 days
> 3. **Return the broken blender** (Home)
>
> The printer ink is overdue — might be worth prioritizing. Want me to mark any of these as active?

---

### Pattern 3: Morning Briefing Composition

**When to use:** Start of day. The user wants an overview of where things stand — routines due, overdue tasks, domain health.

**Tool sequence:**

1. `get_routine_adherence` — Check routine health for the current week
2. `list_tasks` — Get overdue tasks
3. `get_domain_balance` — Check for neglected domains
4. `list_routines` — Get today's routines (filter by status=active)
5. *(Synthesize into a briefing)*

**What Claude does between calls:**

- After Step 1: Note which routines have broken streaks or low adherence. These become "attention items."
- After Step 2: Count overdue tasks and note the most urgent ones.
- After Step 3: Identify any domain with `days_since_last_activity` > 7 as potentially neglected.
- After Step 4: Identify which active routines should be done today based on their schedules.
- Synthesize: Open with the most important item (overdue blockers > broken streaks > neglected domains), then provide a quick summary of the day ahead.

**Example conversation flow:**

> **User:** Good morning! What does today look like?
>
> **Claude:** *Calls `get_routine_adherence(after="2026-03-22T00:00:00", before="2026-03-29T00:00:00")`*
> *Calls `list_tasks(status="pending", overdue=true)`*
> *Calls `get_domain_balance()`*
> *Calls `list_routines(status="active")`*
>
> **Claude:** Good morning! Here's your Saturday briefing:
>
> **Heads up:** You have 2 overdue tasks — "Submit expense report" (3 days) and "Schedule dentist appointment" (5 days). The expense report has a real deadline, so that might be worth knocking out first.
>
> **Routines:** Morning meditation is on a 12-day streak — nice. Evening journaling has dropped to 36% adherence this week. Worth revisiting tonight?
>
> **Domain check:** Finances hasn't had any activity in 12 days. You have 4 pending tasks there, 3 of which are overdue.
>
> Want to start with a check-in so I can suggest tasks that match your energy?

---

### Pattern 4: Weekly Reflection

**When to use:** End of week. The user wants to look back at what they accomplished, how they felt, and where patterns are forming.

**Tool sequence:**

1. `get_activity_summary` — Week's aggregated stats
2. `get_domain_balance` — Current domain health
3. `get_routine_adherence` — Week's routine performance
4. `get_friction_analysis` — Friction calibration patterns
5. *(Synthesize into a reflection)*

**What Claude does between calls:**

- After Step 1: Note completion rate (completed vs skipped+deferred). Calculate energy delta trend — is the user ending tasks with more or less energy than they started?
- After Step 2: Compare to last week if user has historical context. Flag any domain that's trending toward neglect.
- After Step 3: Identify the strongest routine (highest adherence) and the weakest (lowest or broken streak). These become talking points.
- After Step 4: Look for friction miscalibration. If the user consistently overestimates friction for a cognitive type, that's a coaching insight ("You think errands are harder than they actually are").
- Synthesize: Lead with wins, then insights, then gentle recommendations. Frame everything constructively — this is a reflection, not a performance review.

**Example conversation flow:**

> **User:** Let's do the weekly review.
>
> **Claude:** *Calls all four report tools with this week's date range*
>
> **Claude:** Here's your week in review:
>
> **Activity:** 23 entries this week — 15 completed, 3 skipped, 5 deferred. You logged about 8 hours of focused work. Your average energy delta was +0.3, meaning tasks generally left you slightly more energized than when you started. That's a good sign.
>
> **Routines:** Morning meditation hit 89% (25/28 expected) — solid. Evening journaling dropped to 36%. That one's been slipping for two weeks now.
>
> **Domains:** Health and Career are getting regular attention. Finances hasn't been touched in 12 days — there are 3 overdue tasks there.
>
> **Friction insight:** You consistently overestimate friction for focus_work tasks (predicted 4.2, actual 3.1). Once you start, they're easier than you expect. Errands are the opposite — you underestimate how much friction they carry.
>
> What stands out to you? Anything you want to adjust for next week?

---

### Pattern 5: Streak Recovery

**When to use:** Claude detects (or the user mentions) that a routine streak has broken. The goal is to help the user recommit or consciously adjust the routine.

**Tool sequence:**

1. `list_routines` — Filter by `streak_broken=true`
2. `get_routine` — Get details on the broken routine(s)
3. *(Discuss with user)*
4. Either `complete_routine` (recommit) or `update_routine` (adjust frequency/retire)

**What Claude does between calls:**

- After Step 1: Identify how many routines have broken streaks. If it's just one, focus there. If it's several, there may be a capacity issue.
- After Step 2: Look at the routine's `best_streak` and `current_streak`. A routine that had a 30-day streak before breaking is different from one that never got past 3 days. Also check `energy_cost` and `activation_friction` — a high-friction routine that keeps breaking may need adjustment.
- During discussion: Avoid guilt. Frame the streak break as information, not failure. Offer concrete options: "Do you want to do it now and restart the streak? Lower the frequency? Or is this one you want to retire?"

**Example conversation flow:**

> **User:** I feel like I've been dropping the ball on my routines.
>
> **Claude:** *Calls `list_routines(status="active", streak_broken=true)`*
>
> **Claude:** Let me check... You have 2 routines with broken streaks:
>
> **Claude:** *Calls `get_routine(routine_id="...")` for each*
>
> **Claude:** Here's what I see:
>
> 1. **Evening journaling** — was on a 7-day streak, broke 4 days ago. This had a best streak of 14 days. Frequency: daily.
> 2. **Meal prep Sunday** — missed last Sunday. Best streak was 6 weeks. Frequency: weekly.
>
> The journaling has been struggling for a couple weeks now. Meal prep might just be a one-time miss. How do you want to handle these — restart, adjust, or let one go?

---

### Pattern 6: Domain Neglect Detection

**When to use:** Proactively (during a briefing or review), or when the user asks "what am I neglecting?" The goal is to surface life areas that are falling behind.

**Tool sequence:**

1. `get_domain_balance` — Get per-domain health metrics
2. `list_tasks` — Get pending tasks in the neglected domain(s)
3. *(Present findings with actionable suggestions)*

**What Claude does between calls:**

- After Step 1: Sort domains by `days_since_last_activity`. Anything over 7 days is worth flagging. Cross-reference with `overdue_tasks` — a neglected domain with overdue tasks is more urgent than one with pending-but-not-due tasks.
- After Step 2: Filter to low-energy, low-friction tasks in the neglected domain. The user is more likely to re-engage with something easy than something hard.
- Present: Frame it as "here's what I noticed" rather than "you're neglecting X." Offer one or two easy re-entry tasks.

**Example conversation flow:**

> **User:** What areas of my life need attention?
>
> **Claude:** *Calls `get_domain_balance()`*
>
> **Claude:** Finances stands out — no activity in 12 days, and 3 overdue tasks. Relationships is at 8 days with 1 overdue task. Everything else looks active.
>
> **Claude:** *Calls `list_tasks(status="pending", energy_cost_max=2, friction_max=2)` and filters results to the neglected domains*
>
> **Claude:** For Finances, the easiest re-entry point is "Review bank statement" — low energy, low friction, ~10 minutes. That could also help you spot anything urgent in the other 2 overdue tasks.
>
> For Relationships, "Text Alex back" is sitting there — 2 minutes, no friction. Want to knock that one out now?

---

### Pattern 7: Task Completion with Reflection

**When to use:** The user finishes a task and wants to log the experience. This captures energy impact and actual friction for the friction analysis report.

**Tool sequence:**

1. `update_task` — Mark as completed
2. `log_activity` — Record the experience with energy/friction data
3. *(Optionally)* `list_tasks` — Suggest next task based on updated energy

**What Claude does between calls:**

- After Step 1: Confirm completion to the user.
- During Step 2: Ask brief reflection questions — "How do you feel? Did that take more or less energy than expected?" Map answers to the `energy_before`, `energy_after`, and `friction_actual` fields.
- After Step 2: If the user's `energy_after` is still decent, offer to surface another task. Use the new energy level as the ceiling.

**Example conversation flow:**

> **User:** Done with the budget review!
>
> **Claude:** *Calls `update_task(task_id="...", status="completed")`*
>
> **Claude:** Nice work! Quick reflection — how are you feeling? More or less energy than when you started? And was the friction what you expected?
>
> **User:** Actually feel more focused now. Friction was lower than I expected, maybe a 2.
>
> **Claude:** *Calls `log_activity(action_type="completed", task_id="...", energy_before=3, energy_after=4, friction_actual=2, duration_minutes=25)`*
>
> **Claude:** Logged. Interesting — you predicted friction of 3 but experienced 2. That's consistent with a pattern I've noticed: your focus_work tasks tend to be easier than you expect once you get started.
>
> Your energy is at 4 now — want to ride the momentum? I've got some medium-energy tasks that could work.

---

### Pattern 8: Routine Completion with Activity Logging

**When to use:** The user completes a routine. Since `complete_routine` does not automatically log activity, this pattern chains both operations.

**Tool sequence:**

1. `complete_routine` — Record the completion, update streak
2. `log_activity` — Record the experience linked to the routine
3. *(Report streak status)*

**What Claude does between calls:**

- After Step 1: Check the streak status from the response. If the streak was broken and just recovered, celebrate it. If it's a new best streak, note that.
- During Step 2: Capture how the user felt about the routine.

**Example conversation flow:**

> **User:** Just finished meditating.
>
> **Claude:** *Calls `complete_routine(routine_id="e5f6a7b8-...")`*
>
> **Claude:** Recorded! That's day 13 of your streak. How did it feel today?
>
> **User:** Good, really calming. Feel more focused.
>
> **Claude:** *Calls `log_activity(action_type="completed", routine_id="e5f6a7b8-...", energy_after=4, mood_rating=4, notes="Calming, improved focus")`*
>
> **Claude:** Logged. 13-day streak and counting — you're closing in on your best of 30.

### Pattern 9: Agent Session Bootstrap

**Scenario:** A specialized agent (e.g., Apollo Swagger) starts a session and needs to load its full operating context.

**Tool chain:**

1. `list_skills(is_default=true)` — find the default skill, or `list_skills(search="core-protocol")` for a specific one
2. `get_skill_full(skill_id="...")` — load everything: domains, protocols, directives (grouped and prioritized)
3. `resolve_directives(skill_id="...", scope_ref="...")` — optionally resolve agent-specific directives

**Why this works:** `get_skill_full` is a single-call bootstrap. It returns protocols with steps, directives sorted by priority (global first, then skill-scoped), linked domains, and the skill's artifact. The agent has everything it needs to operate without multiple round trips.

**Conversation flow:**

> **User:** (activates Apollo Swagger agent)
>
> **Claude:** *Calls `get_skill_full(skill_id="c3d4e5f6-...")`*
>
> **Claude:** Context loaded. I have 3 protocols (session-startup, bug-triage, release-process), 5 global directives, and 2 skill-specific directives. My highest-priority rule is "Document reality, not intent" (priority 9). Ready to work.

### Pattern 10: Seeding a New Skill with Batch Operations

**Scenario:** Setting up a new agent operating mode with protocols, directives, and a reference artifact.

**Tool chain:**

1. `create_artifact(title="Agent Brief", artifact_type="brief", content="...")` — create reference doc
2. `batch_create_protocols(items=[...])` — create multiple protocols at once
3. `batch_create_directives(items=[...])` — create behavioral rules
4. `create_skill(name="new-agent", artifact_id="...", protocol_ids=[...], directive_ids=[...])` — link everything

**Why this works:** Batch operations reduce round trips and ensure atomicity. If any protocol fails validation, none are created — no partial state. The skill creation ties everything together with bulk linking at creation time.

### Pattern 11: Cross-Entity Tag Discovery

**Scenario:** Finding all BRAIN content related to a specific topic using tags.

**Tool chain:**

1. `list_tags(search="session")` — find the tag
2. `list_tagged_artifacts(tag_id="...")` — reference docs
3. `list_tagged_protocols(tag_id="...")` — procedures
4. `list_tagged_directives(tag_id="...")` — rules
5. `list_tagged_activities(tag_id="...")` — activity history

**Why this works:** Tags are the universal cross-cutting label in BRAIN. Any taggable entity (tasks, activities, artifacts, protocols, directives) can be discovered through reverse tag lookups. This pattern builds a complete picture of everything related to a topic.

---

## Integration Guide

### Prerequisites

- **Python 3.12+** installed and on your PATH
- **BRAIN 3.0 API** running and accessible (see the [brain3 README](https://github.com/WilliM233/brain3) for setup)
- A Claude client that supports MCP: **Claude Desktop**, **Claude Code**, or the **MCP Inspector** for testing

### Installation

```bash
cd brain3-mcp/mcp
pip install -r requirements.txt
```

### Configuration

The MCP server needs to know where the BRAIN 3.0 API is running. Default: `http://localhost:8000`.

**Override via environment variable:**

```bash
export BRAIN3_API_URL="http://192.168.1.100:8000"
```

The environment variable is read at server startup. If the API moves to a different host or port, update the variable and restart the MCP server.

### Claude Desktop Configuration

Add the following to your Claude Desktop config file:

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "brain3": {
      "command": "python",
      "args": ["/absolute/path/to/brain3-mcp/mcp/server.py"],
      "env": {
        "BRAIN3_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

Replace `/absolute/path/to/` with the actual path to your `brain3-mcp` directory.

### Claude Code Configuration

Add to your project `.mcp.json` or Claude Code settings:

```json
{
  "mcpServers": {
    "brain3": {
      "command": "python",
      "args": ["/absolute/path/to/brain3-mcp/mcp/server.py"],
      "env": {
        "BRAIN3_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

### Testing with MCP Inspector

For standalone testing without Claude:

```bash
cd brain3-mcp/mcp
mcp dev server.py
```

This launches a web UI where you can invoke each tool individually and inspect responses.

### Verification

After configuration, verify the connection:

1. Open Claude (Desktop or Code)
2. The BRAIN 3.0 tools should appear in Claude's tool list
3. Ask Claude: "Check if the BRAIN API is connected" — Claude should call `health_check` and report the status
4. If `health_check` returns `{"status": "healthy", "database": "connected"}`, everything is working

### Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| "Cannot connect to BRAIN 3.0 API" | API server not running or wrong URL | Start the API: `cd brain3 && uvicorn app.main:app --reload`. Check `BRAIN3_API_URL` points to the correct address. |
| Tools not appearing in Claude | Config file not loaded | Restart Claude Desktop/Code after editing the config. Verify the JSON is valid (no trailing commas). Check that `python` is on your PATH. |
| "Request timed out" | API is slow or under heavy load | Default timeout is 30 seconds. Check API health directly: `curl http://localhost:8000/health` |
| API errors passed through | Expected behavior | The MCP passes API error messages (validation errors, 404s) directly to Claude so it can understand what went wrong and self-correct. This is by design. |
| "Invalid UUID" errors | Wrong ID format | All entity IDs are UUIDs (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`). Use `list_*` tools to find valid IDs. |
| Permission/path errors on startup | Python can't find the server file | Use absolute paths in the config. Verify the path exists. |

### Authentication

BRAIN 3.0 v1.0.0 runs without authentication. This is by design for a single-user system. Authentication will be added in a future phase. The HTTP client layer is designed so adding a Bearer token is a one-line change when that time comes.

---

## Error Reference

The MCP server has three distinct error tiers. Each produces a different message format so Claude (and the user) can diagnose the problem.

### Tier 1: API Returned an Error

**What happened:** The HTTP request reached the BRAIN 3.0 API, but the API returned a 4xx or 5xx status code.

**Message format:**

```
API error (STATUS_CODE): DETAIL_MESSAGE
```

**Common scenarios:**

| Status | Scenario | Example Message |
|--------|----------|-----------------|
| 404 | Entity not found | `API error (404): Domain not found` |
| 422 | Validation failed | `API error (422): [{"loc": ["body", "title"], "msg": "field required", "type": "value_error.missing"}]` |
| 409 | Conflict (e.g., duplicate) | `API error (409): Tag with this name already exists` |

**What Claude should do:** Read the error detail and adjust. A 404 means the ID is wrong — try `list_*` to find the correct one. A 422 means a required field is missing or a value is invalid — check the parameters and retry.

### Tier 2: API Unreachable

**What happened:** The MCP server could not connect to the BRAIN 3.0 API at all. The HTTP request never reached the server.

**Message format:**

```
Cannot connect to BRAIN 3.0 API at {url}. Is the API running?
```

or

```
Request to BRAIN 3.0 API timed out (METHOD /path).
```

**Common causes:**

- The BRAIN 3.0 API is not running
- `BRAIN3_API_URL` points to the wrong host or port
- A firewall is blocking the connection
- The API server crashed

**What Claude should do:** Tell the user the API is unreachable and suggest they check if it's running. Do not retry repeatedly — one retry is reasonable, then inform the user.

### Tier 3: Invalid Tool Parameters

**What happened:** The MCP server caught an invalid parameter **before** making the HTTP request. This is pre-flight validation.

**Message format:**

```
Invalid PARAM_NAME: 'VALUE' is not a valid UUID. Expected format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

```
Invalid PARAM_NAME: 'VALUE'. Must be one of: value1, value2, value3
```

```
Invalid PARAM_NAME: VALUE is out of range. Must be between MIN and MAX.
```

```
Missing required parameter: PARAM_NAME. Must be a non-empty string.
```

**Validated before request:**

| Validation | Fields | Rule |
|------------|--------|------|
| UUID format | All `*_id` parameters | Must be valid UUID |
| Enum values | `status`, `cognitive_type`, `frequency`, `checkin_type`, `action_type`, `day_of_week` | Must match allowed values |
| Range | `energy_cost`, `activation_friction`, `energy_level`, `mood`, `focus_level`, `energy_before`, `energy_after`, `mood_rating`, `friction_actual`, `energy_cost_min/max`, `friction_min/max` | Must be integer between 1 and 5 |
| Required strings | `name` (domains, tags), `title` (goals, projects, tasks, routines), `time_of_day` | Must be non-empty string |

**What Claude should do:** Read the validation message, fix the parameter, and retry. These errors are self-explanatory and always include the valid options.

---

*MCP Tool Guide · Apollo Swagger · BRAIN 3.0 v1.2.0 · April 2026*
*Project Flux Meridian · March 2026*
