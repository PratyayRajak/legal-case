"""Follow-up Q&A endpoints. STUB."""
from __future__ import annotations

from fastapi import APIRouter

from app.schemas.api import QARequest

router = APIRouter()


@router.post("/ask")
async def ask_question(request: QARequest) -> dict[str, str]:
    """Ask a follow-up question grounded in the uploaded case file."""
    return {"status": "not_implemented"}
