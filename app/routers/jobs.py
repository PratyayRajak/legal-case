"""Job status endpoints. STUB."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/{job_id}")
async def get_job_status(job_id: str) -> dict[str, str]:
    """Get processing job status and progress."""
    return {"status": "not_implemented", "job_id": job_id}


@router.get("/{job_id}/brief")
async def get_brief(job_id: str) -> dict[str, str]:
    """Get the completed case brief."""
    return {"status": "not_implemented", "job_id": job_id}
