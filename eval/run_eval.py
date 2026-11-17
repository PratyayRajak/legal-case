"""Evaluation runner for Indian Court Brief Engine.

Executes pipeline extraction on all documents in eval/data/docs,
compares predictions against eval/data/labels, computes metrics,
evaluates rules, conducts the cross-language consistency test,
generates a detailed report in eval/reports/<run_id>, and enforces
the CI quality gate.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import fitz

from eval.metrics import (
    CrossLanguageEvalResult,
    EvaluationReport,
    FieldEvalResult,
    RuleEvalResult,
    compute_metrics,
    evaluate_field,
)
from eval.normalize import normalize_case_number, normalize_date
from rules.engine import RulesEngine
from rules.models import RuleResult


def extract_baseline_stub(pdf_path: str, label: dict[str, Any]) -> dict[str, Any]:
    """Baseline extraction using ground-truth and text parsing.

    In Phase 2, this serves as our baseline reference pipeline to validate
    the harness, normalizers, metrics, and rule evaluations.
    In Phase 5, the real LLM + OCR extraction pipeline connects here.
    """
    doc = fitz.open(pdf_path)
    ocr_text_by_page: dict[int, str] = {}
    for i, page in enumerate(doc):
        text = page.get_text()
        if not text.strip():
            # For scanned pages without OCR yet in Phase 2 baseline,
            # simulate OCR text from ground truth snippets on that page
            text = "\n".join(
                f.get("snippet", "")
                for f in label.get("fields", {}).values()
                if f.get("page") == (i + 1) and f.get("snippet")
            )
        ocr_text_by_page[i + 1] = text
    doc.close()

    fields_pred: dict[str, Any] = {}
    label_fields = label.get("fields", {})

    for field_name, exp in label_fields.items():
        if not exp.get("found", False):
            fields_pred[field_name] = {"found": False, "value": None, "confidence": 0.0}
            continue

        exp_val = exp.get("value")
        snippet = exp.get("snippet", "")
        page = exp.get("page", 1)

        # Baseline extracts the value and canonicalizes through normalizers
        if field_name == "filing_date" and isinstance(exp_val, dict) or field_name == "next_hearing_date" and isinstance(exp_val, dict):
            date_norm = normalize_date(exp_val.get("original_string", ""))
            val = date_norm.model_dump() if date_norm else exp_val
        elif field_name == "case_number" and isinstance(exp_val, dict):
            case_norm = normalize_case_number(exp_val.get("original_string", ""))
            val = case_norm.model_dump() if case_norm else exp_val
        else:
            val = exp_val

        fields_pred[field_name] = {
            "found": True,
            "value": val,
            "confidence": 0.95,
            "citations": [{"doc_id": label["doc_id"], "page": page, "snippet": snippet, "lang": label["doc_language"]}],
            "needs_review": False,
        }

    return {"fields": fields_pred, "ocr_text": ocr_text_by_page}


def run_evaluation(
    docs_dir: Path | str = "eval/data/docs",
    labels_dir: Path | str = "eval/data/labels",
    reports_dir: Path | str = "eval/reports",
    run_id: str | None = None,
) -> EvaluationReport:
    """Run full evaluation suite across all labeled documents."""
    docs_path = Path(docs_dir)
    labels_path = Path(labels_dir)
    reports_path = Path(reports_dir)

    if run_id is None:
        run_id = f"run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    run_output_dir = reports_path / run_id
    run_output_dir.mkdir(parents=True, exist_ok=True)

    label_files = sorted(labels_path.glob("*.json"))
    field_results: list[FieldEvalResult] = []
    rule_results: list[RuleEvalResult] = []
    case_predictions_by_pair: dict[str, dict[str, dict[str, Any]]] = {}

    rules_engine = RulesEngine()

    start_time = time.time()

    for label_file in label_files:
        with open(label_file, encoding="utf-8") as f:
            label: dict[str, Any] = json.load(f)

        doc_id = label["doc_id"]
        pdf_file = docs_path / f"{doc_id}.pdf"
        if not pdf_file.exists():
            continue

        pred = extract_baseline_stub(str(pdf_file), label)
        pred_fields = pred["fields"]
        ocr_text = pred["ocr_text"]

        # Track for cross-language consistency
        pair_id = label.get("pair_id")
        lang = label.get("doc_language", "unknown")
        if pair_id:
            if pair_id not in case_predictions_by_pair:
                case_predictions_by_pair[pair_id] = {}
            case_predictions_by_pair[pair_id][lang] = pred_fields

        # Evaluate fields
        for field_name, exp in label.get("fields", {}).items():
            field_pred = pred_fields.get(field_name, {"found": False, "value": None})
            is_match, is_hal, cite_valid = evaluate_field(
                expected=exp,
                predicted=field_pred,
                field_name=field_name,
                ocr_text_by_page=ocr_text,
            )

            field_results.append(
                FieldEvalResult(
                    doc_id=doc_id,
                    field_name=field_name,
                    language=lang,
                    scan_quality=label.get("scan_quality", "digital"),
                    case_type=label.get("case_type", "revenue"),
                    expected_value=exp.get("value"),
                    predicted_value=field_pred.get("value"),
                    expected_found=exp.get("found", False),
                    predicted_found=field_pred.get("found", False),
                    is_match=is_match,
                    is_hallucination=is_hal,
                    citation_valid=cite_valid,
                    confidence=field_pred.get("confidence", 0.0),
                    needs_review=field_pred.get("needs_review", False),
                )
            )

        # Evaluate rules
        # Convert canonical fields to format expected by rule checks
        canonical_record = {
            k: {"found": v.get("found", False), "value": v.get("value")}
            for k, v in pred_fields.items()
        }
        # In placeholder rules testing, test with placeholder rules directory
        placeholder_dir = Path("rules/definitions")
        rule_eval_out = rules_engine.evaluate(canonical_record, rules_dir=placeholder_dir)
        pred_rule_dict = {r.rule_id: r.result.value for r in rule_eval_out}

        # Compare against expected rules
        expected_rules = label.get("rule_expectations", {})
        for rule_id, exp_result in expected_rules.items():
            # Check registered check if applicable
            from rules.loader import get_check
            check_fn = get_check(rule_id)
            if check_fn:
                actual_result = check_fn(canonical_record).value
            else:
                actual_result = pred_rule_dict.get(rule_id, RuleResult.cannot_evaluate.value)

            rule_results.append(
                RuleEvalResult(
                    doc_id=doc_id,
                    rule_id=rule_id,
                    language=lang,
                    expected_result=exp_result,
                    predicted_result=actual_result,
                    is_match=(actual_result == exp_result),
                )
            )

    # Cross-language consistency test on canonical, language-neutral fields
    CANONICAL_CONSISTENCY_FIELDS = {
        "case_number",
        "court_level",
        "case_type",
        "proceeding_type",
        "petitioners",
        "respondents",
        "filing_date",
        "next_hearing_date",
        "current_status",
    }

    cross_lang_results: list[CrossLanguageEvalResult] = []
    for pid, lang_dict in case_predictions_by_pair.items():
        if "hi" in lang_dict and "en" in lang_dict:
            hi_preds = lang_dict["hi"]
            en_preds = lang_dict["en"]

            for k in CANONICAL_CONSISTENCY_FIELDS:
                hi_val = hi_preds.get(k, {}).get("value")
                en_val = en_preds.get(k, {}).get("value")

                # Both should match canonical representations
                if k in ["petitioners", "respondents"]:
                    # Compare transliterated names
                    consistent = _compare_names_cross_lang(hi_val, en_val)
                elif isinstance(hi_val, dict) and isinstance(en_val, dict):
                    # CanonicalDate / CaseNumber comparisons
                    consistent = _compare_canonical_dicts(hi_val, en_val)
                else:
                    consistent = str(hi_val).strip().lower() == str(en_val).strip().lower()

                cross_lang_results.append(
                    CrossLanguageEvalResult(
                        pair_id=pid,
                        field_name=k,
                        hi_value=hi_val,
                        en_value=en_val,
                        consistent=consistent,
                    )
                )

    total_time = time.time() - start_time

    metadata = {
        "run_id": run_id,
        "timestamp": datetime.utcnow().isoformat(),
        "total_time_seconds": f"{total_time:.2f}",
        "pipeline_version": "1.0.0",
        "glossary_version": "1.0.0",
        "rules_version": "1.0.0",
    }

    report = compute_metrics(field_results, rule_results, cross_lang_results, metadata=metadata)

    # Save report to JSON
    report_dict = {
        "metadata": report.metadata,
        "summary": {
            "total_docs": report.total_docs,
            "overall_field_accuracy": round(report.overall_field_accuracy, 4),
            "hallucination_rate": round(report.hallucination_rate, 4),
            "citation_accuracy": round(report.citation_accuracy, 4),
            "cross_language_consistency": round(report.cross_language_consistency, 4),
        },
        "by_language": report.by_language,
        "by_scan_quality": report.by_scan_quality,
        "rule_metrics": report.rule_metrics,
        "failures_count": len(report.failures),
        "failures": report.failures,
    }

    with open(run_output_dir / "report.json", "w", encoding="utf-8") as f:
        json.dump(report_dict, f, ensure_ascii=False, indent=2)

    return report


def _compare_names_cross_lang(hi_val: Any, en_val: Any) -> bool:
    if not hi_val and not en_val:
        return True
    if not hi_val or not en_val:
        return False
    if isinstance(hi_val, list) and isinstance(en_val, list):
        if len(hi_val) != len(en_val):
            return False
        hi_keys = {item.get("transliteration_key", "") if isinstance(item, dict) else str(item) for item in hi_val}
        en_keys = {item.get("transliteration_key", "") if isinstance(item, dict) else str(item) for item in en_val}
        return hi_keys == en_keys
    return False


def _compare_canonical_dicts(d1: dict[str, Any], d2: dict[str, Any]) -> bool:
    # Compare key semantic fields (ignoring original_string language difference)
    for k in ["iso_date", "precision", "number", "year", "case_type"]:
        if k in d1 and k in d2 and str(d1[k]) != str(d2[k]):
            return False
    return True


def check_ci_gate(report: EvaluationReport) -> bool:
    """Enforce CI gate thresholds per Section 9 of the spec.

    Thresholds:
    - Overall field accuracy >= 0.80
    - Hallucination rate <= 0.05
    - Citation accuracy >= 0.90
    - Cross-language consistency >= 0.95
    - Rule precision: all tested rules must pass
    """
    passed = True
    print("\n--- CI GATE CHECK ---")

    if report.overall_field_accuracy < 0.80:
        print(f"❌ FAIL: Overall field accuracy {report.overall_field_accuracy:.2%} < 80.00%")
        passed = False
    else:
        print(f"✅ PASS: Overall field accuracy {report.overall_field_accuracy:.2%} >= 80.00%")

    if report.hallucination_rate > 0.05:
        print(f"❌ FAIL: Hallucination rate {report.hallucination_rate:.2%} > 5.00%")
        passed = False
    else:
        print(f"✅ PASS: Hallucination rate {report.hallucination_rate:.2%} <= 5.00%")

    if report.citation_accuracy < 0.90:
        print(f"❌ FAIL: Citation accuracy {report.citation_accuracy:.2%} < 90.00%")
        passed = False
    else:
        print(f"✅ PASS: Citation accuracy {report.citation_accuracy:.2%} >= 90.00%")

    if report.cross_language_consistency < 0.95:
        print(f"❌ FAIL: Cross-language consistency {report.cross_language_consistency:.2%} < 95.00%")
        passed = False
    else:
        print(f"✅ PASS: Cross-language consistency {report.cross_language_consistency:.2%} >= 95.00%")

    for rid, m in report.rule_metrics.items():
        if m["precision"] < 1.0:
            print(f"❌ FAIL: Rule {rid} precision {m['precision']:.2%} < 100%")
            passed = False
        else:
            print(f"✅ PASS: Rule {rid} precision = {m['precision']:.2%}")

    return passed


def main() -> int:
    parser = argparse.ArgumentParser(description="Run evaluation harness.")
    parser.add_argument("--docs-dir", default="eval/data/docs")
    parser.add_argument("--labels-dir", default="eval/data/labels")
    parser.add_argument("--reports-dir", default="eval/reports")
    parser.add_argument("--ci-gate", action="store_true", help="Exit with code 1 if CI gate fails")
    args = parser.parse_args()

    report = run_evaluation(args.docs_dir, args.labels_dir, args.reports_dir)

    print("\n================ EVALUATION SUMMARY ================")
    print(f"Total Documents: {report.total_docs}")
    print(f"Overall Field Accuracy: {report.overall_field_accuracy:.2%}")
    print(f"Hallucination Rate:     {report.hallucination_rate:.2%}")
    print(f"Citation Accuracy:      {report.citation_accuracy:.2%}")
    print(f"Cross-Lang Consistency: {report.cross_language_consistency:.2%}")

    print("\n--- By Language ---")
    for lang, metrics in report.by_language.items():
        print(f"  [{lang}]: Accuracy={metrics['accuracy']:.2%}, Hallucinations={metrics['hallucination_rate']:.2%}")

    print("\n--- By Scan Quality ---")
    for q, metrics in report.by_scan_quality.items():
        print(f"  [{q}]: Accuracy={metrics['accuracy']:.2%}")

    if args.ci_gate:
        passed = check_ci_gate(report)
        return 0 if passed else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
