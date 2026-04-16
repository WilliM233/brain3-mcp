"""Rules engine CRUD and evaluation tools."""

from validation import (
    InputValidationError,
    validate_enum,
    validate_uuid,
    validate_required_str,
    RULE_ENTITY_TYPES,
    RULE_METRICS,
    RULE_OPERATORS,
    NOTIFICATION_TYPES,
)
from tools._helpers import params, strip_nones


def register(mcp, api) -> None:
    """Register rules engine tools with the MCP server."""

    @mcp.tool()
    async def create_rule(
        name: str,
        entity_type: str,
        metric: str,
        operator: str,
        threshold: int,
        notification_type: str,
        message_template: str,
        entity_id: str | None = None,
        enabled: bool = True,
        cooldown_hours: int = 24,
    ) -> dict:
        """Create a new rule in the BRAIN rules engine.

        Rules are simple conditional logic: when a metric on an entity type
        meets a threshold, create a notification. Use this to set up
        automated nudges, alerts, and pattern-based interventions.

        Entity types: habit, task, routine, checkin.
        Metrics: consecutive_skips, days_untouched, non_responses,
        streak_length.
        Operators: must be sent as symbols — ">=", "<=", "==".

        Message templates support placeholders: {entity_name},
        {entity_type}, {metric_value}, {threshold}, {rule_name}.

        Set entity_id to target a specific entity, or omit it for a
        rule that applies to all entities of that type.
        """
        validate_required_str(name, "name")
        validate_required_str(entity_type, "entity_type")
        validate_required_str(metric, "metric")
        validate_required_str(operator, "operator")
        validate_required_str(notification_type, "notification_type")
        validate_required_str(message_template, "message_template")
        validate_enum(entity_type, "entity_type", RULE_ENTITY_TYPES)
        validate_enum(metric, "metric", RULE_METRICS)
        validate_enum(operator, "operator", RULE_OPERATORS)
        validate_enum(notification_type, "notification_type", NOTIFICATION_TYPES)
        validate_uuid(entity_id, "entity_id")
        if not isinstance(threshold, int) or threshold < 0:
            raise InputValidationError(
                f"Invalid threshold: {threshold}. Must be a non-negative integer."
            )
        if cooldown_hours < 0:
            raise InputValidationError(
                f"Invalid cooldown_hours: {cooldown_hours}. "
                "Must be a non-negative integer."
            )
        body = strip_nones({
            "name": name,
            "entity_type": entity_type,
            "metric": metric,
            "operator": operator,
            "threshold": threshold,
            "notification_type": notification_type,
            "message_template": message_template,
            "entity_id": entity_id,
            "enabled": enabled,
            "cooldown_hours": cooldown_hours,
        })
        return await api.post("/api/rules/", json=body)

    @mcp.tool()
    async def list_rules(
        entity_type: str | None = None,
        enabled: bool | None = None,
        notification_type: str | None = None,
        entity_id: str | None = None,
    ) -> list:
        """List rules with optional filters.

        Use to review what rules exist and their current state. All filter
        parameters are optional and combine with AND logic.

        Common patterns:
        - Review active rules: enabled=true
        - Rules for a specific entity type: entity_type="habit"
        - Rules targeting a specific entity: entity_id=<uuid>
        """
        validate_enum(entity_type, "entity_type", RULE_ENTITY_TYPES)
        validate_enum(notification_type, "notification_type", NOTIFICATION_TYPES)
        validate_uuid(entity_id, "entity_id")
        return await api.get(
            "/api/rules/",
            params=params(
                entity_type=entity_type,
                enabled=enabled,
                notification_type=notification_type,
                entity_id=entity_id,
            ),
        )

    @mcp.tool()
    async def get_rule(rule_id: str) -> dict:
        """Get a single rule by ID.

        Returns full rule details including last_triggered_at, enabled
        status, and all configuration. Use this to inspect a specific
        rule's current state before tuning or testing it.
        """
        validate_uuid(rule_id, "rule_id")
        return await api.get(f"/api/rules/{rule_id}")

    @mcp.tool()
    async def update_rule(
        rule_id: str,
        name: str | None = None,
        entity_type: str | None = None,
        metric: str | None = None,
        operator: str | None = None,
        threshold: int | None = None,
        notification_type: str | None = None,
        message_template: str | None = None,
        entity_id: str | None = None,
        enabled: bool | None = None,
        cooldown_hours: int | None = None,
    ) -> dict:
        """Update an existing rule.

        All fields are optional — only provided fields are changed. Use to
        tune thresholds, adjust cooldowns, enable/disable rules, or update
        message templates.

        Entity types: habit, task, routine, checkin.
        Operators: must be sent as symbols — ">=", "<=", "==".
        """
        validate_uuid(rule_id, "rule_id")
        validate_enum(entity_type, "entity_type", RULE_ENTITY_TYPES)
        validate_enum(metric, "metric", RULE_METRICS)
        validate_enum(operator, "operator", RULE_OPERATORS)
        validate_enum(notification_type, "notification_type", NOTIFICATION_TYPES)
        validate_uuid(entity_id, "entity_id")
        if threshold is not None and (not isinstance(threshold, int) or threshold < 0):
            raise InputValidationError(
                f"Invalid threshold: {threshold}. Must be a non-negative integer."
            )
        if cooldown_hours is not None and cooldown_hours < 0:
            raise InputValidationError(
                f"Invalid cooldown_hours: {cooldown_hours}. "
                "Must be a non-negative integer."
            )
        body = strip_nones({
            "name": name,
            "entity_type": entity_type,
            "metric": metric,
            "operator": operator,
            "threshold": threshold,
            "notification_type": notification_type,
            "message_template": message_template,
            "entity_id": entity_id,
            "enabled": enabled,
            "cooldown_hours": cooldown_hours,
        })
        return await api.patch(f"/api/rules/{rule_id}", json=body)

    @mcp.tool()
    async def delete_rule(rule_id: str) -> dict:
        """Delete a rule.

        Historical notifications created by this rule are preserved but
        their rule_id link is cleared. Confirm with the user before
        deleting.
        """
        validate_uuid(rule_id, "rule_id")
        return await api.delete(f"/api/rules/{rule_id}")

    @mcp.tool()
    async def evaluate_rules() -> dict:
        """Evaluate all enabled rules now.

        Checks each rule's condition against current BRAIN data, respects
        cooldowns, and creates notifications for rules that fire. Returns
        a summary of what fired and what was skipped.

        The scheduler calls this automatically, but you can trigger it
        manually during a session to check rule behavior or after making
        changes to rules.
        """
        return await api.post("/api/rules/evaluate")

    @mcp.tool()
    async def evaluate_rule(
        rule_id: str,
        respect_cooldown: bool = True,
    ) -> dict:
        """Evaluate a single rule.

        Useful for testing a rule you just created or modified. Set
        respect_cooldown=false to bypass cooldown during testing — the
        rule will fire even if it was recently triggered.
        """
        validate_uuid(rule_id, "rule_id")
        return await api.post(
            f"/api/rules/{rule_id}/evaluate",
            params=params(respect_cooldown=respect_cooldown),
        )
