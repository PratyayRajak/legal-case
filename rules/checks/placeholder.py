"""PLACEHOLDER rule check functions.

These are pure, typed, unit-tested check functions for the placeholder rules.
Real rules will come from the Hindi rule set provided by the legal expert.
"""
from __future__ import annotations

from typing import Any

from rules.loader import register_check
from rules.models import RuleResult


@register_check("R001_PLACEHOLDER")
def check_court_hierarchy(fields: dict[str, Any]) -> RuleResult:
    """PLACEHOLDER: Court hierarchy check.

    If court_level is high court, prior_court_history must contain district court.
    """
    court_level = fields.get("court_level", {})
    prior_history = fields.get("prior_court_history", {})

    if not isinstance(court_level, dict) or not court_level.get("found"):
        return RuleResult.cannot_evaluate

    cl_val = court_level.get("value")
    if cl_val != "high":
        # Rule only applies when filing in High Court
        return RuleResult.cannot_evaluate

    if not isinstance(prior_history, dict) or not prior_history.get("found"):
        return RuleResult.cannot_evaluate

    history = prior_history.get("value", [])
    if isinstance(history, list) and any(
        h.get("court_level") == "district" if isinstance(h, dict) else False for h in history
    ):
        return RuleResult.pass_
    return RuleResult.fail


@register_check("R002_PLACEHOLDER")
def check_limitation_period(fields: dict[str, Any]) -> RuleResult:
    """PLACEHOLDER: Check that filing date is valid and present."""
    filing_date = fields.get("filing_date", {})
    if not isinstance(filing_date, dict) or not filing_date.get("found"):
        return RuleResult.cannot_evaluate

    val = filing_date.get("value")
    if not val:
        return RuleResult.cannot_evaluate
    # Limitation placeholder check: filing date is present and valid
    return RuleResult.pass_


@register_check("R003_PLACEHOLDER")
def check_jurisdiction(fields: dict[str, Any]) -> RuleResult:
    """PLACEHOLDER: Check court level is appropriate for revenue matters."""
    court_level = fields.get("court_level", {})
    case_type = fields.get("case_type", {})

    if not isinstance(court_level, dict) or not court_level.get("found"):
        return RuleResult.cannot_evaluate
    if not isinstance(case_type, dict) or not case_type.get("found"):
        return RuleResult.cannot_evaluate

    cl_val = court_level.get("value")
    ct_val = case_type.get("value")

    # Revenue court initial matters lie in district / sub-divisional courts
    if ct_val == "revenue":
        if cl_val in ["district", "revenue_board"]:
            return RuleResult.pass_
        return RuleResult.cannot_evaluate

    return RuleResult.pass_


@register_check("R004_PLACEHOLDER")
def check_required_document_present(fields: dict[str, Any]) -> RuleResult:
    """PLACEHOLDER: Check that required documents list is present."""
    docs_list = fields.get("documents_list", {})
    if not isinstance(docs_list, dict) or not docs_list.get("found"):
        return RuleResult.cannot_evaluate

    val = docs_list.get("value")
    if isinstance(val, list) and len(val) > 0:
        return RuleResult.pass_
    return RuleResult.fail


@register_check("R005_PLACEHOLDER")
def check_date_consistency(fields: dict[str, Any]) -> RuleResult:
    """PLACEHOLDER: Check that filing_date is before next_hearing_date."""
    filing_date = fields.get("filing_date", {})
    next_hearing = fields.get("next_hearing_date", {})

    if not isinstance(filing_date, dict) or not filing_date.get("found"):
        return RuleResult.cannot_evaluate
    if not isinstance(next_hearing, dict) or not next_hearing.get("found"):
        return RuleResult.cannot_evaluate

    f_val = filing_date.get("value")
    h_val = next_hearing.get("value")
    if not f_val or not h_val:
        return RuleResult.cannot_evaluate

    f_iso = f_val.get("iso_date") if isinstance(f_val, dict) else str(f_val)
    h_iso = h_val.get("iso_date") if isinstance(h_val, dict) else str(h_val)

    if f_iso and h_iso:
        if f_iso > h_iso:
            return RuleResult.fail
        return RuleResult.pass_

    return RuleResult.cannot_evaluate
