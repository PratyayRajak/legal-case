"""Document upload and case brief retrieval endpoints."""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Response, UploadFile, status

from app.services.audit import audit_service
from app.services.job_runner import JobStatus, job_runner
from pipeline.ingest import calculate_file_hash, validate_pdf_bytes

router = APIRouter()

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    """Upload a case PDF (Hindi/English, scanned or digital) for processing."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF documents are supported (.pdf)",
        )

    content = await file.read()
    try:
        validate_pdf_bytes(content)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid or corrupted PDF file: {exc}",
        ) from exc

    doc_hash = calculate_file_hash(content)
    doc_id = f"doc_{uuid.uuid4().hex[:10]}"

    # Save to disk
    save_path = UPLOAD_DIR / f"{doc_hash}.pdf"
    if not save_path.exists():
        with open(save_path, "wb") as f:
            f.write(content)

    # Register Job
    job = job_runner.create_job(
        doc_id=doc_id,
        doc_hash=doc_hash,
        pdf_path=str(save_path),
    )

    # Audit upload
    audit_service.log(
        action="document_upload",
        document_id=doc_id,
        doc_hash=doc_hash,
        details={"filename": file.filename, "size_bytes": len(content)},
    )

    # Queue background processing
    background_tasks.add_task(job_runner.execute_job, job.job_id)

    return {
        "doc_id": doc_id,
        "job_id": job.job_id,
        "doc_hash": doc_hash,
        "status": job.status.value,
        "filename": file.filename,
        "disclaimer": "AI-assisted summary. Verify against the source document.",
    }


@router.get("/{doc_id}")
async def get_document_status(doc_id: str) -> dict[str, Any]:
    """Get status and metadata for an uploaded document."""
    job = job_runner.get_job_by_doc_id(doc_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

    return {
        "doc_id": job.doc_id,
        "job_id": job.job_id,
        "doc_hash": job.doc_hash,
        "status": job.status.value,
        "progress": job.progress,
        "current_step": job.current_step,
        "error": job.error,
        "disclaimer": "AI-assisted summary. Verify against the source document.",
    }


@router.get("/{doc_id}/brief")
async def get_document_brief(doc_id: str) -> dict[str, Any]:
    """Retrieve the generated canonical case brief."""
    job = job_runner.get_job_by_doc_id(doc_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

    if job.status != JobStatus.completed or not job.case_brief:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=f"Document is still {job.status.value}: {job.current_step}",
        )

    audit_service.log(
        action="view_brief",
        document_id=doc_id,
        doc_hash=job.doc_hash,
    )
    return job.case_brief.model_dump()


@router.get("/{doc_id}/rules")
async def get_document_rules_report(doc_id: str) -> dict[str, Any]:
    """Retrieve the rule compliance report for the case."""
    job = job_runner.get_job_by_doc_id(doc_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

    if job.status != JobStatus.completed or job.rules_results is None:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=f"Document is still {job.status.value}: {job.current_step}",
        )

    audit_service.log(
        action="check_rules",
        document_id=doc_id,
        doc_hash=job.doc_hash,
    )
    return {
        "doc_id": doc_id,
        "rules_results": [r.model_dump() for r in job.rules_results],
        "total_rules": len(job.rules_results),
        "disclaimer": "AI-assisted summary. Verify against the source document.",
    }


@router.get("/{doc_id}/conflicts")
async def get_document_conflicts_report(doc_id: str) -> dict[str, Any]:
    """Retrieve the cross-document conflict report."""
    job = job_runner.get_job_by_doc_id(doc_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

    if job.status != JobStatus.completed or job.conflict_report is None:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=f"Document is still {job.status.value}: {job.current_step}",
        )

    audit_service.log(
        action="view_conflicts",
        document_id=doc_id,
        doc_hash=job.doc_hash,
    )
    return job.conflict_report.model_dump()


@router.get("/{doc_id}/export/pdf")
async def export_document_brief_pdf(doc_id: str) -> Response:
    """Export the case brief as a judge-ready, downloadable PDF."""
    job = job_runner.get_job_by_doc_id(doc_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

    if job.status != JobStatus.completed or job.case_brief is None:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=f"Document is still {job.status.value}: {job.current_step}",
        )

    from app.services.export_service import BriefExportService
    pdf_bytes = BriefExportService.export_as_pdf_bytes(job.case_brief)

    audit_service.log(
        action="export_brief_pdf",
        document_id=doc_id,
        doc_hash=job.doc_hash,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=case_brief_{doc_id}.pdf"},
    )


@router.get("/{doc_id}/export/text")
async def export_document_brief_text(doc_id: str) -> Response:
    """Export the case brief as a plain text summary."""
    job = job_runner.get_job_by_doc_id(doc_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

    if job.status != JobStatus.completed or job.case_brief is None:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=f"Document is still {job.status.value}: {job.current_step}",
        )

    from app.services.export_service import BriefExportService
    text_summary = BriefExportService.export_as_text_summary(job.case_brief)

    audit_service.log(
        action="export_brief_text",
        document_id=doc_id,
        doc_hash=job.doc_hash,
    )

    return Response(
        content=text_summary,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=case_brief_{doc_id}.txt"},
    )
