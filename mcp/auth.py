"""Bearer token authentication middleware for HTTP transport.

Validates that incoming requests include a valid Authorization: Bearer <token>
header. Used only when running in streamable-http transport mode.
"""

import hmac

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that enforces bearer token authentication.

    Token comparison uses hmac.compare_digest for constant-time comparison,
    preventing timing attacks against the shared secret.
    """

    def __init__(self, app, token: str) -> None:
        super().__init__(app)
        self.token = token

    async def dispatch(self, request: Request, call_next) -> Response:
        auth_header = request.headers.get("authorization", "")

        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                {"error": "Missing bearer token"}, status_code=401
            )

        provided = auth_header[7:]
        if not hmac.compare_digest(provided, self.token):
            return JSONResponse(
                {"error": "Invalid bearer token"}, status_code=401
            )

        return await call_next(request)
