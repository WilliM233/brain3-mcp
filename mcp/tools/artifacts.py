"""Artifact CRUD and tag tools."""

from validation import (
    validate_enum,
    validate_required_str,
    validate_uuid,
    ARTIFACT_TYPES,
)
from tools._helpers import params, strip_nones


def register(mcp, api) -> None:
    """Register artifact tools with the MCP server."""

    @mcp.tool()
    async def create_artifact(
        title: str,
        artifact_type: str,
        content: str | None = None,
        parent_id: str | None = None,
        is_seedable: bool = False,
        tag_ids: list[str] | None = None,
    ) -> dict:
        """Store a reference document in BRAIN.

        Use for CLAUDE.md files, design docs, briefs, templates, prompts --
        anything that needs to persist beyond a conversation. Supports inline
        tagging via tag_ids.

        Artifact types: document, protocol, brief, prompt, template, journal,
        spec.
        """
        validate_required_str(title, "title")
        validate_enum(artifact_type, "artifact_type", ARTIFACT_TYPES)
        validate_uuid(parent_id, "parent_id")
        if tag_ids is not None:
            for tid in tag_ids:
                validate_uuid(tid, "tag_ids element")
        body = strip_nones({
            "title": title,
            "artifact_type": artifact_type,
            "content": content,
            "parent_id": parent_id,
            "is_seedable": is_seedable,
            "tag_ids": tag_ids,
        })
        return await api.post("/api/artifacts/", json=body)

    @mcp.tool()
    async def get_artifact(artifact_id: str) -> dict:
        """Retrieve a stored document with full content and resolved parent.

        Use when you need to read a specific artifact's content.
        """
        validate_uuid(artifact_id, "artifact_id")
        return await api.get(f"/api/artifacts/{artifact_id}")

    @mcp.tool()
    async def list_artifacts(
        artifact_type: str | None = None,
        is_seedable: bool | None = None,
        search: str | None = None,
        parent_id: str | None = None,
        tag: str | None = None,
    ) -> list:
        """Browse stored documents by type, tags, seedability, or search.

        Returns metadata only (no content) -- use get_artifact to read
        specific ones. Filter by artifact type, seedability, parent, or
        tag names (comma-separated, AND logic).
        """
        validate_enum(artifact_type, "artifact_type", ARTIFACT_TYPES)
        validate_uuid(parent_id, "parent_id")
        return await api.get(
            "/api/artifacts/",
            params=params(
                artifact_type=artifact_type,
                is_seedable=is_seedable,
                search=search,
                parent_id=parent_id,
                tag=tag,
            ),
        )

    @mcp.tool()
    async def update_artifact(
        artifact_id: str,
        title: str | None = None,
        artifact_type: str | None = None,
        content: str | None = None,
        parent_id: str | None = None,
        is_seedable: bool | None = None,
    ) -> dict:
        """Update a stored document.

        Content changes auto-increment the version number and recompute
        content_size. Only provided fields are changed.
        """
        validate_uuid(artifact_id, "artifact_id")
        validate_enum(artifact_type, "artifact_type", ARTIFACT_TYPES)
        validate_uuid(parent_id, "parent_id")
        body = strip_nones({
            "title": title,
            "artifact_type": artifact_type,
            "content": content,
            "parent_id": parent_id,
            "is_seedable": is_seedable,
        })
        return await api.patch(f"/api/artifacts/{artifact_id}", json=body)

    @mcp.tool()
    async def delete_artifact(artifact_id: str) -> dict:
        """Remove a stored document from BRAIN.

        Children get parent_id set to NULL.
        """
        validate_uuid(artifact_id, "artifact_id")
        return await api.delete(f"/api/artifacts/{artifact_id}")

    @mcp.tool()
    async def tag_artifact(artifact_id: str, tag_id: str) -> dict:
        """Tag a document for categorization. Idempotent."""
        validate_uuid(artifact_id, "artifact_id")
        validate_uuid(tag_id, "tag_id")
        return await api.post(f"/api/artifacts/{artifact_id}/tags/{tag_id}")

    @mcp.tool()
    async def untag_artifact(artifact_id: str, tag_id: str) -> dict:
        """Remove a tag from a document."""
        validate_uuid(artifact_id, "artifact_id")
        validate_uuid(tag_id, "tag_id")
        return await api.delete(f"/api/artifacts/{artifact_id}/tags/{tag_id}")

    @mcp.tool()
    async def list_artifact_tags(artifact_id: str) -> list:
        """See which tags are on a document."""
        validate_uuid(artifact_id, "artifact_id")
        return await api.get(f"/api/artifacts/{artifact_id}/tags")

    @mcp.tool()
    async def list_tagged_artifacts(tag_id: str) -> list:
        """Find all artifacts with a specific tag."""
        validate_uuid(tag_id, "tag_id")
        return await api.get(f"/api/tags/{tag_id}/artifacts")
