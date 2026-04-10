"""Skill CRUD, relationship management, and full-context tools."""

from validation import validate_required_str, validate_uuid
from tools._helpers import params, strip_nones


def register(mcp, api) -> None:
    """Register skill tools with the MCP server."""

    @mcp.tool()
    async def create_skill(
        name: str,
        description: str | None = None,
        adhd_patterns: str | None = None,
        artifact_id: str | None = None,
        is_seedable: bool = True,
        is_default: bool = False,
        domain_ids: list[str] | None = None,
        protocol_ids: list[str] | None = None,
        directive_ids: list[str] | None = None,
    ) -> dict:
        """Define a new operating mode with linked domains, protocols, and directives.

        Supports bulk linking via domain_ids, protocol_ids, directive_ids at
        creation. Name must be unique. At most one skill can be the default.
        """
        validate_required_str(name, "name")
        validate_uuid(artifact_id, "artifact_id")
        if domain_ids is not None:
            for did in domain_ids:
                validate_uuid(did, "domain_ids element")
        if protocol_ids is not None:
            for pid in protocol_ids:
                validate_uuid(pid, "protocol_ids element")
        if directive_ids is not None:
            for did in directive_ids:
                validate_uuid(did, "directive_ids element")
        body = strip_nones({
            "name": name,
            "description": description,
            "adhd_patterns": adhd_patterns,
            "artifact_id": artifact_id,
            "is_seedable": is_seedable,
            "is_default": is_default,
            "domain_ids": domain_ids,
            "protocol_ids": protocol_ids,
            "directive_ids": directive_ids,
        })
        return await api.post("/api/skills/", json=body)

    @mcp.tool()
    async def get_skill(skill_id: str) -> dict:
        """Get a skill with its linked relationships (domains, protocols, directives)."""
        validate_uuid(skill_id, "skill_id")
        return await api.get(f"/api/skills/{skill_id}")

    @mcp.tool()
    async def get_skill_full(skill_id: str) -> dict:
        """Primary bootstrap tool. Load complete skill context.

        Returns resolved protocols, grouped directives (global + skill-scoped
        sorted by priority), domains, and linked artifact. Call this at
        session start to load your operating context.
        """
        validate_uuid(skill_id, "skill_id")
        return await api.get(f"/api/skills/{skill_id}/full")

    @mcp.tool()
    async def list_skills(
        search: str | None = None,
        is_seedable: bool | None = None,
        is_default: bool | None = None,
        domain_id: str | None = None,
    ) -> list:
        """Browse available operating modes.

        Filter by name, seedability, default status, or linked domain.
        """
        validate_uuid(domain_id, "domain_id")
        return await api.get(
            "/api/skills/",
            params=params(
                search=search,
                is_seedable=is_seedable,
                is_default=is_default,
                domain_id=domain_id,
            ),
        )

    @mcp.tool()
    async def update_skill(
        skill_id: str,
        name: str | None = None,
        description: str | None = None,
        adhd_patterns: str | None = None,
        artifact_id: str | None = None,
        is_seedable: bool | None = None,
        is_default: bool | None = None,
    ) -> dict:
        """Modify a skill's properties.

        Use link/unlink tools for relationship changes. Only provided
        fields are changed.
        """
        validate_uuid(skill_id, "skill_id")
        validate_uuid(artifact_id, "artifact_id")
        body = strip_nones({
            "name": name,
            "description": description,
            "adhd_patterns": adhd_patterns,
            "artifact_id": artifact_id,
            "is_seedable": is_seedable,
            "is_default": is_default,
        })
        return await api.patch(f"/api/skills/{skill_id}", json=body)

    @mcp.tool()
    async def delete_skill(skill_id: str) -> dict:
        """Remove a skill and its join-table entries."""
        validate_uuid(skill_id, "skill_id")
        return await api.delete(f"/api/skills/{skill_id}")

    # --- Domain relationships ---

    @mcp.tool()
    async def list_skill_domains(skill_id: str) -> list:
        """List all domains linked to a skill."""
        validate_uuid(skill_id, "skill_id")
        return await api.get(f"/api/skills/{skill_id}/domains")

    @mcp.tool()
    async def link_skill_domain(skill_id: str, domain_id: str) -> dict:
        """Associate a domain with a skill. Idempotent."""
        validate_uuid(skill_id, "skill_id")
        validate_uuid(domain_id, "domain_id")
        return await api.post(
            f"/api/skills/{skill_id}/domains/{domain_id}"
        )

    @mcp.tool()
    async def unlink_skill_domain(skill_id: str, domain_id: str) -> dict:
        """Remove domain association."""
        validate_uuid(skill_id, "skill_id")
        validate_uuid(domain_id, "domain_id")
        return await api.delete(
            f"/api/skills/{skill_id}/domains/{domain_id}"
        )

    # --- Protocol relationships ---

    @mcp.tool()
    async def list_skill_protocols(skill_id: str) -> list:
        """List all protocols linked to a skill."""
        validate_uuid(skill_id, "skill_id")
        return await api.get(f"/api/skills/{skill_id}/protocols")

    @mcp.tool()
    async def link_skill_protocol(skill_id: str, protocol_id: str) -> dict:
        """Associate a protocol with a skill. Idempotent."""
        validate_uuid(skill_id, "skill_id")
        validate_uuid(protocol_id, "protocol_id")
        return await api.post(
            f"/api/skills/{skill_id}/protocols/{protocol_id}"
        )

    @mcp.tool()
    async def unlink_skill_protocol(skill_id: str, protocol_id: str) -> dict:
        """Remove protocol association."""
        validate_uuid(skill_id, "skill_id")
        validate_uuid(protocol_id, "protocol_id")
        return await api.delete(
            f"/api/skills/{skill_id}/protocols/{protocol_id}"
        )

    # --- Directive relationships ---

    @mcp.tool()
    async def list_skill_directives(skill_id: str) -> list:
        """List all directives linked to a skill."""
        validate_uuid(skill_id, "skill_id")
        return await api.get(f"/api/skills/{skill_id}/directives")

    @mcp.tool()
    async def link_skill_directive(
        skill_id: str, directive_id: str
    ) -> dict:
        """Associate a directive with a skill. Idempotent."""
        validate_uuid(skill_id, "skill_id")
        validate_uuid(directive_id, "directive_id")
        return await api.post(
            f"/api/skills/{skill_id}/directives/{directive_id}"
        )

    @mcp.tool()
    async def unlink_skill_directive(
        skill_id: str, directive_id: str
    ) -> dict:
        """Remove directive association."""
        validate_uuid(skill_id, "skill_id")
        validate_uuid(directive_id, "directive_id")
        return await api.delete(
            f"/api/skills/{skill_id}/directives/{directive_id}"
        )
