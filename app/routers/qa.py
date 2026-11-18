"""Grounded Follow-up Q&A endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.schemas.canonical import Citation, Language
from app.services.audit import audit_service
from app.services.job_runner import job_runner
from pipeline.ocr_engine import detect_language
from pipeline.retriever import HybridRetriever

router = APIRouter()


class QARequest(BaseModel):
    doc_id: str
    question: str = Field(..., min_length=2)
    user_id: str | None = None


@router.post("/ask")
async def ask_question(payload: QARequest) -> dict[str, Any]:
    """Answer questions grounded exclusively in the uploaded case file."""
    job = job_runner.get_job_by_doc_id(payload.doc_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Document {payload.doc_id} not found")

    q_lang = detect_language(payload.question)

    # Use the pipeline retriever from state or build one from chunks
    retriever: HybridRetriever = job_runner.chunk_node.retriever
    hits = await retriever.search(payload.question, top_k=3)

    citations: list[dict[str, Any]] = []
    snippets: list[str] = []
    for h in hits:
        citations.append(
            Citation(
                doc_id=payload.doc_id,
                page=h.chunk.page_number,
                snippet=h.chunk.text[:200],
                lang=Language.hi if h.chunk.language == "hi" else Language.en,
            ).model_dump()
        )
        snippets.append(f"[पृष्ठ {h.chunk.page_number}]: {h.chunk.text}")

    # Grounded answer synthesis
    if hits:
        if q_lang == "hi":
            answer = f"दस्तावेज़ के अनुसार: {hits[0].chunk.text[:300]}"
        else:
            answer = f"According to the source document: {hits[0].chunk.text[:300]}"
    else:
        if q_lang == "hi":
            answer = "इस प्रश्न का उत्तर संलग्न पत्रावली में नहीं पाया गया।"
        else:
            answer = "The answer to this question was not found in the uploaded file."

    audit_service.log(
        action="qa_query",
        document_id=payload.doc_id,
        user_id=payload.user_id,
        details={"question": payload.question, "lang": q_lang},
    )

    return {
        "doc_id": payload.doc_id,
        "question": payload.question,
        "answer": answer,
        "citations": citations,
        "language": q_lang,
        "disclaimer": "AI-assisted summary. Verify against the source document.",
    }
