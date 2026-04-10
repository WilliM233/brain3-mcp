"""Directive CRUD, resolve, and tag tools."""

from validation import (
    validate_enum,
    validate_range,
    validate_required_str,
    validate_uuid,
    DIRECTIVE_SCOPES,
)
from tools._helpers import params, strip_nones


def register(mcp, api) -> None:
    """Register directive tools with the MCP server."""

    @mcp.tool()
    async def create_directive(
        name: str,
        content: str,
        scope: str,
        scope_ref: str | None = None,
        priority: int = 5,
        is_seedable: bool = True,
        tag_ids: list[str] | None = None,
    ) -> dict:
        """Define a behavioral rule or guardrail.

        Scope it as global (always applies), skill-specific, or
        agent-specific. Global directives must NOT have a scope_ref.
        Skill/agent directives require one.

        Priority: 1-10 (higher = more important). Default 5.
        """
        validate_required_str(name, "name")
        validate_required_str(content, "content")
        validate_enum(scope, "scope", DIRECTIVE_SCOPES)
        validate_uuid(scope_ref, "scope_ref")
        validate_range(priority, "priority", 1, 10)
        if tag_ids is not None:
            for tid in tag_ids:
                validate_uuid(tid, "tag_ids element")
        body = strip_nones({
            "name": name,
            "content": content,
            "scope": scope,
            "scope_ref": scope_ref,
            "priority": priority,
            "is_seedable": is_seedable,
            "tag_ids": tag_ids,
        })
        return await api.post("/api/directives/", json=body)

    @mcp.tool()
    async def get_directive(directive_id: str) -> dict:
        """Read a specific directive."""
        validate_uuid(directive_id, "directive_id")
        return await api.get(f"/api/directives/{directive_id}")

    @mcp.tool()
    async def list_directives(
        scope: str | None = None,
        scope_ref: str | None = None,
        is_seedable: bool | None = None,
        priority_min: int | None = None,
        priority_max: int | None = None,
        search: str | None = None,
        tag: str | None = None,
    ) -> list:
        """Browse directives with scope, priority, and tag filters.

        Filter by scope (global, skill, agent), scope reference, seedability,
        priority range (1-10), name search, or tag names (comma-separated,
        AND logic).
        """
        validate_enum(scope, "scope", DIRECTIVE_SCOPES)
        validate_uuid(scope_ref, "scope_ref")
        validate_range(priority_min, "priority_min", 1, 10)
        validate_range(priority_max, "priority_max", 1, 10)
        return await api.get(
            "/api/directives/",
            params=params(
                scope=scope,
                scope_ref=scope_ref,
                is_seedable=is_seedable,
                priority_min=priority_min,
                priority_max=priority_max,
                search=search,
                tag=tag,
            ),
        )

    @mcp.tool()
    async def update_directive(
        directive_id: str,
        name: str | None = None,
        content: str | None = None,
        scope: str | None = None,
        scope_ref: str | None = None,
        priority: int | None = None,
        is_seedable: bool | None = None,
    ) -> dict:
        """Modify a directive.

        API validates scope/scope_ref constraints after merge. Only provided
        fields are changed.
        """
        validate_uuid(directive_id, "directive_id")
        validate_enum(scope, "scope", DIRECTIVE_SCOPES)
        validate_uuid(scope_ref, "scope_ref")
        validate_range(priority, "priority", 1, 10)
        body = strip_nones({
            "name": name,
            "content": content,
            "scope": scope,
            "scope_ref": scope_ref,
            "priority": priority,
            "is_seedable": is_seedable,
        })
        return await api.patch(f"/api/directives/{directive_id}", json=body)

    @mcp.tool()
    async def delete_directive(directive_id: str) -> dict:
        """Remove a directive."""
        validate_uuid(directive_id, "directive_id")
        return await api.delete(f"/api/directives/{directive_id}")

    @mcp.tool()
    async def resolve_directives(
        skill_id: str | None = None,
        scope_ref: str | None = None,
    ) -> dict:
        """Get the merged directive set for a skill + optional agent context.

        Returns global + skill + agent directives grouped and sorted by
        priority. **Use this at session start to load behavioral rules.**
        """
        validate_uuid(skill_id, "skill_id")
        validate_uuid(scope_ref, "scope_ref")
        return await api.get(
            "/api/directives/resolve",
            params=params(skill_id=skill_id, scope_ref=scope_ref),
        )

    @mcp.tool()
    async def tag_directive(directive_id: str, tag_id: str) -> dict:
        """Tag a directive. Idempotent."""
        validate_uuid(directive_id, "directive_id")
        validate_uuid(tag_id, "tag_id")
        return await api.post(
            f"/api/directives/{directive_id}/tags/{tag_id}"
        )

    @mcp.tool()
    async def untag_directive(directive_id: str, tag_id: str) -> dict:
        """Remove a tag from a directive."""
        validate_uuid(directive_id, "directive_id")
        validate_uuid(tag_id, "tag_id")
        return await api.delete(
            f"/api/directives/{directive_id}/tags/{tag_id}"
        )

    @mcp.tool()
    async def list_directive_tags(directive_id: str) -> list:
        """List tags on a directive."""
        validate_uuid(directive_id, "directive_id")
        return await api.get(f"/api/directives/{directive_id}/tags")
