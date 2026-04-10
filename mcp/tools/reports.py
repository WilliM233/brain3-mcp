"""Reporting and aggregation tools."""

from validation import validate_required_str
from tools._helpers import params


def register(mcp, api) -> None:
    """Register reporting tools with the MCP server."""

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
            params=params(after=after, before=before),
        )
