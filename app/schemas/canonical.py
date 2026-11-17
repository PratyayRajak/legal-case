"""Canonical, language-neutral data models for the Indian Court AI system.

These are the shared data types used across the entire pipeline.
No business logic lives here — only validated data shapes.

DESIGN PRINCIPLE (Section 4): Rules run on canonical fields only.
Language only matters at two edges: extraction (document in) and display (message out).
"""
from __future__ import annotations

import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class Language(str, Enum):
    hi = "hi"
    en = "en"
    mixed = "mixed"
    unknown = "unknown"


class CourtLevel(str, Enum):
    district = "district"
    high = "high"
    supreme = "supreme"
    tribunal = "tribunal"
    revenue_board = "revenue_board"
    other = "other"


class CaseStatus(str, Enum):
    pending = "pending"
    disposed = "disposed"
    stayed = "stayed"
    rejected = "rejected"
    allowed = "allowed"
    withdrawn = "withdrawn"
    other = "other"


class ProceedingType(str, Enum):
    """Revenue-court proceeding types. Loaded from glossary for other case types."""

    mutation = "mutation"
    partition = "partition"  # type: ignore[assignment]
    boundary_dispute = "boundary_dispute"
    land_acquisition = "land_acquisition"
    tenancy = "tenancy"
    other = "other"


class DocumentType(str, Enum):
    petition = "petition"
    order_sheet = "order_sheet"
    judgment = "judgment"
    annexure = "annexure"
    notice = "notice"
    application = "application"
    vakalatnama = "vakalatnama"
    other = "other"


class DatePrecision(str, Enum):
    full = "full"
    month = "month"
    year = "year"


class ConceptRef(BaseModel):
    """Reference to a glossary concept, language-neutral."""

    concept_id: str = Field(..., description="Concept ID from glossary/concepts.yaml")
    surface_form: str = Field(..., description="Original text as it appeared in document")
    language: Language
    confidence: float = Field(ge=0.0, le=1.0)


class CanonicalDate(BaseModel):
    """ISO date with precision and original string preserved."""

    iso_date: str = Field(..., description="ISO date: YYYY-MM-DD, YYYY-MM, or YYYY")
    precision: DatePrecision
    original_string: str = Field(..., description="Date as it appeared in the source document")

    @field_validator("iso_date")
    @classmethod
    def validate_iso_date(cls, v: str) -> str:
        """Validate ISO date format matches the declared precision."""
        patterns = [
            r"^\d{4}-\d{2}-\d{2}$",
            r"^\d{4}-\d{2}$",
            r"^\d{4}$",
        ]
        if not any(re.match(p, v) for p in patterns):
            raise ValueError(f"iso_date must be YYYY-MM-DD, YYYY-MM, or YYYY. Got: {v!r}")
        return v


class PersonName(BaseModel):
    """Bilingual person name with transliteration key for fuzzy matching."""

    original: str
    script: str = Field(..., description="'devanagari' or 'latin'")
    transliteration_key: str = Field(
        ...,
        description="Normalized ASCII key for fuzzy matching, e.g. 'ram_kumar_sharma'",
    )
    aliases: list[str] = Field(default_factory=list)


class CaseNumber(BaseModel):
    """Canonical case number."""

    case_type: str
    number: str
    year: int = Field(ge=1800, le=2100)
    original_string: str = Field(..., description="Case number as it appeared in document")


class BoundingBox(BaseModel):
    """PDF bounding box (points from top-left)."""

    x0: float
    y0: float
    x1: float
    y1: float


class Citation(BaseModel):
    """Evidence citation linking a value to a source location in the original document."""

    doc_id: str
    page: int = Field(ge=1)
    bbox: BoundingBox | None = None
    snippet: str = Field(
        ...,
        description="Verbatim text snippet from OCR output — must exist in source",
    )
    lang: Language


class ExtractedField(BaseModel):
    """
    Wrapper for any extracted field value with citation and confidence.

    If the field is not found in the document:
      found=False, value=None. Never guess.

    A value without a verifiable citation snippet is flagged needs_review=True.
    """

    field: str
    value: Any = None
    found: bool
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    citations: list[Citation] = Field(default_factory=list)
    needs_review: bool = False
    review_reasons: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def found_requires_citation(self) -> ExtractedField:
        """Enforce: a found field must have at least one citation."""
        if self.found and self.value is not None and not self.citations:
            self.needs_review = True
            self.review_reasons.append("Field marked found but no citation provided")
        return self


class OrderSummary(BaseModel):
    """Summary of a single court order."""

    date: CanonicalDate
    court_level: CourtLevel
    gist: str = Field(..., max_length=500, description="Max 2 lines summary of the order")
    citation: Citation | None = None


class CourtHistoryEntry(BaseModel):
    """Prior court proceedings history entry."""

    court_level: CourtLevel
    case_number: CaseNumber | None = None
    outcome: str | None = None
    date: CanonicalDate | None = None


class DocumentEntry(BaseModel):
    """An identified sub-document or annexure within the uploaded file."""

    doc_type: DocumentType
    page_start: int = Field(ge=1)
    page_end: int = Field(ge=1)
    detected_date: CanonicalDate | None = None
    language: Language

    @model_validator(mode="after")
    def page_range_valid(self) -> DocumentEntry:
        if self.page_end < self.page_start:
            raise ValueError("page_end must be >= page_start")
        return self


class RevenueCaseBrief(BaseModel):
    """
    The structured brief for a revenue case.

    Every field is an ExtractedField with citation and confidence.
    This is the primary output of the pipeline.

    Disclaimer is always included and must appear in every export.
    """

    # Pipeline provenance
    doc_id: str
    pipeline_version: str
    glossary_version: str
    rules_version: str

    # Case identity
    case_number: ExtractedField
    court_name: ExtractedField
    court_level: ExtractedField
    case_type: ExtractedField
    proceeding_type: ExtractedField

    # Parties
    petitioners: ExtractedField
    respondents: ExtractedField
    advocates: ExtractedField

    # Dates
    filing_date: ExtractedField
    previous_hearing_dates: ExtractedField
    next_hearing_date: ExtractedField

    # Status
    current_status: ExtractedField
    rejection_reason: ExtractedField

    # History
    orders_summary: ExtractedField
    prior_court_history: ExtractedField
    documents_list: ExtractedField

    # Mandatory disclaimer — present on every export
    disclaimer: str = "AI-assisted summary. Verify against the source document."
