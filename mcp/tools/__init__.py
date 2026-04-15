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
from tools.habits import register as register_habits
from tools.checkins import register as register_checkins
from tools.activity import register as register_activity
from tools.reports import register as register_reports
from tools.artifacts import register as register_artifacts
from tools.protocols import register as register_protocols
from tools.directives import register as register_directives
from tools.skills import register as register_skills
from tools.notifications import register as register_notifications
from tools.batch import register as register_batch
from tools.rules import register as register_rules


def register_all(mcp, api) -> None:
    """Register all tool modules with the MCP server."""
    register_domains(mcp, api)
    register_goals(mcp, api)
    register_projects(mcp, api)
    register_tasks(mcp, api)
    register_tags(mcp, api)
    register_routines(mcp, api)
    register_habits(mcp, api)
    register_checkins(mcp, api)
    register_activity(mcp, api)
    register_reports(mcp, api)
    register_artifacts(mcp, api)
    register_protocols(mcp, api)
    register_directives(mcp, api)
    register_skills(mcp, api)
    register_notifications(mcp, api)
    register_batch(mcp, api)
    register_rules(mcp, api)
