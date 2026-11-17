"""PLACEHOLDER rule check functions.

These are example check functions for the pipeline to work end-to-end.
Real rules will come from the Hindi rule set provided by the legal expert.
PLACEHOLDER rules are DRAFT status and never run in production.
"""
from __future__ import annotations

from typing import Any

from rules.loader import register_check
from rules.models import RuleResult


@register_check("R001_PLACEHOLDER")
def check_court_hierarchy(fields: dict[str, Any]) -> RuleResult:
    """PLACEHOLDER: Court hierarchy must be followed (district → high → supreme).
    
    Real rule text in Hindi will be provided by legal expert.
    """
    prior_history = fields.get("prior_court_history", {})
    court_level = fields.get("court_level", {})
    
    if not isinstance(prior_history, dict) or not prior_history.get("found"):
        return RuleResult.cannot_evaluate
    if not isinstance(court_level, dict) or not court_level.get("found"):
        return RuleResult.cannot_evaluate
    
    # PLACEHOLDER logic — real logic from rule YAML
    return RuleResult.pass_


@register_check("R002_PLACEHOLDER")
def check_limitation_period(fields: dict[str, Any]) -> RuleResult:
    """PLACEHOLDER: Check that the case was filed within the limitation period."""
    filing_date = fields.get("filing_date", {})
    
    if not isinstance(filing_date, dict) or not filing_date.get("found"):
        return RuleResult.cannot_evaluate
    
    # PLACEHOLDER — real limitation periods from legal expert
    return RuleResult.pass_


@register_check("R003_PLACEHOLDER")
def check_jurisdiction(fields: dict[str, Any]) -> RuleResult:
    """PLACEHOLDER: Check that the court has jurisdiction over the case."""
    court_level = fields.get("court_level", {})
    case_type = fields.get("case_type", {})
    
    if not isinstance(court_level, dict) or not court_level.get("found"):
        return RuleResult.cannot_evaluate
    if not isinstance(case_type, dict) or not case_type.get("found"):
        return RuleResult.cannot_evaluate
    
    return RuleResult.pass_


@register_check("R004_PLACEHOLDER")
def check_required_document_present(fields: dict[str, Any]) -> RuleResult:
    """PLACEHOLDER: Check that required documents are present in the file."""
    docs_list = fields.get("documents_list", {})
    
    if not isinstance(docs_list, dict) or not docs_list.get("found"):
        return RuleResult.cannot_evaluate
    
    return RuleResult.pass_


@register_check("R005_PLACEHOLDER")
def check_date_consistency(fields: dict[str, Any]) -> RuleResult:
    """PLACEHOLDER: Check that filing date is before hearing dates."""
    filing_date = fields.get("filing_date", {})
    next_hearing = fields.get("next_hearing_date", {})
    
    if not isinstance(filing_date, dict) or not filing_date.get("found"):
        return RuleResult.cannot_evaluate
    if not isinstance(next_hearing, dict) or not next_hearing.get("found"):
        return RuleResult.cannot_evaluate
    
    # PLACEHOLDER — real date comparison in Phase 7
    return RuleResult.pass_
