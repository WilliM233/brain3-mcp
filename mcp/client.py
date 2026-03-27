"""HTTP client for the BRAIN 3.0 API.

Thin async wrapper around httpx that handles connection errors,
API errors, and provides a clean interface for the MCP tool layer.
Designed so adding an Authorization header is a one-line change.
"""

import os

import httpx


class BrainAPIError(Exception):
    """Raised when a BRAIN 3.0 API call fails."""


class BrainAPIClient:
    """Async HTTP client for the BRAIN 3.0 FastAPI backend."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.base_url = (
            base_url
            or os.environ.get("BRAIN3_API_URL", "http://localhost:8000")
        )
        headers: dict[str, str] = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=30.0,
        )

    async def get(
        self, path: str, params: dict | None = None
    ) -> dict | list:
        """Send a GET request. Returns parsed JSON."""
        return await self._request("GET", path, params=params)

    async def post(self, path: str, json: dict | None = None) -> dict:
        """Send a POST request with optional JSON body."""
        return await self._request("POST", path, json=json)

    async def patch(self, path: str, json: dict | None = None) -> dict:
        """Send a PATCH request with optional JSON body."""
        return await self._request("PATCH", path, json=json)

    async def delete(self, path: str) -> dict:
        """Send a DELETE request. Returns confirmation dict."""
        await self._request("DELETE", path)
        return {"deleted": True}

    async def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json: dict | None = None,
    ) -> dict | list:
        """Execute an HTTP request with three-tier error handling.

        Tier 1: API unreachable (connection/timeout errors)
        Tier 2: API returned an error (4xx/5xx)
        Tier 3: Unexpected errors
        """
        try:
            response = await self._client.request(
                method, path, params=params, json=json
            )
        except (httpx.ConnectError, httpx.ConnectTimeout):
            raise BrainAPIError(
                f"Cannot connect to BRAIN 3.0 API at {self.base_url}. "
                "Is the API running?"
            )
        except httpx.TimeoutException:
            raise BrainAPIError(
                f"Request to BRAIN 3.0 API timed out ({method} {path})."
            )
        except Exception as exc:
            raise BrainAPIError(f"Unexpected error: {exc}")

        if response.status_code == 204:
            return {}

        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise BrainAPIError(
                f"API error ({response.status_code}): {detail}"
            )

        return response.json()
