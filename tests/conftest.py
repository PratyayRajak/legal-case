"""Shared pytest fixtures and test helpers."""
from __future__ import annotations

import os
from collections.abc import Coroutine
from typing import Any

# Set required env vars before importing settings
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-ci")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/testdb")


def run_coro(coro: Coroutine[Any, Any, Any]) -> Any:
    """Execute a simple coroutine synchronously without starting a socket-based event loop."""
    try:
        coro.send(None)
    except StopIteration as exc:
        return exc.value
    raise RuntimeError("Coroutine did not complete synchronously")
