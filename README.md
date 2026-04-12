# BRAIN 3.0 MCP Server

MCP (Model Context Protocol) server that gives Claude full access to the BRAIN 3.0 API. Every API endpoint is exposed as a tool Claude can call — 109 tools covering the seven pillars, knowledge layer, batch operations, and reporting. Turns your task/routine/goal/knowledge database into a conversational partner.

## Project Structure

```
brain3-mcp/
├── README.md              ← Setup, config, tool inventory (you are here)
├── LICENSE                ← AGPL-3.0
├── docs/
│   └── MCP_TOOL_GUIDE.md ← Detailed tool reference with usage patterns
└── mcp/
    ├── server.py          ← MCP server entry point + health_check tool
    ├── client.py          ← Async HTTP client for the BRAIN 3.0 API
    ├── validation.py      ← Input validation helpers (UUID, enum, range)
    ├── requirements.txt   ← Python dependencies (mcp, httpx)
    └── tools/             ← Tool definitions organized by entity
        ├── __init__.py    ← register_all(mcp, api) orchestrator
        ├── _helpers.py    ← Shared utilities (strip_nones, params)
        ├── activity.py    ← Activity logging + tagging (9 tools)
        ├── artifacts.py   ← Document storage + tagging (9 tools)
        ├── batch.py       ← Batch create + batch tag (9 tools)
        ├── habits.py      ← Habit CRUD + completion (6 tools)
        ├── checkins.py    ← Check-in CRUD (5 tools)
        ├── directives.py  ← Behavioral rules + tagging + resolve (10 tools)
        ├── domains.py     ← Life domain CRUD (5 tools)
        ├── goals.py       ← Goal CRUD (5 tools)
        ├── projects.py    ← Project CRUD (5 tools)
        ├── protocols.py   ← Procedure CRUD + tagging (9 tools)
        ├── reports.py     ← Analytics endpoints (4 tools)
        ├── routines.py    ← Routine CRUD + scheduling (9 tools)
        ├── skills.py      ← Operating modes + entity linking (15 tools)
        ├── tags.py        ← Tag CRUD (5 tools)
        └── tasks.py       ← Task CRUD + tagging (9 tools)
```

Each module in `tools/` exports a `register(mcp, api)` function that defines tools using `@mcp.tool()` decorators. The `__init__.py` orchestrates registration by calling each module's `register()` function via `register_all(mcp, api)`. Adding a new tool means adding a function in the appropriate entity module — no changes to `__init__.py` or `server.py` needed.

## Prerequisites

- Python 3.12+
- BRAIN 3.0 API running (default: `http://localhost:8000`)
- Compatible with: brain3 v1.2.0+

## Installation

```bash
cd brain3-mcp/mcp
pip install -r requirements.txt
```

## Configuration

The API base URL is configured via the `BRAIN3_API_URL` environment variable:

```bash
export BRAIN3_API_URL="http://localhost:8000"  # default
```

## Running

### Standalone (for testing with MCP Inspector)

```bash
cd brain3-mcp/mcp
mcp dev server.py
```

This launches a web UI where you can test each tool individually.

### Claude Desktop

