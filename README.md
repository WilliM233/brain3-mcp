# BRAIN 3.0 MCP Server

MCP (Model Context Protocol) server that gives Claude full access to the BRAIN 3.0 API. Every API endpoint is exposed as a tool Claude can call, turning your task/routine/goal database into a conversational partner.

## Prerequisites

- Python 3.12+
- BRAIN 3.0 API running (default: `http://localhost:8000`)
- Compatible with: brain3 v1.1.0+

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

## Available Tools (53)

### Health Check
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

### Tasks (5)
| Tool | Description |
|------|-------------|
| `create_task` | Create a task with ADHD-aware metadata |
| `list_tasks` | List tasks with 12 composable filters |
| `get_task` | Get task with tags |
| `update_task` | Update task details or status |
| `delete_task` | Delete a task |

### Tags (13)
| Tool | Description |
|------|-------------|
| `create_tag` | Create a tag (get-or-create semantics) |
| `list_tags` | List/search tags |
| `get_tag` | Get a tag |
| `update_tag` | Update tag name or color |
| `delete_tag` | Delete a tag |
| `tag_task` | Attach a tag to a task |
| `untag_task` | Remove a tag from a task |
| `list_task_tags` | List tags on a task |
| `list_tagged_tasks` | List tasks with a specific tag |
| `tag_activity` | Attach a tag to an activity log entry |
| `untag_activity` | Remove a tag from an activity log entry |
| `list_activity_tags` | List tags on an activity log entry |
| `list_tagged_activities` | List activity entries with a specific tag |

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

### Check-ins (5)
| Tool | Description |
|------|-------------|
| `create_checkin` | Log energy, mood, and focus levels |
| `list_checkins` | List check-ins (filter by type, context, date range) |
| `get_checkin` | Get a check-in |
| `update_checkin` | Update check-in details |
| `delete_checkin` | Delete a check-in |

### Activity Log (5)
| Tool | Description |
|------|-------------|
| `log_activity` | Record what happened and how it felt (optional tag_ids for tagging at creation) |
| `list_activity` | List activity (filter by type, task, routine, dates, tags) |
| `get_activity` | Get activity entry with resolved references |
| `update_activity` | Update an activity entry |
| `delete_activity` | Delete an activity entry |

### Reports (4)
| Tool | Description |
|------|-------------|
| `get_activity_summary` | Aggregated stats for a date range |
| `get_domain_balance` | Per-domain item counts and recency |
| `get_routine_adherence` | Completion rates and streak health |
| `get_friction_analysis` | Predicted vs actual friction patterns |

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

## Related

- [BRAIN 3.0 API](https://github.com/WilliM233/brain3) — FastAPI backend
