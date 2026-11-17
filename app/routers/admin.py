"""Admin endpoints. STUB."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health/detailed")
async def detailed_health() -> dict[str, str]:
    """Detailed health check for monitoring."""
    return {"status": "not_implemented"}
