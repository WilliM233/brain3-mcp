"""Graduation, frequency step-down, and stacking recommendation tools."""

from validation import validate_uuid
from tools._helpers import params, strip_nones


def register(mcp, api) -> None:
    """Register graduation tools with the MCP server."""

    @mcp.tool()
    async def evaluate_graduation(habit_id: str) -> dict:
        """Check if a habit is ready to graduate from active scaffolding.

        Returns the current "already done" rate, progress toward the
        graduation target, and blocking reasons if not yet eligible. Use
        this to show the user their progress or to check readiness before
        recommending graduation.

        When to use: during session reviews, when discussing habit
        progress, before suggesting graduation. "Let me check how your
        brushing habit is doing..."
        """
        validate_uuid(habit_id, "habit_id")
        return await api.post(
            f"/api/habits/{habit_id}/evaluate-graduation"
        )

    @mcp.tool()
    async def graduate_habit(
        habit_id: str,
        force: bool = False,
    ) -> dict:
        """Graduate a habit from active scaffolding.

        Stops individual nudge notifications while keeping the habit in
        routine checklists. Requires the habit to meet graduation criteria
        unless force=true.

        Re-scaffolded habits face tighter criteria on subsequent
        graduations. The default flow is: evaluate_graduation -> discuss
        with user -> graduate_habit. Use force=true only when the user
        explicitly agrees despite not meeting criteria.
        """
        validate_uuid(habit_id, "habit_id")
        body = strip_nones({"force": force if force else None})
        return await api.post(
            f"/api/habits/{habit_id}/graduate", json=body or None
        )

    @mcp.tool()
    async def evaluate_frequency(habit_id: str) -> dict:
        """Check if a habit's notification frequency should step down.

        Evaluates the "already done" rate over recent notifications and
        checks cooldown status. Steps go: daily -> every other day ->
        twice a week -> weekly.

        When to use: during habit check-ins, when the user mentions a
        habit feels easy, or when reviewing notification settings.
        "You've been ahead of the reminders -- let me check if we can
        reduce them."
        """
        validate_uuid(habit_id, "habit_id")
        return await api.post(
            f"/api/habits/{habit_id}/evaluate-frequency"
        )

    @mcp.tool()
    async def step_down_frequency(habit_id: str) -> dict:
        """Reduce a habit's notification frequency by one level.

        Progression: daily -> every other day -> twice a week -> weekly.
        Validates that step-down is recommended before applying. Does not
        skip levels.

        When to use: after reviewing frequency evaluation with the user.
        Default flow: evaluate_frequency -> discuss -> step_down_frequency.
        Can also be proactive during session wrap-up: "I noticed your
        brushing is consistently ahead of reminders -- stepped down to
        every other day."
        """
        validate_uuid(habit_id, "habit_id")
        return await api.post(
            f"/api/habits/{habit_id}/step-down-frequency"
        )

    @mcp.tool()
    async def evaluate_slip(habit_id: str) -> dict:
        """Check if a graduated habit shows signs of regression.

        Looks for missed completions and routine checklist gaps. Returns
        severity-graded slip signals and a recommendation (re-scaffold,
        monitor, or no action).

        When to use: when reviewing graduated habits during sessions,
        when the user mentions struggling with a previously-graduated
        habit, or when reviewing routine checklist partial completions.
        """
        validate_uuid(habit_id, "habit_id")
        return await api.post(
            f"/api/habits/{habit_id}/evaluate-slip"
        )

    @mcp.tool()
    async def re_scaffold_habit(habit_id: str) -> dict:
        """Reverse graduation and return a habit to daily accountability.

        Used when a graduated habit has slipped. The habit's graduation
        criteria are tightened for next time -- the system demands
        stronger evidence before re-graduating. Streaks are preserved.

        When to use: after detecting a slip and discussing with the user.
        Frame positively: "Re-scaffolding isn't failure -- it means the
        system is adapting to support you. We'll bring back daily
        reminders and the bar for next graduation will be a bit higher."
        """
        validate_uuid(habit_id, "habit_id")
        return await api.post(
            f"/api/habits/{habit_id}/re-scaffold"
        )

    @mcp.tool()
    async def get_graduation_status(habit_id: str) -> dict:
        """Get a habit's full graduation dashboard.

        Returns current scaffolding status, notification frequency,
        progress toward graduation, frequency step-down eligibility,
        and re-scaffold history. Use this for comprehensive habit reviews.

        When to use: as the first call when discussing a specific habit's
        scaffolding journey. Gives all the context in one call instead of
        needing to run evaluate_graduation + evaluate_frequency separately.
        """
        validate_uuid(habit_id, "habit_id")
        return await api.get(
            f"/api/habits/{habit_id}/graduation-status"
        )

    @mcp.tool()
    async def get_stacking_recommendation(routine_id: str) -> dict:
        """Check if a routine is ready for a new habit and suggest what to introduce next.

        Evaluates whether all current accountable habits are stable.
        Recommends paused habits first (give them another shot), then
        tracking habits (next in the routine's order). One habit at a
        time prevents the stacking-and-abandoning pattern.

        When to use: during routine reviews, especially when the user is
        excited about adding habits. The recommendation serves as both a
        guard ("hold steady, flossing needs more time") and an
        encouragement ("you've been solid -- ready to add face washing?").
        """
        validate_uuid(routine_id, "routine_id")
        return await api.get(
            "/api/graduation/suggest-next",
            params=params(routine_id=routine_id),
        )
