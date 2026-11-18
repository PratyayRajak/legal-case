"""Tests for Revenue Case Brief Assembler."""
from __future__ import annotations

from app.schemas.canonical import ExtractedField
from pipeline.assembler import assemble_revenue_brief


class TestBriefAssembler:
    def test_assemble_brief_with_disclaimer_and_provenance(self):
        fields = {
            "case_number": ExtractedField(
                field="case_number",
                value={"number": "104", "year": 2024},
                found=True,
                confidence=0.95,
                citations=[],
                needs_review=True,  # No citation flags needs_review
            )
        }
        brief = assemble_revenue_brief(doc_id="test_doc", extracted_fields=fields)

        assert brief.doc_id == "test_doc"
        assert brief.pipeline_version == "0.1.0"
        assert brief.disclaimer == "AI-assisted summary. Verify against the source document."
        assert brief.case_number.found is True

        # Check default empty fields
        assert brief.filing_date.found is False
        assert brief.court_name.found is False
        assert brief.petitioners.found is False
