"""Batch create and batch tag tools."""

from validation import InputValidationError, validate_uuid


def register(mcp, api) -> None:
    """Register batch operation tools with the MCP server."""

    # --- Batch Create ---

    @mcp.tool()
    async def batch_create_tasks(items: list[dict]) -> dict:
        """Create multiple tasks in one atomic operation. Max 100.

        All succeed or all fail. Each item follows the create_task schema.
        Per-item validation is handled by the API.
        """
        if not items or len(items) > 100:
            raise InputValidationError(
                "items must contain 1 to 100 entries."
            )
        return await api.post("/api/tasks/batch", json={"items": items})

    @mcp.tool()
    async def batch_create_activity(items: list[dict]) -> dict:
        """Log multiple activities at once. Max 100.

        All succeed or all fail. Use for session recaps or batch imports.
        Each item follows the log_activity schema.
        """
        if not items or len(items) > 100:
            raise InputValidationError(
                "items must contain 1 to 100 entries."
            )
        return await api.post("/api/activity/batch", json={"items": items})

    @mcp.tool()
    async def batch_create_artifacts(items: list[dict]) -> dict:
        """Store multiple documents at once. Max 100.

        All succeed or all fail. Use for seed data or content migration.
        Each item follows the create_artifact schema.
        """
        if not items or len(items) > 100:
            raise InputValidationError(
                "items must contain 1 to 100 entries."
            )
        return await api.post("/api/artifacts/batch", json={"items": items})

    @mcp.tool()
    async def batch_create_protocols(items: list[dict]) -> dict:
        """Create multiple protocols at once. Max 100.

        All succeed or all fail. Each item follows the create_protocol schema.
        """
        if not items or len(items) > 100:
            raise InputValidationError(
                "items must contain 1 to 100 entries."
            )
        return await api.post("/api/protocols/batch", json={"items": items})

    @mcp.tool()
    async def batch_create_directives(items: list[dict]) -> dict:
        """Create multiple directives at once. Max 100.

        All succeed or all fail. Each item follows the create_directive schema.
        """
        if not items or len(items) > 100:
            raise InputValidationError(
                "items must contain 1 to 100 entries."
            )
        return await api.post(
            "/api/directives/batch", json={"items": items}
        )

    @mcp.tool()
    async def batch_create_skills(items: list[dict]) -> dict:
        """Create multiple skills at once. Max 100.

        All succeed or all fail. Returns with resolved relationships.
        Each item follows the create_skill schema.
        """
        if not items or len(items) > 100:
            raise InputValidationError(
                "items must contain 1 to 100 entries."
            )
        return await api.post("/api/skills/batch", json={"items": items})

    # --- Batch Tag ---

    @mcp.tool()
    async def batch_tag_task(
        task_id: str, tag_ids: list[str]
    ) -> dict:
        """Attach multiple tags to a task at once. Idempotent. Max 100 tags."""
        validate_uuid(task_id, "task_id")
        if not tag_ids or len(tag_ids) > 100:
            raise InputValidationError(
                "tag_ids must contain 1 to 100 entries."
            )
        for tid in tag_ids:
            validate_uuid(tid, "tag_ids element")
        return await api.post(
            f"/api/tasks/{task_id}/tags/batch",
            json={"tag_ids": tag_ids},
        )

    @mcp.tool()
    async def batch_tag_activity(
        activity_id: str, tag_ids: list[str]
    ) -> dict:
        """Attach multiple tags to an activity at once. Idempotent. Max 100 tags."""
        validate_uuid(activity_id, "activity_id")
        if not tag_ids or len(tag_ids) > 100:
            raise InputValidationError(
                "tag_ids must contain 1 to 100 entries."
            )
        for tid in tag_ids:
            validate_uuid(tid, "tag_ids element")
        return await api.post(
            f"/api/activity/{activity_id}/tags/batch",
            json={"tag_ids": tag_ids},
        )

    @mcp.tool()
    async def batch_tag_artifact(
        artifact_id: str, tag_ids: list[str]
    ) -> dict:
        """Attach multiple tags to an artifact at once. Idempotent. Max 100 tags."""
        validate_uuid(artifact_id, "artifact_id")
        if not tag_ids or len(tag_ids) > 100:
            raise InputValidationError(
                "tag_ids must contain 1 to 100 entries."
            )
        for tid in tag_ids:
            validate_uuid(tid, "tag_ids element")
        return await api.post(
            f"/api/artifacts/{artifact_id}/tags/batch",
            json={"tag_ids": tag_ids},
        )

    # --- Reverse Tag Lookups ---

    @mcp.tool()
    async def list_tagged_artifacts(tag_id: str) -> list:
        """Find all artifacts with a specific tag."""
        validate_uuid(tag_id, "tag_id")
        return await api.get(f"/api/tags/{tag_id}/artifacts")

    @mcp.tool()
    async def list_tagged_protocols(tag_id: str) -> list:
        """Find all protocols with a specific tag."""
        validate_uuid(tag_id, "tag_id")
        return await api.get(f"/api/tags/{tag_id}/protocols")

    @mcp.tool()
    async def list_tagged_directives(tag_id: str) -> list:
        """Find all directives with a specific tag."""
        validate_uuid(tag_id, "tag_id")
        return await api.get(f"/api/tags/{tag_id}/directives")
