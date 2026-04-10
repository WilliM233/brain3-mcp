"""Tool registration for the BRAIN 3.0 MCP server.

Imports all tool modules and registers them with the MCP server instance.
Each module defines a register(mcp, api) function that attaches tools.
"""

from tools.domains import register as register_domains
from tools.goals import register as register_goals
from tools.projects import register as register_projects
from tools.tasks import register as register_tasks
from tools.tags import register as register_tags
from tools.routines import register as register_routines
from tools.checkins import register as register_checkins
from tools.activity import register as register_activity
from tools.reports import register as register_reports


def register_all(mcp, api) -> None:
    """Register all tool modules with the MCP server."""
    register_domains(mcp, api)
    register_goals(mcp, api)
    register_projects(mcp, api)
    register_tasks(mcp, api)
    register_tags(mcp, api)
    register_routines(mcp, api)
    register_checkins(mcp, api)
    register_activity(mcp, api)
    register_reports(mcp, api)
