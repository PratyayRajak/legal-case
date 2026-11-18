"""Job status and progress tracking endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.services.job_runner import JobStatus, job_runner

router = APIRouter()


@router.get("/{job_id}")
async def get_job_status(job_id: str) -> dict[str, Any]:
    """Get processing job status, step, and percentage progress."""
    job = job_runner.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return {
        "job_id": job.job_id,
        "doc_id": job.doc_id,
        "status": job.status.value,
        "progress": job.progress,
        "current_step": job.current_step,
        "error": job.error,
        "disclaimer": "AI-assisted summary. Verify against the source document.",
    }


@router.get("/{job_id}/brief")
async def get_job_brief(job_id: str) -> dict[str, Any]:
    """Retrieve the completed case brief by job ID."""
    job = job_runner.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if job.status != JobStatus.completed or not job.case_brief:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=f"Job is {job.status.value}: {job.current_step}",
        )

    return job.case_brief.model_dump()
