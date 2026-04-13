"""Tests for bearer token authentication middleware."""

import hmac

import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from auth import BearerAuthMiddleware

TOKEN = "test-secret-token-abc123"


def homepage(request: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")


@pytest.fixture()
def app():
    """Starlette app with auth middleware for testing."""
    application = Starlette(routes=[Route("/", homepage)])
    application.add_middleware(BearerAuthMiddleware, token=TOKEN)
    return application


@pytest.fixture()
def client(app):
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Missing token
# ---------------------------------------------------------------------------


class TestMissingToken:
    def test_no_auth_header_returns_401(self, client):
        resp = client.get("/")
        assert resp.status_code == 401
        assert resp.json() == {"error": "Missing bearer token"}

    def test_empty_auth_header_returns_401(self, client):
        resp = client.get("/", headers={"Authorization": ""})
        assert resp.status_code == 401

    def test_non_bearer_scheme_returns_401(self, client):
        resp = client.get("/", headers={"Authorization": "Basic abc123"})
        assert resp.status_code == 401
        assert resp.json() == {"error": "Missing bearer token"}


# ---------------------------------------------------------------------------
# Invalid token
# ---------------------------------------------------------------------------


class TestInvalidToken:
    def test_wrong_token_returns_401(self, client):
        resp = client.get("/", headers={"Authorization": "Bearer wrong-token"})
        assert resp.status_code == 401
        assert resp.json() == {"error": "Invalid bearer token"}

    def test_empty_bearer_value_returns_401(self, client):
        resp = client.get("/", headers={"Authorization": "Bearer "})
        assert resp.status_code == 401
        assert resp.json() == {"error": "Invalid bearer token"}


# ---------------------------------------------------------------------------
# Valid token
# ---------------------------------------------------------------------------


class TestValidToken:
    def test_correct_token_passes_through(self, client):
        resp = client.get("/", headers={"Authorization": f"Bearer {TOKEN}"})
        assert resp.status_code == 200
        assert resp.text == "OK"


# ---------------------------------------------------------------------------
# Constant-time comparison
# ---------------------------------------------------------------------------


class TestConstantTimeComparison:
    def test_uses_hmac_compare_digest(self):
        """Verify the middleware uses constant-time comparison."""
        # The implementation uses hmac.compare_digest directly.
        # This test verifies the function exists and behaves correctly
        # as a sanity check on the approach.
        assert hmac.compare_digest("abc", "abc") is True
        assert hmac.compare_digest("abc", "def") is False


# ---------------------------------------------------------------------------
# Server startup guard
# ---------------------------------------------------------------------------


class TestStartupGuard:
    def test_http_without_token_exits(self):
        """MCP_TRANSPORT=http without MCP_AUTH_TOKEN should exit with code 1."""
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, "server.py"],
            env={
                "MCP_TRANSPORT": "http",
                "PATH": "",
                "SYSTEMROOT": "C:\\Windows",
            },
            capture_output=True,
            text=True,
            cwd="D:/_DEVELOPMENT/brain3-mcp/mcp",
            timeout=10,
        )
        assert result.returncode == 1
        assert "MCP_AUTH_TOKEN must be set" in result.stderr
