"""Tag CRUD tools."""

from validation import validate_required_str, validate_uuid
from tools._helpers import params, strip_nones


def register(mcp, api) -> None:
    """Register tag tools with the MCP server."""

    @mcp.tool()
    async def create_tag(
        name: str,
        color: str | None = None,
    ) -> dict:
        """Create a tag, or return the existing one if the name already exists.

        Tags are labels that can be attached to tasks for flexible grouping
        (e.g. "quick-win", "deep-focus", "waiting-on"). This uses get-or-create
        semantics — if a tag with this name exists (case-insensitive), it's
        returned instead of creating a duplicate.
        """
        validate_required_str(name, "name")
        body = strip_nones({"name": name, "color": color})
        return await api.post("/api/tags/", json=body)

    @mcp.tool()
    async def list_tags(
        search: str | None = None,
    ) -> list:
        """List all tags, optionally filtered by name search.

        The search parameter does a case-insensitive partial match on tag
        names. Use this to find existing tags before creating new ones.
        """
        return await api.get("/api/tags/", params=params(search=search))

    @mcp.tool()
    async def get_tag(tag_id: str) -> dict:
        """Get a single tag by ID."""
        validate_uuid(tag_id, "tag_id")
        return await api.get(f"/api/tags/{tag_id}")

    @mcp.tool()
    async def update_tag(
        tag_id: str,
        name: str | None = None,
        color: str | None = None,
    ) -> dict:
        """Update a tag's name or color.

        Only provided fields are changed.
        """
        validate_uuid(tag_id, "tag_id")
        body = strip_nones({"name": name, "color": color})
        return await api.patch(f"/api/tags/{tag_id}", json=body)

    @mcp.tool()
    async def delete_tag(tag_id: str) -> dict:
        """Delete a tag. Removes it from all tasks that use it."""
        validate_uuid(tag_id, "tag_id")
        return await api.delete(f"/api/tags/{tag_id}")
