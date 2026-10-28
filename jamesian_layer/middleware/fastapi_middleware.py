"""ASGI middleware injecting somatic telemetry headers (spec section 5.6)."""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp


class FastAPIInteroceptiveMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, daemon):
        super().__init__(app)
        self.daemon = daemon

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Intercepts agent API requests, injecting somatic telemetry headers."""
        response = await call_next(request)
        state = self.daemon.get_state()
        response.headers["X-Jamesian-Sigma"] = str(round(state.sigma, 2))
        response.headers["X-Jamesian-Tcoil"] = str(round(state.T_coil, 1))
        return response
