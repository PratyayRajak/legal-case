"""Integration test: health endpoint and app setup."""
from __future__ import annotations

from app.main import app, health
from tests.conftest import run_coro


def test_health_endpoint() -> None:
    data = run_coro(health())
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


def test_app_configuration() -> None:
    assert app.title == "Court Brief Engine"
    assert app.version == "0.1.0"
    routes = [route.path for route in app.routes]
    assert "/health" in routes
    assert "/api/v1/documents/upload" in routes
    assert "/api/v1/jobs/{job_id}" in routes
    assert "/api/v1/qa/ask" in routes
