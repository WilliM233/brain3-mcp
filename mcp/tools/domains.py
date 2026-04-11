"""Domain CRUD tools."""

from validation import validate_required_str, validate_uuid
from tools._helpers import strip_nones


def register(mcp, api) -> None:
    """Register domain tools with the MCP server."""

    @mcp.tool()
    async def create_domain(
        name: str,
        description: str | None = None,
        color: str | None = None,
        sort_order: int = 0,
    ) -> dict:
        """Create a new life domain.

        Domains are top-level categories that organize goals (e.g. Health,
        Finances, Career, Relationships). Use this when the user wants to
        establish a new area of focus in their life.
        """
        validate_required_str(name, "name")
        body = strip_nones({
            "name": name,
            "description": description,
            "color": color,
            "sort_order": sort_order,
        })
        return await api.post("/api/domains/", json=body)

    @mcp.tool()
    async def list_domains() -> list:
        """List all life domains.

        Returns every domain sorted by sort_order then name. Use this to see
        what areas of life are being tracked, or to find a domain_id for
        creating goals.
        """
        return await api.get("/api/domains/")

    @mcp.tool()
    async def get_domain(domain_id: str) -> dict:
        """Get a domain with its nested goals.

        Use this to see the full picture of a life domain — its details and
        all goals underneath it. The domain_id should be a UUID.
        """
        validate_uuid(domain_id, "domain_id")
        return await api.get(f"/api/domains/{domain_id}")

    @mcp.tool()
    async def update_domain(
        domain_id: str,
        name: str | None = None,
        description: str | None = None,
        color: str | None = None,
        sort_order: int | None = None,
    ) -> dict:
        """Update a domain's details.

        Only provided fields are changed — omit fields to leave them as-is.
        Use this to rename, recolor, or reorder domains.
        """
        validate_uuid(domain_id, "domain_id")
        body = strip_nones({
            "name": name,
            "description": description,
            "color": color,
            "sort_order": sort_order,
        })
        return await api.patch(f"/api/domains/{domain_id}", json=body)

    @mcp.tool()
    async def delete_domain(domain_id: str) -> dict:
        """Delete a domain and cascade to its goals.

        This permanently removes the domain. Use with care — confirm with
        the user before deleting.
        """
        validate_uuid(domain_id, "domain_id")
        return await api.delete(f"/api/domains/{domain_id}")
