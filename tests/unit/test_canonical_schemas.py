"""Tests for canonical Pydantic schemas."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.canonical import (
    BoundingBox,
    CanonicalDate,
    Citation,
    ConceptRef,
    DatePrecision,
    DocumentEntry,
    DocumentType,
    ExtractedField,
    Language,
    PersonName,
    RevenueCaseBrief,
)


class TestCanonicalDate:
    def test_full_date_valid(self):
        d = CanonicalDate(iso_date="2024-03-15", precision=DatePrecision.full, original_string="15/03/2024")
        assert d.iso_date == "2024-03-15"

    def test_month_date_valid(self):
        d = CanonicalDate(iso_date="2024-03", precision=DatePrecision.month, original_string="मार्च 2024")
        assert d.iso_date == "2024-03"

    def test_year_date_valid(self):
        d = CanonicalDate(iso_date="2024", precision=DatePrecision.year, original_string="2024")
        assert d.iso_date == "2024"

    def test_invalid_date_format(self):
        with pytest.raises(ValidationError):
            CanonicalDate(iso_date="15-03-2024", precision=DatePrecision.full, original_string="15-03-2024")

    def test_invalid_date_gibberish(self):
        with pytest.raises(ValidationError):
            CanonicalDate(iso_date="not-a-date", precision=DatePrecision.full, original_string="x")


class TestConceptRef:
    def test_valid_concept(self):
        c = ConceptRef(concept_id="STATUS_REJECTED", surface_form="खारिज", language=Language.hi, confidence=0.95)
        assert c.confidence == 0.95

    def test_confidence_out_of_range_high(self):
        with pytest.raises(ValidationError):
            ConceptRef(concept_id="X", surface_form="x", language=Language.en, confidence=1.1)

    def test_confidence_out_of_range_low(self):
        with pytest.raises(ValidationError):
            ConceptRef(concept_id="X", surface_form="x", language=Language.en, confidence=-0.1)


class TestPersonName:
    def test_basic_name(self):
        n = PersonName(original="राम कुमार शर्मा", script="devanagari", transliteration_key="ram_kumar_sharma")
        assert n.aliases == []

    def test_name_with_aliases(self):
        n = PersonName(
            original="Ram Kumar",
            script="latin",
            transliteration_key="ram_kumar",
            aliases=["R.K. Sharma", "Ram K."],
        )
        assert len(n.aliases) == 2


class TestBoundingBox:
    def test_valid_bbox(self):
        b = BoundingBox(x0=10.5, y0=20.0, x1=200.3, y1=250.7)
        assert b.x0 == 10.5


class TestExtractedField:
    def test_found_with_citation(self):
        citation = Citation(
            doc_id="doc1",
            page=3,
            snippet="Case No. 123/2024",
            lang=Language.en,
        )
        field = ExtractedField(
            field="case_number",
            value="123/2024",
            found=True,
            confidence=0.9,
            citations=[citation],
        )
        assert field.found is True
        assert field.needs_review is False

    def test_found_without_citation_flags_needs_review(self):
        field = ExtractedField(
            field="case_number",
            value="123/2024",
            found=True,
            confidence=0.9,
            citations=[],
        )
        assert field.needs_review is True
        assert any("citation" in r.lower() for r in field.review_reasons)

    def test_not_found_no_value(self):
        field = ExtractedField(field="next_hearing_date", value=None, found=False)
        assert field.value is None
        assert field.found is False


class TestDocumentEntry:
    def test_valid_entry(self):
        e = DocumentEntry(
            doc_type=DocumentType.petition,
            page_start=1,
            page_end=5,
            language=Language.hi,
        )
        assert e.page_end >= e.page_start

    def test_invalid_page_range(self):
        with pytest.raises(ValidationError):
            DocumentEntry(
                doc_type=DocumentType.judgment,
                page_start=10,
                page_end=5,
                language=Language.en,
            )


class TestRevenueCaseBrief:
    def _make_not_found(self, field_name: str) -> ExtractedField:
        return ExtractedField(field=field_name, value=None, found=False, confidence=0.0)

    def test_brief_construction_and_serialization(self):
        brief = RevenueCaseBrief(
            doc_id="test-doc-001",
            pipeline_version="1.0.0",
            glossary_version="1.0.0",
            rules_version="1.0.0",
            case_number=self._make_not_found("case_number"),
            court_name=self._make_not_found("court_name"),
            court_level=self._make_not_found("court_level"),
            case_type=self._make_not_found("case_type"),
            proceeding_type=self._make_not_found("proceeding_type"),
            petitioners=self._make_not_found("petitioners"),
            respondents=self._make_not_found("respondents"),
            advocates=self._make_not_found("advocates"),
            filing_date=self._make_not_found("filing_date"),
            previous_hearing_dates=self._make_not_found("previous_hearing_dates"),
            next_hearing_date=self._make_not_found("next_hearing_date"),
            current_status=self._make_not_found("current_status"),
            rejection_reason=self._make_not_found("rejection_reason"),
            orders_summary=self._make_not_found("orders_summary"),
            prior_court_history=self._make_not_found("prior_court_history"),
            documents_list=self._make_not_found("documents_list"),
        )
        json_str = brief.model_dump_json()
        assert "AI-assisted summary" in json_str
        assert brief.disclaimer == "AI-assisted summary. Verify against the source document."
