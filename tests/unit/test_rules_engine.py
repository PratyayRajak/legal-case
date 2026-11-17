"""Tests for the rules engine."""
from __future__ import annotations

from rules.engine import RulesEngine
from rules.models import ReviewInfo, Rule, RuleResult, RuleSeverity, RuleStatus


class TestRulesEngine:
    def test_no_active_rules_returns_empty(self):
        engine = RulesEngine()
        # All placeholder rules are DRAFT, so nothing runs
        results = engine.evaluate({"case_type": {"value": "revenue", "found": True}})
        assert results == []

    def test_cannot_evaluate_on_missing_fields(self):
        """Engine returns cannot_evaluate when required fields are missing."""
        rule = Rule(
            id="TEST_R001",
            text_hi="परीक्षण नियम",
            source="test",
            effective_from="2020-01-01",
            applies_to={"case_types": ["revenue"]},
            requires_fields=["court_level"],
            logic={},
            severity=RuleSeverity.blocking,
            message_hi="विफल",
            message_en="Failed",
            status=RuleStatus.ACTIVE,
            review=ReviewInfo(verified_by="expert"),
        )
        engine = RulesEngine()
        result = engine._evaluate_rule(
            rule, {"case_type": {"value": "revenue", "found": True}}
        )
        assert result.result == RuleResult.cannot_evaluate
        assert "court_level" in result.missing_fields
