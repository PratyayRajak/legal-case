"""Tests for Declarative Rules Logic Evaluator."""
from __future__ import annotations

from rules.evaluator import evaluate_condition


class TestRulesEvaluator:
    def test_equals_and_not_equals(self):
        fields = {"court_level": "district", "case_type": "revenue"}
        assert evaluate_condition({"field": "court_level", "equals": "district"}, fields) is True
        assert evaluate_condition({"field": "court_level", "equals": "high"}, fields) is False
        assert evaluate_condition({"field": "court_level", "not_equals": "high"}, fields) is True

    def test_in_and_not_in(self):
        fields = {"current_status": "rejected"}
        assert evaluate_condition({"field": "current_status", "in": ["rejected", "dismissed"]}, fields) is True
        assert evaluate_condition({"field": "current_status", "not_in": ["allowed", "stayed"]}, fields) is True

    def test_exists_and_is_null(self):
        fields = {"prior_court_history": [{"court": "district"}], "missing_field": None}
        assert evaluate_condition({"field": "prior_court_history", "exists": True}, fields) is True
        assert evaluate_condition({"field": "missing_field", "is_null": True}, fields) is True

    def test_compound_and_or_not(self):
        fields = {"court_level": "district", "current_status": "rejected"}
        cond = {
            "and": [
                {"field": "court_level", "equals": "district"},
                {"field": "current_status", "equals": "rejected"},
            ]
        }
        assert evaluate_condition(cond, fields) is True

        cond_or = {
            "or": [
                {"field": "court_level", "equals": "high"},
                {"field": "current_status", "equals": "rejected"},
            ]
        }
        assert evaluate_condition(cond_or, fields) is True

    def test_implication_if_require(self):
        # Case 1: 'if' condition triggers, 'require' holds -> True
        fields1 = {"court_level": "high", "prior_orders": [{"court": "district"}]}
        cond = {
            "if": {"field": "court_level", "equals": "high"},
            "require": {"field": "prior_orders", "exists": True},
        }
        assert evaluate_condition(cond, fields1) is True

        # Case 2: 'if' condition triggers, 'require' FAILS -> False
        fields2 = {"court_level": "high", "prior_orders": None}
        assert evaluate_condition(cond, fields2) is False

        # Case 3: 'if' condition does not trigger -> True (requirement not enforced)
        fields3 = {"court_level": "district", "prior_orders": None}
        assert evaluate_condition(cond, fields3) is True
