"""Shared helper functions for MCP tool modules."""


def strip_nones(d: dict) -> dict:
    """Remove keys with None values so PATCH only sends provided fields."""
    return {k: v for k, v in d.items() if v is not None}


def params(**kwargs: object) -> dict | None:
    """Build query params dict, dropping None values. Returns None if empty."""
    filtered = {k: v for k, v in kwargs.items() if v is not None}
    return filtered or None
