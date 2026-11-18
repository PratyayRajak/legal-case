"""Asynchronous Pipeline Job Runner for Court Documents.

Coordinates pipeline stages:
1. Ingest (10%)
2. OCR (25%)
3. PII Masking (35%)
4. Document Classification (45%)
5. Chunking & Indexing (60%)
6. Canonical Extraction (75%)
7. Normalization (85%)
8. Conflict Check (90%)
9. Rules Check (95%)
10. Brief Assembly (100%)
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.schemas.canonical import ConflictReport, RevenueCaseBrief
from app.services.audit import audit_service
from pipeline.nodes.stubs import (
    AssembleBriefNode,
    ChunkIndexNode,
    ClassifyNode,
    ConfidenceScoreNode,
    ConflictCheckNode,
    ExtractFieldsNode,
    IngestNode,
    NormalizeNode,
    OCRNode,
    PIIMaskNode,
    RulesCheckNode,
)
from rules.models import RuleCheckResult


class JobStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"


@dataclass
class JobInfo:
    job_id: str
    doc_id: str
    doc_hash: str
    pdf_path: str
    status: JobStatus
    progress: int
    current_step: str
    case_brief: RevenueCaseBrief | None = None
    rules_results: list[RuleCheckResult] | None = None
    conflict_report: ConflictReport | None = None
    error: str | None = None


class JobRunner:
    """In-memory job coordinator for pipeline execution."""

    def __init__(self) -> None:
        self.jobs: dict[str, JobInfo] = {}
        self.doc_to_job: dict[str, str] = {}

        # Pipeline nodes
        self.ingest_node = IngestNode()
        self.ocr_node = OCRNode()
        self.pii_node = PIIMaskNode()
        self.classify_node = ClassifyNode()
        self.chunk_node = ChunkIndexNode()
        self.extract_node = ExtractFieldsNode()
        self.normalize_node = NormalizeNode()
        self.conflict_node = ConflictCheckNode()
        self.rules_node = RulesCheckNode()
        self.confidence_node = ConfidenceScoreNode()
        self.assemble_node = AssembleBriefNode()

    def create_job(self, doc_id: str, doc_hash: str, pdf_path: str) -> JobInfo:
        """Register a new job in queued state."""
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        info = JobInfo(
            job_id=job_id,
            doc_id=doc_id,
            doc_hash=doc_hash,
            pdf_path=pdf_path,
            status=JobStatus.queued,
            progress=0,
            current_step="Document queued for processing",
        )
        self.jobs[job_id] = info
        self.doc_to_job[doc_id] = job_id
        return info

    def get_job(self, job_id: str) -> JobInfo | None:
        return self.jobs.get(job_id)

    def get_job_by_doc_id(self, doc_id: str) -> JobInfo | None:
        job_id = self.doc_to_job.get(doc_id)
        if job_id:
            return self.jobs.get(job_id)
        return None

    async def execute_job(self, job_id: str) -> JobInfo:
        """Execute all pipeline stages for a document sequentially."""
        job = self.jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.status = JobStatus.processing
        state: dict[str, Any] = {
            "doc_id": job.doc_id,
            "pdf_path": job.pdf_path,
        }

        try:
            # 1. Ingest (10%)
            job.current_step = "Validating PDF and extracting metadata"
            job.progress = 10
            state = await self.ingest_node.run(state)

            # 2. OCR (25%)
            job.current_step = "Extracting text and word bounding boxes"
            job.progress = 25
            state = await self.ocr_node.run(state)

            # 3. PII Masking (35%)
            job.current_step = "Masking sensitive PII with encrypted vault"
            job.progress = 35
            state = await self.pii_node.run(state)

            # 4. Classification (45%)
            job.current_step = "Classifying document type and court level"
            job.progress = 45
            state = await self.classify_node.run(state)

            # 5. Chunking & Indexing (60%)
            job.current_step = "Building structure-aware chunks and hybrid search index"
            job.progress = 60
            state = await self.chunk_node.run(state)

            # 6. Field Extraction (75%)
            job.current_step = "Extracting canonical fields with verifiable citations"
            job.progress = 75
            state = await self.extract_node.run(state)

            # 7. Normalization (85%)
            job.current_step = "Normalizing terms against legal concepts glossary"
            job.progress = 85
            state = await self.normalize_node.run(state)

            # 8. Conflict Detection (90%)
            job.current_step = "Checking for cross-document inconsistencies"
            job.progress = 90
            state = await self.conflict_node.run(state)

            # 9. Rules Evaluation (95%)
            job.current_step = "Evaluating procedural rules against canonical fields"
            job.progress = 95
            state = await self.rules_node.run(state)
            state = await self.confidence_node.run(state)

            # 10. Brief Assembly (100%)
            job.current_step = "Assembling final case brief with legal disclaimer"
            job.progress = 100
            state = await self.assemble_node.run(state)

            # Update Job record with outputs
            job.case_brief = state.get("case_brief")
            job.rules_results = state.get("rules_results", [])
            job.conflict_report = state.get("conflict_report")
            job.status = JobStatus.completed
            job.current_step = "Processing completed successfully"

            # Record in Audit Log
            audit_service.log(
                action="document_processed",
                document_id=job.doc_id,
                doc_hash=job.doc_hash,
                details={
                    "total_pages": state.get("total_pages", 1),
                    "total_chunks": state.get("total_chunks", 0),
                    "rules_evaluated": len(job.rules_results or []),
                    "conflicts_found": state.get("total_conflicts", 0),
                },
            )

        except Exception as exc:
            job.status = JobStatus.failed
            job.error = str(exc)
            job.current_step = f"Processing failed: {exc}"

        return job


# Global singleton job runner
job_runner = JobRunner()
