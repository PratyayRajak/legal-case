"""Document upload and retrieval endpoints. STUB — full impl in Phase 8."""
from __future__ import annotations

from fastapi import APIRouter, UploadFile

router = APIRouter()


@router.post("/upload")
async def upload_document(file: UploadFile) -> dict[str, str]:
    """Upload a case PDF for processing."""
    return {"status": "not_implemented", "note": "Implemented in Phase 8"}


@router.get("/{doc_id}")
async def get_document(doc_id: str) -> dict[str, str]:
    """Get document metadata."""
    return {"status": "not_implemented", "doc_id": doc_id}
