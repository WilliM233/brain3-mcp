"""End-to-end regression tests for BrainAPIClient error-body handling.

These tests exercise the real ``_request`` code path (no client-level
mocking) via ``httpx.MockTransport`` — the same transport boundary a
live brain3 server would respond on. Canned responses simulate the
FastAPI 422 body shape (``{"detail": [{...}]}``) so the test hits the
exact parsing and f-string branches that MCP-BUG-01 fixed.

Scope: these are the "live-API-equivalent" tests called out in the
Packet 5 investigation §Suggested Fix (P1.3 commitment). A true
brain3-subprocess integration test would require adding brain3 as a
test dependency, which is out of scope for this PR.
"""

import json

import httpx
import pytest

from client import BrainAPIClient, BrainAPIError


def _transport_returning(status_code: int, body: dict | list | str) -> httpx.MockTransport:
    """Build a MockTransport that answers every request with the given body."""

    def handler(request: httpx.Request) -> httpx.Response:
        if isinstance(body, str):
            return httpx.Response(status_code, text=body)
        return httpx.Response(status_code, json=body)

    return httpx.MockTransport(handler)


def _client_with_transport(transport: httpx.MockTransport) -> BrainAPIClient:
    """Construct a BrainAPIClient whose underlying httpx uses the given transport."""
    client = BrainAPIClient(base_url="http://brain3.test")
    # Swap the AsyncClient for one bound to the mock transport.
    client._client = httpx.AsyncClient(
        base_url="http://brain3.test",
        transport=transport,
        timeout=5.0,
    )
    return client


@pytest.mark.anyio
async def test_request_422_list_detail_message_is_json_parseable():
    """FastAPI 422 list-of-dicts detail is serialized as JSON in the error message."""
    detail = [
        {
            "type": "missing",
            "loc": ["body", "notification_type"],
            "msg": "Field required",
            "input": {},
        },
    ]
    client = _client_with_transport(_transport_returning(422, {"detail": detail}))

    with pytest.raises(BrainAPIError) as exc_info:
        await client.post("/api/notifications/", json={})

    message = str(exc_info.value)
    assert message.startswith("API error (422): ")
    payload = message.removeprefix("API error (422): ")
    # Real JSON round-trip — catches any repr regression immediately.
    assert json.loads(payload) == detail
    # Double-quoted keys distinguish the fix from Python repr.
    assert '"msg"' in message


@pytest.mark.anyio
async def test_request_400_dict_detail_is_json_encoded():
    """HTTPException(detail={...}) with dict detail is JSON-serialized, not repr."""
    detail = {"error": "conflict", "hint": "re-read current state"}
    client = _client_with_transport(_transport_returning(400, {"detail": detail}))

    with pytest.raises(BrainAPIError) as exc_info:
        await client.post("/api/things/", json={})

    message = str(exc_info.value)
    payload = message.removeprefix("API error (400): ")
    assert json.loads(payload) == detail


@pytest.mark.anyio
async def test_request_404_string_detail_passes_through_unchanged():
    """String detail is untouched — back-compat for the common HTTPException case."""
    client = _client_with_transport(
        _transport_returning(404, {"detail": "Routine not found"}),
    )

    with pytest.raises(BrainAPIError) as exc_info:
        await client.get("/api/routines/deadbeef")

    assert str(exc_info.value) == "API error (404): Routine not found"


@pytest.mark.anyio
async def test_request_500_non_json_body_falls_back_to_text():
    """Non-JSON error bodies still produce a usable error message."""
    client = _client_with_transport(_transport_returning(500, "upstream exploded"))

    with pytest.raises(BrainAPIError) as exc_info:
        await client.get("/api/health")

    assert str(exc_info.value) == "API error (500): upstream exploded"
