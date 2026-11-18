"""Tests for Canonical Normalizer and Glossary Concept Mapping."""
from __future__ import annotations

from app.schemas.canonical import (
    CaseStatus,
    Citation,
    CourtLevel,
    ExtractedField,
    Language,
    ProceedingType,
)
from pipeline.normalizer import CanonicalNormalizer


class TestCanonicalNormalizer:
    def test_map_to_concept_surface_forms(self):
        normalizer = CanonicalNormalizer()
        # Hindi surface form
        cref_hi = normalizer.map_to_concept("खारिज", Language.hi)
        assert cref_hi is not None
        assert cref_hi.concept_id == "STATUS_REJECTED"

        # English surface form
        cref_en = normalizer.map_to_concept("dismissed", Language.en)
        assert cref_en is not None
        assert cref_en.concept_id == "STATUS_REJECTED"

    def test_normalize_status_enums(self):
        normalizer = CanonicalNormalizer()
        status, flag, _ = normalizer.normalize_status("खारिज किया गया")
        assert status == CaseStatus.rejected
        assert flag is False

        status, flag, _ = normalizer.normalize_status("allowed")
        assert status == CaseStatus.allowed
        assert flag is False

    def test_normalize_court_level(self):
        normalizer = CanonicalNormalizer()
        cl, flag, _ = normalizer.normalize_court_level("न्यायालय उप-जिलाधिकारी")
        assert cl == CourtLevel.district
        assert flag is False

        cl, flag, _ = normalizer.normalize_court_level("High Court of Judicature")
        assert cl == CourtLevel.high
        assert flag is False

    def test_normalize_proceeding_type(self):
        normalizer = CanonicalNormalizer()
        proc, flag, _ = normalizer.normalize_proceeding_type("नामान्तरण प्रार्थना पत्र")
        assert proc == ProceedingType.mutation
        assert flag is False

        proc, flag, _ = normalizer.normalize_proceeding_type("विभाजन वाद")
        assert proc == ProceedingType.partition
        assert flag is False

    def test_normalize_unmappable_flags_needs_review(self):
        normalizer = CanonicalNormalizer()
        fld = ExtractedField(
            field="current_status",
            value="विचित्र आदेश",
            found=True,
            confidence=0.8,
            citations=[Citation(doc_id="d1", page=1, snippet="विचित्र आदेश", lang=Language.hi)],
        )
        norm_fld = normalizer.normalize_field(fld)
        assert norm_fld.needs_review is True
        assert len(norm_fld.review_reasons) > 0
        assert "Unrecognized case status" in norm_fld.review_reasons[0]
