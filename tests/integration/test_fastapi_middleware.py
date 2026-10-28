"""FastAPI middleware injects somatic telemetry headers."""

import asyncio

import httpx
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from jamesian_layer.core.autonomic_daemon import AutonomicDaemon
from jamesian_layer.middleware.fastapi_middleware import FastAPIInteroceptiveMiddleware


async def home(request):
    return PlainTextResponse("ok")


def test_telemetry_headers_present_and_rounded():
    daemon = AutonomicDaemon()
    app = Starlette(routes=[Route("/", home)])
    app.add_middleware(FastAPIInteroceptiveMiddleware, daemon=daemon)

    async def fetch():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/")

    response = asyncio.run(fetch())
    assert response.status_code == 200
    assert response.headers["X-Jamesian-Sigma"] == "0.2"
    assert response.headers["X-Jamesian-Tcoil"] == "25.0"
