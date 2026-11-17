"""API-facing request and response schemas.

These are the JSON shapes the frontend sees. They wrap canonical types
but are kept separate to allow API versioning independently of the
internal canonical schema.
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.canonical import RevenueCaseBrief


class JobStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    done = "done"
    failed = "failed"


class UploadResponse(BaseModel):
    job_id: str
    document_hash: str
    message: str = "Document received. Processing started."


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: int = Field(ge=0, le=100, description="Percent complete (0-100)")
    current_step: str = ""
    error: str = ""


class BriefResponse(BaseModel):
    job_id: str
    brief: RevenueCaseBrief
    rules_report: list[dict[str, Any]]  # typed in Phase 7
    conflicts_report: list[dict[str, Any]]  # typed in Phase 6


class QARequest(BaseModel):
    job_id: str
    question: str
    language: str = Field(default="en", pattern="^(hi|en)$")


class QAResponse(BaseModel):
    answer: str
    citations: list[dict[str, Any]]
    language: str
    not_found: bool = False
    disclaimer: str = "AI-assisted answer. Verify against the source document."
