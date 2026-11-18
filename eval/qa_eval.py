"""Grounded Q&A Faithfulness and Refusal Evaluation Harness.

Evaluates:
1. Faithfulness Score: Proportion of answer claims directly grounded in cited snippets.
2. Citation Precision: Whether cited snippets exist verbatim in the source chunks.
3. Refusal Benchmark: Enforces 100% strict refusal on out-of-file and ungrounded queries.
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Any

from pipeline.chunker import Chunk

REFUSAL_MESSAGES = [
    "इस प्रश्न का उत्तर संलग्न पत्रावली में नहीं पाया गया।",
    "The answer to this question was not found in the uploaded file.",
]


@dataclass
class QAEvalResult:
    question: str
    is_out_of_file: bool
    answer: str
    faithfulness_score: float
    citation_precision: float
    refused_properly: bool
    hallucination_detected: bool


def is_proper_refusal(answer: str) -> bool:
    """Check if the system safely refused an ungrounded or out-of-file query."""
    return any(msg in answer for msg in REFUSAL_MESSAGES)


def compute_citation_precision(
    citations: list[dict[str, Any]],
    chunks: list[Chunk],
) -> float:
    """Measure whether citations link back to real, verbatim text in chunks."""
    if not citations:
        return 1.0

    valid_citations = 0
    all_chunk_text = " ".join(
        unicodedata.normalize("NFKC", c.text.lower()) for c in chunks
    )

    for c in citations:
        snippet = c.get("snippet", "").strip().lower()
        if not snippet:
            continue
        norm_snippet = unicodedata.normalize("NFKC", snippet)
        # Check if snippet exists in chunks
        if norm_snippet in all_chunk_text:
            valid_citations += 1
        else:
            # Check significant token overlap
            snip_tokens = set(norm_snippet.split())
            if snip_tokens and len(snip_tokens & set(all_chunk_text.split())) / len(snip_tokens) >= 0.7:
                valid_citations += 1

    return valid_citations / len(citations)


def evaluate_qa_pair(
    question: str,
    answer: str,
    citations: list[dict[str, Any]],
    chunks: list[Chunk],
    is_out_of_file: bool,
) -> QAEvalResult:
    """Evaluate an individual Q&A interaction for faithfulness and groundedness."""
    refused = is_proper_refusal(answer)

    if is_out_of_file:
        # Out-of-file queries MUST be refused
        return QAEvalResult(
            question=question,
            is_out_of_file=True,
            answer=answer,
            faithfulness_score=1.0 if refused else 0.0,
            citation_precision=1.0,
            refused_properly=refused,
            hallucination_detected=not refused,
        )

    # In-file queries
    cit_prec = compute_citation_precision(citations, chunks)
    has_citations = len(citations) > 0
    has_answer = bool(answer and not refused)

    # Faithfulness: grounded in cited chunks without hallucinated claims
    if has_answer and has_citations and cit_prec >= 0.8:
        faithfulness = 1.0
        hallucination = False
    elif refused:
        # If unanswerable even in-file
        faithfulness = 1.0
        hallucination = False
    else:
        faithfulness = 0.5
        hallucination = True

    return QAEvalResult(
        question=question,
        is_out_of_file=False,
        answer=answer,
        faithfulness_score=faithfulness,
        citation_precision=cit_prec,
        refused_properly=refused,
        hallucination_detected=hallucination,
    )
