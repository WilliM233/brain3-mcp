"""Protocol CRUD and tag tools."""

from validation import validate_required_str, validate_uuid
from tools._helpers import params, strip_nones


def register(mcp, api) -> None:
    """Register protocol tools with the MCP server."""

    @mcp.tool()
    async def create_protocol(
        name: str,
        description: str | None = None,
        steps: list[dict] | None = None,
        artifact_id: str | None = None,
        is_seedable: bool = True,
        tag_ids: list[str] | None = None,
    ) -> dict:
        """Define a new step-by-step procedure.

        Use for repeatable workflows like session startup, bug handling,
        release processes. Supports inline tagging. Name must be unique.

        Steps format: list of {order: int, title: str, instruction: str,
        is_optional: bool}.
        """
        validate_required_str(name, "name")
        validate_uuid(artifact_id, "artifact_id")
        if tag_ids is not None:
            for tid in tag_ids:
                validate_uuid(tid, "tag_ids element")
        body = strip_nones({
            "name": name,
            "description": description,
            "steps": steps,
            "artifact_id": artifact_id,
            "is_seedable": is_seedable,
            "tag_ids": tag_ids,
        })
        return await api.post("/api/protocols/", json=body)

    @mcp.tool()
    async def get_protocol(protocol_id: str) -> dict:
        """Load a specific protocol with its steps and linked artifact details."""
        validate_uuid(protocol_id, "protocol_id")
        return await api.get(f"/api/protocols/{protocol_id}")

    @mcp.tool()
    async def list_protocols(
        search: str | None = None,
        is_seedable: bool | None = None,
        has_artifact: bool | None = None,
        tag: str | None = None,
    ) -> list:
        """Browse available protocols.

        Use at session start to see what procedures are defined. Filter by
        name search, seedability, whether they have a linked artifact, or
        tag names (comma-separated, AND logic).
        """
        return await api.get(
            "/api/protocols/",
            params=params(
                search=search,
                is_seedable=is_seedable,
                has_artifact=has_artifact,
                tag=tag,
            ),
        )

    @mcp.tool()
    async def update_protocol(
        protocol_id: str,
        name: str | None = None,
        description: str | None = None,
        steps: list[dict] | None = None,
        artifact_id: str | None = None,
        is_seedable: bool | None = None,
    ) -> dict:
        """Modify a protocol -- update steps, description, or linked artifact.

        Version auto-increments on steps or description changes. Name
        uniqueness enforced. Only provided fields are changed.
        """
        validate_uuid(protocol_id, "protocol_id")
        validate_uuid(artifact_id, "artifact_id")
        body = strip_nones({
            "name": name,
            "description": description,
            "steps": steps,
            "artifact_id": artifact_id,
            "is_seedable": is_seedable,
        })
        return await api.patch(f"/api/protocols/{protocol_id}", json=body)

    @mcp.tool()
    async def delete_protocol(protocol_id: str) -> dict:
        """Remove a protocol from BRAIN."""
        validate_uuid(protocol_id, "protocol_id")
        return await api.delete(f"/api/protocols/{protocol_id}")

    @mcp.tool()
    async def tag_protocol(protocol_id: str, tag_id: str) -> dict:
        """Tag a protocol. Idempotent."""
        validate_uuid(protocol_id, "protocol_id")
        validate_uuid(tag_id, "tag_id")
        return await api.post(f"/api/protocols/{protocol_id}/tags/{tag_id}")

    @mcp.tool()
    async def untag_protocol(protocol_id: str, tag_id: str) -> dict:
        """Remove a tag from a protocol."""
        validate_uuid(protocol_id, "protocol_id")
        validate_uuid(tag_id, "tag_id")
        return await api.delete(f"/api/protocols/{protocol_id}/tags/{tag_id}")

    @mcp.tool()
    async def list_protocol_tags(protocol_id: str) -> list:
        """List tags on a protocol."""
        validate_uuid(protocol_id, "protocol_id")
        return await api.get(f"/api/protocols/{protocol_id}/tags")
