"""Evaluation metrics for Indian Court Brief Engine.

Always sliced by:
- Language: 'hi', 'en', 'mixed'
- Scan quality: 'digital', 'good', 'poor'
- Case type: 'revenue', etc.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from eval.normalize import fuzzy_name_match


@dataclass
class FieldEvalResult:
    doc_id: str
    field_name: str
    language: str
    scan_quality: str
    case_type: str
    expected_value: Any
    predicted_value: Any
    expected_found: bool
    predicted_found: bool
    is_match: bool
    is_hallucination: bool  # Predicted found=True when expected found=False
    citation_valid: bool
    confidence: float
    needs_review: bool


@dataclass
class RuleEvalResult:
    doc_id: str
    rule_id: str
    language: str
    expected_result: str  # pass, fail, cannot_evaluate
    predicted_result: str
    is_match: bool


@dataclass
class CrossLanguageEvalResult:
    pair_id: str  # Same case identifier in Hindi and English
    field_name: str
    hi_value: Any
    en_value: Any
    consistent: bool


@dataclass
class EvaluationReport:
    total_docs: int
    overall_field_accuracy: float
    hallucination_rate: float
    citation_accuracy: float
    cross_language_consistency: float
    by_language: dict[str, dict[str, float]]
    by_scan_quality: dict[str, dict[str, float]]
    rule_metrics: dict[str, dict[str, float]]
    failures: list[dict[str, Any]]
    metadata: dict[str, str] = field(default_factory=dict)


def evaluate_field(
    expected: dict[str, Any],
    predicted: dict[str, Any],
    field_name: str,
    ocr_text_by_page: dict[int, str] | None = None,
) -> tuple[bool, bool, bool]:
    """Evaluate a single extracted field against expected ground truth.

    Returns:
        (is_match, is_hallucination, citation_valid)
    """
    exp_found = expected.get("found", False)
    pred_found = predicted.get("found", False)
    exp_val = expected.get("value")
    pred_val = predicted.get("value")

    # Hallucination: model found something where none exists
    is_hallucination = pred_found and not exp_found

    # Citation validation: citation must exist on predicted page and snippet must be in OCR text
    citation_valid = True
    if pred_found:
        citations = predicted.get("citations", [])
        if not citations:
            citation_valid = False
        elif ocr_text_by_page:
            for cite in citations:
                page = cite.get("page")
                snippet = cite.get("snippet", "")
                page_text = ocr_text_by_page.get(page, "")
                if snippet:
                    import unicodedata
                    norm_snippet = " ".join(unicodedata.normalize("NFKC", snippet).split())
                    norm_page = " ".join(unicodedata.normalize("NFKC", page_text).split())
                    if norm_snippet not in norm_page:
                        citation_valid = False
                        break

    # Accuracy check
    if not exp_found and not pred_found:
        is_match = True
    elif exp_found != pred_found:
        is_match = False
    else:
        # Both found - compare values
        if "name" in field_name or field_name in ["petitioners", "respondents", "advocates"]:
            # Fuzzy / transliteration-aware match for names
            is_match = _compare_names(exp_val, pred_val)
        elif isinstance(exp_val, (int, float)) and isinstance(pred_val, (int, float)):
            is_match = exp_val == pred_val
        elif isinstance(exp_val, dict) and isinstance(pred_val, dict):
            # Nested comparisons (e.g. CanonicalDate, CaseNumber)
            is_match = _compare_dicts(exp_val, pred_val)
        elif isinstance(exp_val, list) and isinstance(pred_val, list):
            is_match = _compare_lists(exp_val, pred_val, field_name)
        else:
            is_match = str(exp_val).strip().lower() == str(pred_val).strip().lower()

    return is_match, is_hallucination, citation_valid


def _compare_names(exp_val: Any, pred_val: Any) -> bool:
    if isinstance(exp_val, str) and isinstance(pred_val, str):
        return fuzzy_name_match(exp_val, pred_val)
    if isinstance(exp_val, list) and isinstance(pred_val, list):
        if len(exp_val) != len(pred_val):
            return False
        # Each expected name should match at least one predicted name
        for exp in exp_val:
            exp_str = exp.get("original", "") if isinstance(exp, dict) else str(exp)
            matched = any(
                fuzzy_name_match(exp_str, p.get("original", "") if isinstance(p, dict) else str(p))
                for p in pred_val
            )
            if not matched:
                return False
        return True
    return False


def _compare_dicts(d1: dict[str, Any], d2: dict[str, Any]) -> bool:
    return all(not (k in d2 and str(d2[k]).lower() != str(v).lower()) for k, v in d1.items())


def _compare_lists(l1: list[Any], l2: list[Any], field_name: str) -> bool:
    if len(l1) != len(l2):
        return False
    return sorted(str(x) for x in l1) == sorted(str(x) for x in l2)


def compute_metrics(
    field_results: list[FieldEvalResult],
    rule_results: list[RuleEvalResult],
    cross_lang_results: list[CrossLanguageEvalResult],
    metadata: dict[str, str] | None = None,
) -> EvaluationReport:
    """Aggregate per-field and per-rule results into a comprehensive EvaluationReport."""
    if not field_results:
        return EvaluationReport(
            total_docs=0,
            overall_field_accuracy=0.0,
            hallucination_rate=0.0,
            citation_accuracy=0.0,
            cross_language_consistency=0.0,
            by_language={},
            by_scan_quality={},
            rule_metrics={},
            failures=[],
            metadata=metadata or {},
        )

    doc_ids = {r.doc_id for r in field_results}
    total_fields = len(field_results)
    correct_fields = sum(1 for r in field_results if r.is_match)
    hallucinations = sum(1 for r in field_results if r.is_hallucination)
    cited_fields = [r for r in field_results if r.predicted_found]
    valid_citations = sum(1 for r in cited_fields if r.citation_valid)

    overall_acc = correct_fields / max(1, total_fields)
    hallucination_rate = hallucinations / max(1, total_fields)
    citation_acc = valid_citations / max(1, len(cited_fields))

    # Cross-language consistency
    if cross_lang_results:
        cl_matches = sum(1 for r in cross_lang_results if r.consistent)
        cl_consistency = cl_matches / len(cross_lang_results)
    else:
        cl_consistency = 1.0

    # Slices by language
    by_lang: dict[str, dict[str, float]] = {}
    lang_groups: dict[str, list[FieldEvalResult]] = defaultdict(list)
    for r in field_results:
        lang_groups[r.language].append(r)

    for lang, items in lang_groups.items():
        tot = len(items)
        cor = sum(1 for x in items if x.is_match)
        hal = sum(1 for x in items if x.is_hallucination)
        by_lang[lang] = {
            "accuracy": cor / max(1, tot),
            "hallucination_rate": hal / max(1, tot),
            "count": float(tot),
        }

    # Slices by scan quality
    by_quality: dict[str, dict[str, float]] = {}
    qual_groups: dict[str, list[FieldEvalResult]] = defaultdict(list)
    for r in field_results:
        qual_groups[r.scan_quality].append(r)

    for q, items in qual_groups.items():
        tot = len(items)
        cor = sum(1 for x in items if x.is_match)
        by_quality[q] = {
            "accuracy": cor / max(1, tot),
            "count": float(tot),
        }

    # Rule metrics
    rule_metrics: dict[str, dict[str, float]] = {}
    rule_groups: dict[str, list[RuleEvalResult]] = defaultdict(list)
    for rule_res in rule_results:
        rule_groups[rule_res.rule_id].append(rule_res)

    for rid, rule_items in rule_groups.items():
        tot = len(rule_items)
        cor = sum(1 for x in rule_items if x.is_match)
        rule_metrics[rid] = {
            "precision": cor / max(1, tot),
            "total_evals": float(tot),
        }

    # Failures list
    failures = [
        {
            "doc_id": r.doc_id,
            "field": r.field_name,
            "language": r.language,
            "expected": r.expected_value,
            "predicted": r.predicted_value,
            "is_hallucination": r.is_hallucination,
            "citation_valid": r.citation_valid,
            "confidence": r.confidence,
        }
        for r in field_results
        if not r.is_match or not r.citation_valid
    ]

    return EvaluationReport(
        total_docs=len(doc_ids),
        overall_field_accuracy=overall_acc,
        hallucination_rate=hallucination_rate,
        citation_accuracy=citation_acc,
        cross_language_consistency=cl_consistency,
        by_language=by_lang,
        by_scan_quality=by_quality,
        rule_metrics=rule_metrics,
        failures=failures,
        metadata=metadata or {},
    )
