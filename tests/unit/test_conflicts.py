"""Tests for Cross-Document Conflict Detection."""
from __future__ import annotations

from app.schemas.canonical import (
    Citation,
    ConflictSeverity,
    ConflictType,
    ExtractedField,
    Language,
)
from pipeline.conflicts import CrossDocumentConflictDetector


class TestCrossDocumentConflictDetector:
    def test_detect_case_number_mismatch(self):
        detector = CrossDocumentConflictDetector()
        extracted = {
            "case_number": ExtractedField(
                field="case_number",
                value={"number": "104", "year": 2024},
                found=True,
                citations=[Citation(doc_id="d1", page=1, snippet="वाद संख्या: 104 / 2024", lang=Language.hi)],
            )
        }
        pages = {
            1: "वाद संख्या: 104 / 2024 न्यायालय उपजिलाधिकारी",
            2: "संलग्नक में वाद संख्या 105 / 2024 का उल्लेख है।",
        }
        report = detector.detect_conflicts(pages, extracted, doc_id="d1")

        assert report.total_conflicts >= 1
        assert report.has_blocking is True
        c = report.conflicts[0]
        assert c.conflict_type == ConflictType.case_number_mismatch
        assert c.severity == ConflictSeverity.blocking
        assert c.evidence_a.page == 1
        assert c.evidence_b.page == 2

    def test_detect_date_mismatch(self):
        detector = CrossDocumentConflictDetector()
        extracted = {
            "filing_date": ExtractedField(
                field="filing_date",
                value={"iso_date": "2024-01-15", "original_string": "15/01/2024"},
                found=True,
                citations=[Citation(doc_id="d1", page=1, snippet="दायर करने की तिथि: 15/01/2024", lang=Language.hi)],
            )
        }
        pages = {
            1: "दायर करने की तिथि: 15/01/2024",
            2: "आदेश पत्रक: वाद संस्थित दिनांक: 20/02/2024",
        }
        report = detector.detect_conflicts(pages, extracted, doc_id="d1")

        date_conflicts = [c for c in report.conflicts if c.conflict_type == ConflictType.date_mismatch]
        assert len(date_conflicts) == 1
        assert date_conflicts[0].evidence_b.page == 2

    def test_detect_status_contradiction(self):
        detector = CrossDocumentConflictDetector()
        extracted = {
            "current_status": ExtractedField(
                field="current_status",
                value="rejected",
                found=True,
                citations=[Citation(doc_id="d1", page=2, snippet="आवेदन खारिज किया जाता है।", lang=Language.hi)],
            )
        }
        pages = {
            1: "पत्रावली पेश हुई। अंतरिम स्थगन आदेश प्रभावी रहेगा।",
            2: "अंतिम आदेश: आवेदन खारिज किया जाता है।",
        }
        report = detector.detect_conflicts(pages, extracted, doc_id="d1")

        status_conflicts = [c for c in report.conflicts if c.conflict_type == ConflictType.status_contradiction]
        assert len(status_conflicts) == 1
        assert status_conflicts[0].evidence_b.page == 1
