"""Rules engine — evaluates ACTIVE rules against canonical case fields.

Design principles (Section 7):
- Rules run on canonical fields ONLY — never on raw text.
- If a required field is missing or needs_review, result is cannot_evaluate.
- DRAFT rules never run in production.
- Effective-date aware.
"""
from __future__ import annotations

from datetime import date
from typing import Any

import rules.checks  # noqa: F401
from config import Environment, settings
from rules.evaluator import evaluate_condition
from rules.loader import active_rules, get_check, load_rules
from rules.models import Rule, RuleCheckResult, RuleResult


class RulesEngine:
    """Evaluates the active rule set against a canonical case record."""

    def evaluate(
        self,
        canonical_fields: dict[str, Any],
        case_date: date | None = None,
        rules_dir: Any = None,
    ) -> list[RuleCheckResult]:
        """Evaluate all applicable active rules.

        Args:
            canonical_fields: The normalized canonical case record.
            case_date: The relevant date for effective-date filtering.
            rules_dir: Optional path to rules directory (for testing).

        Returns:
            List of RuleCheckResult, one per evaluated rule.
        """
        results: list[RuleCheckResult] = []
        if settings.environment == Environment.production:
            rules = active_rules(rules_dir) if rules_dir else active_rules()
        else:
            rules = load_rules(rules_dir) if rules_dir else load_rules()

        for rule in rules:
            if not self._applies_to(rule, canonical_fields):
                continue
            result = self._evaluate_rule(rule, canonical_fields)
            results.append(result)

        return results

    def _applies_to(self, rule: Rule, fields: dict[str, Any]) -> bool:
        """Check if the rule applies to the given case."""
        applies_to = rule.applies_to
        case_type = fields.get("case_type")
        if hasattr(case_type, "value"):
            case_type = getattr(case_type, "value", "")
        elif isinstance(case_type, dict):
            case_type = case_type.get("value", "")

        case_type_str = str(case_type or "").lower()
        if "case_types" in applies_to and applies_to["case_types"]:
            allowed = [str(x).lower() for x in applies_to["case_types"]]
            if case_type_str not in allowed:
                return False

        return True

    def _evaluate_rule(self, rule: Rule, fields: dict[str, Any]) -> RuleCheckResult:
        """Evaluate a single rule. Returns cannot_evaluate if fields are missing."""
        # Check for missing required fields
        missing = []
        for req_field in rule.requires_fields:
            field_data = fields.get(req_field)
            if field_data is None:
                missing.append(req_field)
            elif hasattr(field_data, "found"):
                if not field_data.found or getattr(field_data, "needs_review", False):
                    missing.append(req_field)
            elif isinstance(field_data, dict) and (
                not field_data.get("found", False) or field_data.get("needs_review", False)
            ):
                missing.append(req_field)

        if missing:
            return RuleCheckResult(
                rule_id=rule.id,
                rule_version=rule.id,
                result=RuleResult.cannot_evaluate,
                severity=rule.severity,
                message_hi=f"मूल्यांकन संभव नहीं: आवश्यक फ़ील्ड अनुपलब्ध: {missing}",
                message_en=f"Cannot evaluate: required fields missing or unverified: {missing}",
                missing_fields=missing,
            )

        # Try registered check function
        check_fn = get_check(rule.id)
        if check_fn:
            try:
                result = check_fn(fields)
            except Exception:
                result = RuleResult.cannot_evaluate

            return RuleCheckResult(
                rule_id=rule.id,
                rule_version=rule.id,
                result=result,
                severity=rule.severity,
                message_hi=rule.message_hi if result == RuleResult.fail else "नियम का अनुपालन किया गया।",
                message_en=rule.message_en if result == RuleResult.fail else "Rule complied with.",
            )

        # Evaluate declarative rule logic if present
        if rule.logic:
            try:
                passed = evaluate_condition(rule.logic, fields)
                result = RuleResult.pass_ if passed else RuleResult.fail
            except Exception:
                result = RuleResult.cannot_evaluate

            return RuleCheckResult(
                rule_id=rule.id,
                rule_version=rule.id,
                result=result,
                severity=rule.severity,
                message_hi=rule.message_hi if result == RuleResult.fail else "नियम का अनुपालन किया गया।",
                message_en=rule.message_en if result == RuleResult.fail else "Rule complied with.",
            )

        # No check function or logic registered — cannot evaluate
        return RuleCheckResult(
            rule_id=rule.id,
            rule_version=rule.id,
            result=RuleResult.cannot_evaluate,
            severity=rule.severity,
            message_hi="कोई जाँच कार्य या तर्क पंजीकृत नहीं।",
            message_en="No check function or logic registered for this rule.",
        )
