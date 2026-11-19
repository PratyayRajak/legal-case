"""Tests for IL-TUR adapter and judicial brief export service."""
from __future__ import annotations

from typing import Any

from app.services.export_service import BriefExportService
from eval.iltur_adapter import ILTURBenchmarkAdapter
from pipeline.assembler import assemble_revenue_brief


class TestILTUREval:
    def test_iltur_adapter_loads_reference_samples(self) -> None:
        adapter = ILTURBenchmarkAdapter()
        samples = adapter.load_samples()
        assert len(samples) >= 2
        assert any(s.language == "hi" for s in samples)
        assert any(s.language == "en" for s in samples)

    def test_iltur_evaluation_metrics(self) -> None:
        adapter = ILTURBenchmarkAdapter()

        class MockExtractor:
            def extract_from_text(self, text: str, doc_id: str, page: int) -> dict[str, Any]:
                return {
                    "fields": {
                        "petitioners": {"found": True, "value": "Petitioner"},
                        "respondents": {"found": True, "value": "Respondent"},
                    }
                }

        results = adapter.evaluate_extractor_on_iltur(MockExtractor())
        assert results["total_benchmark_samples"] >= 2
        assert results["entity_accuracy"] >= 80.0
        assert results["hallucination_rate"] <= 5.0
        assert results["benchmark_passed"] == 1.0


class TestBriefExport:
    def test_brief_export_pdf_and_text(self) -> None:
        brief = assemble_revenue_brief(doc_id="REV_EXPORT_TEST", extracted_fields={})
        text_out = BriefExportService.export_as_text_summary(brief)
        assert "COURT BRIEF ENGINE" in text_out
        assert "LEGAL DISCLAIMER" in text_out

        pdf_bytes = BriefExportService.export_as_pdf_bytes(brief)
        assert len(pdf_bytes) > 500
        assert pdf_bytes.startswith(b"%PDF")