Add this to your Claude Desktop configuration file:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "brain3": {
      "command": "python",
      "args": ["D:/_DEVELOPMENT/brain3-mcp/mcp/server.py"],
      "env": {
        "BRAIN3_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

### Claude Code

Add to your Claude Code settings or project `.mcp.json`:

```json
{
  "mcpServers": {
    "brain3": {
      "command": "python",
      "args": ["D:/_DEVELOPMENT/brain3-mcp/mcp/server.py"],
      "env": {
        "BRAIN3_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

## Available Tools (115)

### Health Check (1)
| Tool | Description |
|------|-------------|
| `health_check` | Verify API connectivity and database status |

### Domains (5)
| Tool | Description |
|------|-------------|
| `create_domain` | Create a life domain (e.g. Health, Career) |
| `list_domains` | List all domains |
| `get_domain` | Get domain with nested goals |
| `update_domain` | Update domain details |
| `delete_domain` | Delete a domain |

### Goals (5)
| Tool | Description |
|------|-------------|
| `create_goal` | Create a goal under a domain |
| `list_goals` | List goals (filter by domain, status) |
| `get_goal` | Get goal with nested projects |
| `update_goal` | Update goal details |
| `delete_goal` | Delete a goal |

### Projects (5)
| Tool | Description |
|------|-------------|
| `create_project` | Create a project under a goal |
| `list_projects` | List projects (filter by goal, status, deadline, overdue) |
| `get_project` | Get project with nested tasks and progress |
| `update_project` | Update project details |
| `delete_project` | Delete a project |

### Tasks (9)
| Tool | Description |
|------|-------------|
| `create_task` | Create a task with ADHD-aware metadata |
| `list_tasks` | List tasks with 12 composable filters |
| `get_task` | Get task with tags |
| `update_task` | Update task details or status |
| `delete_task` | Delete a task |
| `tag_task` | Attach a tag to a task |
| `untag_task` | Remove a tag from a task |
| `list_task_tags` | List tags on a task |
| `list_tagged_tasks` | List tasks with a specific tag |

### Tags (5)
| Tool | Description |
|------|-------------|
| `create_tag` | Create a tag (get-or-create semantics) |
| `list_tags` | List/search tags |
| `get_tag` | Get a tag |
| `update_tag` | Update tag name or color |
| `delete_tag` | Delete a tag |

### Routines (9)
| Tool | Description |
|------|-------------|
| `create_routine` | Create a routine with frequency and energy metadata |
| `list_routines` | List routines (filter by domain, status, frequency, streak) |
| `get_routine` | Get routine with schedules and streak info |
| `update_routine` | Update routine details |
| `delete_routine` | Delete a routine |
| `complete_routine` | Record completion and evaluate streak |
| `add_routine_schedule` | Add a schedule entry (day + time) |
| `list_routine_schedules` | List schedule entries |
| `delete_routine_schedule` | Remove a schedule entry |

### Habits (6)
| Tool | Description |
|------|-------------|
| `create_habit` | Create a new habit (standalone or under a routine) |
| `get_habit` | Get habit with parent routine info |
| `list_habits` | List habits with filters (routine, status, scaffolding) |
| `update_habit` | Update habit details or scaffolding status |
| `delete_habit` | Delete a habit |
| `complete_habit` | Record individual habit completion (idempotent) |

### Check-ins (5)
| Tool | Description |
|------|-------------|
| `create_checkin` | Log energy, mood, and focus levels |
| `list_checkins` | List check-ins (filter by type, context, date range) |
| `get_checkin` | Get a check-in |
| `update_checkin` | Update check-in details |
| `delete_checkin` | Delete a check-in |

### Activity Log (9)
| Tool | Description |
|------|-------------|
| `log_activity` | Record what happened and how it felt (optional tag_ids) |
| `list_activity` | List activity (filter by type, task, routine, dates, tags) |
| `get_activity` | Get activity entry with resolved references |
| `update_activity` | Update an activity entry |
| `delete_activity` | Delete an activity entry |
| `tag_activity` | Attach a tag to an activity entry |
| `untag_activity` | Remove a tag from an activity entry |
| `list_activity_tags` | List tags on an activity entry |
| `list_tagged_activities` | List activity entries with a specific tag |

### Reports (4)
| Tool | Description |
|------|-------------|
| `get_activity_summary` | Aggregated stats for a date range |
| `get_domain_balance` | Per-domain item counts and recency |
| `get_routine_adherence` | Completion rates and streak health |
| `get_friction_analysis` | Predicted vs actual friction patterns |

### Artifacts (9)
| Tool | Description |
|------|-------------|
| `create_artifact` | Store a reference document (CLAUDE.md, briefs, templates, etc.) |
| `get_artifact` | Retrieve a document with full content |
| `list_artifacts` | Browse documents by type, tags, seedability, or search |
| `update_artifact` | Update a document (auto-increments version) |
| `delete_artifact` | Remove a document |
| `tag_artifact` | Tag a document |
| `untag_artifact` | Remove a tag from a document |
| `list_artifact_tags` | List tags on a document |
| `list_tagged_artifacts` | Find all artifacts with a specific tag |

### Protocols (9)
| Tool | Description |
|------|-------------|
| `create_protocol` | Define a step-by-step procedure |
| `get_protocol` | Load a protocol with steps and linked artifact |
| `list_protocols` | Browse available protocols |
| `update_protocol` | Modify a protocol (auto-increments version) |
| `delete_protocol` | Remove a protocol |
| `tag_protocol` | Tag a protocol |
| `untag_protocol` | Remove a tag from a protocol |
| `list_protocol_tags` | List tags on a protocol |
| `list_tagged_protocols` | Find all protocols with a specific tag |

### Directives (10)
| Tool | Description |
|------|-------------|
| `create_directive` | Define a behavioral rule or guardrail |
| `get_directive` | Read a specific directive |
| `list_directives` | Browse directives (scope, priority, tag filters) |
| `update_directive` | Modify a directive |
| `delete_directive` | Remove a directive |
| `resolve_directives` | Get merged directive set for a skill + agent context |
| `tag_directive` | Tag a directive |
| `untag_directive` | Remove a tag from a directive |
| `list_directive_tags` | List tags on a directive |
| `list_tagged_directives` | Find all directives with a specific tag |

### Skills (15)
| Tool | Description |
|------|-------------|
| `create_skill` | Define an operating mode with linked entities |
| `get_skill` | Get a skill with relationships |
| `get_skill_full` | **Bootstrap tool** — load complete skill context |
| `list_skills` | Browse available operating modes |
| `update_skill` | Modify a skill's properties |
| `delete_skill` | Remove a skill |
| `list_skill_domains` | List domains linked to a skill |
| `link_skill_domain` | Associate a domain with a skill |
| `unlink_skill_domain` | Remove domain association |
| `list_skill_protocols` | List protocols linked to a skill |
| `link_skill_protocol` | Associate a protocol with a skill |
| `unlink_skill_protocol` | Remove protocol association |
| `list_skill_directives` | List directives linked to a skill |
| `link_skill_directive` | Associate a directive with a skill |
| `unlink_skill_directive` | Remove directive association |

### Batch Operations (9)
| Tool | Description |
|------|-------------|
| `batch_create_tasks` | Create multiple tasks atomically (max 100) |
| `batch_create_activity` | Log multiple activities atomically (max 100) |
| `batch_create_artifacts` | Store multiple documents atomically (max 100) |
| `batch_create_protocols` | Create multiple protocols atomically (max 100) |
| `batch_create_directives` | Create multiple directives atomically (max 100) |
| `batch_create_skills` | Create multiple skills atomically (max 100) |
| `batch_tag_task` | Attach multiple tags to a task at once |
| `batch_tag_activity` | Attach multiple tags to an activity at once |
| `batch_tag_artifact` | Attach multiple tags to an artifact at once |

## Troubleshooting

**"Cannot connect to BRAIN 3.0 API"**
- Make sure the brain3 API is running: `cd brain3 && uvicorn app.main:app --reload`
- Check `BRAIN3_API_URL` points to the correct address

**Tools not appearing in Claude**
- Restart Claude Desktop/Code after updating the config
- Check the config JSON is valid (no trailing commas)
- Verify Python is on your PATH

**API errors being passed through**
- This is expected behavior. The MCP passes API error messages (e.g. validation errors, 404s) directly to Claude so it can understand what went wrong and adjust.

## Architecture

The MCP server is a **thin, stateless translation layer**. It makes no decisions — Claude's intelligence handles reasoning and composition. The server translates tool calls into HTTP requests and returns the API response.

```
Claude Desktop / Claude Code
        | stdio
   brain3-mcp (this server)
        | HTTP (httpx)
   brain3 FastAPI (localhost or TrueNAS IP)
        |
   PostgreSQL
```

**Design principles:**
- **1:1 mapping** — one MCP tool per API endpoint. No composite or "smart" tools in Phase 1.
- **Stateless** — all state lives in the BRAIN 3.0 database. Nothing stored locally.
- **Descriptions for Claude** — tool descriptions are written as guidance for a partner, not dry API docs.
- **Fail clearly** — three error paths (API error passthrough, API unreachable, invalid input) each return a meaningful message.

## Related

- [BRAIN 3.0 API](https://github.com/WilliM233/brain3) — FastAPI backend
