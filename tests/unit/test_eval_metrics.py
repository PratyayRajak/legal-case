"""Tests for evaluation metrics and harness."""
from __future__ import annotations

from eval.metrics import (
    CrossLanguageEvalResult,
    FieldEvalResult,
    RuleEvalResult,
    compute_metrics,
    evaluate_field,
)
from eval.run_eval import check_ci_gate


class TestFieldEvaluation:
    def test_exact_match(self):
        exp = {"found": True, "value": "revenue", "page": 1, "snippet": "revenue"}
        pred = {"found": True, "value": "revenue", "citations": [{"page": 1, "snippet": "revenue"}]}
        ocr = {1: "revenue matter before court"}
        is_match, is_hal, cite_valid = evaluate_field(exp, pred, "case_type", ocr)
        assert is_match is True
        assert is_hal is False
        assert cite_valid is True

    def test_hallucination_detected(self):
        exp = {"found": False, "value": None}
        pred = {"found": True, "value": "invented value", "citations": []}
        is_match, is_hal, _ = evaluate_field(exp, pred, "next_hearing_date")
        assert is_match is False
        assert is_hal is True

    def test_citation_missing_in_ocr_text(self):
        exp = {"found": True, "value": "2024-01-01", "page": 1, "snippet": "01/01/2024"}
        pred = {"found": True, "value": "2024-01-01", "citations": [{"page": 1, "snippet": "nonexistent text"}]}
        ocr = {1: "court proceeding order sheet text"}
        _, _, cite_valid = evaluate_field(exp, pred, "filing_date", ocr)
        assert cite_valid is False

    def test_not_found_correctness(self):
        exp = {"found": False, "value": None}
        pred = {"found": False, "value": None}
        is_match, is_hal, _ = evaluate_field(exp, pred, "rejection_reason")
        assert is_match is True
        assert is_hal is False


class TestComputeMetrics:
    def test_aggregation_and_slices(self):
        f_results = [
            FieldEvalResult(
                doc_id="D1",
                field_name="status",
                language="hi",
                scan_quality="digital",
                case_type="revenue",
                expected_value="rejected",
                predicted_value="rejected",
                expected_found=True,
                predicted_found=True,
                is_match=True,
                is_hallucination=False,
                citation_valid=True,
                confidence=0.9,
                needs_review=False,
            ),
            FieldEvalResult(
                doc_id="D2",
                field_name="status",
                language="en",
                scan_quality="poor",
                case_type="revenue",
                expected_value="pending",
                predicted_value="rejected",
                expected_found=True,
                predicted_found=True,
                is_match=False,
                is_hallucination=False,
                citation_valid=True,
                confidence=0.5,
                needs_review=True,
            ),
        ]
        report = compute_metrics(f_results, [], [])
        assert report.total_docs == 2
        assert report.overall_field_accuracy == 0.5
        assert report.hallucination_rate == 0.0
        assert report.by_language["hi"]["accuracy"] == 1.0
        assert report.by_language["en"]["accuracy"] == 0.0
        assert report.by_scan_quality["digital"]["accuracy"] == 1.0
        assert report.by_scan_quality["poor"]["accuracy"] == 0.0

    def test_ci_gate_pass(self):
        f_results = [
            FieldEvalResult(
                doc_id="D1",
                field_name="status",
                language="en",
                scan_quality="digital",
                case_type="revenue",
                expected_value="pending",
                predicted_value="pending",
                expected_found=True,
                predicted_found=True,
                is_match=True,
                is_hallucination=False,
                citation_valid=True,
                confidence=0.95,
                needs_review=False,
            )
        ]
        r_results = [
            RuleEvalResult(
                doc_id="D1",
                rule_id="R001",
                language="en",
                expected_result="pass",
                predicted_result="pass",
                is_match=True,
            )
        ]
        cl_results = [
            CrossLanguageEvalResult(
                pair_id="P1",
                field_name="status",
                hi_value="pending",
                en_value="pending",
                consistent=True,
            )
        ]
        report = compute_metrics(f_results, r_results, cl_results)
        assert check_ci_gate(report) is True
